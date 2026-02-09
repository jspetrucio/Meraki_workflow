"""
Tests for Epic 8: Network Security & Monitoring.

Tests all 5 stories (8.1-8.5):
- Story 8.1: Site-to-Site VPN
- Story 8.2: Content Filtering
- Story 8.3: IPS/Intrusion Detection
- Story 8.4: AMP/Malware Protection
- Story 8.5: Traffic Shaping
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Import modules to test
from scripts import api, discovery, config
from scripts.agent_router import FUNCTION_REGISTRY
from scripts.agent_tools import TOOL_SAFETY
from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel
from meraki.exceptions import APIError


class TestEpic8API(unittest.TestCase):
    """Test api.py methods for Epic 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = api.MerakiClient()
        self.client.dashboard = MagicMock()
        self.network_id = "N_123456"
        self.org_id = "123456"

    # ==================== Story 8.1: VPN ====================

    def test_get_vpn_config(self):
        """Test get_vpn_config calls correct SDK method."""
        expected = {"mode": "spoke", "hubs": []}
        self.client.dashboard.appliance.getNetworkApplianceSiteToSiteVpn.return_value = expected

        result = self.client.get_vpn_config(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceSiteToSiteVpn.assert_called_once_with(
            self.network_id
        )

    def test_update_vpn_config(self):
        """Test update_vpn_config calls correct SDK method."""
        expected = {"mode": "hub"}
        self.client.dashboard.appliance.updateNetworkApplianceSiteToSiteVpn.return_value = expected

        result = self.client.update_vpn_config(self.network_id, mode="hub")

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.updateNetworkApplianceSiteToSiteVpn.assert_called_once_with(
            self.network_id, mode="hub"
        )

    def test_get_vpn_statuses(self):
        """Test get_vpn_statuses calls correct SDK method."""
        expected = [{"networkId": "N_1", "vpnMode": "spoke"}]
        self.client.dashboard.appliance.getOrganizationApplianceVpnStatuses.return_value = expected

        result = self.client.get_vpn_statuses(self.org_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getOrganizationApplianceVpnStatuses.assert_called_once_with(
            self.org_id
        )

    # ==================== Story 8.2: Content Filtering ====================

    def test_get_content_filtering(self):
        """Test get_content_filtering calls correct SDK method."""
        expected = {"blockedUrlPatterns": ["*.gambling.*"]}
        self.client.dashboard.appliance.getNetworkApplianceContentFiltering.return_value = expected

        result = self.client.get_content_filtering(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceContentFiltering.assert_called_once_with(
            self.network_id
        )

    def test_update_content_filtering(self):
        """Test update_content_filtering calls correct SDK method."""
        expected = {"blockedUrlPatterns": ["*.gambling.*", "*.adult.*"]}
        self.client.dashboard.appliance.updateNetworkApplianceContentFiltering.return_value = expected

        result = self.client.update_content_filtering(
            self.network_id, blockedUrlPatterns=["*.gambling.*", "*.adult.*"]
        )

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.updateNetworkApplianceContentFiltering.assert_called_once_with(
            self.network_id, blockedUrlPatterns=["*.gambling.*", "*.adult.*"]
        )

    def test_get_content_categories(self):
        """Test get_content_categories calls correct SDK method."""
        expected = {"categories": ["adult", "gambling"]}
        self.client.dashboard.appliance.getNetworkApplianceContentFilteringCategories.return_value = expected

        result = self.client.get_content_categories(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceContentFilteringCategories.assert_called_once_with(
            self.network_id
        )

    # ==================== Story 8.3: IPS ====================

    def test_get_intrusion_settings(self):
        """Test get_intrusion_settings calls correct SDK method."""
        expected = {"mode": "prevention", "idsRulesets": "balanced"}
        self.client.dashboard.appliance.getNetworkApplianceSecurityIntrusion.return_value = expected

        result = self.client.get_intrusion_settings(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceSecurityIntrusion.assert_called_once_with(
            self.network_id
        )

    def test_update_intrusion_settings(self):
        """Test update_intrusion_settings calls correct SDK method."""
        expected = {"mode": "detection"}
        self.client.dashboard.appliance.updateNetworkApplianceSecurityIntrusion.return_value = expected

        result = self.client.update_intrusion_settings(self.network_id, mode="detection")

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.updateNetworkApplianceSecurityIntrusion.assert_called_once_with(
            self.network_id, mode="detection"
        )

    # ==================== Story 8.4: AMP ====================

    def test_get_malware_settings(self):
        """Test get_malware_settings calls correct SDK method."""
        expected = {"mode": "enabled"}
        self.client.dashboard.appliance.getNetworkApplianceSecurityMalware.return_value = expected

        result = self.client.get_malware_settings(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceSecurityMalware.assert_called_once_with(
            self.network_id
        )

    def test_update_malware_settings(self):
        """Test update_malware_settings calls correct SDK method."""
        expected = {"mode": "disabled"}
        self.client.dashboard.appliance.updateNetworkApplianceSecurityMalware.return_value = expected

        result = self.client.update_malware_settings(self.network_id, mode="disabled")

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.updateNetworkApplianceSecurityMalware.assert_called_once_with(
            self.network_id, mode="disabled"
        )

    # ==================== Story 8.5: Traffic Shaping ====================

    def test_get_traffic_shaping(self):
        """Test get_traffic_shaping calls correct SDK method."""
        expected = {"rules": []}
        self.client.dashboard.appliance.getNetworkApplianceTrafficShapingRules.return_value = expected

        result = self.client.get_traffic_shaping(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceTrafficShapingRules.assert_called_once_with(
            self.network_id
        )

    def test_update_traffic_shaping(self):
        """Test update_traffic_shaping calls correct SDK method."""
        expected = {"rules": [{"priority": "high"}]}
        self.client.dashboard.appliance.updateNetworkApplianceTrafficShapingRules.return_value = expected

        result = self.client.update_traffic_shaping(self.network_id, rules=[{"priority": "high"}])

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.updateNetworkApplianceTrafficShapingRules.assert_called_once_with(
            self.network_id, rules=[{"priority": "high"}]
        )

    def test_get_uplink_bandwidth(self):
        """Test get_uplink_bandwidth calls correct SDK method."""
        expected = {"bandwidthLimits": {"wan1": {"limitUp": 100, "limitDown": 100}}}
        self.client.dashboard.appliance.getNetworkApplianceTrafficShapingUplinkBandwidth.return_value = expected

        result = self.client.get_uplink_bandwidth(self.network_id)

        self.assertEqual(result, expected)
        self.client.dashboard.appliance.getNetworkApplianceTrafficShapingUplinkBandwidth.assert_called_once_with(
            self.network_id
        )


class TestEpic8Discovery(unittest.TestCase):
    """Test discovery.py functions for Epic 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock(spec=api.MerakiClient)
        self.network_id = "N_123456"
        self.org_id = "123456"

    # ==================== Story 8.1: VPN ====================

    def test_discover_vpn_topology(self):
        """Test discover_vpn_topology returns expected data structure."""
        self.client.org_id = self.org_id
        self.client.safe_call = MagicMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
        self.client.get_networks.return_value = [
            {"id": "N_1", "name": "HQ", "productTypes": ["appliance"]},
            {"id": "N_2", "name": "Branch", "productTypes": ["switch"]},
        ]
        self.client.get_vpn_config.return_value = {"mode": "hub"}
        self.client.get_vpn_statuses.return_value = [{"networkId": "N_1", "vpnMode": "hub"}]

        result = discovery.discover_vpn_topology(self.org_id, self.client)

        self.assertIn("vpn_configs", result)
        self.assertIn("vpn_statuses", result)
        self.assertIn("mx_networks", result)
        self.assertEqual(len(result["mx_networks"]), 1)
        self.assertEqual(result["mx_networks"][0]["id"], "N_1")

    # ==================== Story 8.2: Content Filtering ====================

    def test_discover_content_filtering(self):
        """Test discover_content_filtering returns expected data."""
        self.client.safe_call = MagicMock(
            return_value={"blockedUrlPatterns": ["*.gambling.*"], "urlCategoryListSize": "fullList"}
        )

        result = discovery.discover_content_filtering(self.network_id, self.client)

        self.assertIn("blockedUrlPatterns", result)
        self.assertEqual(result["blockedUrlPatterns"], ["*.gambling.*"])

    # ==================== Story 8.3: IPS ====================

    def test_discover_ips_settings(self):
        """Test discover_ips_settings returns expected data."""
        self.client.safe_call = MagicMock(return_value={"mode": "prevention", "idsRulesets": "balanced"})

        result = discovery.discover_ips_settings(self.network_id, self.client)

        self.assertIn("mode", result)
        self.assertEqual(result["mode"], "prevention")

    # ==================== Story 8.4: AMP ====================

    def test_discover_amp_settings(self):
        """Test discover_amp_settings returns expected data."""
        self.client.safe_call = MagicMock(return_value={"mode": "enabled"})

        result = discovery.discover_amp_settings(self.network_id, self.client)

        self.assertIn("mode", result)
        self.assertEqual(result["mode"], "enabled")

    # ==================== Story 8.5: Traffic Shaping ====================

    def test_discover_traffic_shaping(self):
        """Test discover_traffic_shaping returns expected data."""
        self.client.safe_call = MagicMock(return_value={"rules": [], "defaultRulesEnabled": True})

        result = discovery.discover_traffic_shaping(self.network_id, self.client)

        self.assertIn("rules", result)
        self.assertIsInstance(result["rules"], list)


class TestEpic8Config(unittest.TestCase):
    """Test config.py functions for Epic 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock(spec=api.MerakiClient)
        self.network_id = "N_123456"
        self.org_id = "123456"
        self.client_name = "test-client"

    @patch("scripts.config.backup_config")
    def test_configure_s2s_vpn_success(self, mock_backup):
        """Test configure_s2s_vpn creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_vpn_config.return_value = {"mode": "hub"}

        result = config.configure_s2s_vpn(
            self.network_id, mode="hub", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "vpn")
        mock_backup.assert_called_once()
        self.client.update_vpn_config.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_configure_s2s_vpn_dry_run(self, mock_backup):
        """Test configure_s2s_vpn dry-run does NOT call update."""
        result = config.configure_s2s_vpn(
            self.network_id, mode="hub", dry_run=True, client=self.client
        )

        self.assertTrue(result.success)
        self.assertIn("DRY-RUN", result.message)
        mock_backup.assert_not_called()
        self.client.update_vpn_config.assert_not_called()

    @patch("scripts.config.backup_config")
    def test_configure_s2s_vpn_api_error(self, mock_backup):
        """Test configure_s2s_vpn handles APIError gracefully."""
        mock_backup.return_value = Path("backup.json")
        # Build proper APIError with all required fields
        mock_response = MagicMock()
        mock_response.status_code = 404
        metadata = {
            "tags": ["test"],
            "operation": "updateNetworkApplianceSiteToSiteVpn",
            "url": "https://api.meraki.com/api/v1/networks/N_123/appliance/vpn/siteToSite",
            "user_agent": "test",
        }
        self.client.update_vpn_config.side_effect = APIError(metadata, mock_response)

        result = config.configure_s2s_vpn(
            self.network_id, mode="hub", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertFalse(result.success)
        self.assertIn("Falha", result.message)

    @patch("scripts.config.backup_config")
    def test_add_vpn_peer_success(self, mock_backup):
        """Test add_vpn_peer creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.get_vpn_config.return_value = {"thirdPartyPeers": []}
        self.client.update_vpn_config.return_value = {"thirdPartyPeers": [{"name": "Branch"}]}

        result = config.add_vpn_peer(
            self.network_id,
            name="Branch",
            public_ip="1.2.3.4",
            private_subnets=["10.0.0.0/24"],
            secret="secret123",
            backup=True,
            client_name=self.client_name,
            client=self.client,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "vpn_peer")
        mock_backup.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_configure_content_filter_success(self, mock_backup):
        """Test configure_content_filter creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_content_filtering.return_value = {"blockedUrlPatterns": ["*.gambling.*"]}

        result = config.configure_content_filter(
            self.network_id,
            blocked_url_patterns=["*.gambling.*"],
            backup=True,
            client_name=self.client_name,
            client=self.client,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "content_filtering")
        mock_backup.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_add_blocked_url_success(self, mock_backup):
        """Test add_blocked_url appends to existing list."""
        mock_backup.return_value = Path("backup.json")
        self.client.get_content_filtering.return_value = {"blockedUrlPatterns": ["*.gambling.*"]}
        self.client.update_content_filtering.return_value = {
            "blockedUrlPatterns": ["*.gambling.*", "*.adult.*"]
        }

        result = config.add_blocked_url(
            self.network_id, url="*.adult.*", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "blocked_url")
        self.client.update_content_filtering.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_configure_ips_success(self, mock_backup):
        """Test configure_ips creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_intrusion_settings.return_value = {"mode": "prevention"}

        result = config.configure_ips(
            self.network_id, mode="prevention", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "ips")
        mock_backup.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_set_ips_mode_success(self, mock_backup):
        """Test set_ips_mode wrapper calls configure_ips."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_intrusion_settings.return_value = {"mode": "detection"}

        result = config.set_ips_mode(
            self.network_id, mode="detection", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "ips")

    @patch("scripts.config.backup_config")
    def test_configure_amp_success(self, mock_backup):
        """Test configure_amp creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_malware_settings.return_value = {"mode": "enabled"}

        result = config.configure_amp(
            self.network_id, mode="enabled", backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "amp")
        mock_backup.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_configure_traffic_shaping_success(self, mock_backup):
        """Test configure_traffic_shaping creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.update_traffic_shaping.return_value = {"rules": []}

        result = config.configure_traffic_shaping(
            self.network_id, rules=[], backup=True, client_name=self.client_name, client=self.client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "traffic_shaping")
        mock_backup.assert_called_once()

    @patch("scripts.config.backup_config")
    def test_set_bandwidth_limit_success(self, mock_backup):
        """Test set_bandwidth_limit creates backup and returns ConfigResult."""
        mock_backup.return_value = Path("backup.json")
        self.client.get_uplink_bandwidth.return_value = {"bandwidthLimits": {}}

        result = config.set_bandwidth_limit(
            self.network_id,
            wan1_up=100,
            wan1_down=100,
            backup=True,
            client_name=self.client_name,
            client=self.client,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.resource_type, "bandwidth_limit")
        mock_backup.assert_called_once()


class TestEpic8IssueDetection(unittest.TestCase):
    """Test issue detection for Epic 8 security features."""

    def test_vpn_peer_down_issue(self):
        """Test VPN peer down issue detection (placeholder - full test needs real data)."""
        # This is a placeholder test - full implementation would need proper mock data
        pass

    def test_content_filter_permissive_issue(self):
        """Test content filter permissive issue detection."""
        from scripts.discovery import DiscoveryResult, NetworkInfo
        from datetime import datetime

        result = DiscoveryResult(
            timestamp=datetime.now(),
            org_id="123",
            org_name="Test Org",
            networks=[NetworkInfo(id="N_1", name="Net1", organization_id="123", product_types=["appliance"])],
            devices=[],
            configurations={
                "N_1": {
                    "content_filtering": {"urlCategoryListSize": "topSites", "blockedUrlCategories": []},
                    "ips_settings": {},
                    "amp_settings": {},
                }
            },
            issues=[],
            suggestions=[],
        )

        issues = discovery.find_issues(result)

        # Should detect content_filter_permissive issue
        issue_types = [i["type"] for i in issues]
        self.assertIn("content_filter_permissive", issue_types)

    def test_ips_disabled_issue(self):
        """Test IPS disabled issue detection."""
        from scripts.discovery import DiscoveryResult, NetworkInfo
        from datetime import datetime

        result = DiscoveryResult(
            timestamp=datetime.now(),
            org_id="123",
            org_name="Test Org",
            networks=[NetworkInfo(id="N_1", name="Net1", organization_id="123", product_types=["appliance"])],
            devices=[],
            configurations={
                "N_1": {
                    "content_filtering": {},
                    "ips_settings": {"mode": "disabled"},
                    "amp_settings": {},
                }
            },
            issues=[],
            suggestions=[],
        )

        issues = discovery.find_issues(result)

        # Should detect ips_disabled issue
        issue_types = [i["type"] for i in issues]
        self.assertIn("ips_disabled", issue_types)

    def test_amp_disabled_issue(self):
        """Test AMP disabled issue detection."""
        from scripts.discovery import DiscoveryResult, NetworkInfo
        from datetime import datetime

        result = DiscoveryResult(
            timestamp=datetime.now(),
            org_id="123",
            org_name="Test Org",
            networks=[NetworkInfo(id="N_1", name="Net1", organization_id="123", product_types=["appliance"])],
            devices=[],
            configurations={
                "N_1": {
                    "content_filtering": {},
                    "ips_settings": {},
                    "amp_settings": {"mode": "disabled"},
                }
            },
            issues=[],
            suggestions=[],
        )

        issues = discovery.find_issues(result)

        # Should detect amp_disabled issue
        issue_types = [i["type"] for i in issues]
        self.assertIn("amp_disabled", issue_types)


class TestEpic8Registry(unittest.TestCase):
    """Test FUNCTION_REGISTRY and SAFETY_CLASSIFICATION entries."""

    def test_all_discovery_functions_in_registry(self):
        """Test all Epic 8 discovery functions are in FUNCTION_REGISTRY."""
        discovery_functions = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
        ]

        for func_name in discovery_functions:
            self.assertIn(func_name, FUNCTION_REGISTRY, f"{func_name} missing from FUNCTION_REGISTRY")

    def test_all_config_functions_in_registry(self):
        """Test all Epic 8 config functions are in FUNCTION_REGISTRY."""
        config_functions = [
            "configure_s2s_vpn",
            "add_vpn_peer",
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        for func_name in config_functions:
            self.assertIn(func_name, FUNCTION_REGISTRY, f"{func_name} missing from FUNCTION_REGISTRY")

    def test_all_functions_in_safety_classification(self):
        """Test all Epic 8 functions have SAFETY_CLASSIFICATION entries."""
        all_functions = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
            "configure_s2s_vpn",
            "add_vpn_peer",
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        for func_name in all_functions:
            self.assertIn(
                func_name, SAFETY_CLASSIFICATION, f"{func_name} missing from SAFETY_CLASSIFICATION"
            )

    def test_all_functions_in_tool_safety(self):
        """Test all Epic 8 functions have TOOL_SAFETY entries."""
        all_functions = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
            "configure_s2s_vpn",
            "add_vpn_peer",
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        for func_name in all_functions:
            self.assertIn(func_name, TOOL_SAFETY, f"{func_name} missing from TOOL_SAFETY")

    def test_safety_levels_match(self):
        """Test SAFETY_CLASSIFICATION and TOOL_SAFETY have same levels for Epic 8 functions."""
        from scripts.agent_tools import SafetyLevel as ToolSafetyLevel

        all_functions = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
            "configure_s2s_vpn",
            "add_vpn_peer",
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        for func_name in all_functions:
            safety_level = SAFETY_CLASSIFICATION[func_name]
            tool_safety_level = TOOL_SAFETY[func_name]

            # Both are enums, compare values
            self.assertEqual(
                safety_level.value,
                tool_safety_level.value,
                f"{func_name} has mismatched safety levels",
            )

    def test_dangerous_operations_classification(self):
        """Test VPN operations are classified as DANGEROUS."""
        dangerous_ops = ["configure_s2s_vpn", "add_vpn_peer"]

        for func_name in dangerous_ops:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name], SafetyLevel.DANGEROUS, f"{func_name} should be DANGEROUS"
            )

    def test_moderate_operations_classification(self):
        """Test security config operations are classified as MODERATE."""
        moderate_ops = [
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        for func_name in moderate_ops:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name], SafetyLevel.MODERATE, f"{func_name} should be MODERATE"
            )

    def test_safe_discovery_classification(self):
        """Test discovery operations are classified as SAFE."""
        safe_ops = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
        ]

        for func_name in safe_ops:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name], SafetyLevel.SAFE, f"{func_name} should be SAFE"
            )


class TestEpic8ToolSchemas(unittest.TestCase):
    """Test tool schemas have correct additionalProperties."""

    def test_all_tool_schemas_have_additional_properties_false(self):
        """Test all Epic 8 tool schemas have additionalProperties: False."""
        from scripts.agent_tools import NETWORK_ANALYST_TOOLS, MERAKI_SPECIALIST_TOOLS

        epic8_functions = [
            "discover_vpn_topology",
            "discover_content_filtering",
            "discover_ips_settings",
            "discover_amp_settings",
            "discover_traffic_shaping",
            "configure_s2s_vpn",
            "add_vpn_peer",
            "configure_content_filter",
            "add_blocked_url",
            "configure_ips",
            "set_ips_mode",
            "configure_amp",
            "configure_traffic_shaping",
            "set_bandwidth_limit",
        ]

        all_tools = NETWORK_ANALYST_TOOLS + MERAKI_SPECIALIST_TOOLS

        for tool in all_tools:
            func_name = tool["function"]["name"]
            if func_name in epic8_functions:
                params = tool["function"]["parameters"]
                self.assertEqual(
                    params.get("additionalProperties"),
                    False,
                    f"{func_name} schema missing additionalProperties: False",
                )


if __name__ == "__main__":
    unittest.main()
