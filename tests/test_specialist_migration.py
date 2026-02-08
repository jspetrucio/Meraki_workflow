"""
Tests for Story 7.6: Meraki Specialist Skill Migration.

Covers:
- YAML frontmatter parsing of 6 specialist task files
- Trigger keyword matching
- Risk levels (high/medium)
- Step definitions (safety gates mandatory for write tasks)
- Mandatory safety pattern: backup → preview → gate → apply → verify
- Catalyst detection and SGT preflight in configure-switching
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
    """AC#4-9: All 6 task files parse correctly."""

    def test_configure_wireless_parses(self):
        """AC#4: configure-wireless.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-wireless.md")
        assert task.name == "configure-wireless"
        assert task.agent == "meraki-specialist"
        assert task.risk_level == RiskLevel.HIGH

    def test_configure_wireless_steps(self):
        """AC#4: configure-wireless has 7 steps in correct order."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-wireless.md")
        assert len(task.steps) == 7
        step_names = [s.name for s in task.steps]
        assert step_names == [
            "parse_intent", "resolve_targets", "backup_current_state",
            "generate_preview", "confirm", "apply_changes", "verify",
        ]

    def test_configure_switching_parses(self):
        """AC#5: configure-switching.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-switching.md")
        assert task.name == "configure-switching"
        assert task.agent == "meraki-specialist"
        assert task.risk_level == RiskLevel.HIGH

    def test_configure_switching_steps(self):
        """AC#5: configure-switching has 9 steps with catalyst/SGT."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-switching.md")
        assert len(task.steps) == 9
        step_names = [s.name for s in task.steps]
        assert step_names == [
            "parse_intent", "resolve_targets", "catalyst_detection",
            "sgt_preflight_check", "backup_current_state",
            "generate_preview", "confirm", "apply_changes", "verify",
        ]

    def test_configure_security_parses(self):
        """AC#6: configure-security.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-security.md")
        assert task.name == "configure-security"
        assert task.agent == "meraki-specialist"
        assert len(task.steps) == 7

    def test_configure_monitoring_parses(self):
        """AC#7: configure-monitoring.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-monitoring.md")
        assert task.name == "configure-monitoring"
        assert task.agent == "meraki-specialist"
        assert task.risk_level == RiskLevel.MEDIUM

    def test_configure_monitoring_no_gate(self):
        """AC#7: configure-monitoring has NO gate step (low risk)."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-monitoring.md")
        step_types = [s.type for s in task.steps]
        assert StepType.GATE not in step_types
        assert len(task.steps) == 4

    def test_rollback_parses(self):
        """AC#8: rollback.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "rollback.md")
        assert task.name == "rollback"
        assert task.agent == "meraki-specialist"
        assert task.risk_level == RiskLevel.HIGH

    def test_rollback_steps(self):
        """AC#8: rollback has gate for backup selection + preview + confirm."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "rollback.md")
        assert len(task.steps) == 7
        step_names = [s.name for s in task.steps]
        assert "select_backup" in step_names
        assert "generate_preview" in step_names
        assert "confirm_rollback" in step_names
        gate_step = next(s for s in task.steps if s.name == "select_backup")
        assert gate_step.type == StepType.GATE
        confirm_step = next(s for s in task.steps if s.name == "confirm_rollback")
        assert confirm_step.type == StepType.GATE

    def test_executar_especifico_parses(self):
        """AC#9: executar-especifico.md has valid frontmatter."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "executar-especifico.md")
        assert task.name == "executar-especifico"
        assert task.agent == "meraki-specialist"
        assert task.risk_level == RiskLevel.HIGH
        assert task.trigger_keywords == []


# ==================== Safety Pattern Tests ====================


class TestSafetyPattern:
    """AC#10-13: Mandatory safety pattern for write tasks."""

    @pytest.fixture(params=[
        "configure-wireless",
        "configure-switching",
        "configure-security",
    ])
    def write_task(self, request):
        """Load each write task."""
        return parse_task_file(
            TASKS_DIR / "meraki-specialist" / f"{request.param}.md"
        )

    def test_backup_before_changes(self, write_task):
        """AC#10: Every write task has backup_current_state BEFORE apply."""
        step_names = [s.name for s in write_task.steps]
        backup_idx = step_names.index("backup_current_state")
        apply_idx = step_names.index("apply_changes")
        assert backup_idx < apply_idx, (
            f"{write_task.name}: backup at {backup_idx}, apply at {apply_idx}"
        )

    def test_gate_before_apply(self, write_task):
        """AC#11: Every write task has a gate step BEFORE apply."""
        step_names = [s.name for s in write_task.steps]
        confirm_idx = step_names.index("confirm")
        apply_idx = step_names.index("apply_changes")
        assert confirm_idx < apply_idx

    def test_verify_after_apply(self, write_task):
        """AC#12: Every write task has verify step AFTER apply."""
        step_names = [s.name for s in write_task.steps]
        apply_idx = step_names.index("apply_changes")
        verify_idx = step_names.index("verify")
        assert verify_idx > apply_idx

    def test_gate_is_gate_type(self, write_task):
        """Gate step is actually StepType.GATE."""
        confirm = next(s for s in write_task.steps if s.name == "confirm")
        assert confirm.type == StepType.GATE

    def test_switching_has_catalyst_detection(self):
        """AC#13: configure-switching has catalyst_detection BEFORE backup."""
        task = parse_task_file(
            TASKS_DIR / "meraki-specialist" / "configure-switching.md"
        )
        step_names = [s.name for s in task.steps]
        assert "catalyst_detection" in step_names
        assert "sgt_preflight_check" in step_names
        cat_idx = step_names.index("catalyst_detection")
        sgt_idx = step_names.index("sgt_preflight_check")
        backup_idx = step_names.index("backup_current_state")
        assert cat_idx < backup_idx, "catalyst_detection must be before backup"
        assert sgt_idx < backup_idx, "sgt_preflight_check must be before backup"

    def test_catalyst_detection_tool(self):
        """catalyst_detection uses detect_catalyst_mode tool."""
        task = parse_task_file(
            TASKS_DIR / "meraki-specialist" / "configure-switching.md"
        )
        cat_step = next(s for s in task.steps if s.name == "catalyst_detection")
        assert cat_step.type == StepType.TOOL
        assert cat_step.tool == "detect_catalyst_mode"

    def test_sgt_preflight_tool(self):
        """sgt_preflight uses sgt_preflight_check tool (matching FUNCTION_REGISTRY)."""
        task = parse_task_file(
            TASKS_DIR / "meraki-specialist" / "configure-switching.md"
        )
        sgt_step = next(s for s in task.steps if s.name == "sgt_preflight_check")
        assert sgt_step.type == StepType.TOOL
        assert sgt_step.tool == "sgt_preflight_check"


# ==================== Trigger Keywords Tests ====================


class TestTriggerKeywords:
    """AC#14-19: Trigger keywords correctly defined."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_wireless_keywords(self, registry):
        """AC#14: configure-wireless keywords."""
        task = registry.get_task("configure-wireless")
        assert task is not None
        assert "ssid" in task.trigger_keywords
        assert "wifi" in task.trigger_keywords
        assert "wireless" in task.trigger_keywords

    def test_switching_keywords(self, registry):
        """AC#15: configure-switching keywords."""
        task = registry.get_task("configure-switching")
        assert task is not None
        assert "vlan" in task.trigger_keywords
        assert "acl" in task.trigger_keywords
        assert "sgt" in task.trigger_keywords

    def test_security_keywords(self, registry):
        """AC#16: configure-security keywords."""
        task = registry.get_task("configure-security")
        assert task is not None
        assert "firewall" in task.trigger_keywords
        assert "vpn" in task.trigger_keywords
        assert "nat" in task.trigger_keywords

    def test_monitoring_keywords(self, registry):
        """AC#17: configure-monitoring keywords."""
        task = registry.get_task("configure-monitoring")
        assert task is not None
        assert "alert" in task.trigger_keywords
        assert "snmp" in task.trigger_keywords
        assert "syslog" in task.trigger_keywords

    def test_rollback_keywords(self, registry):
        """AC#18: rollback keywords."""
        task = registry.get_task("rollback")
        assert task is not None
        assert "rollback" in task.trigger_keywords
        assert "undo" in task.trigger_keywords
        assert "revert" in task.trigger_keywords

    def test_executar_no_keywords(self, registry):
        """AC#19: executar-especifico has no keywords (fallback)."""
        task = registry.get_task("executar-especifico")
        assert task is not None
        assert task.trigger_keywords == []


# ==================== Risk Level Tests ====================


class TestRiskLevels:
    """AC#20-25: Risk levels correctly assigned."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_high_risk_tasks(self, registry):
        """AC#20-22,24-25: High-risk tasks."""
        high_risk = [
            "configure-wireless",
            "configure-switching",
            "configure-security",
            "rollback",
            "executar-especifico",
        ]
        for name in high_risk:
            task = registry.get_task(name)
            assert task is not None, f"Task {name} not found"
            assert task.risk_level == RiskLevel.HIGH, f"{name} is not high risk"

    def test_medium_risk_monitoring(self, registry):
        """AC#23: configure-monitoring is medium risk."""
        task = registry.get_task("configure-monitoring")
        assert task is not None
        assert task.risk_level == RiskLevel.MEDIUM


# ==================== Integration Verification ====================


class TestIntegrationVerification:
    """IV1-IV5: Integration verification tests."""

    @pytest.fixture
    def registry(self):
        reg = TaskRegistry()
        reg.load_tasks(TASKS_DIR)
        return reg

    def test_iv1_vlan_matches_switching(self, registry):
        """IV1: 'configure VLAN 100 on switch X' -> configure-switching."""
        task = registry.find_matching_task("configure VLAN 100 on switch X")
        assert task is not None
        assert task.name == "configure-switching"

    def test_iv2_firewall_matches_security(self, registry):
        """IV2: 'add firewall rule to block port 23' -> configure-security."""
        task = registry.find_matching_task("add firewall rule to block port 23")
        assert task is not None
        assert task.name == "configure-security"

    def test_iv3_undo_matches_rollback(self, registry):
        """IV3: 'undo last change' -> rollback."""
        task = registry.find_matching_task("undo last change")
        assert task is not None
        assert task.name == "rollback"

    def test_iv4_switching_has_catalyst_before_write(self, registry):
        """IV4: configure-switching runs catalyst_detection before any write."""
        task = registry.get_task("configure-switching")
        step_names = [s.name for s in task.steps]
        cat_idx = step_names.index("catalyst_detection")
        apply_idx = step_names.index("apply_changes")
        assert cat_idx < apply_idx

    def test_iv5_all_write_tasks_have_backup(self, registry):
        """IV5: All write tasks create backup before applying changes."""
        write_tasks = [
            "configure-wireless",
            "configure-switching",
            "configure-security",
        ]
        for name in write_tasks:
            task = registry.get_task(name)
            step_names = [s.name for s in task.steps]
            assert "backup_current_state" in step_names, f"{name} missing backup"
            backup_idx = step_names.index("backup_current_state")
            apply_idx = step_names.index("apply_changes")
            assert backup_idx < apply_idx, f"{name}: backup after apply"

    def test_ssid_matches_wireless(self, registry):
        """'create a new SSID for guests' -> configure-wireless."""
        task = registry.find_matching_task("create a new SSID for guests")
        assert task is not None
        assert task.name == "configure-wireless"

    def test_acl_matches_switching(self, registry):
        """'add ACL to block telnet' -> configure-switching."""
        task = registry.find_matching_task("add ACL to block telnet")
        assert task is not None
        assert task.name == "configure-switching"

    def test_rollback_revert_match(self, registry):
        """'revert the last configuration' -> rollback."""
        task = registry.find_matching_task("revert the last configuration")
        assert task is not None
        assert task.name == "rollback"

    def test_vpn_matches_security(self, registry):
        """'configure VPN tunnel to branch office' -> configure-security."""
        task = registry.find_matching_task("configure VPN tunnel to branch office")
        assert task is not None
        assert task.name == "configure-security"

    def test_snmp_matches_monitoring(self, registry):
        """'enable SNMP monitoring' -> configure-monitoring."""
        task = registry.find_matching_task("enable SNMP monitoring")
        assert task is not None
        assert task.name == "configure-monitoring"


# ==================== Hooks Tests ====================


class TestHooks:
    """Task hooks are correctly defined."""

    def test_write_tasks_have_hooks(self):
        """Write tasks have pre/post hooks."""
        for name in ["configure-wireless", "configure-switching", "configure-security"]:
            task = parse_task_file(TASKS_DIR / "meraki-specialist" / f"{name}.md")
            assert task.hooks is not None, f"{name} missing hooks"
            assert task.hooks.get("pre") == "pre-task", f"{name} missing pre hook"
            assert task.hooks.get("post") == "post-task", f"{name} missing post hook"

    def test_rollback_has_hooks(self):
        """Rollback also has hooks for audit logging."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "rollback.md")
        assert task.hooks.get("pre") == "pre-task"
        assert task.hooks.get("post") == "post-task"

    def test_executar_has_hooks(self):
        """executar-especifico (high-risk fallback) has pre/post hooks for safety."""
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "executar-especifico.md")
        assert task.hooks.get("pre") == "pre-task"
        assert task.hooks.get("post") == "post-task"


# ==================== Body Content Tests ====================


class TestBodyContent:
    """Markdown body preserved for agent steps."""

    def test_wireless_body(self):
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-wireless.md")
        assert "SSID" in task.body
        assert "Safety Rules" in task.body

    def test_switching_body(self):
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-switching.md")
        assert "Catalyst" in task.body
        assert "SGT" in task.body

    def test_security_body(self):
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "configure-security.md")
        assert "Firewall" in task.body or "firewall" in task.body

    def test_rollback_body(self):
        task = parse_task_file(TASKS_DIR / "meraki-specialist" / "rollback.md")
        assert "rollback" in task.body.lower()
