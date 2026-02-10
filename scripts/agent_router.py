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
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import AsyncGenerator, Optional

from scripts.agent_tools import get_agent_tools
from scripts.ai_engine import AIEngine, AIEngineError
from scripts.executor_utils import (
    execute_function as _public_execute_function,
    serialize_result as _public_serialize_result,
)
from scripts.settings import Settings, SettingsManager
from scripts.task_models import TaskDefinition
from scripts.task_registry import TaskRegistry
from scripts.verb_utils import detect_verb_type

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
    task_definition: Optional[TaskDefinition] = None

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        result = {
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "requires_confirmation": self.requires_confirmation,
        }
        if self.task_definition:
            result["task_name"] = self.task_definition.name
        return result


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
        description="Network discovery, analysis, diagnostics, health checks, bandwidth usage, client monitoring, traffic analysis",
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
            "discover_clients",
            "discover_traffic",
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
            "which device is consuming more bandwidth",
            "show top bandwidth consumers",
            "show network traffic",
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
    registry["discover_clients"] = discovery.discover_clients
    registry["discover_traffic"] = discovery.discover_traffic
    registry["discover_vpn_topology"] = discovery.discover_vpn_topology
    registry["discover_content_filtering"] = discovery.discover_content_filtering
    registry["discover_ips_settings"] = discovery.discover_ips_settings
    registry["discover_amp_settings"] = discovery.discover_amp_settings
    registry["discover_traffic_shaping"] = discovery.discover_traffic_shaping
    # Epic 9: Alerts, Firmware, Observability
    registry["discover_alerts"] = discovery.discover_alerts
    registry["discover_webhooks"] = discovery.discover_webhooks
    registry["discover_firmware_status"] = discovery.discover_firmware_status
    registry["discover_snmp_config"] = discovery.discover_snmp_config
    registry["discover_syslog_config"] = discovery.discover_syslog_config
    registry["discover_recent_changes"] = discovery.discover_recent_changes
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
    registry["detect_catalyst_mode"] = config.detect_catalyst_mode
    registry["sgt_preflight_check"] = config.sgt_preflight_check
    registry["check_license"] = config.check_license
    registry["backup_current_state"] = config.backup_current_state
    # Epic 8: Security & Monitoring
    registry["backup_vpn_config"] = config.backup_vpn_config
    registry["configure_s2s_vpn"] = config.configure_s2s_vpn
    registry["add_vpn_peer"] = config.add_vpn_peer
    registry["configure_content_filter"] = config.configure_content_filter
    registry["add_blocked_url"] = config.add_blocked_url
    registry["configure_ips"] = config.configure_ips
    registry["set_ips_mode"] = config.set_ips_mode
    registry["configure_amp"] = config.configure_amp
    registry["configure_traffic_shaping"] = config.configure_traffic_shaping
    registry["set_bandwidth_limit"] = config.set_bandwidth_limit
    # Epic 9: Alerts, Firmware, SNMP, Syslog
    registry["configure_alerts"] = config.configure_alerts
    registry["create_webhook_endpoint"] = config.create_webhook_endpoint
    registry["schedule_firmware_upgrade"] = config.schedule_firmware_upgrade
    registry["cancel_firmware_upgrade"] = config.cancel_firmware_upgrade
    registry["configure_snmp"] = config.configure_snmp
    registry["configure_syslog"] = config.configure_syslog
    # Epic 10: Advanced Switching, Wireless & Platform - Discovery
    registry["discover_switch_routing"] = discovery.discover_switch_routing
    registry["discover_stp_config"] = discovery.discover_stp_config
    registry["discover_nat_rules"] = discovery.discover_nat_rules
    registry["discover_port_forwarding"] = discovery.discover_port_forwarding
    registry["discover_rf_profiles"] = discovery.discover_rf_profiles
    registry["discover_wireless_health"] = discovery.discover_wireless_health
    registry["discover_qos_config"] = discovery.discover_qos_config
    registry["discover_org_admins"] = discovery.discover_org_admins
    registry["discover_inventory"] = discovery.discover_inventory

    # ===== Phase 2 - Wave 1 =====
    # Story 11.5: Policy Objects
    registry["discover_policy_objects"] = discovery.discover_policy_objects
    registry["manage_policy_object"] = config.manage_policy_object
    # Story 11.2: Client VPN
    registry["discover_client_vpn"] = discovery.discover_client_vpn
    registry["configure_client_vpn"] = config.configure_client_vpn
    # Story 12.3: Port Schedules
    registry["discover_port_schedules"] = discovery.discover_port_schedules
    registry["configure_port_schedule"] = config.configure_port_schedule
    # Story 13.5: LLDP/CDP
    registry["discover_lldp_cdp"] = discovery.discover_lldp_cdp
    # Story 13.7: NetFlow
    registry["discover_netflow_config"] = discovery.discover_netflow_config
    registry["configure_netflow"] = config.configure_netflow
    # Story 13.8: PoE Status
    registry["discover_poe_status"] = discovery.discover_poe_status

    # ===== Phase 2 - Wave 2 =====
    # Story 11.1: SD-WAN
    registry["discover_sdwan_config"] = discovery.discover_sdwan_config
    registry["configure_sdwan_policy"] = config.configure_sdwan_policy
    registry["set_uplink_preference"] = config.set_uplink_preference
    # Story 11.4: Config Templates
    registry["discover_templates"] = discovery.discover_templates
    registry["manage_template"] = config.manage_template
    # Story 12.2: Access Policies
    registry["discover_access_policies"] = discovery.discover_access_policies
    registry["configure_access_policy"] = config.configure_access_policy
    # Story 12.5: Air Marshal
    registry["discover_rogue_aps"] = discovery.discover_rogue_aps
    # Story 12.6: SSID Firewall
    registry["discover_ssid_firewall"] = discovery.discover_ssid_firewall
    registry["configure_ssid_firewall"] = config.configure_ssid_firewall
    # Story 12.7: Splash Pages
    registry["discover_splash_config"] = discovery.discover_splash_config
    registry["configure_splash_page"] = config.configure_splash_page

    # ===== Phase 2 - Wave 3 =====
    # Story 11.3: Adaptive Policy / SGT
    registry["discover_adaptive_policies"] = discovery.discover_adaptive_policies
    registry["configure_adaptive_policy"] = config.configure_adaptive_policy
    # Story 12.1: Switch Stacks
    registry["discover_switch_stacks"] = discovery.discover_switch_stacks
    registry["manage_switch_stack"] = config.manage_switch_stack
    # Story 12.4: HA / Warm Spare
    registry["discover_ha_config"] = discovery.discover_ha_config
    registry["configure_warm_spare"] = config.configure_warm_spare
    registry["trigger_failover"] = config.trigger_failover
    # Story 13.1: Camera Analytics & Snapshots
    registry["discover_camera_analytics"] = discovery.discover_camera_analytics
    # Story 13.2: Sensor Readings & Alerts
    registry["discover_sensors"] = discovery.discover_sensors
    registry["configure_sensor_alert"] = config.configure_sensor_alert

    # ===== Phase 2 - Wave 4 =====
    # Story 13.3: Floor Plans
    registry["discover_floor_plans"] = discovery.discover_floor_plans
    registry["create_floor_plan"] = lambda network_id, name, **kw: get_client().create_floor_plan(network_id, name, **kw)
    registry["update_floor_plan"] = lambda network_id, floor_plan_id, **kw: get_client().update_floor_plan(network_id, floor_plan_id, **kw)
    registry["delete_floor_plan"] = lambda network_id, floor_plan_id: get_client().delete_floor_plan(network_id, floor_plan_id)
    # Story 13.4: Group Policies
    registry["discover_group_policies"] = discovery.discover_group_policies
    registry["configure_group_policy"] = config.configure_group_policy
    # Story 13.6: Packet Capture
    registry["create_packet_capture"] = lambda device_serial, **kw: get_client().create_packet_capture(device_serial, **kw)
    registry["get_packet_capture_status"] = lambda device_serial, capture_id: get_client().get_packet_capture_status(device_serial, capture_id)
    # Story 13.9: Static Routes (Appliance)
    registry["discover_static_routes"] = discovery.discover_static_routes
    registry["manage_static_route"] = config.manage_static_route

    # Epic 10: Advanced Switching, Wireless & Platform - Config
    registry["configure_switch_l3_interface"] = config.configure_switch_l3_interface
    registry["add_switch_static_route"] = config.add_switch_static_route
    registry["configure_stp"] = config.configure_stp
    registry["configure_1to1_nat"] = config.configure_1to1_nat
    registry["configure_port_forwarding"] = config.configure_port_forwarding
    registry["configure_rf_profile"] = config.configure_rf_profile
    registry["configure_qos"] = config.configure_qos
    registry["manage_admin"] = config.manage_admin
    # Epic 10: Direct API actions (reboot, blink, claim, release)
    from scripts.api import get_client
    registry["reboot_device"] = lambda serial: get_client().reboot_device(serial)
    registry["blink_leds"] = lambda serial, duration=20: get_client().blink_leds(serial, duration)
    registry["claim_device"] = lambda serials: get_client().claim_device(serials=serials)
    registry["release_device"] = lambda serials: get_client().release_device(serials=serials)
    registry["get_wireless_connection_stats"] = lambda network_id, **kw: get_client().get_wireless_connection_stats(network_id, **kw)
    registry["get_wireless_latency_stats"] = lambda network_id, **kw: get_client().get_wireless_latency_stats(network_id, **kw)
    registry["get_wireless_signal_quality"] = lambda network_id, **kw: get_client().get_wireless_signal_quality(network_id, **kw)
    registry["get_channel_utilization"] = lambda network_id, **kw: get_client().get_channel_utilization(network_id, **kw)
    registry["get_failed_connections"] = lambda network_id, **kw: get_client().get_failed_connections(network_id, **kw)

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

# Module-level TaskRegistry (lazy-loaded from tasks/ directory)
_task_registry = TaskRegistry()

def _get_task_registry() -> TaskRegistry:
    """Get the module-level task registry, loading tasks on first access.

    Note: load_tasks() performs synchronous disk I/O (YAML parsing).
    This is acceptable as a one-time cold-start cost; results are cached
    in the module-level ``_task_registry`` for all subsequent calls.
    """
    if not _task_registry.tasks:
        tasks_dir = Path(__file__).parent.parent / "tasks"
        if tasks_dir.exists():
            _task_registry.load_tasks(tasks_dir)
            logger.info(f"Loaded {len(_task_registry.tasks)} modular tasks from {tasks_dir}")
    return _task_registry


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

    # Verb-aware pre-pass (Story 7.7 / HIGH-1)
    has_action, has_analysis = detect_verb_type(message_lower)

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

    # Apply verb-based score adjustments (only between analyst/specialist)
    # Workflow-creator is unaffected — its keywords are highly specific
    verb_boost = 0.0
    wf_score = match_scores.get("workflow-creator", 0)
    analyst_score = match_scores.get("network-analyst", 0)
    specialist_score = match_scores.get("meraki-specialist", 0)

    # Only apply verb boost when workflow-creator has no matches
    # (workflow keywords are highly specific, verb boost shouldn't override them)
    if wf_score == 0:
        if has_action and not has_analysis:
            # Pure action intent → boost specialist, penalize analyst
            match_scores["meraki-specialist"] = specialist_score + 2.0
            match_scores["network-analyst"] = max(analyst_score - 1.0, 0)
            verb_boost = 2.0
        elif has_analysis and not has_action:
            # Pure analysis intent → boost analyst, penalize specialist
            match_scores["network-analyst"] = analyst_score + 2.0
            match_scores["meraki-specialist"] = max(specialist_score - 1.0, 0)
            verb_boost = 2.0

    # Get best match
    if match_scores:
        best_agent = max(match_scores, key=match_scores.get)
        best_score = match_scores[best_agent]

        if best_score > 0:
            # Calculate confidence (normalize to 0.6-0.95 range)
            confidence = min(0.6 + (best_score * 0.1), 0.95)
            reasoning = f"Pattern match (score: {best_score:.1f})"
            if verb_boost > 0:
                reasoning += f", verb-aware boost applied"

            return ClassificationResult(
                agent_name=best_agent,
                confidence=confidence,
                reasoning=reasoning,
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
    message: str,
    ai_engine: Optional[AIEngine] = None,
    settings: Optional[Settings] = None,
) -> ClassificationResult:
    """
    Classify user intent to route to appropriate agent.

    Pipeline:
    1. Check explicit prefix (@analyst, @specialist, @workflow)
    2. Task registry match WITH verb check (if use_modular_tasks enabled)
    3. Quick regex classify (if confidence > 0.9, return)
    4. LLM classify (if AI engine available)
    5. If final confidence < 0.7, set requires_confirmation

    Args:
        message: User message to classify
        ai_engine: Optional AIEngine instance
        settings: Optional Settings instance for feature flags

    Returns:
        ClassificationResult with agent selection and confidence
    """
    # Try quick classify first (handles explicit prefix at confidence=1.0)
    quick_result = _quick_classify(message)

    # If explicit prefix (confidence=1.0), use it immediately
    if quick_result and quick_result.confidence == 1.0:
        logger.info(
            f"Explicit prefix: {quick_result.agent_name}"
        )
        return quick_result

    # Task registry check (after prefix, before regex/LLM) — Story 7.3 / HIGH-1
    use_modular = True
    if settings:
        use_modular = getattr(settings, "use_modular_tasks", True)

    if use_modular:
        registry = _get_task_registry()
        task_match = registry.find_matching_task(message)
        if task_match:
            logger.info(f"Routing to task_executor: {task_match.name}")
            return ClassificationResult(
                agent_name=task_match.agent,
                confidence=1.0,
                reasoning=f"Matched task: {task_match.name}",
                requires_confirmation=False,
                task_definition=task_match,
            )

    # If high confidence regex match, use it
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
    logger.info("Routing to legacy LLM flow for agent: network-analyst")
    return ClassificationResult(
        agent_name="network-analyst",
        confidence=0.3,
        reasoning="Default fallback",
        requires_confirmation=True,
    )


# ==================== Function Execution ====================


def _serialize_result(obj):
    """Delegate to executor_utils.serialize_result (CRITICAL-1)."""
    return _public_serialize_result(obj)


async def _execute_function(
    func_name: str, args: dict
) -> tuple[bool, Optional[dict], Optional[str]]:
    """Delegate to executor_utils.execute_function (CRITICAL-1)."""
    return await _public_execute_function(func_name, args, FUNCTION_REGISTRY)


# ==================== Message Processing ====================


async def process_message(
    message: str,
    session_id: str = "default",
    ai_engine: Optional[AIEngine] = None,
    session_context: Optional[list] = None,
    settings: Optional[Settings] = None,
) -> AsyncGenerator[dict, None]:
    """
    Process user message and route to appropriate agent.

    Pipeline:
    1. Classify intent → select agent (includes task registry check)
    2a. If task_definition matched → delegate to task_executor
    2b. Otherwise → legacy LLM flow (build prompt, chat_completion, tool_calls)

    Args:
        message: User message to process
        session_id: Session identifier for context
        ai_engine: Optional AIEngine instance
        session_context: Optional list of previous messages (last 20)
        settings: Optional Settings for feature flags

    Yields:
        Dict with type=stream|data|error and content
    """
    # Classify intent (includes task registry check if use_modular_tasks enabled)
    classification = await classify_intent(message, ai_engine, settings=settings)

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

    # === Task Executor Path (Story 7.3) ===
    if classification.task_definition:
        from scripts.task_executor import TaskExecutor

        executor = TaskExecutor(
            ai_engine=ai_engine,
            settings=settings,
            function_registry=FUNCTION_REGISTRY,
        )

        session_ctx = {"session_id": session_id}
        client_name = None
        if settings:
            client_name = getattr(settings, "meraki_profile", None)

        try:
            async for chunk in executor.execute(
                task_def=classification.task_definition,
                user_message=message,
                session_context=session_ctx,
                client_name=client_name,
            ):
                yield chunk
        except Exception as exc:
            logger.exception(f"Task executor error for {classification.task_definition.name}")
            yield {
                "type": "error",
                "error": "Task execution failed. Check server logs for details.",
            }
        return

    # === Legacy LLM Flow ===
    logger.info(f"Routing to legacy LLM flow for agent: {classification.agent_name}")

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

    # Call AI Engine with tool-call conversation loop.
    # After executing tools, feed results back to the LLM so it can
    # generate a natural language interpretation instead of raw JSON.
    MAX_TOOL_ROUNDS = 5  # prevent infinite loops

    try:
        for _round in range(MAX_TOOL_ROUNDS):
            response_stream = await ai_engine.chat_completion(
                messages=messages,
                tools=tools if tools else None,
                stream=True,
                session_id=session_id,
            )

            # Accumulate streaming tool call chunks before executing
            pending_tool_calls: dict[int, dict] = {}
            assistant_content = ""

            async for chunk in response_stream:
                if not hasattr(chunk, "choices") or len(chunk.choices) == 0:
                    continue

                choice = chunk.choices[0]

                # Stream delta content
                if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    content = choice.delta.content
                    if content:
                        assistant_content += content
                        yield {
                            "type": "stream",
                            "chunk": content,
                            "agent": agent.name,
                        }

                # Accumulate tool call chunks (name, arguments, id)
                if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        idx = tool_call.index if hasattr(tool_call, "index") else 0
                        if idx not in pending_tool_calls:
                            pending_tool_calls[idx] = {
                                "id": None, "name": None, "arguments": "",
                            }
                        if hasattr(tool_call, "id") and tool_call.id:
                            pending_tool_calls[idx]["id"] = tool_call.id
                        if hasattr(tool_call, "function"):
                            if tool_call.function.name:
                                pending_tool_calls[idx]["name"] = tool_call.function.name
                            if tool_call.function.arguments:
                                pending_tool_calls[idx]["arguments"] += tool_call.function.arguments

            # No tool calls — LLM responded with text, we're done
            if not pending_tool_calls:
                break

            # Execute all accumulated tool calls
            tool_results: list[dict] = []
            assistant_tool_calls: list[dict] = []

            for _idx, tc in sorted(pending_tool_calls.items()):
                func_name = tc["name"]
                if not func_name:
                    continue

                tc_id = tc["id"] or f"call_{func_name}_{_idx}"

                try:
                    func_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    func_args = {}

                # Build the assistant tool_calls entry for the conversation
                assistant_tool_calls.append({
                    "id": tc_id,
                    "type": "function",
                    "function": {"name": func_name, "arguments": tc["arguments"] or "{}"},
                })

                success, result, error = await _execute_function(
                    func_name, func_args
                )

                result_content = _serialize_result(result) if success else json.dumps({"error": error})

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_content if isinstance(result_content, str) else json.dumps(result_content),
                })

                # Yield tool execution status to frontend
                if success:
                    yield {
                        "type": "tool_status",
                        "function": func_name,
                        "status": "ok",
                        "agent": agent.name,
                    }
                else:
                    yield {
                        "type": "function_error",
                        "function": func_name,
                        "error": error,
                        "agent": agent.name,
                    }

            # Append assistant message with tool calls + tool results to conversation
            messages.append({
                "role": "assistant",
                "content": assistant_content or None,
                "tool_calls": assistant_tool_calls,
            })
            messages.extend(tool_results)

            # Loop continues — LLM will see tool results and generate NL response

    except Exception as exc:
        logger.exception("Error in process_message")
        yield {
            "type": "error",
            "error": "Processing failed. Check server logs for details.",
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
