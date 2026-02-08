"""
Tests for Story 7.2: YAML Frontmatter Parser & Task Registry.

Covers:
- verb_utils.py shared verb sets
- task_registry.py parser and registry
- Verb-aware matching (HIGH-1)
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.verb_utils import ACTION_VERBS, ANALYSIS_VERBS, detect_verb_type
from scripts.task_models import (
    RiskLevel,
    StepType,
    TaskDefinition,
    TaskParseError,
)
from scripts.task_registry import (
    TaskRegistry,
    parse_task_file,
)


# ==================== verb_utils.py Tests ====================


class TestVerbUtils:
    def test_action_verbs_content(self):
        assert "configure" in ACTION_VERBS
        assert "create" in ACTION_VERBS
        assert "delete" in ACTION_VERBS
        assert "update" in ACTION_VERBS

    def test_analysis_verbs_content(self):
        assert "analyze" in ANALYSIS_VERBS
        assert "check" in ANALYSIS_VERBS
        assert "show" in ANALYSIS_VERBS
        assert "status" in ANALYSIS_VERBS

    def test_no_overlap(self):
        overlap = ACTION_VERBS & ANALYSIS_VERBS
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_detect_action_only(self):
        has_action, has_analysis = detect_verb_type("configure VLAN 100")
        assert has_action is True
        assert has_analysis is False

    def test_detect_analysis_only(self):
        has_action, has_analysis = detect_verb_type("analyze my VLANs")
        assert has_action is False
        assert has_analysis is True

    def test_detect_both(self):
        has_action, has_analysis = detect_verb_type("check and update VLAN")
        assert has_action is True
        assert has_analysis is True

    def test_detect_neither(self):
        has_action, has_analysis = detect_verb_type("hello world")
        assert has_action is False
        assert has_analysis is False


# ==================== Parser Tests ====================


VALID_TASK_MD = """---
name: test-task
agent: network-analyst
trigger_keywords: [vlan, network, analyze]
risk_level: low
steps:
  - name: discover
    type: tool
    tool: full_discovery
  - name: report
    type: agent
    description: "Generate report"
---

# System Prompt

You are a network analyst. Analyze the data.
"""

MINIMAL_TASK_MD = """---
name: minimal
agent: network-analyst
---
Body text here.
"""

NO_FRONTMATTER_MD = """# Just a regular markdown file
No frontmatter here.
"""

INVALID_YAML_MD = """---
name: bad
agent: [invalid: yaml: here
---
Body.
"""

MISSING_FIELDS_MD = """---
trigger_keywords: [test]
---
Body.
"""

INVALID_STEP_TYPE_MD = """---
name: bad-steps
agent: test
steps:
  - name: bad_step
    type: unknown_type
---
"""

STEP_MISSING_NAME_MD = """---
name: bad-steps
agent: test
steps:
  - type: tool
    tool: some_func
---
"""


class TestParseTaskFile:
    def test_valid_task(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(VALID_TASK_MD)
        task = parse_task_file(f)

        assert task.name == "test-task"
        assert task.agent == "network-analyst"
        assert task.trigger_keywords == ["vlan", "network", "analyze"]
        assert task.risk_level == RiskLevel.LOW
        assert len(task.steps) == 2
        assert task.steps[0].type == StepType.TOOL
        assert task.steps[0].tool == "full_discovery"
        assert task.steps[1].type == StepType.AGENT
        assert "network analyst" in task.body.lower()

    def test_minimal_task(self, tmp_path):
        f = tmp_path / "minimal.md"
        f.write_text(MINIMAL_TASK_MD)
        task = parse_task_file(f)

        assert task.name == "minimal"
        assert task.agent == "network-analyst"
        assert task.trigger_keywords == []
        assert task.steps == []
        assert task.body == "Body text here."

    def test_file_not_found(self):
        with pytest.raises(TaskParseError, match="File not found"):
            parse_task_file("/nonexistent/file.md")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        with pytest.raises(TaskParseError, match="empty"):
            parse_task_file(f)

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "nofm.md"
        f.write_text(NO_FRONTMATTER_MD)
        with pytest.raises(TaskParseError, match="No YAML frontmatter"):
            parse_task_file(f)

    def test_invalid_yaml(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text(INVALID_YAML_MD)
        with pytest.raises(TaskParseError, match="Invalid YAML"):
            parse_task_file(f)

    def test_missing_required_fields(self, tmp_path):
        f = tmp_path / "missing.md"
        f.write_text(MISSING_FIELDS_MD)
        with pytest.raises(TaskParseError, match="Missing required fields"):
            parse_task_file(f)

    def test_invalid_step_type(self, tmp_path):
        f = tmp_path / "badsteps.md"
        f.write_text(INVALID_STEP_TYPE_MD)
        with pytest.raises(TaskParseError, match="invalid type"):
            parse_task_file(f)

    def test_step_missing_name(self, tmp_path):
        f = tmp_path / "noname.md"
        f.write_text(STEP_MISSING_NAME_MD)
        with pytest.raises(TaskParseError, match="missing 'name'"):
            parse_task_file(f)

    def test_source_file_preserved(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(VALID_TASK_MD)
        task = parse_task_file(f)
        assert task.source_file == str(f)

    def test_risk_level_high(self, tmp_path):
        content = """---
name: risky
agent: meraki-specialist
risk_level: high
---
Body.
"""
        f = tmp_path / "risky.md"
        f.write_text(content)
        task = parse_task_file(f)
        assert task.risk_level == RiskLevel.HIGH

    def test_hooks_parsed(self, tmp_path):
        content = """---
name: hooked
agent: test
hooks:
  pre: pre-analysis
  post: post-analysis
---
Body.
"""
        f = tmp_path / "hooked.md"
        f.write_text(content)
        task = parse_task_file(f)
        assert task.hooks["pre"] == "pre-analysis"
        assert task.hooks["post"] == "post-analysis"


# ==================== Registry Tests ====================


class TestTaskRegistry:
    def _make_task_files(self, tmp_path):
        """Create a directory with sample task files."""
        analyst_dir = tmp_path / "network-analyst"
        analyst_dir.mkdir()

        spec_dir = tmp_path / "meraki-specialist"
        spec_dir.mkdir()

        # Analyst task
        (analyst_dir / "analyze-network.md").write_text("""---
name: analyze-network
agent: network-analyst
trigger_keywords: [analyze, network, scan, discovery, health]
risk_level: low
steps:
  - name: discover
    type: tool
    tool: full_discovery
---
Analyze the network thoroughly.
""")

        # Specialist task
        (spec_dir / "configure-switching.md").write_text("""---
name: configure-switching
agent: meraki-specialist
trigger_keywords: [vlan, acl, switch, trunk, stp, port]
risk_level: high
steps:
  - name: parse_intent
    type: agent
  - name: confirm
    type: gate
    message_template: "Proceed?"
  - name: apply
    type: tool
    tool: update_switch_acls
---
Configure switching infrastructure.
""")

        return tmp_path

    def test_load_tasks(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        tasks = registry.load_tasks(root)
        assert len(tasks) == 2
        assert "analyze-network" in tasks
        assert "configure-switching" in tasks

    def test_load_nonexistent_dir(self):
        registry = TaskRegistry()
        tasks = registry.load_tasks(Path("/nonexistent/dir"))
        assert len(tasks) == 0

    def test_find_matching_task_analyst(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.find_matching_task("analyze my network health")
        assert task is not None
        assert task.name == "analyze-network"

    def test_find_matching_task_specialist(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.find_matching_task("configure vlan 100 on switch")
        assert task is not None
        assert task.name == "configure-switching"

    def test_find_no_match(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.find_matching_task("hello world")
        assert task is None

    def test_verb_awareness_analysis_query(self, tmp_path):
        """HIGH-1: 'analyze my VLANs' should NOT match configure-switching."""
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.find_matching_task("analyze my VLANs")
        # Should NOT match configure-switching (high risk, write task)
        # VLAN keyword matches configure-switching but "analyze" is analysis verb
        assert task is None or task.name != "configure-switching"

    def test_verb_awareness_action_query(self, tmp_path):
        """HIGH-1: 'configure VLAN 100' should match configure-switching."""
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.find_matching_task("configure vlan on the switch")
        assert task is not None
        assert task.name == "configure-switching"

    def test_minimum_threshold(self, tmp_path):
        """Need 2+ keywords or 1 keyword + matching verb."""
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        # Single keyword without matching verb — no match
        task = registry.find_matching_task("something about vlan only")
        assert task is None

    def test_register_task(self):
        registry = TaskRegistry()
        task = TaskDefinition(
            name="custom-task",
            agent="test",
            trigger_keywords=["custom", "test"],
        )
        registry.register_task(task)
        assert registry.get_task("custom-task") is not None

    def test_list_tasks(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)
        names = registry.list_tasks()
        assert sorted(names) == ["analyze-network", "configure-switching"]

    def test_reload(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)
        assert len(registry.tasks) == 2

        count = registry.reload()
        assert count == 2

    def test_get_task(self, tmp_path):
        root = self._make_task_files(tmp_path)
        registry = TaskRegistry()
        registry.load_tasks(root)

        task = registry.get_task("analyze-network")
        assert task is not None
        assert task.agent == "network-analyst"

        assert registry.get_task("nonexistent") is None

    def test_empty_message(self):
        registry = TaskRegistry()
        assert registry.find_matching_task("") is None
        assert registry.find_matching_task(None) is None

    def test_empty_registry(self):
        registry = TaskRegistry()
        assert registry.find_matching_task("analyze network") is None

    def test_multiword_keyword(self, tmp_path):
        d = tmp_path / "tasks"
        d.mkdir()
        (d / "test.md").write_text("""---
name: switch-port-task
agent: meraki-specialist
trigger_keywords: [switch port, trunk port]
risk_level: medium
steps:
  - name: step1
    type: tool
    tool: configure_switch_port
---
Configure switch ports.
""")
        registry = TaskRegistry()
        registry.load_tasks(d)

        task = registry.find_matching_task("configure switch port on device")
        assert task is not None
        assert task.name == "switch-port-task"
