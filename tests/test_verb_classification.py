"""
Tests for Story 7.7: Verb-Aware Classification in _quick_classify().

Covers:
- Action verbs boost meraki-specialist
- Analysis verbs boost network-analyst
- Overlapping keyword disambiguation (VLAN, firewall, switch, SSID, port)
- Mixed verb+keyword scenarios
- Existing classification accuracy preserved
"""

from scripts.agent_router import _quick_classify


# ==================== Core Verb Disambiguation ====================


class TestVerbDisambiguation:
    """AC#1-2: Verb context in _quick_classify()."""

    def test_analyze_vlans_routes_to_analyst(self):
        """AC#3: 'analyze my VLANs' → network-analyst."""
        result = _quick_classify("analyze my VLANs")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_configure_vlan_routes_to_specialist(self):
        """AC#4: 'configure VLAN 100 on network X' → meraki-specialist."""
        result = _quick_classify("configure VLAN 100 on network X")
        assert result is not None
        assert result.agent_name == "meraki-specialist"

    def test_show_firewall_rules_routes_to_analyst(self):
        """AC#5: 'show me the firewall rules' → network-analyst."""
        result = _quick_classify("show me the firewall rules")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_add_firewall_rule_routes_to_specialist(self):
        """AC#6: 'add a firewall rule to block port 23' → meraki-specialist."""
        result = _quick_classify("add a firewall rule to block port 23")
        assert result is not None
        assert result.agent_name == "meraki-specialist"


# ==================== Extended Overlapping Keywords ====================


class TestOverlappingKeywords:
    """Test all overlapping keywords from the story task list."""

    def test_check_switch_status(self):
        """Analysis verb + specialist keyword → analyst."""
        result = _quick_classify("check the switch status")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_configure_switch_port(self):
        """Action verb + specialist keyword → specialist."""
        result = _quick_classify("configure switch port 24 as trunk")
        assert result is not None
        assert result.agent_name == "meraki-specialist"

    def test_verify_ssid_settings(self):
        """Analysis verb + specialist keyword → analyst."""
        result = _quick_classify("verify the SSID settings")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_create_ssid_for_guests(self):
        """Action verb + specialist keyword → specialist."""
        result = _quick_classify("create a new SSID for guests")
        assert result is not None
        assert result.agent_name == "meraki-specialist"

    def test_inspect_acl_entries(self):
        """Analysis verb + specialist keyword → analyst."""
        result = _quick_classify("inspect the ACL entries on the switch")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_delete_acl_rule(self):
        """Action verb + specialist keyword → specialist."""
        result = _quick_classify("delete the ACL rule blocking port 80")
        assert result is not None
        assert result.agent_name == "meraki-specialist"

    def test_list_port_configurations(self):
        """Analysis verb + specialist keyword → analyst."""
        result = _quick_classify("list all port configurations")
        assert result is not None
        assert result.agent_name == "network-analyst"

    def test_update_port_vlan(self):
        """Action verb + specialist keyword → specialist."""
        result = _quick_classify("update port 5 to VLAN 200")
        assert result is not None
        assert result.agent_name == "meraki-specialist"


# ==================== Mixed Verb Scenarios ====================


class TestMixedVerbScenarios:
    """Mixed or no verb signals should fall back to keyword weights."""

    def test_mixed_verbs_uses_keywords(self):
        """Both action + analysis verbs → falls back to keyword scoring."""
        result = _quick_classify("check and update the VLAN settings")
        assert result is not None
        # Both verbs present, so no verb boost; keyword scoring takes over
        # "update" and "vlan" both match specialist patterns
        assert result.agent_name == "meraki-specialist"

    def test_no_verb_uses_keywords(self):
        """No verb → falls back to pure keyword scoring."""
        result = _quick_classify("VLAN 100 settings")
        assert result is not None
        # VLAN is specialist keyword, no verb to adjust
        assert result.agent_name == "meraki-specialist"


# ==================== Verb Boost Reasoning ====================


class TestVerbBoostReasoning:
    """Verify reasoning string includes verb-aware info."""

    def test_verb_boost_in_reasoning(self):
        """When verb boost applied, reasoning mentions it."""
        result = _quick_classify("analyze the firewall rules")
        assert result is not None
        assert "verb-aware" in result.reasoning

    def test_no_verb_boost_in_mixed(self):
        """When both verbs present, no verb boost."""
        result = _quick_classify("check and configure the switch")
        assert result is not None
        # Mixed verbs — no boost applied
        assert "verb-aware" not in result.reasoning


# ==================== Existing Accuracy Preservation ====================


class TestExistingAccuracy:
    """AC#7: Existing classification accuracy maintained (>96%)."""

    def test_pure_analyst_queries(self):
        """Standard analyst queries still work."""
        analyst_queries = [
            "scan the network for issues",
            "what devices are offline",
            "diagnose the connectivity problem",
            "show me the device inventory",
            "how many access points do we have",
        ]
        for q in analyst_queries:
            result = _quick_classify(q)
            assert result is not None, f"No match for: {q}"
            assert result.agent_name == "network-analyst", f"Wrong agent for: {q} (got {result.agent_name})"

    def test_pure_specialist_queries(self):
        """Standard specialist queries still work."""
        specialist_queries = [
            "configure the SSID to use WPA3",
            "block telnet on all switches",
            "add a VLAN for the guest network",
            "enable DHCP on VLAN 100",
            "set the firewall to deny port 23",
        ]
        for q in specialist_queries:
            result = _quick_classify(q)
            assert result is not None, f"No match for: {q}"
            assert result.agent_name == "meraki-specialist", f"Wrong agent for: {q} (got {result.agent_name})"

    def test_workflow_queries_unaffected(self):
        """Workflow queries still work — verb boost only affects analyst/specialist."""
        workflow_queries = [
            "create a new workflow template",
            "automate compliance checking",
            "set up a remediation handler for alerts",
        ]
        for q in workflow_queries:
            result = _quick_classify(q)
            assert result is not None, f"No match for: {q}"
            assert result.agent_name == "workflow-creator", f"Wrong agent for: {q} (got {result.agent_name})"

    def test_explicit_prefixes_still_work(self):
        """Explicit @agent prefixes are unaffected by verb boost."""
        assert _quick_classify("@analyst configure VLAN").agent_name == "network-analyst"
        assert _quick_classify("@specialist analyze the network").agent_name == "meraki-specialist"
        assert _quick_classify("@workflow check something").agent_name == "workflow-creator"
