"""
YAML Frontmatter Parser & Task Registry for CNL.

Parses task .md files with YAML frontmatter into TaskDefinition objects
and provides keyword-based matching with verb awareness.

Created: Story 7.2
"""

import logging
import re
from pathlib import Path
from typing import Optional

import yaml

from scripts.task_models import (
    RiskLevel,
    StepDefinition,
    StepType,
    TaskDefinition,
    TaskParseError,
)
from scripts.verb_utils import ACTION_VERBS, ANALYSIS_VERBS, detect_verb_type

logger = logging.getLogger(__name__)

# Regex to split YAML frontmatter from Markdown body
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?(.*)",
    re.DOTALL,
)

# Required fields in frontmatter
_REQUIRED_FIELDS = {"name", "agent"}

# Valid step types
_VALID_STEP_TYPES = {"tool", "agent", "gate"}


# ==================== Parser ====================


def parse_task_file(file_path: str | Path) -> TaskDefinition:
    """Parse a task .md file with YAML frontmatter.

    Extracts YAML frontmatter between ``---`` delimiters and preserves
    the Markdown body for agent steps.

    Args:
        file_path: Path to the .md file

    Returns:
        Parsed TaskDefinition

    Raises:
        TaskParseError: If file cannot be parsed or validation fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise TaskParseError(str(file_path), "File not found")

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise TaskParseError(str(file_path), f"Cannot read file: {exc}") from exc

    if not content.strip():
        raise TaskParseError(str(file_path), "File is empty")

    # Extract frontmatter
    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise TaskParseError(str(file_path), "No YAML frontmatter found (expected --- delimiters)")

    yaml_text = match.group(1)
    body = match.group(2).strip()

    # Parse YAML
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise TaskParseError(str(file_path), f"Invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise TaskParseError(str(file_path), "Frontmatter must be a YAML mapping")

    # Validate required fields
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise TaskParseError(str(file_path), f"Missing required fields: {', '.join(sorted(missing))}")

    # Parse steps
    steps = _parse_steps(data.get("steps", []), file_path)

    # Parse risk level
    risk_str = data.get("risk_level", "low").lower()
    try:
        risk_level = RiskLevel(risk_str)
    except ValueError:
        risk_level = RiskLevel.LOW

    return TaskDefinition(
        name=data["name"],
        agent=data["agent"],
        trigger_keywords=data.get("trigger_keywords", []),
        risk_level=risk_level,
        steps=steps,
        hooks=data.get("hooks", {}),
        description=data.get("description", ""),
        source_file=str(file_path),
        body=body,
    )


def _parse_steps(steps_data: list, file_path: Path) -> list[StepDefinition]:
    """Parse and validate step definitions from YAML data."""
    if not isinstance(steps_data, list):
        return []

    parsed = []
    for idx, step_data in enumerate(steps_data):
        if not isinstance(step_data, dict):
            raise TaskParseError(
                str(file_path),
                f"Step {idx} must be a mapping, got {type(step_data).__name__}",
            )

        name = step_data.get("name")
        if not name:
            raise TaskParseError(str(file_path), f"Step {idx} missing 'name' field")

        step_type_str = step_data.get("type")
        if not step_type_str:
            raise TaskParseError(str(file_path), f"Step '{name}' missing 'type' field")

        if step_type_str not in _VALID_STEP_TYPES:
            raise TaskParseError(
                str(file_path),
                f"Step '{name}' has invalid type '{step_type_str}' (expected: {_VALID_STEP_TYPES})",
            )

        parsed.append(
            StepDefinition(
                name=name,
                type=StepType(step_type_str),
                description=step_data.get("description", ""),
                tool=step_data.get("tool"),
                args=step_data.get("args"),
                args_from=step_data.get("args_from"),
                condition=step_data.get("condition"),
                message_template=step_data.get("message_template"),
            )
        )

    return parsed


# ==================== Registry ====================


class TaskRegistry:
    """Registry of available modular task definitions.

    Loads task .md files from directories and provides keyword-based
    matching with verb awareness.

    Usage:
        registry = TaskRegistry()
        registry.load_tasks(Path("CNL_agents"))
        task = registry.find_matching_task("analyze my VLANs")
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskDefinition] = {}

    @property
    def tasks(self) -> dict[str, TaskDefinition]:
        """All registered tasks keyed by name."""
        return dict(self._tasks)

    def load_tasks(self, directory: Path) -> dict[str, TaskDefinition]:
        """Scan directory recursively for task .md files.

        Args:
            directory: Root directory to scan

        Returns:
            Dict of loaded tasks keyed by name
        """
        directory = Path(directory)
        if not directory.exists():
            logger.warning(f"Task directory does not exist: {directory}")
            return {}

        loaded = 0
        for md_file in sorted(directory.rglob("*.md")):
            try:
                task = parse_task_file(md_file)
                self._tasks[task.name] = task
                loaded += 1
                logger.debug(f"Loaded task: {task.name} from {md_file}")
            except TaskParseError as exc:
                logger.warning(f"Skipping invalid task file: {exc}")
            except Exception as exc:
                logger.warning(f"Unexpected error loading {md_file}: {exc}")

        logger.info(f"TaskRegistry loaded {loaded} tasks from {directory}")
        return dict(self._tasks)

    def register_task(self, task: TaskDefinition) -> None:
        """Register a single task definition.

        Args:
            task: The task definition to register
        """
        self._tasks[task.name] = task

    def find_matching_task(self, message: str) -> Optional[TaskDefinition]:
        """Find the best matching task for a user message.

        Uses keyword matching with verb awareness (HIGH-1):
        - If message has only analysis verbs, don't match write/config tasks
        - Minimum threshold: 2+ keywords OR 1 keyword + matching verb
        - Case-insensitive, whole-word matching
        - On ties, prefer higher risk_level (more specific)

        Args:
            message: User message

        Returns:
            Best matching TaskDefinition, or None
        """
        if not self._tasks or not message:
            return None

        message_lower = message.lower()
        message_words = set(message_lower.split())
        has_action, has_analysis = detect_verb_type(message)

        best_task: Optional[TaskDefinition] = None
        best_score: float = 0.0

        for task in self._tasks.values():
            if not task.trigger_keywords:
                continue

            # Count keyword matches (whole word, case-insensitive)
            keyword_count = 0
            for keyword in task.trigger_keywords:
                kw_lower = keyword.lower()
                # Multi-word keywords: check substring
                if " " in kw_lower:
                    if kw_lower in message_lower:
                        keyword_count += 1
                else:
                    if kw_lower in message_words:
                        keyword_count += 1

            if keyword_count == 0:
                continue

            # Verb-awareness filter (HIGH-1)
            task_is_write = task.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
            if task_is_write and has_analysis and not has_action:
                # Analysis query + write task = skip
                continue

            # Minimum threshold: 2+ keywords OR 1 keyword + matching verb
            verb_match = (task_is_write and has_action) or (not task_is_write and has_analysis)
            if keyword_count < 2 and not (keyword_count >= 1 and verb_match):
                continue

            # Score: keyword count + verb bonus
            score = keyword_count
            if verb_match:
                score += 0.5

            if score > best_score:
                best_score = score
                best_task = task
            elif score == best_score and best_task is not None:
                # Tie-break: prefer higher risk (more specific)
                risk_order = {RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
                if risk_order.get(task.risk_level, 0) > risk_order.get(best_task.risk_level, 0):
                    best_task = task

        return best_task

    def reload(self, directory: Optional[Path] = None) -> int:
        """Hot-reload: clear and re-scan tasks.

        Args:
            directory: Directory to scan (uses previous dirs if None)

        Returns:
            Number of tasks loaded
        """
        # Gather source directories from existing tasks
        if directory is None:
            dirs = {Path(t.source_file).parent for t in self._tasks.values() if t.source_file}
        else:
            dirs = {Path(directory)}

        self._tasks.clear()
        for d in dirs:
            self.load_tasks(d)

        return len(self._tasks)

    def get_task(self, name: str) -> Optional[TaskDefinition]:
        """Get a specific task by name."""
        return self._tasks.get(name)

    def list_tasks(self) -> list[str]:
        """List all registered task names."""
        return list(self._tasks.keys())
