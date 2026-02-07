"""
Shared data models for the CNL Deterministic Task Executor.

Contains all dataclasses and exceptions used by task_executor.py,
task_registry.py, and downstream consumers.

Created: Story 7.1 (MEDIUM-2 amendment)
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ==================== Exceptions ====================


class TaskParseError(Exception):
    """Raised when a task .md file cannot be parsed.

    Attributes:
        file_path: Path to the file that failed to parse
        message: Human-readable error description
    """

    def __init__(self, file_path: str, message: str) -> None:
        self.file_path = file_path
        self.message = message
        super().__init__(f"Failed to parse {file_path}: {message}")


# ==================== Enums ====================


class StepType(str, Enum):
    """Types of steps in a task definition."""

    TOOL = "tool"
    AGENT = "agent"
    GATE = "gate"


class TaskStatus(str, Enum):
    """Execution status for a task run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StepStatus(str, Enum):
    """Execution status for an individual step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    """Risk level for a task definition."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ==================== Step & Task Definitions ====================


@dataclass
class StepDefinition:
    """A single step within a task definition.

    Attributes:
        name: Human-readable step name
        type: Step type (tool, agent, gate)
        description: What this step does
        tool: Function name for tool steps (from FUNCTION_REGISTRY)
        args: Static arguments for tool steps
        args_from: Dot-notation path to resolve args from prior step results
        condition: Optional condition expression to evaluate
        message_template: Template for agent/gate steps
    """

    name: str
    type: StepType
    description: str = ""
    tool: Optional[str] = None
    args: Optional[dict] = None
    args_from: Optional[str] = None
    condition: Optional[str] = None
    message_template: Optional[str] = None


@dataclass
class TaskDefinition:
    """A parsed task definition from a YAML-frontmatter .md file.

    Attributes:
        name: Unique task name (e.g., "analyze-network")
        agent: Which agent owns this task (network-analyst, meraki-specialist)
        trigger_keywords: Keywords that activate this task
        risk_level: Declared risk level
        steps: Ordered list of step definitions
        hooks: Pre/post hooks configuration
        description: Human-readable description
        source_file: Path to the .md file this was parsed from
        body: Markdown body (used as LLM prompt for agent steps)
    """

    name: str
    agent: str
    trigger_keywords: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    steps: list[StepDefinition] = field(default_factory=list)
    hooks: dict = field(default_factory=dict)
    description: str = ""
    source_file: str = ""
    body: str = ""


# ==================== Runtime State ====================


@dataclass
class StepResult:
    """Result of executing a single step.

    Attributes:
        step_name: Name of the step
        type: Step type
        status: Execution status
        result: Return value (for tool steps) or generated text (for agent steps)
        error: Error message if failed
        started_at: Timestamp when step started
        completed_at: Timestamp when step completed
    """

    step_name: str
    type: StepType
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "step_name": self.step_name,
            "type": self.type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ChangeEntry:
    """Record of a change made during task execution.

    Attributes:
        action: What was done (e.g., "update_vlan", "add_firewall_rule")
        resource_type: Type of resource modified (e.g., "vlan", "firewall_rule")
        resource_id: Identifier of the resource
        backup_path: Path to the backup file created before the change
        timestamp: When the change was made
    """

    action: str
    resource_type: str
    resource_id: str = ""
    backup_path: str = ""
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "backup_path": self.backup_path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class TaskRunState:
    """Persistent state for a task execution run.

    Attributes:
        task_id: Unique run identifier (UUID)
        task_name: Name of the task definition
        status: Current execution status
        started_at: When the run began
        steps_completed: Results of completed steps
        current_step: Index of the current/last step
        change_log: Record of all changes for rollback
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    steps_completed: list[StepResult] = field(default_factory=list)
    current_step: int = 0
    change_log: list[ChangeEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict for persistence."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "steps_completed": [s.to_dict() for s in self.steps_completed],
            "current_step": self.current_step,
            "change_log": [c.to_dict() for c in self.change_log],
        }
