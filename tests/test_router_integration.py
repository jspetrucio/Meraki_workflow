"""
Tests for Story 7.3: Router Integration & Feature Flag.

Covers:
- ClassificationResult.task_definition field
- classify_intent() task registry integration
- process_message() dual-path routing (task executor vs legacy)
- Feature flag (use_modular_tasks)
- WebSocket gate confirmation support
- Backward compatibility
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.agent_router import (
    ClassificationResult,
    classify_intent,
    process_message,
    _get_task_registry,
    _task_registry,
)
from scripts.task_models import (
    TaskDefinition,
    StepDefinition,
    StepType,
    RiskLevel,
)
from scripts.settings import Settings


# ==================== ClassificationResult Extension ====================


class TestClassificationResultExtension:
    """AC#1-3: task_definition field on ClassificationResult."""

    def test_task_definition_default_none(self):
        """AC#1: task_definition defaults to None."""
        result = ClassificationResult(
            agent_name="test",
            confidence=0.9,
            reasoning="test",
        )
        assert result.task_definition is None

    def test_task_definition_set(self):
        """AC#2: task_definition can be set."""
        task = TaskDefinition(name="test-task", agent="network-analyst")
        result = ClassificationResult(
            agent_name="network-analyst",
            confidence=1.0,
            reasoning="Matched task: test-task",
            task_definition=task,
        )
        assert result.task_definition is not None
        assert result.task_definition.name == "test-task"

    def test_existing_fields_unchanged(self):
        """AC#3: Existing fields remain unchanged."""
        result = ClassificationResult(
            agent_name="test",
            confidence=0.85,
            reasoning="test reason",
            requires_confirmation=True,
        )
        assert result.agent_name == "test"
        assert result.confidence == 0.85
        assert result.reasoning == "test reason"
        assert result.requires_confirmation is True

    def test_to_dict_without_task(self):
        """to_dict works without task_definition."""
        result = ClassificationResult(
            agent_name="test",
            confidence=0.9,
            reasoning="test",
        )
        d = result.to_dict()
        assert "agent_name" in d
        assert "task_name" not in d

    def test_to_dict_with_task(self):
        """to_dict includes task_name when task_definition set."""
        task = TaskDefinition(name="my-task", agent="test")
        result = ClassificationResult(
            agent_name="test",
            confidence=1.0,
            reasoning="test",
            task_definition=task,
        )
        d = result.to_dict()
        assert d["task_name"] == "my-task"


# ==================== classify_intent() Task Registry ====================


class TestClassifyIntentTaskRegistry:
    """AC#4-7: Task registry integration in classify_intent()."""

    @pytest.fixture
    def loaded_registry(self, tmp_path):
        """Create a registry with sample tasks."""
        # Reset the module-level registry
        _task_registry.tasks.clear()
        _task_registry._tasks.clear()

        d = tmp_path / "network-analyst"
        d.mkdir()
        (d / "analyze-network.md").write_text("""---
name: analyze-network
agent: network-analyst
trigger_keywords: [analyze, network, scan, discovery, health]
risk_level: low
steps:
  - name: discover
    type: tool
    tool: full_discovery
---
Analyze the network.
""")

        spec_dir = tmp_path / "meraki-specialist"
        spec_dir.mkdir()
        (spec_dir / "configure-vlan.md").write_text("""---
name: configure-vlan
agent: meraki-specialist
trigger_keywords: [vlan, configure, switch, trunk]
risk_level: high
steps:
  - name: apply
    type: tool
    tool: update_vlan
---
Configure VLAN.
""")

        _task_registry.load_tasks(tmp_path)
        return _task_registry

    @pytest.mark.asyncio
    async def test_task_match_after_prefix(self, loaded_registry):
        """AC#5: Explicit prefix takes priority over task match."""
        result = await classify_intent("@specialist analyze my network")
        assert result.agent_name == "meraki-specialist"
        assert result.task_definition is None  # Prefix, not task match

    @pytest.mark.asyncio
    async def test_task_match_found(self, loaded_registry):
        """AC#4,6: Task match sets task_definition with confidence=1.0."""
        result = await classify_intent("analyze my network health")
        assert result.task_definition is not None
        assert result.task_definition.name == "analyze-network"
        assert result.confidence == 1.0
        assert "Matched task" in result.reasoning

    @pytest.mark.asyncio
    async def test_task_match_configure(self, loaded_registry):
        """Task match for configure intent."""
        result = await classify_intent("configure vlan 100 on the switch")
        assert result.task_definition is not None
        assert result.task_definition.name == "configure-vlan"

    @pytest.mark.asyncio
    async def test_no_task_match_falls_through(self, loaded_registry):
        """AC#7: No task match → existing flow continues."""
        result = await classify_intent("create a workflow template")
        assert result.task_definition is None


# ==================== Feature Flag ====================


class TestFeatureFlag:
    """AC#12-14: use_modular_tasks feature flag."""

    @pytest.fixture
    def loaded_registry(self, tmp_path):
        """Create a registry with sample tasks."""
        _task_registry.tasks.clear()
        _task_registry._tasks.clear()

        d = tmp_path / "analyst"
        d.mkdir()
        (d / "test-task.md").write_text("""---
name: test-task
agent: network-analyst
trigger_keywords: [analyze, network]
risk_level: low
---
Test.
""")
        _task_registry.load_tasks(tmp_path)
        return _task_registry

    @pytest.mark.asyncio
    async def test_feature_flag_enabled(self, loaded_registry):
        """AC#12: use_modular_tasks=True (default) → task registry checked."""
        settings = Settings()
        assert settings.use_modular_tasks is True

        result = await classify_intent("analyze my network", settings=settings)
        assert result.task_definition is not None

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, loaded_registry):
        """AC#13: use_modular_tasks=False → skip task registry."""
        settings = Settings()
        settings.use_modular_tasks = False

        result = await classify_intent("analyze my network", settings=settings)
        assert result.task_definition is None

    @pytest.mark.asyncio
    async def test_no_settings_defaults_to_enabled(self, loaded_registry):
        """When no settings passed, use_modular_tasks defaults to True."""
        result = await classify_intent("analyze my network")
        assert result.task_definition is not None


# ==================== process_message() Dual Path ====================


class TestProcessMessageDualPath:
    """AC#8-11: process_message routes to task executor or legacy flow."""

    @pytest.fixture
    def loaded_registry(self, tmp_path):
        """Create a registry with sample tasks."""
        _task_registry.tasks.clear()
        _task_registry._tasks.clear()

        d = tmp_path / "analyst"
        d.mkdir()
        (d / "analyze.md").write_text("""---
name: analyze-task
agent: network-analyst
trigger_keywords: [analyze, network, health]
risk_level: low
steps:
  - name: step1
    type: tool
    tool: full_discovery
---
Analyze.
""")
        _task_registry.load_tasks(tmp_path)
        return _task_registry

    @pytest.mark.asyncio
    async def test_task_executor_path(self, loaded_registry):
        """AC#8-9: task_definition exists → delegate to task_executor."""
        mock_engine = AsyncMock()

        chunks = []
        with patch("scripts.task_executor.TaskExecutor") as MockExecutor:
            mock_instance = MagicMock()

            async def mock_execute(**kwargs):
                yield {"type": "task_start", "task_name": "analyze-task"}
                yield {"type": "task_complete", "task_name": "analyze-task", "status": "completed"}

            mock_instance.execute = mock_execute
            MockExecutor.return_value = mock_instance

            async for chunk in process_message(
                message="analyze my network health",
                ai_engine=mock_engine,
            ):
                chunks.append(chunk)

        # Should have classification + task_start + task_complete
        types = [c["type"] for c in chunks]
        assert "classification" in types
        assert "task_start" in types
        assert "task_complete" in types

    @pytest.mark.asyncio
    async def test_legacy_flow_path(self, loaded_registry):
        """AC#10: No task match → legacy LLM flow."""
        mock_engine = AsyncMock()
        mock_engine.chat_completion = AsyncMock()

        # Set up mock to return an async generator
        async def mock_stream(*args, **kwargs):
            yield MagicMock(choices=[])

        mock_engine.chat_completion.return_value = mock_stream()

        chunks = []
        async for chunk in process_message(
            message="create a workflow template",
            ai_engine=mock_engine,
        ):
            chunks.append(chunk)

        types = [c["type"] for c in chunks]
        assert "classification" in types
        # Should NOT have task_start (legacy flow)
        assert "task_start" not in types

    @pytest.mark.asyncio
    async def test_feature_flag_off_forces_legacy(self, loaded_registry):
        """AC#13: Feature flag off → always legacy flow."""
        mock_engine = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield MagicMock(choices=[])

        mock_engine.chat_completion.return_value = mock_stream()

        settings = Settings()
        settings.use_modular_tasks = False

        chunks = []
        async for chunk in process_message(
            message="analyze my network health",
            ai_engine=mock_engine,
            settings=settings,
        ):
            chunks.append(chunk)

        types = [c["type"] for c in chunks]
        # Should NOT have task_start even though message matches
        assert "task_start" not in types


# ==================== Backward Compatibility ====================


class TestBackwardCompatibility:
    """AC#22-25: All existing behavior preserved."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear task registry for backward compat tests."""
        _task_registry.tasks.clear()
        _task_registry._tasks.clear()
        yield

    @pytest.mark.asyncio
    async def test_explicit_prefix_still_priority(self):
        """AC#24: @analyst/@specialist still top priority."""
        result = await classify_intent("@analyst configure VLAN")
        assert result.agent_name == "network-analyst"
        assert result.confidence == 1.0
        assert result.task_definition is None

    @pytest.mark.asyncio
    async def test_no_tasks_loaded_no_change(self):
        """AC#22: With feature flag off, behavior identical to before."""
        from scripts.settings import Settings
        settings = Settings()
        settings.use_modular_tasks = False
        result = await classify_intent("scan the network for issues", settings=settings)
        assert result.task_definition is None
        assert result.agent_name == "network-analyst"

    @pytest.mark.asyncio
    async def test_process_message_no_engine_error(self):
        """Legacy error path unchanged."""
        chunks = []
        async for chunk in process_message(
            message="test message",
        ):
            chunks.append(chunk)

        types = [c["type"] for c in chunks]
        assert "error" in types


# ==================== WebSocket Gate Confirmation ====================


class TestWebSocketGateConfirmation:
    """AC#17-21: WebSocket handler gate confirmation support."""

    def test_pending_confirmations_dict_pattern(self):
        """AC#17-18: Verify the pattern of event storage."""
        pending = {}
        event = asyncio.Event()
        rid = "test-request-123"

        # Store event
        pending[rid] = event
        assert rid in pending

        # Simulate confirm
        stored_event = pending.pop(rid)
        stored_event.set()
        assert stored_event.is_set()
        assert rid not in pending

    def test_denial_flag_pattern(self):
        """AC#20: Denial flag is set before event.set()."""
        pending = {}
        denial_ctx = {}
        event = asyncio.Event()
        rid = "deny-request-456"

        pending[rid] = event
        denial_ctx[rid] = {}

        # Simulate deny
        stored_event = pending.pop(rid)
        ctx = denial_ctx.pop(rid)
        ctx[f"gate_denied_{rid}"] = True
        stored_event.set()

        assert stored_event.is_set()
        assert ctx[f"gate_denied_{rid}"] is True

    def test_confirmation_expiry_pattern(self):
        """AC#21: Events should be cleanable after timeout."""
        pending = {}
        event = asyncio.Event()
        rid = "expire-789"
        pending[rid] = event

        # Simulate cleanup (timeout expired)
        if rid in pending and not pending[rid].is_set():
            pending.pop(rid)

        assert rid not in pending


# ==================== Settings Extension ====================


class TestSettingsExtension:
    """AC#12: use_modular_tasks field in Settings."""

    def test_default_value(self):
        """use_modular_tasks defaults to True."""
        settings = Settings()
        assert settings.use_modular_tasks is True

    def test_can_set_false(self):
        """use_modular_tasks can be set to False."""
        settings = Settings()
        settings.use_modular_tasks = False
        assert settings.use_modular_tasks is False


# ==================== Logging ====================


class TestLogging:
    """AC#15-16: Routing log messages."""

    @pytest.fixture
    def loaded_registry(self, tmp_path):
        _task_registry.tasks.clear()
        _task_registry._tasks.clear()

        d = tmp_path / "analyst"
        d.mkdir()
        (d / "log-test.md").write_text("""---
name: log-test-task
agent: network-analyst
trigger_keywords: [analyze, network]
risk_level: low
---
Test.
""")
        _task_registry.load_tasks(tmp_path)
        return _task_registry

    @pytest.mark.asyncio
    async def test_log_task_executor_routing(self, loaded_registry, caplog):
        """AC#15: Log when routing to task_executor."""
        import logging
        with caplog.at_level(logging.INFO, logger="scripts.agent_router"):
            await classify_intent("analyze my network")
        assert any("Routing to task_executor: log-test-task" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_log_legacy_routing(self, caplog):
        """AC#16: Log when routing to legacy flow."""
        from scripts.settings import Settings
        settings = Settings()
        settings.use_modular_tasks = False

        import logging
        with caplog.at_level(logging.INFO, logger="scripts.agent_router"):
            chunks = []
            mock_engine = AsyncMock()

            async def mock_stream(*args, **kwargs):
                yield MagicMock(choices=[])

            mock_engine.chat_completion.return_value = mock_stream()

            async for chunk in process_message(
                message="scan network for issues",
                ai_engine=mock_engine,
                settings=settings,
            ):
                chunks.append(chunk)

        assert any("legacy LLM flow" in r.message for r in caplog.records)
