"""
Deterministic Task Executor for CNL (Cisco Neural Language).

Runs pre-defined task steps sequentially in a Python loop.
The LLM only participates in 'agent' steps requiring interpretation.
Safety hooks run ALWAYS via safety.py — no LLM involvement.

Created: Story 7.1
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from scripts.ai_engine import AIEngine
from scripts.executor_utils import execute_function, serialize_result
from scripts.safety import (
    before_operation,
    classify_operation,
    execute_undo,
)
from scripts.settings import Settings
from scripts.task_models import (
    ChangeEntry,
    RiskLevel,
    StepDefinition,
    StepResult,
    StepStatus,
    StepType,
    TaskDefinition,
    TaskRunState,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Deterministic task executor that runs steps sequentially.

    The executor controls step ordering, safety hooks, and state
    persistence. The LLM only participates in ``agent`` steps.

    Args:
        ai_engine: AIEngine instance for agent steps
        settings: Current settings (for client info, feature flags)
        function_registry: The FUNCTION_REGISTRY dict from agent_router
    """

    def __init__(
        self,
        ai_engine: AIEngine,
        settings: Settings,
        function_registry: Optional[dict] = None,
    ) -> None:
        self.ai_engine = ai_engine
        self.settings = settings
        # Lazily import registry if not provided
        if function_registry is not None:
            self._registry = function_registry
        else:
            self._registry = None

    @property
    def registry(self) -> dict:
        """Lazy-load FUNCTION_REGISTRY to avoid circular imports."""
        if self._registry is None:
            from scripts.agent_router import FUNCTION_REGISTRY

            self._registry = FUNCTION_REGISTRY
        return self._registry

    # ==================== Main Execution Loop ====================

    async def execute(
        self,
        task_def: TaskDefinition,
        user_message: str,
        session_context: Optional[dict] = None,
        client_name: str = "",
    ) -> AsyncGenerator[dict, None]:
        """
        Execute a task definition step-by-step.

        Yields streaming dicts compatible with the WebSocket handler.

        Args:
            task_def: The parsed task definition
            user_message: Original user message
            session_context: Optional session context dict
            client_name: Client name for state persistence and backups
        """
        session_context = session_context or {}
        session_id = session_context.get("session_id", "default")
        client_name = client_name or self.settings.meraki_profile or "default"

        # Initialize run state
        state = TaskRunState(
            task_name=task_def.name,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )

        # Step results dict for args_from resolution
        step_results: dict[str, dict] = {}

        yield {
            "type": "task_start",
            "task_name": task_def.name,
            "total_steps": len(task_def.steps),
            "task_id": state.task_id,
        }

        # --- Pre-task hooks ---
        try:
            async for chunk in self._run_hooks(
                task_def, "pre", user_message, session_context
            ):
                yield chunk
        except Exception as exc:
            state.status = TaskStatus.FAILED
            self._save_state(state, client_name)
            yield {
                "type": "task_error",
                "error": f"Pre-task hook failed: {exc}",
                "task_name": task_def.name,
            }
            return

        # --- Step Loop ---
        for idx, step in enumerate(task_def.steps):
            state.current_step = idx

            # Evaluate condition — skip if False
            if step.condition and not self._evaluate_condition(
                step.condition, step_results, session_context
            ):
                step_result = StepResult(
                    step_name=step.name,
                    type=step.type,
                    status=StepStatus.SKIPPED,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                )
                state.steps_completed.append(step_result)
                yield {
                    "type": "step_skipped",
                    "step": step.name,
                    "step_index": idx,
                    "reason": f"Condition not met: {step.condition}",
                }
                continue

            yield {
                "type": "step_start",
                "step": step.name,
                "step_index": idx,
                "step_type": step.type.value,
            }

            step_result = StepResult(
                step_name=step.name,
                type=step.type,
                status=StepStatus.RUNNING,
                started_at=datetime.now(),
            )

            try:
                if step.type == StepType.TOOL:
                    result = await self._execute_tool_step(
                        step, step_results, state, client_name, session_id
                    )
                    step_result.result = result
                    step_result.status = StepStatus.COMPLETED
                    step_results[step.name] = result or {}
                    yield {
                        "type": "function_result",
                        "function": step.tool,
                        "result": result,
                        "success": True,
                        "step": step.name,
                    }

                elif step.type == StepType.AGENT:
                    collected_text = ""
                    async for chunk in self._execute_agent_step(
                        step, task_def, user_message, step_results, session_context
                    ):
                        yield chunk
                        if chunk.get("type") == "stream":
                            collected_text += chunk.get("chunk", "")
                    step_result.result = collected_text
                    step_result.status = StepStatus.COMPLETED
                    step_results[step.name] = {"text": collected_text}

                elif step.type == StepType.GATE:
                    confirmed = False
                    async for chunk in self._execute_gate_step(
                        step, step_results, session_context
                    ):
                        yield chunk
                        if chunk.get("type") == "gate_result":
                            confirmed = chunk.get("confirmed", False)

                    if not confirmed:
                        step_result.status = StepStatus.FAILED
                        step_result.error = "User denied or gate timed out"
                        step_result.completed_at = datetime.now()
                        state.steps_completed.append(step_result)
                        state.status = TaskStatus.FAILED
                        self._save_state(state, client_name)
                        yield {
                            "type": "step_complete",
                            "step": step.name,
                            "status": "denied",
                        }
                        yield {
                            "type": "task_complete",
                            "task_name": task_def.name,
                            "status": "aborted",
                            "summary": f"User denied at gate step: {step.name}",
                        }
                        return
                    step_result.status = StepStatus.COMPLETED
                    step_results[step.name] = {"confirmed": True}

            except asyncio.TimeoutError:
                step_result.status = StepStatus.FAILED
                step_result.error = "Gate step timed out (300s)"
                step_result.completed_at = datetime.now()
                state.steps_completed.append(step_result)
                state.status = TaskStatus.FAILED
                self._save_state(state, client_name)
                yield {
                    "type": "step_complete",
                    "step": step.name,
                    "status": "timeout",
                }
                yield {
                    "type": "task_complete",
                    "task_name": task_def.name,
                    "status": "failed",
                    "summary": f"Gate timed out: {step.name}",
                }
                return

            except Exception as exc:
                step_result.status = StepStatus.FAILED
                step_result.error = str(exc)
                step_result.completed_at = datetime.now()
                state.steps_completed.append(step_result)
                state.status = TaskStatus.FAILED
                self._save_state(state, client_name)
                yield {
                    "type": "step_error",
                    "step": step.name,
                    "error": str(exc),
                }
                yield {
                    "type": "task_complete",
                    "task_name": task_def.name,
                    "status": "failed",
                    "summary": f"Step failed: {step.name} — {exc}",
                }
                return

            step_result.completed_at = datetime.now()
            state.steps_completed.append(step_result)
            self._save_state(state, client_name)

            yield {
                "type": "step_complete",
                "step": step.name,
                "status": step_result.status.value,
            }

        # --- Post-task hooks ---
        try:
            async for chunk in self._run_hooks(
                task_def, "post", user_message, session_context
            ):
                yield chunk
        except Exception as exc:
            logger.warning(f"Post-task hook failed (non-fatal): {exc}")

        # --- Finalize ---
        state.status = TaskStatus.COMPLETED
        self._save_state(state, client_name)

        yield {
            "type": "task_complete",
            "task_name": task_def.name,
            "status": "completed",
            "summary": f"Task '{task_def.name}' completed successfully ({len(task_def.steps)} steps)",
        }

    # ==================== Step Handlers ====================

    async def _execute_tool_step(
        self,
        step: StepDefinition,
        step_results: dict,
        state: TaskRunState,
        client_name: str,
        session_id: str,
    ) -> Optional[dict]:
        """Execute a tool step via FUNCTION_REGISTRY.

        Integrates with safety.py: calls before_operation() for backup
        and classify_operation() for dynamic safety classification.
        """
        func_name = step.tool
        if not func_name:
            raise ValueError(f"Tool step '{step.name}' has no tool specified")

        # Resolve arguments
        args = self._resolve_args(step, step_results)

        # Safety integration: backup before write operations
        safety_check = classify_operation(func_name, args)
        if safety_check.backup_required:
            backup_result = before_operation(
                func_name, args, client_name, session_id
            )
            if backup_result.get("backup_created"):
                state.change_log.append(
                    ChangeEntry(
                        action=func_name,
                        resource_type=self._infer_resource_type(func_name),
                        resource_id=str(args.get("network_id", args.get("vlan_id", ""))),
                        backup_path=backup_result.get("backup_path", ""),
                        timestamp=datetime.now(),
                    )
                )

        # Execute via executor_utils
        success, result, error = await execute_function(
            func_name, args, self.registry
        )

        if not success:
            raise RuntimeError(f"Tool '{func_name}' failed: {error}")

        return result

    async def _execute_agent_step(
        self,
        step: StepDefinition,
        task_def: TaskDefinition,
        user_message: str,
        step_results: dict,
        session_context: dict,
    ) -> AsyncGenerator[dict, None]:
        """Execute an agent step via ai_engine.chat_completion with streaming."""
        # Build system prompt from task body + step description
        system_prompt = task_def.body or ""
        if step.description:
            system_prompt += f"\n\nCurrent step: {step.description}"

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Add prior step results as context if available
        if step_results:
            context_summary = json.dumps(
                {k: serialize_result(v) for k, v in step_results.items()},
                indent=2,
                default=str,
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Previous step results:\n```json\n{context_summary}\n```",
                }
            )

        try:
            session_id = session_context.get("session_id", "default")
            response = await self.ai_engine.chat_completion(
                messages=messages,
                stream=True,
                temperature=0.1,
                session_id=session_id,
            )

            async for chunk in response:
                # Extract text content from streaming chunk
                text = self._extract_stream_text(chunk)
                if text:
                    yield {"type": "stream", "chunk": text, "step": step.name}

        except Exception as exc:
            # Retry once with simplified prompt per AC#35
            logger.warning(f"Agent step '{step.name}' failed, retrying: {exc}")
            try:
                simple_messages = [
                    {"role": "system", "content": step.description or "Analyze the data."},
                    {"role": "user", "content": user_message},
                ]
                response = await self.ai_engine.chat_completion(
                    messages=simple_messages,
                    stream=True,
                    temperature=0.1,
                    session_id=session_context.get("session_id", "default"),
                )
                async for chunk in response:
                    text = self._extract_stream_text(chunk)
                    if text:
                        yield {"type": "stream", "chunk": text, "step": step.name}
            except Exception as retry_exc:
                raise RuntimeError(
                    f"Agent step '{step.name}' failed after retry: {retry_exc}"
                ) from retry_exc

    async def _execute_gate_step(
        self,
        step: StepDefinition,
        step_results: dict,
        session_context: dict,
    ) -> AsyncGenerator[dict, None]:
        """Execute a gate step — pauses for user confirmation.

        Uses asyncio.Event pattern (CRITICAL-2): yields the event object
        for the WebSocket handler to call event.set() on.
        """
        request_id = str(uuid.uuid4())
        confirm_event = asyncio.Event()
        # denial_flag tracked via session_context
        denial_key = f"_gate_denied_{request_id}"

        message = step.message_template or step.description or "Confirm to proceed?"
        # Template variable substitution
        for key, val in step_results.items():
            message = message.replace(f"{{{key}}}", str(val))

        yield {
            "type": "confirmation_required",
            "message": message,
            "request_id": request_id,
            "step": step.name,
            "_event": confirm_event,
            "_denial_key": denial_key,
            "_session_context": session_context,
        }

        # Wait for confirmation with timeout
        try:
            await asyncio.wait_for(confirm_event.wait(), timeout=300)
        except asyncio.TimeoutError:
            yield {"type": "gate_result", "confirmed": False, "reason": "timeout"}
            return

        # Check if it was a denial
        if session_context.get(denial_key, False):
            yield {"type": "gate_result", "confirmed": False, "reason": "denied"}
            return

        yield {"type": "gate_result", "confirmed": True}

    # ==================== Hooks ====================

    async def _run_hooks(
        self,
        task_def: TaskDefinition,
        phase: str,
        user_message: str,
        session_context: dict,
    ) -> AsyncGenerator[dict, None]:
        """Run pre-task or post-task hooks.

        Hooks are defined in task_def.hooks dict, keyed by phase name.
        Example: {"pre": "pre-task", "post": "post-task"}
        """
        hook_name = task_def.hooks.get(phase)
        if not hook_name:
            return

        yield {
            "type": "hook_start",
            "hook": hook_name,
            "phase": phase,
        }

        # Hooks are simple — just log/validate for now
        # In future, could load hook .md files and execute them
        logger.info(f"Running {phase}-task hook: {hook_name}")

        yield {
            "type": "hook_complete",
            "hook": hook_name,
            "phase": phase,
        }

    # ==================== State Persistence ====================

    def _save_state(self, state: TaskRunState, client_name: str) -> None:
        """Save task run state to JSON file."""
        try:
            state_dir = Path("clients") / client_name / "task-runs"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / f"{state.task_id}.json"
            state_file.write_text(
                json.dumps(state.to_dict(), indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(f"Failed to save task state: {exc}")

    @staticmethod
    def load_state(task_id: str, client_name: str) -> Optional[TaskRunState]:
        """Load task run state from JSON file."""
        state_file = Path("clients") / client_name / "task-runs" / f"{task_id}.json"
        if not state_file.exists():
            return None

        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return TaskRunState(
                task_id=data["task_id"],
                task_name=data["task_name"],
                status=TaskStatus(data["status"]),
                started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
                current_step=data.get("current_step", 0),
            )
        except Exception as exc:
            logger.warning(f"Failed to load task state {task_id}: {exc}")
            return None

    # ==================== Rollback ====================

    async def rollback(self, state: TaskRunState, session_id: str = "default") -> dict:
        """Rollback a failed task using safety.execute_undo().

        Iterates change_log in reverse and attempts undo for each entry.
        """
        results = []
        for entry in reversed(state.change_log):
            try:
                undo_result = execute_undo(session_id)
                results.append({"action": entry.action, "undo": undo_result})
            except ValueError as exc:
                results.append({"action": entry.action, "error": str(exc)})

        state.status = TaskStatus.ROLLED_BACK
        return {"rollback_results": results, "status": state.status.value}

    # ==================== Helpers ====================

    def _resolve_args(
        self, step: StepDefinition, step_results: dict
    ) -> dict:
        """Resolve step arguments from static args and args_from.

        Uses dot-notation path resolution per PO recommendation:
        e.g., ``args_from: "discover.result.networks"`` resolves to
        ``step_results["discover"]["result"]["networks"]``.
        """
        args = dict(step.args) if step.args else {}

        if step.args_from:
            resolved = self._resolve_dot_path(step.args_from, step_results)
            if isinstance(resolved, dict):
                args.update(resolved)
            else:
                args["_resolved"] = resolved

        return args

    @staticmethod
    def _resolve_dot_path(path: str, data: dict):
        """Resolve a dot-notation path against step results.

        Example: "discover.result.networks" resolves to
        data["discover"]["result"]["networks"].
        """
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _evaluate_condition(
        self, condition: str, step_results: dict, session_context: dict
    ) -> bool:
        """Evaluate a step condition string.

        Supports simple expressions:
        - "step_name.success" — check if step succeeded
        - "step_name.result.key" — check if a value is truthy
        - "risk_level == high" — compare risk level
        """
        if not condition:
            return True

        condition = condition.strip()

        # Simple equality check
        if "==" in condition:
            left, right = condition.split("==", 1)
            left_val = self._resolve_dot_path(left.strip(), step_results)
            right_val = right.strip().strip("'\"")
            return str(left_val) == right_val

        # Simple inequality
        if "!=" in condition:
            left, right = condition.split("!=", 1)
            left_val = self._resolve_dot_path(left.strip(), step_results)
            right_val = right.strip().strip("'\"")
            return str(left_val) != right_val

        # Truthy check on dot-path
        val = self._resolve_dot_path(condition, step_results)
        return bool(val)

    @staticmethod
    def _extract_stream_text(chunk) -> Optional[str]:
        """Extract text from a streaming LLM chunk."""
        if isinstance(chunk, dict):
            # Standard format: {"choices": [{"delta": {"content": "text"}}]}
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content")
        # LiteLLM ModelResponse object
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content"):
                return delta.content
        return None

    @staticmethod
    def _infer_resource_type(func_name: str) -> str:
        """Infer resource type from function name for change log."""
        mappings = {
            "vlan": "vlan",
            "firewall": "firewall_rule",
            "ssid": "ssid",
            "switch": "switch_port",
            "acl": "acl",
        }
        func_lower = func_name.lower()
        for keyword, resource in mappings.items():
            if keyword in func_lower:
                return resource
        return "config"
