"""
Agent Router for CNL (Cisco Neural Language).

Routes natural language commands to appropriate agents using:
- Quick regex-based classification (fast path)
- LLM-based classification via AIEngine (fallback)
- Explicit prefix routing (@analyst, @specialist, @workflow)

Executes agent functions via asyncio.to_thread() for sync module integration.
"""

import asyncio
import dataclasses
import inspect
import json
import logging
import re
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Optional

from scripts.agent_tools import get_agent_tools
from scripts.ai_engine import AIEngine, AIEngineError
from scripts.settings import Settings, SettingsManager

logger = logging.getLogger(__name__)

# ==================== Data Classes ====================


@dataclass
class AgentDefinition:
    """Definition of an agent with its capabilities."""

    name: str
    description: str
    system_prompt: str
    functions: list[str]
    icon: str = "🤖"
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "functions": self.functions,
            "icon": self.icon,
        }


@dataclass
class ClassificationResult:
    """Result of intent classification."""

    agent_name: str
    confidence: float
    reasoning: str
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "requires_confirmation": self.requires_confirmation,
        }


# ==================== Agent Registry ====================


def _load_agent_prompt(agent_name: str) -> str:
    """
    Load agent system prompt from .claude/agents/{agent_name}.md.

    Args:
        agent_name: Name of the agent

    Returns:
        System prompt content or empty string if file not found
    """
    prompt_path = Path(".claude/agents") / f"{agent_name}.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        logger.warning(f"Agent prompt file not found: {prompt_path} ({exc})")
        return ""


# Agent definitions
AGENTS = {
    "network-analyst": AgentDefinition(
        name="network-analyst",
        description="Network discovery, analysis, diagnostics, health checks",
        system_prompt=_load_agent_prompt("network-analyst"),
        functions=[
            "full_discovery",
            "discover_networks",
            "discover_devices",
            "discover_ssids",
            "discover_vlans",
            "discover_firewall_rules",
            "discover_switch_ports",
            "discover_switch_acls",
            "find_issues",
            "generate_suggestions",
            "save_snapshot",
            "compare_snapshots",
        ],
        icon="🔍",
        examples=[
            "analyze the network",
            "discover all networks",
            "check device status",
            "find network issues",
        ],
    ),
    "meraki-specialist": AgentDefinition(
        name="meraki-specialist",
        description="Configure ACL, Firewall, SSID, VLAN, Switch ports, Camera settings",
        system_prompt=_load_agent_prompt("meraki-specialist"),
        functions=[
            "configure_ssid",
            "enable_ssid",
            "disable_ssid",
            "create_vlan",
            "update_vlan",
            "delete_vlan",
            "add_firewall_rule",
            "remove_firewall_rule",
            "add_switch_acl",
            "backup_config",
            "rollback_config",
        ],
        icon="⚙️",
        examples=[
            "create SSID for guests",
            "add firewall rule to block port 23",
            "configure VLAN 10",
            "block telnet on switch",
        ],
    ),
    "workflow-creator": AgentDefinition(
        name="workflow-creator",
        description="Create automation workflows in Cisco/SecureX format",
        system_prompt=_load_agent_prompt("workflow-creator"),
        functions=[
            "create_device_offline_handler",
            "create_firmware_compliance_check",
            "create_scheduled_report",
            "create_security_alert_handler",
            "save_workflow",
            "list_workflows",
        ],
        icon="🔄",
        examples=[
            "create workflow for offline devices",
            "automate firmware compliance",
            "schedule weekly reports",
        ],
    ),
}


# ==================== Function Registry ====================


def _build_function_registry() -> dict:
    """
    Build function registry mapping function names to callables.

    Returns:
        Dict of function_name -> callable
    """
    registry = {}

    # Import modules
    try:
        from scripts import discovery, config, workflow, report
    except ImportError as exc:
        logger.error(f"Failed to import modules: {exc}")
        return registry

    # Discovery functions
    registry["full_discovery"] = discovery.full_discovery
    registry["discover_networks"] = discovery.discover_networks
    registry["discover_devices"] = discovery.discover_devices
    registry["discover_ssids"] = discovery.discover_ssids
    registry["discover_vlans"] = discovery.discover_vlans
    registry["discover_firewall_rules"] = discovery.discover_firewall_rules
    registry["discover_switch_ports"] = discovery.discover_switch_ports
    registry["discover_switch_acls"] = discovery.discover_switch_acls
    registry["find_issues"] = discovery.find_issues
    registry["generate_suggestions"] = discovery.generate_suggestions
    registry["save_snapshot"] = discovery.save_snapshot
    registry["compare_snapshots"] = discovery.compare_snapshots

    # Config functions
    registry["configure_ssid"] = config.configure_ssid
    registry["enable_ssid"] = config.enable_ssid
    registry["disable_ssid"] = config.disable_ssid
    registry["create_vlan"] = config.create_vlan
    registry["update_vlan"] = config.update_vlan
    registry["delete_vlan"] = config.delete_vlan
    registry["add_firewall_rule"] = config.add_firewall_rule
    registry["remove_firewall_rule"] = config.remove_firewall_rule
    registry["add_switch_acl"] = config.add_switch_acl
    registry["backup_config"] = config.backup_config
    registry["rollback_config"] = config.rollback_config

    # Workflow functions
    registry["create_device_offline_handler"] = workflow.create_device_offline_handler
    registry["create_firmware_compliance_check"] = workflow.create_firmware_compliance_check
    registry["create_scheduled_report"] = workflow.create_scheduled_report
    registry["create_security_alert_handler"] = workflow.create_security_alert_handler
    registry["save_workflow"] = workflow.save_workflow
    registry["list_workflows"] = workflow.list_workflows

    # Report functions
    registry["generate_discovery_report"] = report.generate_discovery_report

    logger.info(f"Function registry built with {len(registry)} functions")
    return registry


FUNCTION_REGISTRY = _build_function_registry()


# ==================== Classification ====================


def _sanitize_input(text: str) -> str:
    """
    Sanitize NL input to prevent ReDoS attacks.

    Args:
        text: User input text

    Returns:
        Sanitized text (truncated, safe characters only)
    """
    # Limit length
    text = text[:500]

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    return text


def _quick_classify(message: str) -> Optional[ClassificationResult]:
    """
    Quick rule-based classification using regex patterns.

    Args:
        message: User message to classify

    Returns:
        ClassificationResult or None if no match
    """
    # Sanitize input
    message = _sanitize_input(message)
    message_lower = message.lower()

    # Check explicit prefix first
    if message_lower.startswith("@analyst") or message_lower.startswith("@network"):
        return ClassificationResult(
            agent_name="network-analyst",
            confidence=1.0,
            reasoning="Explicit prefix @analyst/@network",
            requires_confirmation=False,
        )

    if message_lower.startswith("@specialist") or message_lower.startswith("@config"):
        return ClassificationResult(
            agent_name="meraki-specialist",
            confidence=1.0,
            reasoning="Explicit prefix @specialist/@config",
            requires_confirmation=False,
        )

    if message_lower.startswith("@workflow") or message_lower.startswith("@automat"):
        return ClassificationResult(
            agent_name="workflow-creator",
            confidence=1.0,
            reasoning="Explicit prefix @workflow/@automat",
            requires_confirmation=False,
        )

    # Pattern-based matching with prioritization
    # Each agent has discovery patterns (what it does) and trigger keywords
    patterns = {
        "network-analyst": {
            "keywords": [
                r"\b(discover|scan|analyz\w*|diagnos\w*|health|status|offline|inventory|check|inspect|audit)\b",
                r"\b(network|device|issue|problem|find|show|list|give|what|how many|do we have)\b",
            ],
            "weight": 1.0,
        },
        "meraki-specialist": {
            "keywords": [
                r"\b(config\w*|ssid|vlan|firewall|acl|switch|port|camera|block|allow|deny|secure)\b",
                r"\b(create|add|update|modify|delete|remove|enable|disable|set|change|apply)\b",
            ],
            "weight": 1.2,  # Prioritize config actions
        },
        "workflow-creator": {
            "keywords": [
                r"\b(workflow|automat\w*|schedule|alert|notif\w*|trigger|template|remediat\w*|handler|compliance)\b",
            ],
            "weight": 1.5,  # Highly specific keywords
        },
    }

    # Count matches for each agent with weights
    match_scores = {}
    for agent_name, agent_config in patterns.items():
        score = 0.0
        matched_keywords = set()
        for pattern in agent_config["keywords"]:
            matches = re.findall(pattern, message_lower)
            if matches:
                # Add matched words to set to count unique keywords
                matched_keywords.update(matches)
                score += len(matches) * agent_config["weight"]
        match_scores[agent_name] = score

    # Get best match
    if match_scores:
        best_agent = max(match_scores, key=match_scores.get)
        best_score = match_scores[best_agent]

        if best_score > 0:
            # Calculate confidence (normalize to 0.6-0.95 range)
            confidence = min(0.6 + (best_score * 0.1), 0.95)

            return ClassificationResult(
                agent_name=best_agent,
                confidence=confidence,
                reasoning=f"Pattern match (score: {best_score:.1f})",
                requires_confirmation=confidence < 0.7,
            )

    # No match
    return None


async def _llm_classify(message: str, ai_engine: AIEngine) -> ClassificationResult:
    """
    LLM-based classification using AIEngine.classify().

    Args:
        message: User message to classify
        ai_engine: AIEngine instance

    Returns:
        ClassificationResult

    Raises:
        AIEngineError: If classification fails
    """
    # Build agent list for classification
    agents_list = [
        {"name": agent.name, "description": agent.description}
        for agent in AGENTS.values()
    ]

    try:
        result = await ai_engine.classify(message, agents_list, session_id="router")

        agent_name = result.get("agent", "network-analyst")
        confidence = result.get("confidence", 0.5)
        reasoning = result.get("reasoning", "LLM classification")

        return ClassificationResult(
            agent_name=agent_name,
            confidence=confidence,
            reasoning=reasoning,
            requires_confirmation=confidence < 0.7,
        )

    except (AIEngineError, Exception) as exc:
        logger.warning(f"LLM classification failed: {exc}")
        # Fallback to quick classify with lower confidence
        quick_result = _quick_classify(message)
        if quick_result:
            quick_result.confidence *= 0.8  # Reduce confidence
            quick_result.reasoning += " (LLM unavailable)"
            return quick_result

        # Ultimate fallback
        return ClassificationResult(
            agent_name="network-analyst",
            confidence=0.3,
            reasoning="Fallback to default (LLM unavailable)",
            requires_confirmation=True,
        )


async def classify_intent(
    message: str, ai_engine: Optional[AIEngine] = None
) -> ClassificationResult:
    """
    Classify user intent to route to appropriate agent.

    Pipeline:
    1. Check explicit prefix (@analyst, @specialist, @workflow)
    2. Quick regex classify (if confidence > 0.9, return)
    3. LLM classify (if AI engine available)
    4. If final confidence < 0.7, set requires_confirmation

    Args:
        message: User message to classify
        ai_engine: Optional AIEngine instance

    Returns:
        ClassificationResult with agent selection and confidence
    """
    # Try quick classify first
    quick_result = _quick_classify(message)

    # If explicit prefix or high confidence, use it
    if quick_result and quick_result.confidence >= 0.9:
        logger.info(
            f"Quick classify: {quick_result.agent_name} "
            f"(confidence: {quick_result.confidence:.2f})"
        )
        return quick_result

    # Try LLM classify if available
    if ai_engine:
        try:
            llm_result = await _llm_classify(message, ai_engine)
            logger.info(
                f"LLM classify: {llm_result.agent_name} "
                f"(confidence: {llm_result.confidence:.2f})"
            )
            return llm_result
        except Exception as exc:
            logger.warning(f"LLM classification error: {exc}")

    # Fallback to quick result or default
    if quick_result:
        logger.info(
            f"Fallback to quick classify: {quick_result.agent_name} "
            f"(confidence: {quick_result.confidence:.2f})"
        )
        return quick_result

    # Ultimate fallback
    logger.warning("No classification method succeeded, using default")
    return ClassificationResult(
        agent_name="network-analyst",
        confidence=0.3,
        reasoning="Default fallback",
        requires_confirmation=True,
    )


# ==================== Function Execution ====================


def _serialize_result(obj):
    """
    Recursively serialize a function return value to JSON-safe types.

    Handles dataclasses, Path, Enum, objects with to_dict(), and
    nested lists/dicts.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "to_dict"):
        return _serialize_result(obj.to_dict())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _serialize_result(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _serialize_result(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_result(item) for item in obj]
    return str(obj)


async def _execute_function(
    func_name: str, args: dict
) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Execute a function from the registry via asyncio.to_thread().

    Auto-injects ``client``, ``client_name``, and ``org_id`` when the
    target function accepts them and they are not already provided by
    the caller.

    Args:
        func_name: Name of the function to execute
        args: Arguments to pass to the function

    Returns:
        Tuple of (success: bool, result: dict, error: str)
    """
    # Lookup function
    func = FUNCTION_REGISTRY.get(func_name)
    if not func:
        error = f"Function '{func_name}' not found in registry"
        logger.error(error)
        return False, None, error

    try:
        sig = inspect.signature(func)
        params = sig.parameters

        # Auto-inject client if the function accepts it and it wasn't provided
        if "client" in params and "client" not in args:
            try:
                from scripts.api import get_client

                settings = SettingsManager.load()
                profile = settings.meraki_profile or "default"
                args["client"] = get_client(profile=profile)
            except Exception as exc:
                logger.warning(f"Could not auto-inject client: {exc}")

        # Auto-inject client_name from settings
        if "client_name" in params and "client_name" not in args:
            try:
                settings = SettingsManager.load()
                if settings.meraki_profile:
                    args["client_name"] = settings.meraki_profile
            except Exception as exc:
                logger.warning(f"Could not auto-inject client_name: {exc}")

        # Auto-inject org_id from client
        if "org_id" in params and "org_id" not in args:
            client = args.get("client")
            if client and hasattr(client, "org_id"):
                args["org_id"] = client.org_id

        # Execute via asyncio.to_thread() to avoid blocking
        logger.debug(f"Executing function: {func_name} with args: {list(args.keys())}")
        result = await asyncio.to_thread(func, **args)

        logger.info(f"Function {func_name} executed successfully")
        return True, {"result": _serialize_result(result)}, None

    except Exception as exc:
        error = f"Function {func_name} failed: {type(exc).__name__}: {exc}"
        logger.error(error)
        return False, None, error


# ==================== Message Processing ====================


async def process_message(
    message: str,
    session_id: str = "default",
    ai_engine: Optional[AIEngine] = None,
    session_context: Optional[list] = None,
) -> AsyncGenerator[dict, None]:
    """
    Process user message and route to appropriate agent.

    Pipeline:
    1. Classify intent → select agent
    2. Build prompt with agent system prompt + context
    3. Send to AI Engine with function-calling
    4. Execute function calls via FUNCTION_REGISTRY
    5. Yield streaming chunks and data

    Args:
        message: User message to process
        session_id: Session identifier for context
        ai_engine: Optional AIEngine instance
        session_context: Optional list of previous messages (last 20)

    Yields:
        Dict with type=stream|data|error and content
    """
    # Classify intent
    classification = await classify_intent(message, ai_engine)

    # Yield classification result
    yield {
        "type": "classification",
        "agent": classification.agent_name,
        "confidence": classification.confidence,
        "reasoning": classification.reasoning,
        "requires_confirmation": classification.requires_confirmation,
    }

    # If requires confirmation, wait for user response
    if classification.requires_confirmation:
        yield {
            "type": "confirmation_required",
            "agent": classification.agent_name,
            "message": f"Route to {classification.agent_name}? (confidence: {classification.confidence:.0%})",
        }
        # In real implementation, would await user response here
        # For now, we proceed

    # Get agent definition
    agent = AGENTS.get(classification.agent_name)
    if not agent:
        yield {
            "type": "error",
            "error": f"Agent '{classification.agent_name}' not found",
        }
        return

    # Build system prompt
    system_prompt = agent.system_prompt or f"You are {agent.name}. {agent.description}"

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]

    # Add session context (last 20 messages)
    if session_context:
        messages.extend(session_context[-20:])

    # Add current message
    messages.append({"role": "user", "content": message})

    # If no AI engine, return error
    if not ai_engine:
        yield {
            "type": "error",
            "error": "AI Engine not available",
        }
        return

    # Build tool definitions from agent_tools.py schemas
    try:
        tools = get_agent_tools(agent.name)
    except ValueError:
        tools = []

    # Call AI Engine with function-calling
    try:
        response_stream = await ai_engine.chat_completion(
            messages=messages,
            tools=tools if tools else None,
            stream=True,
            session_id=session_id,
        )

        # Stream response chunks
        async for chunk in response_stream:
            # Check for tool calls
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                choice = chunk.choices[0]

                # Stream delta content
                if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    content = choice.delta.content
                    if content:
                        yield {
                            "type": "stream",
                            "chunk": content,
                            "agent": agent.name,
                        }

                # Check for tool calls
                if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        if hasattr(tool_call, "function"):
                            func_name = tool_call.function.name
                            func_args_str = tool_call.function.arguments

                            try:
                                func_args = json.loads(func_args_str) if func_args_str else {}
                            except json.JSONDecodeError:
                                func_args = {}

                            # Execute function
                            success, result, error = await _execute_function(
                                func_name, func_args
                            )

                            if success:
                                yield {
                                    "type": "function_result",
                                    "function": func_name,
                                    "result": result,
                                    "agent": agent.name,
                                }
                            else:
                                yield {
                                    "type": "function_error",
                                    "function": func_name,
                                    "error": error,
                                    "agent": agent.name,
                                }

    except Exception as exc:
        logger.exception("Error in process_message")
        yield {
            "type": "error",
            "error": f"Processing failed: {type(exc).__name__}: {exc}",
        }


# ==================== Main ====================


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def test_classify():
        """Test classification with sample messages."""
        test_messages = [
            "analyze the network",
            "create a firewall rule to block port 23",
            "create a workflow for offline devices",
            "@analyst check network health",
            "configure VLAN 10 on switch",
        ]

        print("\n=== Testing Agent Router Classification ===\n")

        for msg in test_messages:
            print(f"Message: {msg}")
            result = await classify_intent(msg)
            print(f"  → Agent: {result.agent_name}")
            print(f"  → Confidence: {result.confidence:.2%}")
            print(f"  → Reasoning: {result.reasoning}")
            print(f"  → Needs Confirmation: {result.requires_confirmation}")
            print()

    # Run test
    try:
        asyncio.run(test_classify())
        print("\n=== Test completed successfully ===\n")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
