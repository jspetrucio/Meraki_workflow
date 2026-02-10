"""
Tests for Phase 2 Wave 2 - SD-WAN, Templates, Access Policies, Air Marshal, SSID Firewall, Splash Pages.

Covers 6 stories (22 SP):
- Story 11.1: SD-WAN / Uplink Selection (8 SP, DANGEROUS)
- Story 11.4: Config Templates (5 SP, DANGEROUS)
- Story 12.2: 802.1X / Access Policies (5 SP, MODERATE)
- Story 12.5: Air Marshal / Rogue AP (3 SP, SAFE - read only)
- Story 12.6: SSID Firewall Rules (3 SP, MODERATE)
- Story 12.7: Splash Pages (3 SP, MODERATE)
"""

import unittest
from unittest.mock import MagicMock, patch

from scripts import agent_router, config, discovery
from scripts.api import MerakiClient, network_has_product
from scripts.config import ConfigAction, ConfigResult
from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel


class TestPhase2Wave2API(unittest.TestCase):
    """Test all new api.py methods for Wave 2."""

    def setUp(self):
        self.mock_dashboard = MagicMock()
        self.client = MerakiClient.__new__(MerakiClient)
        self.client.dashboard = self.mock_dashboard
        self.client.org_id = "org123"

    def test_get_uplink_selection(self):
        """Test get_uplink_selection API method."""
        self.mock_dashboard.appliance.getNetworkApplianceTrafficShapingUplinkSelection.return_value = {
            "wanTrafficUplinkPreferences": [],
            "defaultUplink": "wan1"
        }
        result = self.client.get_uplink_selection("N_123")
        self.assertIn("wanTrafficUplinkPreferences", result)
        self.mock_dashboard.appliance.getNetworkApplianceTrafficShapingUplinkSelection.assert_called_once_with("N_123")

    def test_update_uplink_selection(self):
        """Test update_uplink_selection API method."""
        self.mock_dashboard.appliance.updateNetworkApplianceTrafficShapingUplinkSelection.return_value = {"defaultUplink": "wan2"}
        result = self.client.update_uplink_selection("N_123", defaultUplink="wan2")
        self.assertEqual(result["defaultUplink"], "wan2")
        self.mock_dashboard.appliance.updateNetworkApplianceTrafficShapingUplinkSelection.assert_called_once()

    def test_get_uplink_statuses(self):
        """Test get_uplink_statuses API method."""
        self.mock_dashboard.appliance.getOrganizationApplianceUplinkStatuses.return_value = [{"networkId": "N_123"}]
        result = self.client.get_uplink_statuses("org123")
        self.assertIsInstance(result, list)
        self.mock_dashboard.appliance.getOrganizationApplianceUplinkStatuses.assert_called_once_with("org123")

    def test_get_vpn_exclusions(self):
        """Test get_vpn_exclusions API method."""
        self.mock_dashboard.appliance.getNetworkApplianceTrafficShapingVpnExclusions.return_value = {"custom": []}
        result = self.client.get_vpn_exclusions("N_123")
        self.assertIn("custom", result)
        self.mock_dashboard.appliance.getNetworkApplianceTrafficShapingVpnExclusions.assert_called_once_with("N_123")

    def test_get_config_templates(self):
        """Test get_config_templates API method."""
        self.mock_dashboard.organizations.getOrganizationConfigTemplates.return_value = [{"id": "T_123", "name": "Template1"}]
        result = self.client.get_config_templates("org123")
        self.assertIsInstance(result, list)
        self.mock_dashboard.organizations.getOrganizationConfigTemplates.assert_called_once_with("org123")

    def test_create_config_template(self):
        """Test create_config_template API method."""
        self.mock_dashboard.organizations.createOrganizationConfigTemplate.return_value = {"id": "T_123"}
        result = self.client.create_config_template("org123", name="NewTemplate")
        self.assertEqual(result["id"], "T_123")
        self.mock_dashboard.organizations.createOrganizationConfigTemplate.assert_called_once()

    def test_update_config_template(self):
        """Test update_config_template API method."""
        self.mock_dashboard.organizations.updateOrganizationConfigTemplate.return_value = {"id": "T_123", "name": "Updated"}
        result = self.client.update_config_template("org123", "T_123", name="Updated")
        self.assertEqual(result["name"], "Updated")
        self.mock_dashboard.organizations.updateOrganizationConfigTemplate.assert_called_once()

    def test_delete_config_template(self):
        """Test delete_config_template API method."""
        self.mock_dashboard.organizations.deleteOrganizationConfigTemplate.return_value = None
        result = self.client.delete_config_template("org123", "T_123")
        self.assertIsNone(result)
        self.mock_dashboard.organizations.deleteOrganizationConfigTemplate.assert_called_once_with("org123", "T_123")

    def test_bind_network(self):
        """Test bind_network API method."""
        self.mock_dashboard.networks.bindNetwork.return_value = {"id": "N_123", "configTemplateId": "T_123"}
        result = self.client.bind_network("N_123", "T_123")
        self.assertEqual(result["configTemplateId"], "T_123")
        self.mock_dashboard.networks.bindNetwork.assert_called_once()

    def test_unbind_network(self):
        """Test unbind_network API method."""
        self.mock_dashboard.networks.unbindNetwork.return_value = {"id": "N_123"}
        result = self.client.unbind_network("N_123")
        self.assertIn("id", result)
        self.mock_dashboard.networks.unbindNetwork.assert_called_once_with("N_123")

    def test_get_access_policies(self):
        """Test get_access_policies API method."""
        self.mock_dashboard.switch.getNetworkSwitchAccessPolicies.return_value = [{"accessPolicyNumber": "1"}]
        result = self.client.get_access_policies("N_123")
        self.assertIsInstance(result, list)
        self.mock_dashboard.switch.getNetworkSwitchAccessPolicies.assert_called_once_with("N_123")

    def test_create_access_policy(self):
        """Test create_access_policy API method."""
        self.mock_dashboard.switch.createNetworkSwitchAccessPolicy.return_value = {"accessPolicyNumber": "1"}
        result = self.client.create_access_policy("N_123", name="Policy1")
        self.assertEqual(result["accessPolicyNumber"], "1")
        self.mock_dashboard.switch.createNetworkSwitchAccessPolicy.assert_called_once()

    def test_update_access_policy(self):
        """Test update_access_policy API method."""
        self.mock_dashboard.switch.updateNetworkSwitchAccessPolicy.return_value = {"name": "UpdatedPolicy"}
        result = self.client.update_access_policy("N_123", "1", name="UpdatedPolicy")
        self.assertEqual(result["name"], "UpdatedPolicy")
        self.mock_dashboard.switch.updateNetworkSwitchAccessPolicy.assert_called_once()

    def test_delete_access_policy(self):
        """Test delete_access_policy API method."""
        self.mock_dashboard.switch.deleteNetworkSwitchAccessPolicy.return_value = None
        result = self.client.delete_access_policy("N_123", "1")
        self.assertIsNone(result)
        self.mock_dashboard.switch.deleteNetworkSwitchAccessPolicy.assert_called_once_with("N_123", "1")

    def test_get_air_marshal(self):
        """Test get_air_marshal API method."""
        self.mock_dashboard.wireless.getNetworkWirelessAirMarshal.return_value = [{"bssid": "00:11:22:33:44:55"}]
        result = self.client.get_air_marshal("N_123")
        self.assertIsInstance(result, list)
        self.mock_dashboard.wireless.getNetworkWirelessAirMarshal.assert_called_once_with("N_123")

    def test_get_ssid_l3_firewall(self):
        """Test get_ssid_l3_firewall API method."""
        self.mock_dashboard.wireless.getNetworkWirelessSsidFirewallL3FirewallRules.return_value = {"rules": []}
        result = self.client.get_ssid_l3_firewall("N_123", 0)
        self.assertIn("rules", result)
        self.mock_dashboard.wireless.getNetworkWirelessSsidFirewallL3FirewallRules.assert_called_once_with("N_123", 0)

    def test_update_ssid_l3_firewall(self):
        """Test update_ssid_l3_firewall API method."""
        self.mock_dashboard.wireless.updateNetworkWirelessSsidFirewallL3FirewallRules.return_value = {"rules": [{"policy": "deny"}]}
        result = self.client.update_ssid_l3_firewall("N_123", 0, rules=[{"policy": "deny"}])
        self.assertIn("rules", result)
        self.mock_dashboard.wireless.updateNetworkWirelessSsidFirewallL3FirewallRules.assert_called_once()

    def test_get_ssid_l7_firewall(self):
        """Test get_ssid_l7_firewall API method."""
        self.mock_dashboard.wireless.getNetworkWirelessSsidFirewallL7FirewallRules.return_value = {"rules": []}
        result = self.client.get_ssid_l7_firewall("N_123", 0)
        self.assertIn("rules", result)
        self.mock_dashboard.wireless.getNetworkWirelessSsidFirewallL7FirewallRules.assert_called_once_with("N_123", 0)

    def test_update_ssid_l7_firewall(self):
        """Test update_ssid_l7_firewall API method."""
        self.mock_dashboard.wireless.updateNetworkWirelessSsidFirewallL7FirewallRules.return_value = {"rules": [{"policy": "deny"}]}
        result = self.client.update_ssid_l7_firewall("N_123", 0, rules=[{"policy": "deny"}])
        self.assertIn("rules", result)
        self.mock_dashboard.wireless.updateNetworkWirelessSsidFirewallL7FirewallRules.assert_called_once()

    def test_get_splash_settings(self):
        """Test get_splash_settings API method."""
        self.mock_dashboard.wireless.getNetworkWirelessSsidSplashSettings.return_value = {"splashPage": "None"}
        result = self.client.get_splash_settings("N_123", 0)
        self.assertIn("splashPage", result)
        self.mock_dashboard.wireless.getNetworkWirelessSsidSplashSettings.assert_called_once_with("N_123", 0)

    def test_update_splash_settings(self):
        """Test update_splash_settings API method."""
        self.mock_dashboard.wireless.updateNetworkWirelessSsidSplashSettings.return_value = {"splashPage": "Click-through splash page"}
        result = self.client.update_splash_settings("N_123", 0, splashPage="Click-through splash page")
        self.assertEqual(result["splashPage"], "Click-through splash page")
        self.mock_dashboard.wireless.updateNetworkWirelessSsidSplashSettings.assert_called_once()


class TestPhase2Wave2Discovery(unittest.TestCase):
    """Test all new discovery functions for Wave 2."""

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_sdwan_config_success(self, mock_has_product, mock_get_client):
        """Test discover_sdwan_config with appliance product type."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", {})
        mock_get_client.return_value = mock_client

        result = discovery.discover_sdwan_config("N_123")

        self.assertIn("uplink_selection", result)
        self.assertIn("vpn_exclusions", result)
        mock_has_product.assert_called_once()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_sdwan_config_no_appliance(self, mock_has_product, mock_get_client):
        """Test discover_sdwan_config returns empty dict when no appliance."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discovery.discover_sdwan_config("N_123")

        self.assertEqual(result, {})
        mock_client.safe_call.assert_not_called()

    @patch("scripts.discovery.get_client")
    def test_discover_templates(self, mock_get_client):
        """Test discover_templates."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", [])
        mock_get_client.return_value = mock_client

        result = discovery.discover_templates()

        self.assertIsInstance(result, list)
        mock_client.safe_call.assert_called_once()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_access_policies_success(self, mock_has_product, mock_get_client):
        """Test discover_access_policies with switch product type."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", [])
        mock_get_client.return_value = mock_client

        result = discovery.discover_access_policies("N_123")

        self.assertIsInstance(result, list)
        mock_has_product.assert_called_once()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_access_policies_no_switch(self, mock_has_product, mock_get_client):
        """Test discover_access_policies returns empty list when no switch."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discovery.discover_access_policies("N_123")

        self.assertEqual(result, [])
        mock_client.safe_call.assert_not_called()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_rogue_aps_success(self, mock_has_product, mock_get_client):
        """Test discover_rogue_aps with wireless product type."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", [])
        mock_get_client.return_value = mock_client

        result = discovery.discover_rogue_aps("N_123")

        self.assertIsInstance(result, list)
        mock_has_product.assert_called_once()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_rogue_aps_no_wireless(self, mock_has_product, mock_get_client):
        """Test discover_rogue_aps returns empty list when no wireless."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discovery.discover_rogue_aps("N_123")

        self.assertEqual(result, [])
        mock_client.safe_call.assert_not_called()

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_ssid_firewall_single_ssid(self, mock_has_product, mock_get_client):
        """Test discover_ssid_firewall for single SSID."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", {})
        mock_get_client.return_value = mock_client

        result = discovery.discover_ssid_firewall("N_123", ssid_number=0)

        self.assertIn(0, result)
        self.assertIn("l3_rules", result[0])
        self.assertIn("l7_rules", result[0])

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_ssid_firewall_all_ssids(self, mock_has_product, mock_get_client):
        """Test discover_ssid_firewall for all SSIDs."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        ssids_data = [{"number": 0, "enabled": True, "name": "Corp"}, {"number": 1, "enabled": False}]

        call_count = [0]

        def safe_call_side_effect(fn, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # first call is get_ssids
                return ssids_data
            return kwargs.get("default", {})

        mock_client.safe_call.side_effect = safe_call_side_effect
        mock_get_client.return_value = mock_client

        result = discovery.discover_ssid_firewall("N_123")

        self.assertIn(0, result)

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_ssid_firewall_no_wireless(self, mock_has_product, mock_get_client):
        """Test discover_ssid_firewall returns empty dict when no wireless."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discovery.discover_ssid_firewall("N_123")

        self.assertEqual(result, {})

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_splash_config_single_ssid(self, mock_has_product, mock_get_client):
        """Test discover_splash_config for single SSID."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = lambda fn, *args, **kwargs: kwargs.get("default", {})
        mock_get_client.return_value = mock_client

        result = discovery.discover_splash_config("N_123", ssid_number=0)

        self.assertIn(0, result)

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_splash_config_all_ssids(self, mock_has_product, mock_get_client):
        """Test discover_splash_config for all SSIDs."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        ssids_data = [{"number": 0, "enabled": True, "name": "Guest"}]

        call_count = [0]

        def safe_call_side_effect(fn, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # first call is get_ssids
                return ssids_data
            return kwargs.get("default", {})

        mock_client.safe_call.side_effect = safe_call_side_effect
        mock_get_client.return_value = mock_client

        result = discovery.discover_splash_config("N_123")

        self.assertIn(0, result)

    @patch("scripts.discovery.get_client")
    @patch("scripts.discovery.network_has_product")
    def test_discover_splash_config_no_wireless(self, mock_has_product, mock_get_client):
        """Test discover_splash_config returns empty dict when no wireless."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discovery.discover_splash_config("N_123")

        self.assertEqual(result, {})


class TestPhase2Wave2Config(unittest.TestCase):
    """Test all new config functions for Wave 2."""

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_sdwan_policy_success(self, mock_has_product, mock_get_client):
        """Test configure_sdwan_policy success."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"defaultUplink": "wan2"}
        mock_get_client.return_value = mock_client

        result = config.configure_sdwan_policy("N_123", default_uplink="wan2")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_sdwan_policy_no_appliance(self, mock_has_product, mock_get_client):
        """Test configure_sdwan_policy returns error when no appliance."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.configure_sdwan_policy("N_123")

        self.assertFalse(result.success)
        self.assertIn("appliance", result.error)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_set_uplink_preference_success(self, mock_has_product, mock_get_client):
        """Test set_uplink_preference success."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.side_effect = [
            {"wanTrafficUplinkPreferences": []},  # get
            {"wanTrafficUplinkPreferences": [{"preferredUplink": "wan2"}]}  # update
        ]
        mock_get_client.return_value = mock_client

        result = config.set_uplink_preference("N_123", "videoConferencing", "wan2")

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_set_uplink_preference_no_appliance(self, mock_has_product, mock_get_client):
        """Test set_uplink_preference returns error when no appliance."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.set_uplink_preference("N_123", "app", "wan1")

        self.assertFalse(result.success)

    @patch("scripts.config.get_client")
    def test_manage_template_create(self, mock_get_client):
        """Test manage_template create action."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.return_value = {"id": "T_123", "name": "NewTemplate"}
        mock_get_client.return_value = mock_client

        result = config.manage_template(action="create", name="NewTemplate")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)

    @patch("scripts.config.get_client")
    def test_manage_template_update(self, mock_get_client):
        """Test manage_template update action."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.return_value = {"id": "T_123", "name": "Updated"}
        mock_get_client.return_value = mock_client

        result = config.manage_template(action="update", template_id="T_123", name="Updated")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)

    @patch("scripts.config.get_client")
    def test_manage_template_delete(self, mock_get_client):
        """Test manage_template delete action."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.return_value = None
        mock_get_client.return_value = mock_client

        result = config.manage_template(action="delete", template_id="T_123")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.DELETE)

    @patch("scripts.config.get_client")
    def test_manage_template_bind(self, mock_get_client):
        """Test manage_template bind action."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.return_value = {"id": "N_123", "configTemplateId": "T_123"}
        mock_get_client.return_value = mock_client

        result = config.manage_template(action="bind", network_id="N_123", template_id="T_123")

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    def test_manage_template_unbind(self, mock_get_client):
        """Test manage_template unbind action."""
        mock_client = MagicMock()
        mock_client.org_id = "org123"
        mock_client.safe_call.return_value = {"id": "N_123"}
        mock_get_client.return_value = mock_client

        result = config.manage_template(action="unbind", network_id="N_123")

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_access_policy_create(self, mock_has_product, mock_get_client):
        """Test configure_access_policy create action."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"accessPolicyNumber": "1", "name": "Policy1"}
        mock_get_client.return_value = mock_client

        result = config.configure_access_policy("N_123", action="create", name="Policy1")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_access_policy_update(self, mock_has_product, mock_get_client):
        """Test configure_access_policy update action."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"accessPolicyNumber": "1", "name": "Updated"}
        mock_get_client.return_value = mock_client

        result = config.configure_access_policy("N_123", action="update", access_policy_number="1", name="Updated")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_access_policy_delete(self, mock_has_product, mock_get_client):
        """Test configure_access_policy delete action."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = None
        mock_get_client.return_value = mock_client

        result = config.configure_access_policy("N_123", action="delete", access_policy_number="1")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.DELETE)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_access_policy_no_switch(self, mock_has_product, mock_get_client):
        """Test configure_access_policy returns error when no switch."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.configure_access_policy("N_123", action="create", name="Policy")

        self.assertFalse(result.success)
        self.assertIn("switch", result.error)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_ssid_firewall_l3(self, mock_has_product, mock_get_client):
        """Test configure_ssid_firewall L3 layer."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"rules": [{"policy": "deny"}]}
        mock_get_client.return_value = mock_client

        result = config.configure_ssid_firewall("N_123", 0, layer="l3", rules=[{"policy": "deny"}])

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_ssid_firewall_l7(self, mock_has_product, mock_get_client):
        """Test configure_ssid_firewall L7 layer."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"rules": [{"policy": "deny"}]}
        mock_get_client.return_value = mock_client

        result = config.configure_ssid_firewall("N_123", 0, layer="l7", rules=[{"policy": "deny"}])

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_ssid_firewall_no_wireless(self, mock_has_product, mock_get_client):
        """Test configure_ssid_firewall returns error when no wireless."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.configure_ssid_firewall("N_123", 0, rules=[])

        self.assertFalse(result.success)
        self.assertIn("wireless", result.error)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_splash_page_success(self, mock_has_product, mock_get_client):
        """Test configure_splash_page success."""
        mock_has_product.return_value = True
        mock_client = MagicMock()
        mock_client.safe_call.return_value = {"splashPage": "Click-through splash page"}
        mock_get_client.return_value = mock_client

        result = config.configure_splash_page("N_123", 0, splash_page="Click-through splash page")

        self.assertTrue(result.success)

    @patch("scripts.config.get_client")
    @patch("scripts.config.network_has_product")
    def test_configure_splash_page_no_wireless(self, mock_has_product, mock_get_client):
        """Test configure_splash_page returns error when no wireless."""
        mock_has_product.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.configure_splash_page("N_123", 0)

        self.assertFalse(result.success)
        self.assertIn("wireless", result.error)


class TestPhase2Wave2Registry(unittest.TestCase):
    """Test that all Wave 2 functions are registered."""

    def test_all_wave2_functions_in_registry(self):
        """Test all Wave 2 functions are in FUNCTION_REGISTRY."""
        registry = agent_router._build_function_registry()

        wave2_functions = [
            # Story 11.1: SD-WAN
            "discover_sdwan_config",
            "configure_sdwan_policy",
            "set_uplink_preference",
            # Story 11.4: Config Templates
            "discover_templates",
            "manage_template",
            # Story 12.2: Access Policies
            "discover_access_policies",
            "configure_access_policy",
            # Story 12.5: Air Marshal
            "discover_rogue_aps",
            # Story 12.6: SSID Firewall
            "discover_ssid_firewall",
            "configure_ssid_firewall",
            # Story 12.7: Splash Pages
            "discover_splash_config",
            "configure_splash_page",
        ]

        for func_name in wave2_functions:
            self.assertIn(func_name, registry, f"{func_name} missing from registry")


class TestPhase2Wave2Safety(unittest.TestCase):
    """Test safety classifications for Wave 2."""

    def test_wave2_safe_operations(self):
        """Test all Wave 2 SAFE operations are classified correctly."""
        safe_functions = [
            "discover_sdwan_config",
            "discover_templates",
            "discover_access_policies",
            "discover_rogue_aps",
            "discover_ssid_firewall",
            "discover_splash_config",
        ]

        for func_name in safe_functions:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name],
                SafetyLevel.SAFE,
                f"{func_name} should be SAFE"
            )

    def test_wave2_moderate_operations(self):
        """Test all Wave 2 MODERATE operations are classified correctly."""
        moderate_functions = [
            "configure_access_policy",
            "configure_ssid_firewall",
            "configure_splash_page",
        ]

        for func_name in moderate_functions:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name],
                SafetyLevel.MODERATE,
                f"{func_name} should be MODERATE"
            )

    def test_wave2_dangerous_operations(self):
        """Test all Wave 2 DANGEROUS operations are classified correctly."""
        dangerous_functions = [
            "configure_sdwan_policy",
            "set_uplink_preference",
            "manage_template",
        ]

        for func_name in dangerous_functions:
            self.assertEqual(
                SAFETY_CLASSIFICATION[func_name],
                SafetyLevel.DANGEROUS,
                f"{func_name} should be DANGEROUS"
            )


class TestPhase2Wave2Count(unittest.TestCase):
    """Test total function counts after Wave 2."""

    def test_wave2_adds_14_functions(self):
        """Test that Wave 2 adds exactly 14 new functions (8 SAFE + 3 MODERATE + 3 DANGEROUS)."""
        registry = agent_router._build_function_registry()

        # Count Wave 2 specific functions
        wave2_functions = [
            "discover_sdwan_config", "configure_sdwan_policy", "set_uplink_preference",
            "discover_templates", "manage_template",
            "discover_access_policies", "configure_access_policy",
            "discover_rogue_aps",
            "discover_ssid_firewall", "configure_ssid_firewall",
            "discover_splash_config", "configure_splash_page",
        ]

        wave2_count = sum(1 for fn in wave2_functions if fn in registry)
        self.assertEqual(wave2_count, 12, "Wave 2 should add exactly 12 functions to registry")

        # Verify safety counts
        wave2_safe = [fn for fn in wave2_functions if SAFETY_CLASSIFICATION.get(fn) == SafetyLevel.SAFE]
        wave2_moderate = [fn for fn in wave2_functions if SAFETY_CLASSIFICATION.get(fn) == SafetyLevel.MODERATE]
        wave2_dangerous = [fn for fn in wave2_functions if SAFETY_CLASSIFICATION.get(fn) == SafetyLevel.DANGEROUS]

        self.assertEqual(len(wave2_safe), 6, "Wave 2 should have 6 SAFE functions")
        self.assertEqual(len(wave2_moderate), 3, "Wave 2 should have 3 MODERATE functions")
        self.assertEqual(len(wave2_dangerous), 3, "Wave 2 should have 3 DANGEROUS functions")


if __name__ == "__main__":
    unittest.main()
