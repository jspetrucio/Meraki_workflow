"""
Tests for Story 7.1: Task Executor Core Engine.

Covers:
- task_models.py data models
- executor_utils.py public wrappers
- task_executor.py core engine (tool/agent/gate steps, hooks, state, rollback)
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.task_models import (
    ChangeEntry,
    RiskLevel,
    StepDefinition,
    StepResult,
    StepStatus,
    StepType,
    TaskDefinition,
    TaskParseError,
    TaskRunState,
    TaskStatus,
)
from scripts.executor_utils import serialize_result, execute_function
from scripts.task_executor import TaskExecutor


# ==================== task_models.py Tests ====================


class TestTaskParseError:
    def test_create_with_message(self):
        err = TaskParseError("/path/to/file.md", "invalid YAML")
        assert err.file_path == "/path/to/file.md"
        assert err.message == "invalid YAML"
        assert "Failed to parse /path/to/file.md" in str(err)

    def test_inherits_exception(self):
        err = TaskParseError("file.md", "bad")
        assert isinstance(err, Exception)


class TestStepType:
    def test_values(self):
        assert StepType.TOOL.value == "tool"
        assert StepType.AGENT.value == "agent"
        assert StepType.GATE.value == "gate"

    def test_string_enum(self):
        assert StepType("tool") == StepType.TOOL
        assert StepType("agent") == StepType.AGENT
        assert StepType("gate") == StepType.GATE


class TestTaskStatus:
    def test_all_statuses(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.ROLLED_BACK.value == "rolled_back"


class TestStepDefinition:
    def test_minimal_step(self):
        step = StepDefinition(name="test", type=StepType.TOOL)
        assert step.name == "test"
        assert step.type == StepType.TOOL
        assert step.tool is None
        assert step.args is None
        assert step.args_from is None
        assert step.condition is None

    def test_full_tool_step(self):
        step = StepDefinition(
            name="discover",
            type=StepType.TOOL,
            description="Run full discovery",
            tool="full_discovery",
            args={"network_id": "N_123"},
        )
        assert step.tool == "full_discovery"
        assert step.args["network_id"] == "N_123"

    def test_gate_step_with_template(self):
        step = StepDefinition(
            name="confirm",
            type=StepType.GATE,
            message_template="Apply changes to {discover.result}?",
        )
        assert step.message_template is not None


class TestTaskDefinition:
    def test_minimal_task(self):
        task = TaskDefinition(name="test-task", agent="network-analyst")
        assert task.name == "test-task"
        assert task.agent == "network-analyst"
        assert task.trigger_keywords == []
        assert task.risk_level == RiskLevel.LOW
        assert task.steps == []

    def test_full_task(self):
        task = TaskDefinition(
            name="analyze-network",
            agent="network-analyst",
            trigger_keywords=["analyze", "scan", "discovery"],
            risk_level=RiskLevel.LOW,
            steps=[
                StepDefinition(name="discover", type=StepType.TOOL, tool="full_discovery"),
                StepDefinition(name="report", type=StepType.AGENT),
            ],
            hooks={"pre": "pre-analysis", "post": "post-analysis"},
            description="Full network analysis",
            source_file="CNL_agents/network-analyst/analyze-network.md",
            body="# Analyst System Prompt\nAnalyze the network...",
        )
        assert len(task.steps) == 2
        assert task.hooks["pre"] == "pre-analysis"
        assert task.body.startswith("# Analyst")


class TestStepResult:
    def test_to_dict(self):
        now = datetime.now()
        result = StepResult(
            step_name="discover",
            type=StepType.TOOL,
            status=StepStatus.COMPLETED,
            result={"networks": 5},
            started_at=now,
            completed_at=now,
        )
        d = result.to_dict()
        assert d["step_name"] == "discover"
        assert d["type"] == "tool"
        assert d["status"] == "completed"
        assert d["result"] == {"networks": 5}
        assert d["started_at"] is not None


class TestChangeEntry:
    def test_to_dict(self):
        entry = ChangeEntry(
            action="update_vlan",
            resource_type="vlan",
            resource_id="100",
            backup_path="/clients/test/backups/backup.json",
            timestamp=datetime.now(),
        )
        d = entry.to_dict()
        assert d["action"] == "update_vlan"
        assert d["resource_type"] == "vlan"


class TestTaskRunState:
    def test_default_uuid(self):
        state = TaskRunState()
        assert len(state.task_id) == 36  # UUID format

    def test_to_dict(self):
        state = TaskRunState(
            task_name="test",
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )
        d = state.to_dict()
        assert d["task_name"] == "test"
        assert d["status"] == "running"
        assert isinstance(d["steps_completed"], list)
        assert isinstance(d["change_log"], list)


# ==================== executor_utils.py Tests ====================


class TestSerializeResult:
    def test_primitives(self):
        assert serialize_result(None) is None
        assert serialize_result("hello") == "hello"
        assert serialize_result(42) == 42
        assert serialize_result(3.14) == 3.14
        assert serialize_result(True) is True

    def test_path(self):
        assert serialize_result(Path("/tmp/test")) == "/tmp/test"

    def test_enum(self):
        assert serialize_result(RiskLevel.HIGH) == "high"

    def test_dict(self):
        result = serialize_result({"a": 1, "b": Path("/tmp")})
        assert result == {"a": 1, "b": "/tmp"}

    def test_list(self):
        result = serialize_result([1, "two", Path("/three")])
        assert result == [1, "two", "/three"]

    def test_dataclass(self):
        entry = ChangeEntry(action="test", resource_type="vlan", timestamp=datetime(2026, 1, 1))
        result = serialize_result(entry)
        assert result["action"] == "test"
        assert result["resource_type"] == "vlan"

    def test_to_dict_method(self):
        class Obj:
            def to_dict(self):
                return {"key": "value"}

        result = serialize_result(Obj())
        assert result == {"key": "value"}

    def test_nested(self):
        data = {"items": [{"path": Path("/a")}, {"path": Path("/b")}]}
        result = serialize_result(data)
        assert result["items"][0]["path"] == "/a"

    def test_unknown_type(self):
        class Custom:
            def __str__(self):
                return "custom_repr"

        assert serialize_result(Custom()) == "custom_repr"


class TestExecuteFunction:
    @pytest.mark.asyncio
    async def test_function_not_found(self):
        success, result, error = await execute_function("nonexistent", {}, {})
        assert success is False
        assert "not found" in error

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        def mock_func(x, y):
            return {"sum": x + y}

        registry = {"add": mock_func}
        success, result, error = await execute_function("add", {"x": 1, "y": 2}, registry)
        assert success is True
        assert result["result"]["sum"] == 3
        assert error is None

    @pytest.mark.asyncio
    async def test_function_raises_exception(self):
        def failing_func():
            raise ValueError("test error")

        registry = {"fail": failing_func}
        success, result, error = await execute_function("fail", {}, registry)
        assert success is False
        assert "test error" in error


# ==================== task_executor.py Tests ====================


def _make_settings(**overrides):
    """Create a mock Settings object."""
    settings = MagicMock()
    settings.meraki_profile = overrides.get("meraki_profile", "test-client")
    settings.ai_provider = overrides.get("ai_provider", "openai")
    settings.ai_model = overrides.get("ai_model", "gpt-4")
    settings.ai_api_key = overrides.get("ai_api_key", "test-key")
    return settings


def _make_task(
    name="test-task",
    agent="network-analyst",
    steps=None,
    hooks=None,
    risk_level=RiskLevel.LOW,
    body="",
):
    """Create a TaskDefinition for testing."""
    return TaskDefinition(
        name=name,
        agent=agent,
        steps=steps or [],
        hooks=hooks or {},
        risk_level=risk_level,
        body=body,
    )


async def _collect_chunks(gen) -> list[dict]:
    """Collect all chunks from an async generator."""
    chunks = []
    async for chunk in gen:
        chunks.append(chunk)
    return chunks


class TestTaskExecutorInit:
    def test_init_with_registry(self):
        ai = MagicMock()
        settings = _make_settings()
        registry = {"fn": lambda: None}
        executor = TaskExecutor(ai, settings, function_registry=registry)
        assert executor.registry == registry

    def test_lazy_registry(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings)
        assert executor._registry is None


class TestTaskExecutorToolStep:
    @pytest.mark.asyncio
    async def test_tool_step_success(self):
        def mock_discover():
            return {"networks": ["N1", "N2"]}

        registry = {"full_discovery": mock_discover}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="discover", type=StepType.TOOL, tool="full_discovery"),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "analyze network"))

        types = [c["type"] for c in chunks]
        assert "task_start" in types
        assert "step_start" in types
        assert "function_result" in types
        assert "step_complete" in types
        assert "task_complete" in types

        # Verify function_result
        fr = next(c for c in chunks if c["type"] == "function_result")
        assert fr["success"] is True
        assert fr["function"] == "full_discovery"

        # Verify task_complete
        tc = next(c for c in chunks if c["type"] == "task_complete")
        assert tc["status"] == "completed"

    @pytest.mark.asyncio
    async def test_tool_step_failure_aborts(self):
        def failing_func():
            raise RuntimeError("API error")

        registry = {"bad_func": failing_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="bad", type=StepType.TOOL, tool="bad_func"),
                StepDefinition(name="never", type=StepType.TOOL, tool="bad_func"),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "do bad thing"))
        types = [c["type"] for c in chunks]
        assert "step_error" in types
        assert "task_complete" in types

        tc = next(c for c in chunks if c["type"] == "task_complete")
        assert tc["status"] == "failed"

    @pytest.mark.asyncio
    async def test_tool_step_no_tool_specified(self):
        registry = {}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[StepDefinition(name="bad", type=StepType.TOOL)]  # no tool field
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))
        types = [c["type"] for c in chunks]
        assert "step_error" in types


class TestTaskExecutorAgentStep:
    @pytest.mark.asyncio
    async def test_agent_step_streaming(self):
        ai = MagicMock()

        async def mock_stream(*args, **kwargs):
            for text in ["Hello", " World"]:
                yield {"choices": [{"delta": {"content": text}}]}

        ai.chat_completion = AsyncMock(return_value=mock_stream())

        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task(
            steps=[
                StepDefinition(name="analyze", type=StepType.AGENT, description="Analyze data"),
            ],
            body="You are a network analyst.",
        )

        chunks = await _collect_chunks(executor.execute(task, "analyze my network"))

        stream_chunks = [c for c in chunks if c["type"] == "stream"]
        assert len(stream_chunks) == 2
        assert stream_chunks[0]["chunk"] == "Hello"
        assert stream_chunks[1]["chunk"] == " World"


class TestTaskExecutorGateStep:
    @pytest.mark.asyncio
    async def test_gate_step_confirmed(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task(
            steps=[
                StepDefinition(
                    name="confirm",
                    type=StepType.GATE,
                    message_template="Proceed with changes?",
                ),
            ]
        )

        chunks = []

        async def collect_and_confirm():
            async for chunk in executor.execute(task, "do it"):
                chunks.append(chunk)
                if chunk.get("type") == "confirmation_required":
                    # Simulate user confirmation
                    event = chunk["_event"]
                    event.set()

        await collect_and_confirm()

        types = [c["type"] for c in chunks]
        assert "confirmation_required" in types
        assert "task_complete" in types

        tc = next(c for c in chunks if c["type"] == "task_complete")
        assert tc["status"] == "completed"

    @pytest.mark.asyncio
    async def test_gate_step_denied(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task(
            steps=[
                StepDefinition(name="confirm", type=StepType.GATE),
            ]
        )

        session_ctx = {"session_id": "test"}
        chunks = []

        async def collect_and_deny():
            async for chunk in executor.execute(
                task, "do it", session_context=session_ctx
            ):
                chunks.append(chunk)
                if chunk.get("type") == "confirmation_required":
                    # Simulate denial
                    denial_key = chunk["_denial_key"]
                    ctx = chunk["_session_context"]
                    ctx[denial_key] = True
                    chunk["_event"].set()

        await collect_and_deny()

        tc = next(c for c in chunks if c["type"] == "task_complete")
        assert tc["status"] == "aborted"

    @pytest.mark.asyncio
    async def test_gate_step_timeout(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task(
            steps=[
                StepDefinition(name="confirm", type=StepType.GATE),
            ]
        )

        # Patch timeout to be very short
        with patch("scripts.task_executor.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            # We need to also patch the inner wait_for in _execute_gate_step
            # Actually the outer catch in execute() will handle it
            pass

        # Alternative: test via the gate step directly with a short timeout
        # For simplicity, test the timeout handling in the main loop
        chunks = []

        async def collect_timeout():
            async for chunk in executor.execute(task, "do it"):
                chunks.append(chunk)
                # Don't set the event — let it timeout

        # Override the gate step's wait_for to timeout immediately
        original_execute_gate = executor._execute_gate_step

        async def fast_timeout_gate(step, step_results, session_context):
            request_id = str(uuid.uuid4())
            confirm_event = asyncio.Event()
            yield {
                "type": "confirmation_required",
                "message": "confirm?",
                "request_id": request_id,
                "step": step.name,
                "_event": confirm_event,
                "_denial_key": f"_gate_denied_{request_id}",
                "_session_context": session_context,
            }
            # Immediate timeout
            yield {"type": "gate_result", "confirmed": False, "reason": "timeout"}

        executor._execute_gate_step = fast_timeout_gate
        await collect_timeout()

        tc = next(c for c in chunks if c["type"] == "task_complete")
        assert tc["status"] == "aborted"


class TestTaskExecutorCondition:
    @pytest.mark.asyncio
    async def test_condition_skip(self):
        def mock_func():
            return {"ok": True}

        registry = {"fn": mock_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(
                    name="conditional",
                    type=StepType.TOOL,
                    tool="fn",
                    condition="nonexistent.value",
                ),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))
        types = [c["type"] for c in chunks]
        assert "step_skipped" in types
        assert "function_result" not in types

    @pytest.mark.asyncio
    async def test_condition_met(self):
        call_count = 0

        def counting_func():
            nonlocal call_count
            call_count += 1
            return {"value": True}

        registry = {"fn": counting_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="first", type=StepType.TOOL, tool="fn"),
                StepDefinition(
                    name="second",
                    type=StepType.TOOL,
                    tool="fn",
                    condition="first.result.value",
                ),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))
        assert call_count == 2  # Both steps executed


class TestTaskExecutorArgsFrom:
    @pytest.mark.asyncio
    async def test_args_from_resolution(self):
        received_args = {}

        def step1():
            return {"network_id": "N_123"}

        def step2(**kwargs):
            received_args.update(kwargs)
            return {"ok": True}

        registry = {"step1_fn": step1, "step2_fn": step2}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="find", type=StepType.TOOL, tool="step1_fn"),
                StepDefinition(
                    name="use",
                    type=StepType.TOOL,
                    tool="step2_fn",
                    args_from="find.result",
                ),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))
        # step2 should have received the result from step1
        assert received_args.get("network_id") == "N_123"


class TestTaskExecutorHooks:
    @pytest.mark.asyncio
    async def test_pre_hook_runs(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task(hooks={"pre": "pre-analysis"})

        chunks = await _collect_chunks(executor.execute(task, "test"))
        hook_chunks = [c for c in chunks if c.get("type") == "hook_start"]
        assert len(hook_chunks) == 1
        assert hook_chunks[0]["phase"] == "pre"

    @pytest.mark.asyncio
    async def test_no_hooks_when_empty(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        task = _make_task()  # no hooks

        chunks = await _collect_chunks(executor.execute(task, "test"))
        hook_chunks = [c for c in chunks if c.get("type") == "hook_start"]
        assert len(hook_chunks) == 0


class TestTaskExecutorState:
    @pytest.mark.asyncio
    async def test_state_saved_on_completion(self, tmp_path):
        def mock_func():
            return {"ok": True}

        registry = {"fn": mock_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[StepDefinition(name="step1", type=StepType.TOOL, tool="fn")]
        )

        # Use tmp_path by patching Path construction
        with patch("scripts.task_executor.Path") as MockPath:
            mock_dir = MagicMock()
            MockPath.return_value.__truediv__ = MagicMock(return_value=mock_dir)
            mock_dir.__truediv__ = MagicMock(return_value=mock_dir)
            mock_dir.mkdir = MagicMock()
            mock_dir.write_text = MagicMock()

            chunks = await _collect_chunks(executor.execute(task, "test"))

            # Verify write_text was called (state saved)
            assert mock_dir.write_text.called

    @pytest.mark.asyncio
    async def test_state_saved_on_failure(self):
        def failing_func():
            raise RuntimeError("boom")

        registry = {"fn": failing_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[StepDefinition(name="bad", type=StepType.TOOL, tool="fn")]
        )

        with patch("scripts.task_executor.Path") as MockPath:
            mock_dir = MagicMock()
            MockPath.return_value.__truediv__ = MagicMock(return_value=mock_dir)
            mock_dir.__truediv__ = MagicMock(return_value=mock_dir)
            mock_dir.mkdir = MagicMock()
            mock_dir.write_text = MagicMock()

            chunks = await _collect_chunks(executor.execute(task, "test"))
            assert mock_dir.write_text.called


class TestTaskExecutorRollback:
    @pytest.mark.asyncio
    async def test_rollback_calls_execute_undo(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})

        state = TaskRunState(
            task_name="test",
            status=TaskStatus.FAILED,
            change_log=[
                ChangeEntry(action="update_vlan", resource_type="vlan"),
                ChangeEntry(action="add_firewall_rule", resource_type="firewall_rule"),
            ],
        )

        with patch("scripts.task_executor.execute_undo") as mock_undo:
            mock_undo.return_value = {"success": True}
            result = await executor.rollback(state)

        assert result["status"] == "rolled_back"
        assert len(result["rollback_results"]) == 2
        assert mock_undo.call_count == 2


class TestTaskExecutorSafety:
    @pytest.mark.asyncio
    async def test_safety_backup_before_write(self):
        def mock_write_func():
            return {"ok": True}

        registry = {"update_vlan": mock_write_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(
                    name="write",
                    type=StepType.TOOL,
                    tool="update_vlan",
                    args={"network_id": "N_123", "vlan_id": "100"},
                ),
            ]
        )

        with patch("scripts.task_executor.classify_operation") as mock_classify, \
             patch("scripts.task_executor.before_operation") as mock_before, \
             patch("scripts.task_executor.Path"):

            mock_classify.return_value = MagicMock(backup_required=True)
            mock_before.return_value = {
                "backup_created": True,
                "backup_path": "/clients/test/backups/backup.json",
            }

            chunks = await _collect_chunks(executor.execute(task, "update vlan"))

            mock_before.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_backup_for_safe_ops(self):
        def mock_read_func():
            return {"networks": []}

        registry = {"list_networks": mock_read_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="list", type=StepType.TOOL, tool="list_networks"),
            ]
        )

        with patch("scripts.task_executor.classify_operation") as mock_classify, \
             patch("scripts.task_executor.before_operation") as mock_before, \
             patch("scripts.task_executor.Path"):

            mock_classify.return_value = MagicMock(backup_required=False)

            chunks = await _collect_chunks(executor.execute(task, "list networks"))

            mock_before.assert_not_called()


class TestTaskExecutorMultiStep:
    @pytest.mark.asyncio
    async def test_three_step_sequence(self):
        results = []

        def step1():
            results.append("s1")
            return {"data": "from_step1"}

        def step2(**kwargs):
            results.append("s2")
            return {"data": "from_step2"}

        def step3():
            results.append("s3")
            return {"done": True}

        registry = {"s1": step1, "s2": step2, "s3": step3}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            steps=[
                StepDefinition(name="first", type=StepType.TOOL, tool="s1"),
                StepDefinition(name="second", type=StepType.TOOL, tool="s2"),
                StepDefinition(name="third", type=StepType.TOOL, tool="s3"),
            ]
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))

        # All 3 steps executed in order
        assert results == ["s1", "s2", "s3"]

        # Verify streaming contract
        types = [c["type"] for c in chunks]
        assert types.count("step_start") == 3
        assert types.count("function_result") == 3
        assert types.count("step_complete") == 3
        assert types.count("task_complete") == 1


class TestHelpers:
    def test_resolve_dot_path_simple(self):
        data = {"step1": {"result": {"network_id": "N_123"}}}
        result = TaskExecutor._resolve_dot_path("step1.result.network_id", data)
        assert result == "N_123"

    def test_resolve_dot_path_missing(self):
        data = {"step1": {"result": {}}}
        result = TaskExecutor._resolve_dot_path("step1.result.missing", data)
        assert result is None

    def test_resolve_dot_path_nested(self):
        data = {"a": {"b": {"c": {"d": 42}}}}
        assert TaskExecutor._resolve_dot_path("a.b.c.d", data) == 42

    def test_evaluate_condition_equality(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})
        step_results = {"check": {"level": "high"}}
        assert executor._evaluate_condition("check.level == high", step_results, {})
        assert not executor._evaluate_condition("check.level == low", step_results, {})

    def test_evaluate_condition_inequality(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})
        step_results = {"check": {"level": "high"}}
        assert executor._evaluate_condition("check.level != low", step_results, {})
        assert not executor._evaluate_condition("check.level != high", step_results, {})

    def test_evaluate_condition_truthy(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})
        step_results = {"step1": {"value": True}}
        assert executor._evaluate_condition("step1.value", step_results, {})

    def test_evaluate_condition_empty(self):
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry={})
        assert executor._evaluate_condition("", {}, {})
        assert executor._evaluate_condition(None, {}, {})

    def test_extract_stream_text_dict(self):
        chunk = {"choices": [{"delta": {"content": "hello"}}]}
        assert TaskExecutor._extract_stream_text(chunk) == "hello"

    def test_extract_stream_text_empty(self):
        assert TaskExecutor._extract_stream_text({}) is None
        assert TaskExecutor._extract_stream_text({"choices": []}) is None

    def test_infer_resource_type(self):
        assert TaskExecutor._infer_resource_type("update_vlan") == "vlan"
        assert TaskExecutor._infer_resource_type("add_firewall_rule") == "firewall_rule"
        assert TaskExecutor._infer_resource_type("configure_ssid") == "ssid"
        assert TaskExecutor._infer_resource_type("unknown_func") == "config"


class TestStreamingContract:
    """Verify the streaming dict contract matches AC#22-28."""

    @pytest.mark.asyncio
    async def test_complete_streaming_contract(self):
        def mock_func():
            return {"ok": True}

        registry = {"fn": mock_func}
        ai = MagicMock()
        settings = _make_settings()
        executor = TaskExecutor(ai, settings, function_registry=registry)

        task = _make_task(
            name="contract-test",
            steps=[StepDefinition(name="step1", type=StepType.TOOL, tool="fn")],
        )

        chunks = await _collect_chunks(executor.execute(task, "test"))

        # AC#22: task_start
        task_start = chunks[0]
        assert task_start["type"] == "task_start"
        assert task_start["task_name"] == "contract-test"
        assert "total_steps" in task_start
        assert "task_id" in task_start

        # AC#23: step_start
        step_starts = [c for c in chunks if c["type"] == "step_start"]
        assert len(step_starts) == 1
        assert step_starts[0]["step"] == "step1"
        assert "step_index" in step_starts[0]

        # AC#24: function_result
        func_results = [c for c in chunks if c["type"] == "function_result"]
        assert len(func_results) == 1
        assert "function" in func_results[0]
        assert "result" in func_results[0]
        assert "success" in func_results[0]

        # AC#27: step_complete
        step_completes = [c for c in chunks if c["type"] == "step_complete"]
        assert len(step_completes) == 1
        assert "status" in step_completes[0]

        # AC#28: task_complete
        task_complete = chunks[-1]
        assert task_complete["type"] == "task_complete"
        assert task_complete["task_name"] == "contract-test"
        assert task_complete["status"] == "completed"
        assert "summary" in task_complete
