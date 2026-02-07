"""
Tests for Story 7.5: Network Analyst Skill Migration.

Covers:
- YAML frontmatter parsing of 5 analyst task files
- Trigger keyword matching
- Risk levels
- Step definitions
- Integration with TaskRegistry
- Legacy fallback
"""

from pathlib import Path

import pytest

from scripts.task_models import RiskLevel, StepType
from scripts.task_registry import TaskRegistry, parse_task_file


TASKS_DIR = Path(__file__).parent.parent / "tasks"


# ==================== File Parsing Tests ====================


class TestTaskFileParsing:
    """AC#4-8: All 5 task files parse correctly."""

    def test_discovery_completo_parses(self):
        """AC#4: discovery-completo.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "discovery-completo.md")
        assert task.name == "discovery-completo"
        assert task.agent == "network-analyst"
        assert task.risk_level == RiskLevel.LOW

    def test_discovery_completo_steps(self):
        """AC#4: discovery-completo has 7 steps."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "discovery-completo.md")
        assert len(task.steps) == 7
        assert task.steps[0].type == StepType.TOOL
        assert task.steps[0].tool == "full_discovery"
        assert task.steps[3].type == StepType.AGENT
        assert task.steps[5].type == StepType.GATE

    def test_health_check_parses(self):
        """AC#5: health-check.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "health-check.md")
        assert task.name == "health-check"
        assert task.agent == "network-analyst"
        assert len(task.steps) == 4

    def test_security_audit_parses(self):
        """AC#6: security-audit.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "security-audit.md")
        assert task.name == "security-audit"
        assert task.agent == "network-analyst"
        assert len(task.steps) == 5

    def test_drift_detection_parses(self):
        """AC#7: drift-detection.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "drift-detection.md")
        assert task.name == "drift-detection"
        assert task.agent == "network-analyst"
        assert len(task.steps) == 4

    def test_investigar_especifico_parses(self):
        """AC#8: investigar-especifico.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "network-analyst" / "investigar-especifico.md")
        assert task.name == "investigar-especifico"
        assert task.agent == "network-analyst"
        assert len(task.steps) == 4
        # No trigger keywords (fallback task)
        assert task.trigger_keywords == []


# ==================== Trigger Keywords Tests ====================


class TestTriggerKeywords:
    """AC#9-13: Trigger keywords correctly defined."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_discovery_keywords(self, registry):
        """AC#9: discovery-completo keywords."""
        task = registry.get_task("discovery-completo")
        assert task is not None
        assert "discovery" in task.trigger_keywords
        assert "scan" in task.trigger_keywords
        assert "analyze network" in task.trigger_keywords

    def test_health_check_keywords(self, registry):
        """AC#10: health-check keywords."""
        task = registry.get_task("health-check")
        assert task is not None
        assert "health" in task.trigger_keywords
        assert "status" in task.trigger_keywords

    def test_security_audit_keywords(self, registry):
        """AC#11: security-audit keywords."""
        task = registry.get_task("security-audit")
        assert task is not None
        assert "security" in task.trigger_keywords
        assert "audit" in task.trigger_keywords
        assert "compliance" in task.trigger_keywords

    def test_drift_detection_keywords(self, registry):
        """AC#12: drift-detection keywords."""
        task = registry.get_task("drift-detection")
        assert task is not None
        assert "drift" in task.trigger_keywords
        assert "baseline" in task.trigger_keywords
        assert "what changed" in task.trigger_keywords

    def test_investigar_no_keywords(self, registry):
        """AC#13: investigar-especifico has no keywords (fallback)."""
        task = registry.get_task("investigar-especifico")
        assert task is not None
        assert task.trigger_keywords == []


# ==================== Risk Level Tests ====================


class TestRiskLevels:
    """AC#14: All analyst tasks are low risk."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_all_tasks_low_risk(self, registry):
        """AC#14: All Network Analyst tasks have risk_level: low."""
        analyst_tasks = [
            "discovery-completo",
            "health-check",
            "security-audit",
            "drift-detection",
            "investigar-especifico",
        ]
        for name in analyst_tasks:
            task = registry.get_task(name)
            assert task is not None, f"Task {name} not found"
            assert task.risk_level == RiskLevel.LOW, f"{name} is not low risk"


# ==================== Integration Verification ====================


class TestIntegrationVerification:
    """IV1-IV4: Integration verification tests."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_iv1_discovery_match(self, registry):
        """IV1: 'do a full discovery of my network' → discovery-completo."""
        task = registry.find_matching_task("do a full discovery of my network")
        assert task is not None
        assert task.name == "discovery-completo"

    def test_iv2_health_check_match(self, registry):
        """IV2: 'check the health of network N_123' → health-check."""
        task = registry.find_matching_task("check the health of network N_123")
        assert task is not None
        assert task.name == "health-check"

    def test_iv3_vlan_no_match(self, registry):
        """IV3: 'configure a VLAN' → None (not an analyst task)."""
        task = registry.find_matching_task("configure a VLAN")
        # Should NOT match any analyst task (configure is action verb + no analyst keywords)
        if task is not None:
            assert task.agent != "network-analyst" or task.name not in [
                "discovery-completo", "health-check", "security-audit",
                "drift-detection", "investigar-especifico"
            ]

    def test_security_audit_match(self, registry):
        """Security audit keyword matching."""
        task = registry.find_matching_task("run a security audit on the network")
        assert task is not None
        assert task.name == "security-audit"

    def test_drift_detection_match(self, registry):
        """Drift detection keyword matching."""
        task = registry.find_matching_task("check for configuration drift since baseline")
        assert task is not None
        assert task.name == "drift-detection"

    def test_scan_matches_discovery(self, registry):
        """'scan the network' → discovery-completo."""
        task = registry.find_matching_task("scan the network for me")
        assert task is not None
        assert task.name == "discovery-completo"


# ==================== Hooks Tests ====================


class TestHooks:
    """Task hooks are correctly defined."""

    def test_discovery_has_hooks(self):
        task = parse_task_file(TASKS_DIR / "network-analyst" / "discovery-completo.md")
        assert task.hooks is not None
        assert task.hooks.get("pre") == "pre-analysis"
        assert task.hooks.get("post") == "post-analysis"

    def test_other_tasks_no_hooks(self):
        """Non-discovery tasks don't require hooks."""
        for name in ["health-check", "security-audit", "drift-detection", "investigar-especifico"]:
            task = parse_task_file(TASKS_DIR / "network-analyst" / f"{name}.md")
            # May or may not have hooks — just verify parsing doesn't fail
            assert task.name == name


# ==================== Body Content Tests ====================


class TestBodyContent:
    """Markdown body preserved for agent steps."""

    def test_discovery_body_contains_instructions(self):
        task = parse_task_file(TASKS_DIR / "network-analyst" / "discovery-completo.md")
        assert "Count everything" in task.body
        assert "Highlight critical issues" in task.body

    def test_health_check_body(self):
        task = parse_task_file(TASKS_DIR / "network-analyst" / "health-check.md")
        assert "health" in task.body.lower()

    def test_security_audit_body(self):
        task = parse_task_file(TASKS_DIR / "network-analyst" / "security-audit.md")
        assert "security audit" in task.body.lower()
