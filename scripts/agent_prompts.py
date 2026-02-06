"""
Agent system prompts and network context management.

Builds structured system prompts for each agent with:
- Base prompt from agent definition (.claude/agents/*.md)
- Current network context (org name, network count, device count)
- Tool usage instructions
- Safety guidelines
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ==================== Data Classes ====================


@dataclass
class NetworkContext:
    """Current network context for prompt injection."""

    org_name: str
    org_id: str
    network_count: int
    device_count: int
    profile_name: str
    timestamp: datetime


# ==================== Cache Management ====================

_CONTEXT_CACHE: dict[str, tuple[NetworkContext, datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _is_cache_valid(profile: str) -> bool:
    """
    Check if cached context is still valid.

    Args:
        profile: Profile name to check

    Returns:
        True if cache is valid, False otherwise
    """
    if profile not in _CONTEXT_CACHE:
        return False

    _, cached_time = _CONTEXT_CACHE[profile]
    age = datetime.now() - cached_time
    return age.total_seconds() < CACHE_TTL_SECONDS


def invalidate_context_cache(profile: Optional[str] = None) -> None:
    """
    Invalidate context cache for profile or all profiles.

    Args:
        profile: Profile to invalidate (None = all)
    """
    if profile:
        _CONTEXT_CACHE.pop(profile, None)
        logger.debug(f"Context cache invalidated for profile: {profile}")
    else:
        _CONTEXT_CACHE.clear()
        logger.debug("All context caches invalidated")


# ==================== Network Context ====================


def get_network_context(profile: str) -> NetworkContext:
    """
    Get current network context for a profile with caching.

    Caches for 5 minutes to avoid repeated API calls.
    Cache is invalidated on profile switch.

    Args:
        profile: Meraki profile name

    Returns:
        NetworkContext with current org/network/device info

    Raises:
        ValueError: If profile not found or API error
    """
    # Check cache
    if _is_cache_valid(profile):
        context, _ = _CONTEXT_CACHE[profile]
        logger.debug(f"Using cached context for profile: {profile}")
        return context

    # Import here to avoid circular dependency
    from scripts.api import get_client
    from scripts.discovery import discover_networks

    try:
        # Get client for profile
        client = get_client()

        # Get org info
        org_data = client.get_organization(client.org_id)
        org_name = org_data["name"]
        org_id = client.org_id

        # Get networks
        networks = discover_networks(org_id, client)
        network_count = len(networks)

        # Count devices across all networks
        device_count = 0
        for network in networks:
            try:
                devices = client.get_network_devices(network.id)
                device_count += len(devices)
            except Exception as e:
                logger.warning(f"Failed to count devices in network {network.id}: {e}")
                continue

        context = NetworkContext(
            org_name=org_name,
            org_id=org_id,
            network_count=network_count,
            device_count=device_count,
            profile_name=profile,
            timestamp=datetime.now(),
        )

        # Cache it
        _CONTEXT_CACHE[profile] = (context, datetime.now())
        logger.info(
            f"Network context cached for {profile}: "
            f"{org_name}, {network_count} networks, {device_count} devices"
        )

        return context

    except Exception as e:
        logger.error(f"Failed to get network context for {profile}: {e}")
        raise ValueError(f"Cannot get network context: {e}") from e


# ==================== Prompt Building ====================


def _sanitize_context_value(value: str) -> str:
    """
    Sanitize network context values to prevent prompt injection.

    Args:
        value: Raw value from network context

    Returns:
        Sanitized value safe for prompt injection
    """
    import re

    # Replace newlines and carriage returns with space FIRST
    sanitized = value.replace("\n", " ").replace("\r", " ")

    # Remove control characters (except spaces which we want to keep)
    sanitized = re.sub(r"[\x00-\x09\x0b-\x1f\x7f-\x9f]", "", sanitized)

    # Escape special characters that could break prompt format
    sanitized = sanitized.replace("\\", "\\\\")
    sanitized = sanitized.replace('"', '\\"')

    # Remove multiple spaces
    sanitized = re.sub(r' +', ' ', sanitized)

    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."

    return sanitized


def load_agent_base_prompt(agent_name: str) -> str:
    """
    Load base system prompt from agent definition file.

    Args:
        agent_name: Name of agent (network-analyst, meraki-specialist, workflow-creator)

    Returns:
        Base system prompt content

    Raises:
        FileNotFoundError: If agent definition not found
    """
    agent_file = Path(".claude/agents") / f"{agent_name}.md"

    if not agent_file.exists():
        logger.error(f"Agent definition not found: {agent_file}")
        raise FileNotFoundError(f"Agent definition not found: {agent_name}")

    try:
        content = agent_file.read_text(encoding="utf-8")
        logger.debug(f"Loaded base prompt for {agent_name} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"Failed to read agent definition {agent_file}: {e}")
        raise


def build_system_prompt(agent_name: str, context: NetworkContext) -> str:
    """
    Build complete system prompt for agent with network context.

    Combines:
    1. Base prompt from agent definition
    2. Network context injection
    3. Tool usage instructions
    4. Safety guidelines

    Args:
        agent_name: Name of agent
        context: Current network context

    Returns:
        Complete system prompt ready for LLM

    Raises:
        FileNotFoundError: If agent definition not found
    """
    # Load base prompt
    base_prompt = load_agent_base_prompt(agent_name)

    # Sanitize context values
    org_name = _sanitize_context_value(context.org_name)
    profile_name = _sanitize_context_value(context.profile_name)

    # Build context section
    context_section = f"""

## Current Network Context

You are currently managing the following Meraki organization:

- **Organization**: {org_name} (ID: {context.org_id})
- **Profile**: {profile_name}
- **Networks**: {context.network_count}
- **Devices**: {context.device_count}
- **Context Updated**: {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Use this context to provide accurate, relevant responses to the user.
"""

    # Tool instructions
    tool_instructions = """

## Tool Usage Instructions

You have access to specialized tools to interact with the Meraki Dashboard API.

**IMPORTANT**:
- Always use the provided tools to execute operations
- Explain what you're doing before executing
- Provide clear feedback after operations complete
- If a tool call fails, explain the error to the user

**Available Tools**:
- Discovery tools: For network analysis and diagnostics
- Configuration tools: For making network changes
- Workflow tools: For creating automation workflows
- Report tools: For generating documentation

**Workflow**:
1. Understand the user's request
2. Explain what you plan to do
3. Execute the appropriate tool(s)
4. Summarize the results
"""

    # Safety guidelines
    safety_section = f"""

## Safety Guidelines

{'**CRITICAL - Configuration Changes**:' if agent_name == 'meraki-specialist' else '**Important**:'}
- For configuration changes, ALWAYS:
  1. Explain the impact of the change
  2. Ask for user confirmation before executing
  3. Create a backup before modifying
  4. Verify the change after execution
- Never execute destructive operations without explicit confirmation
- If unsure, ask for clarification
- Provide rollback instructions if something goes wrong

"""

    # Combine all sections
    full_prompt = base_prompt + context_section + tool_instructions + safety_section

    logger.debug(f"Built system prompt for {agent_name} ({len(full_prompt)} chars)")

    return full_prompt


# ==================== Conversation History Management ====================


def trim_conversation_history(
    messages: list[dict], max_messages: int = 20
) -> list[dict]:
    """
    Trim conversation history to last N messages.

    Preserves system message (first) and last N user/assistant messages.
    Includes tool call results in the trimmed history.

    Args:
        messages: Full message history
        max_messages: Maximum messages to keep (excluding system message)

    Returns:
        Trimmed message list
    """
    if not messages:
        return []

    # Separate system message and conversation
    system_msg = None
    conversation = messages

    if messages[0].get("role") == "system":
        system_msg = messages[0]
        conversation = messages[1:]

    # Keep last max_messages from conversation
    if len(conversation) > max_messages:
        trimmed_conversation = conversation[-max_messages:]
        logger.debug(
            f"Trimmed conversation from {len(conversation)} to {max_messages} messages"
        )
    else:
        trimmed_conversation = conversation

    # Rebuild with system message first
    if system_msg:
        return [system_msg] + trimmed_conversation
    else:
        return trimmed_conversation


# ==================== Cached Prompt Builder ====================


@lru_cache(maxsize=10)
def _cached_base_prompt(agent_name: str) -> str:
    """
    Cached version of base prompt loading.

    Args:
        agent_name: Name of agent

    Returns:
        Base prompt content
    """
    return load_agent_base_prompt(agent_name)


def build_system_prompt_cached(agent_name: str, profile: str) -> str:
    """
    Build system prompt with caching for base prompt.

    This version caches the base prompt but fetches fresh network context.

    Args:
        agent_name: Name of agent
        profile: Meraki profile name

    Returns:
        Complete system prompt
    """
    # Get fresh context (with its own caching)
    context = get_network_context(profile)

    # Use cached base prompt
    base_prompt = _cached_base_prompt(agent_name)

    # Build full prompt (same logic as build_system_prompt but reuses base)
    org_name = _sanitize_context_value(context.org_name)
    profile_name = _sanitize_context_value(context.profile_name)

    context_section = f"""

## Current Network Context

You are currently managing the following Meraki organization:

- **Organization**: {org_name} (ID: {context.org_id})
- **Profile**: {profile_name}
- **Networks**: {context.network_count}
- **Devices**: {context.device_count}
- **Context Updated**: {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Use this context to provide accurate, relevant responses to the user.
"""

    tool_instructions = """

## Tool Usage Instructions

You have access to specialized tools to interact with the Meraki Dashboard API.

**IMPORTANT**:
- Always use the provided tools to execute operations
- Explain what you're doing before executing
- Provide clear feedback after operations complete
- If a tool call fails, explain the error to the user

**Available Tools**:
- Discovery tools: For network analysis and diagnostics
- Configuration tools: For making network changes
- Workflow tools: For creating automation workflows
- Report tools: For generating documentation

**Workflow**:
1. Understand the user's request
2. Explain what you plan to do
3. Execute the appropriate tool(s)
4. Summarize the results
"""

    safety_section = f"""

## Safety Guidelines

{'**CRITICAL - Configuration Changes**:' if agent_name == 'meraki-specialist' else '**Important**:'}
- For configuration changes, ALWAYS:
  1. Explain the impact of the change
  2. Ask for user confirmation before executing
  3. Create a backup before modifying
  4. Verify the change after execution
- Never execute destructive operations without explicit confirmation
- If unsure, ask for clarification
- Provide rollback instructions if something goes wrong

"""

    return base_prompt + context_section + tool_instructions + safety_section


# ==================== Main ====================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)s: %(message)s"
    )

    try:
        print("\n=== Testing agent_prompts.py ===\n")

        # Test 1: Load base prompts
        print("1. Loading base prompts...")
        for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
            prompt = load_agent_base_prompt(agent)
            print(f"  {agent}: {len(prompt)} chars")

        # Test 2: Mock network context
        print("\n2. Creating mock network context...")
        mock_context = NetworkContext(
            org_name="Test Organization",
            org_id="123456",
            network_count=5,
            device_count=25,
            profile_name="test-profile",
            timestamp=datetime.now(),
        )
        print(f"  Context: {mock_context.org_name}, {mock_context.network_count} networks")

        # Test 3: Build full prompts
        print("\n3. Building full system prompts...")
        for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
            full_prompt = build_system_prompt(agent, mock_context)
            print(f"  {agent}: {len(full_prompt)} chars")
            # Verify sections are present
            assert "Current Network Context" in full_prompt
            assert "Tool Usage Instructions" in full_prompt
            assert "Safety Guidelines" in full_prompt
            assert mock_context.org_name in full_prompt

        # Test 4: Trim conversation
        print("\n4. Testing conversation trimming...")
        messages = [
            {"role": "system", "content": "System prompt"},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
              for i in range(30)],
        ]
        trimmed = trim_conversation_history(messages, max_messages=20)
        print(f"  Trimmed from {len(messages)} to {len(trimmed)} messages")
        assert len(trimmed) == 21  # system + 20 messages
        assert trimmed[0]["role"] == "system"

        print("\n=== All tests passed ===\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
