"""
Tests for agent prompts and tool definitions.

Tests:
- System prompt building for each agent
- Network context injection
- Tool schema validation
- Safety classification
- Conversation history trimming
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

from scripts.agent_prompts import (
    NetworkContext,
    build_system_prompt,
    get_network_context,
    invalidate_context_cache,
    load_agent_base_prompt,
    trim_conversation_history,
    _sanitize_context_value,
)
from scripts.agent_tools import (
    AGENT_TOOLS,
    SafetyLevel,
    get_agent_tools,
    get_tool_safety,
    requires_confirmation,
    validate_tool_schema,
    TOOL_SAFETY,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_network_context():
    """Mock network context for testing."""
    return NetworkContext(
        org_name="Test Organization",
        org_id="123456",
        network_count=5,
        device_count=25,
        profile_name="test-profile",
        timestamp=datetime.now(),
    )


@pytest.fixture
def mock_conversation():
    """Mock conversation history."""
    return [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm good"},
    ]


# ==================== Prompt Tests ====================


def test_load_agent_base_prompt():
    """Test loading base prompts for all agents."""
    for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
        prompt = load_agent_base_prompt(agent)
        assert prompt is not None
        assert len(prompt) > 0
        assert isinstance(prompt, str)


def test_load_agent_base_prompt_not_found():
    """Test loading non-existent agent raises error."""
    with pytest.raises(FileNotFoundError):
        load_agent_base_prompt("non-existent-agent")


def test_sanitize_context_value():
    """Test context value sanitization."""
    # Normal string
    assert _sanitize_context_value("Test Org") == "Test Org"

    # With newlines
    assert _sanitize_context_value("Test\nOrg") == "Test Org"

    # With control characters
    assert "\x00" not in _sanitize_context_value("Test\x00Org")

    # Long string truncation
    long_str = "a" * 300
    sanitized = _sanitize_context_value(long_str)
    assert len(sanitized) <= 203  # 200 + "..."


def test_build_system_prompt(mock_network_context):
    """Test building complete system prompts."""
    for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
        prompt = build_system_prompt(agent, mock_network_context)

        # Check required sections
        assert "Current Network Context" in prompt
        assert "Tool Usage Instructions" in prompt
        assert "Safety Guidelines" in prompt

        # Check context injection
        assert mock_network_context.org_name in prompt
        assert str(mock_network_context.network_count) in prompt
        assert str(mock_network_context.device_count) in prompt

        # Check length is reasonable
        assert len(prompt) > 500


def test_build_system_prompt_meraki_specialist_safety(mock_network_context):
    """Test that meraki-specialist gets stricter safety guidelines."""
    prompt = build_system_prompt("meraki-specialist", mock_network_context)
    assert "CRITICAL - Configuration Changes" in prompt
    assert "backup" in prompt.lower()


def test_trim_conversation_history_no_system():
    """Test trimming when no system message."""
    messages = [{"role": "user", "content": f"Message {i}"} for i in range(30)]
    trimmed = trim_conversation_history(messages, max_messages=20)

    assert len(trimmed) == 20
    assert trimmed[0]["content"] == "Message 10"  # Should keep last 20


def test_trim_conversation_history_with_system():
    """Test trimming preserves system message."""
    messages = [
        {"role": "system", "content": "System"},
        *[{"role": "user", "content": f"Message {i}"} for i in range(30)],
    ]
    trimmed = trim_conversation_history(messages, max_messages=20)

    assert len(trimmed) == 21  # system + 20 messages
    assert trimmed[0]["role"] == "system"
    assert trimmed[0]["content"] == "System"


def test_trim_conversation_history_under_limit():
    """Test no trimming when under limit."""
    messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]
    trimmed = trim_conversation_history(messages, max_messages=20)

    assert len(trimmed) == 10
    assert trimmed == messages


def test_trim_conversation_history_empty():
    """Test trimming empty conversation."""
    trimmed = trim_conversation_history([], max_messages=20)
    assert trimmed == []


# ==================== Tool Definition Tests ====================


def test_get_agent_tools():
    """Test retrieving tools for each agent."""
    for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
        tools = get_agent_tools(agent)
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, dict) for t in tools)


def test_get_agent_tools_invalid_agent():
    """Test retrieving tools for non-existent agent."""
    with pytest.raises(ValueError):
        get_agent_tools("non-existent-agent")


def test_all_tool_schemas_valid():
    """Test that all tool schemas are valid OpenAI function-calling format."""
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            valid, error = validate_tool_schema(tool)
            assert valid, f"Invalid tool schema in {agent_name}: {error}"


def test_tool_schema_has_required_fields():
    """Test that each tool has required fields."""
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            # Top level
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool

            func = tool["function"]

            # Function level
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

            params = func["parameters"]

            # Parameters level
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params
            assert params.get("additionalProperties") is False


def test_tool_names_match_function_registry():
    """Test that tool names match functions in agent_router.py."""
    from scripts.agent_router import FUNCTION_REGISTRY

    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            tool_name = tool["function"]["name"]
            assert (
                tool_name in FUNCTION_REGISTRY
            ), f"Tool {tool_name} not in FUNCTION_REGISTRY"


def test_tool_parameter_types():
    """Test that all tool parameters have proper types."""
    valid_types = ["string", "integer", "number", "boolean", "array", "object"]

    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            params = tool["function"]["parameters"]["properties"]
            for param_name, param_def in params.items():
                assert (
                    "type" in param_def
                ), f"Missing type for {param_name} in {tool['function']['name']}"
                assert (
                    param_def["type"] in valid_types
                ), f"Invalid type for {param_name}: {param_def['type']}"


def test_tool_enum_constraints():
    """Test that enum constraints are used where appropriate."""
    # Check that certain parameters use enum
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            func_name = tool["function"]["name"]
            params = tool["function"]["parameters"]["properties"]

            # Policy should be enum
            if "policy" in params:
                assert (
                    "enum" in params["policy"]
                ), f"{func_name}: policy should have enum constraint"
                assert params["policy"]["enum"] == ["allow", "deny"]

            # Protocol should be enum
            if "protocol" in params:
                assert (
                    "enum" in params["protocol"]
                ), f"{func_name}: protocol should have enum constraint"


# ==================== Safety Classification Tests ====================


def test_safety_level_enum():
    """Test SafetyLevel enum values."""
    assert SafetyLevel.SAFE.value == "safe"
    assert SafetyLevel.MODERATE.value == "moderate"
    assert SafetyLevel.DANGEROUS.value == "dangerous"


def test_get_tool_safety():
    """Test safety classification for known tools."""
    # Safe tools
    assert get_tool_safety("full_discovery") == SafetyLevel.SAFE
    assert get_tool_safety("discover_networks") == SafetyLevel.SAFE
    assert get_tool_safety("list_workflows") == SafetyLevel.SAFE

    # Moderate tools
    assert get_tool_safety("configure_ssid") == SafetyLevel.MODERATE
    assert get_tool_safety("create_vlan") == SafetyLevel.MODERATE

    # Dangerous tools
    assert get_tool_safety("delete_vlan") == SafetyLevel.DANGEROUS
    assert get_tool_safety("add_firewall_rule") == SafetyLevel.DANGEROUS
    assert get_tool_safety("remove_firewall_rule") == SafetyLevel.DANGEROUS


def test_get_tool_safety_unknown():
    """Test default safety for unknown tools."""
    safety = get_tool_safety("unknown_tool")
    assert safety == SafetyLevel.MODERATE


def test_requires_confirmation():
    """Test confirmation requirement logic."""
    # Safe tools don't need confirmation
    assert not requires_confirmation("full_discovery")
    assert not requires_confirmation("discover_devices")

    # Moderate and dangerous need confirmation
    assert requires_confirmation("configure_ssid")
    assert requires_confirmation("delete_vlan")
    assert requires_confirmation("add_firewall_rule")


def test_all_tools_have_safety_classification():
    """Test that all tools in AGENT_TOOLS have safety classification."""
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            tool_name = tool["function"]["name"]
            assert (
                tool_name in TOOL_SAFETY
            ), f"Tool {tool_name} missing safety classification"


# ==================== Integration Tests ====================


def test_agent_has_tools_and_prompt():
    """Test that each agent has both tools and can build prompt."""
    for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
        # Has tools
        tools = get_agent_tools(agent)
        assert len(tools) > 0

        # Can build prompt
        context = NetworkContext(
            org_name="Test",
            org_id="123",
            network_count=1,
            device_count=1,
            profile_name="test",
            timestamp=datetime.now(),
        )
        prompt = build_system_prompt(agent, context)
        assert len(prompt) > 0


def test_tool_descriptions_are_informative():
    """Test that all tool descriptions are meaningful."""
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            desc = tool["function"]["description"]
            # Description should be at least 20 chars
            assert len(desc) >= 20, f"Tool {tool['function']['name']} has short description"
            # Should not be generic
            assert "function" not in desc.lower() or "tool" not in desc.lower()


def test_required_parameters_exist():
    """Test that all required parameters are defined."""
    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            params = tool["function"]["parameters"]
            required = params["required"]
            properties = params["properties"]

            for req_param in required:
                assert (
                    req_param in properties
                ), f"{tool['function']['name']}: required param '{req_param}' not in properties"


# ==================== Performance Tests ====================


def test_prompt_building_is_fast(mock_network_context):
    """Test that prompt building completes quickly."""
    import time

    start = time.time()
    for _ in range(10):
        build_system_prompt("network-analyst", mock_network_context)
    elapsed = time.time() - start

    # Should complete 10 builds in under 1 second
    assert elapsed < 1.0


def test_tool_retrieval_is_fast():
    """Test that tool retrieval is fast."""
    import time

    start = time.time()
    for _ in range(100):
        get_agent_tools("network-analyst")
    elapsed = time.time() - start

    # Should complete 100 retrievals in under 0.1 seconds
    assert elapsed < 0.1


# ==================== Edge Cases ====================


def test_context_with_special_characters(mock_network_context):
    """Test context injection with special characters."""
    mock_network_context.org_name = 'Test "Org" with <special> chars'
    prompt = build_system_prompt("network-analyst", mock_network_context)

    # Should be sanitized
    assert "\x00" not in prompt
    assert prompt is not None


def test_empty_tool_list_handling():
    """Test handling of agent with no tools (hypothetical)."""
    # This is more of a validation test
    for agent_name, tools in AGENT_TOOLS.items():
        assert len(tools) > 0, f"{agent_name} has no tools"


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
