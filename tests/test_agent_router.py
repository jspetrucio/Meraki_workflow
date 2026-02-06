"""
Unit tests for agent_router module.

Tests classification, function execution, and message processing.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from scripts.agent_router import (
    AGENTS,
    FUNCTION_REGISTRY,
    AgentDefinition,
    ClassificationResult,
    _execute_function,
    _quick_classify,
    _sanitize_input,
    classify_intent,
    process_message,
)


# ==================== Test Data Classes ====================


def test_agent_definition_creation():
    """Test AgentDefinition dataclass."""
    agent = AgentDefinition(
        name="test-agent",
        description="Test agent",
        system_prompt="You are a test agent",
        functions=["func1", "func2"],
        icon="🧪",
    )

    assert agent.name == "test-agent"
    assert agent.description == "Test agent"
    assert len(agent.functions) == 2
    assert agent.icon == "🧪"

    # Test to_dict
    agent_dict = agent.to_dict()
    assert agent_dict["name"] == "test-agent"
    assert "functions" in agent_dict


def test_classification_result_creation():
    """Test ClassificationResult dataclass."""
    result = ClassificationResult(
        agent_name="network-analyst",
        confidence=0.95,
        reasoning="Pattern match",
        requires_confirmation=False,
    )

    assert result.agent_name == "network-analyst"
    assert result.confidence == 0.95
    assert not result.requires_confirmation

    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["agent_name"] == "network-analyst"
    assert result_dict["confidence"] == 0.95


# ==================== Test Agent Registry ====================


def test_agents_registry():
    """Test AGENTS registry is properly populated."""
    assert len(AGENTS) >= 3
    assert "network-analyst" in AGENTS
    assert "meraki-specialist" in AGENTS
    assert "workflow-creator" in AGENTS

    # Check agent structure
    analyst = AGENTS["network-analyst"]
    assert isinstance(analyst, AgentDefinition)
    assert analyst.name == "network-analyst"
    assert len(analyst.functions) > 0
    assert analyst.icon == "🔍"


def test_function_registry():
    """Test FUNCTION_REGISTRY is populated."""
    assert len(FUNCTION_REGISTRY) > 0

    # Check key functions exist
    expected_functions = [
        "full_discovery",
        "discover_networks",
        "configure_ssid",
        "add_firewall_rule",
        "create_device_offline_handler",
    ]

    for func_name in expected_functions:
        assert func_name in FUNCTION_REGISTRY
        assert callable(FUNCTION_REGISTRY[func_name])


# ==================== Test Sanitization ====================


def test_sanitize_input():
    """Test input sanitization."""
    # Test length truncation
    long_input = "a" * 1000
    sanitized = _sanitize_input(long_input)
    assert len(sanitized) <= 500

    # Test control character removal
    dirty_input = "test\x00\x1f\x7fmessage"
    sanitized = _sanitize_input(dirty_input)
    assert sanitized == "testmessage"

    # Test normal input
    normal_input = "analyze the network"
    sanitized = _sanitize_input(normal_input)
    assert sanitized == normal_input


# ==================== Test Quick Classification ====================


def test_quick_classify_explicit_prefix_analyst():
    """Test explicit @analyst prefix routing."""
    result = _quick_classify("@analyst check network")
    assert result is not None
    assert result.agent_name == "network-analyst"
    assert result.confidence == 1.0
    assert not result.requires_confirmation


def test_quick_classify_explicit_prefix_specialist():
    """Test explicit @specialist prefix routing."""
    result = _quick_classify("@specialist configure SSID")
    assert result is not None
    assert result.agent_name == "meraki-specialist"
    assert result.confidence == 1.0
    assert not result.requires_confirmation


def test_quick_classify_explicit_prefix_workflow():
    """Test explicit @workflow prefix routing."""
    result = _quick_classify("@workflow create handler")
    assert result is not None
    assert result.agent_name == "workflow-creator"
    assert result.confidence == 1.0
    assert not result.requires_confirmation


def test_quick_classify_network_analyst_patterns():
    """Test network-analyst pattern matching."""
    test_cases = [
        "analyze the network",
        "discover all devices",
        "scan for issues",
        "diagnose problems",
        "check health status",
        "inventory devices",
    ]

    for message in test_cases:
        result = _quick_classify(message)
        assert result is not None, f"Failed to classify: {message}"
        assert result.agent_name == "network-analyst", f"Wrong agent for: {message}"
        assert result.confidence > 0.0


def test_quick_classify_meraki_specialist_patterns():
    """Test meraki-specialist pattern matching."""
    test_cases = [
        "configure SSID",
        "create firewall rule",
        "add ACL to switch",
        "block port 23",
        "enable VLAN 10",
        "update switch port",
    ]

    for message in test_cases:
        result = _quick_classify(message)
        assert result is not None, f"Failed to classify: {message}"
        assert result.agent_name == "meraki-specialist", f"Wrong agent for: {message}"
        assert result.confidence > 0.0


def test_quick_classify_workflow_creator_patterns():
    """Test workflow-creator pattern matching."""
    test_cases = [
        "create workflow for alerts",
        "automate compliance",
        "schedule reports",
        "trigger remediation",
        "notify on failure",
    ]

    for message in test_cases:
        result = _quick_classify(message)
        assert result is not None, f"Failed to classify: {message}"
        assert result.agent_name == "workflow-creator", f"Wrong agent for: {message}"
        assert result.confidence > 0.0


def test_quick_classify_no_match():
    """Test messages with no pattern match."""
    result = _quick_classify("hello world")
    assert result is None


def test_quick_classify_confidence_threshold():
    """Test confidence levels and requires_confirmation."""
    # High confidence (explicit prefix)
    result = _quick_classify("@analyst check")
    assert result.confidence == 1.0
    assert not result.requires_confirmation

    # Medium confidence (pattern match)
    result = _quick_classify("analyze network")
    assert 0.5 <= result.confidence < 1.0

    # Check requires_confirmation logic
    if result.confidence < 0.7:
        assert result.requires_confirmation


# ==================== Test LLM Classification ====================


@pytest.mark.asyncio
async def test_llm_classify_success():
    """Test successful LLM classification."""
    # Mock AI Engine
    mock_engine = AsyncMock()
    mock_engine.classify = AsyncMock(return_value={
        "agent": "network-analyst",
        "confidence": 0.85,
        "reasoning": "LLM identified network analysis intent",
    })

    from scripts.agent_router import _llm_classify
    result = await _llm_classify("analyze my network", mock_engine)

    assert result.agent_name == "network-analyst"
    assert result.confidence == 0.85
    assert "LLM" in result.reasoning


@pytest.mark.asyncio
async def test_llm_classify_failure_fallback():
    """Test LLM classification failure with fallback to quick classify."""
    # Mock AI Engine that raises error
    mock_engine = AsyncMock()
    mock_engine.classify = AsyncMock(side_effect=Exception("API Error"))

    from scripts.agent_router import _llm_classify
    result = await _llm_classify("analyze network", mock_engine)

    # Should fallback to quick classify
    assert result.agent_name == "network-analyst"
    assert "unavailable" in result.reasoning.lower()


# ==================== Test Classification Pipeline ====================


@pytest.mark.asyncio
async def test_classify_intent_explicit_prefix():
    """Test classification with explicit prefix (fast path)."""
    result = await classify_intent("@analyst check status")

    assert result.agent_name == "network-analyst"
    assert result.confidence == 1.0
    assert not result.requires_confirmation


@pytest.mark.asyncio
async def test_classify_intent_high_confidence_quick():
    """Test classification with high confidence quick classify."""
    result = await classify_intent("analyze discover scan the network")

    assert result.agent_name == "network-analyst"
    # High match score should give good confidence
    assert result.confidence >= 0.8


@pytest.mark.asyncio
async def test_classify_intent_with_llm():
    """Test classification with LLM fallback."""
    mock_engine = AsyncMock()
    mock_engine.classify = AsyncMock(return_value={
        "agent": "workflow-creator",
        "confidence": 0.75,
        "reasoning": "LLM determined workflow intent",
    })

    result = await classify_intent("create automation", mock_engine)

    assert result.agent_name in ["workflow-creator", "meraki-specialist"]


@pytest.mark.asyncio
async def test_classify_intent_low_confidence():
    """Test classification with low confidence requires confirmation."""
    result = await classify_intent("hello")

    # Should default to network-analyst with low confidence
    assert result.confidence < 0.7
    assert result.requires_confirmation


# ==================== Test Function Execution ====================


@pytest.mark.asyncio
async def test_execute_function_success():
    """Test successful function execution."""
    # Mock a simple function
    def mock_func(test_arg: str):
        return f"Result: {test_arg}"

    with patch.dict(FUNCTION_REGISTRY, {"mock_func": mock_func}):
        success, result, error = await _execute_function("mock_func", {"test_arg": "test"})

        assert success
        assert result is not None
        assert "Result: test" in str(result)
        assert error is None


@pytest.mark.asyncio
async def test_execute_function_not_found():
    """Test function execution with non-existent function."""
    success, result, error = await _execute_function("nonexistent_func", {})

    assert not success
    assert result is None
    assert "not found" in error.lower()


@pytest.mark.asyncio
async def test_execute_function_exception():
    """Test function execution with exception."""
    def failing_func():
        raise ValueError("Test error")

    with patch.dict(FUNCTION_REGISTRY, {"failing_func": failing_func}):
        success, result, error = await _execute_function("failing_func", {})

        assert not success
        assert result is None
        assert "Test error" in error


# ==================== Test Message Processing ====================


@pytest.mark.asyncio
async def test_process_message_basic():
    """Test basic message processing flow."""
    # Mock AI Engine
    mock_engine = AsyncMock()

    # Create a mock response chunk
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta = MagicMock()
    mock_chunk.choices[0].delta.content = "Test response"
    mock_chunk.choices[0].delta.tool_calls = None

    async def mock_stream(*args, **kwargs):
        yield mock_chunk

    mock_engine.chat_completion = mock_stream

    # Process message
    chunks = []
    async for chunk in process_message("analyze network", ai_engine=mock_engine):
        chunks.append(chunk)

    # Should have classification and stream chunks
    assert len(chunks) > 0

    # First chunk should be classification
    assert chunks[0]["type"] == "classification"
    assert "agent" in chunks[0]


@pytest.mark.asyncio
async def test_process_message_no_engine():
    """Test message processing without AI engine."""
    chunks = []
    async for chunk in process_message("analyze network"):
        chunks.append(chunk)

    # Should have classification but error for no AI engine
    classification_chunks = [c for c in chunks if c["type"] == "classification"]
    error_chunks = [c for c in chunks if c["type"] == "error"]

    assert len(classification_chunks) > 0
    assert len(error_chunks) > 0


@pytest.mark.asyncio
async def test_process_message_confirmation_required():
    """Test message processing with low confidence."""
    chunks = []
    async for chunk in process_message("hello"):
        chunks.append(chunk)

    # Find classification chunk
    classification = next((c for c in chunks if c["type"] == "classification"), None)
    assert classification is not None

    # Should require confirmation for ambiguous message
    if classification.get("requires_confirmation"):
        confirmation_chunks = [c for c in chunks if c["type"] == "confirmation_required"]
        assert len(confirmation_chunks) > 0


# ==================== Test Classification Accuracy ====================


def test_classification_accuracy_on_test_set():
    """Test classification accuracy on full test set."""
    test_set_path = Path(__file__).parent / "test_classification_set.json"

    if not test_set_path.exists():
        pytest.skip("Test classification set not found")

    with open(test_set_path) as f:
        test_set = json.load(f)

    correct = 0
    total = len(test_set)

    for test_case in test_set:
        command = test_case["command"]
        expected_agent = test_case["expected_agent"]

        result = _quick_classify(command)

        if result and result.agent_name == expected_agent:
            correct += 1

    accuracy = (correct / total) * 100

    print(f"\nClassification Accuracy: {accuracy:.1f}% ({correct}/{total})")

    # Story requirement: > 90% accuracy
    assert accuracy >= 90, f"Accuracy {accuracy:.1f}% is below 90% threshold"


# ==================== Test Edge Cases ====================


def test_empty_message():
    """Test handling of empty message."""
    result = _quick_classify("")
    assert result is None


def test_very_long_message():
    """Test handling of very long message."""
    long_message = "analyze " * 200
    result = _quick_classify(long_message)
    # Should still classify correctly
    assert result is not None
    assert result.agent_name == "network-analyst"


def test_special_characters():
    """Test handling of special characters."""
    result = _quick_classify("analyze network with special chars: @#$%^&*()")
    assert result is not None
    assert result.agent_name == "network-analyst"


def test_mixed_case():
    """Test case insensitivity."""
    result1 = _quick_classify("ANALYZE NETWORK")
    result2 = _quick_classify("analyze network")

    assert result1 is not None
    assert result2 is not None
    assert result1.agent_name == result2.agent_name


# ==================== Test Integration ====================


@pytest.mark.asyncio
async def test_end_to_end_classification():
    """Test end-to-end classification flow."""
    test_messages = [
        ("@analyst check network", "network-analyst"),
        ("configure firewall", "meraki-specialist"),
        ("create workflow", "workflow-creator"),
    ]

    for message, expected_agent in test_messages:
        result = await classify_intent(message)
        assert result.agent_name == expected_agent, f"Failed for: {message}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
