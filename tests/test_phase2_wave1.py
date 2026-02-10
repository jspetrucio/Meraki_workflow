"""
Test Phase 2 Wave 1: Policy Objects, Client VPN, Port Schedules, LLDP/CDP, NetFlow, PoE Status.

Tests follow the 7-step implementation pattern:
1. api.py methods
2. discovery.py functions
3. config.py functions
4. agent_router.py FUNCTION_REGISTRY
5. agent_tools.py TOOL_SAFETY (skipped - will be added later)
6. safety.py SAFETY_CLASSIFICATION
7. Integration tests
"""

import unittest
from unittest.mock import MagicMock, patch

from scripts import api, discovery, config, agent_router, safety
from scripts.api import MerakiClient
from scripts.config import ConfigAction, ConfigResult
from scripts.safety import SafetyLevel


class TestPhase2Wave1API(unittest.TestCase):
    """Test api.py methods for Phase 2 Wave 1."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_dashboard = MagicMock()
        self.client = MerakiClient.__new__(MerakiClient)
        self.client.dashboard = self.mock_dashboard
        self.client.org_id = "test-org"

    # Story 11.5: Policy Objects
    def test_get_policy_objects(self):
        """Test get_policy_objects API method."""
        expected = [{"id": "1", "name": "CIDR Object", "type": "cidr"}]
        self.mock_dashboard.organizations.getOrganizationPolicyObjects.return_value = expected

        result = self.client.get_policy_objects("test-org")

        self.assertEqual(result, expected)
        self.mock_dashboard.organizations.getOrganizationPolicyObjects.assert_called_once_with("test-org")

    def test_create_policy_object(self):
        """Test create_policy_object API method."""
        expected = {"id": "1", "name": "Test Object"}
        self.mock_dashboard.organizations.createOrganizationPolicyObject.return_value = expected

        result = self.client.create_policy_object("test-org", name="Test Object", category="network")

        self.assertEqual(result, expected)
        self.mock_dashboard.organizations.createOrganizationPolicyObject.assert_called_once()

    def test_update_policy_object(self):
        """Test update_policy_object API method."""
        expected = {"id": "1", "name": "Updated Object"}
        self.mock_dashboard.organizations.updateOrganizationPolicyObject.return_value = expected

        result = self.client.update_policy_object("test-org", "1", name="Updated Object")

        self.assertEqual(result, expected)

    def test_delete_policy_object(self):
        """Test delete_policy_object API method."""
        self.mock_dashboard.organizations.deleteOrganizationPolicyObject.return_value = None

        result = self.client.delete_policy_object("test-org", "1")

        self.assertIsNone(result)
        self.mock_dashboard.organizations.deleteOrganizationPolicyObject.assert_called_once_with("test-org", "1")

    def test_get_policy_object_groups(self):
        """Test get_policy_object_groups API method."""
        expected = [{"id": "1", "name": "Group 1"}]
        self.mock_dashboard.organizations.getOrganizationPolicyObjectsGroups.return_value = expected

        result = self.client.get_policy_object_groups("test-org")

        self.assertEqual(result, expected)

    # Story 11.2: Client VPN
    def test_get_client_vpn(self):
        """Test get_client_vpn API method."""
        expected = {"enabled": True, "subnet": "192.168.128.0/24"}
        self.mock_dashboard.appliance.getNetworkApplianceVpn.return_value = expected

        result = self.client.get_client_vpn("net-1")

        self.assertEqual(result, expected)
        self.mock_dashboard.appliance.getNetworkApplianceVpn.assert_called_once_with("net-1")

    def test_update_client_vpn(self):
        """Test update_client_vpn API method."""
        expected = {"enabled": True}
        self.mock_dashboard.appliance.updateNetworkApplianceVpn.return_value = expected

        result = self.client.update_client_vpn("net-1", enabled=True)

        self.assertEqual(result, expected)

    # Story 12.3: Port Schedules
    def test_get_port_schedules(self):
        """Test get_port_schedules API method."""
        expected = [{"id": "1", "name": "After Hours"}]
        self.mock_dashboard.switch.getNetworkSwitchPortSchedules.return_value = expected

        result = self.client.get_port_schedules("net-1")

        self.assertEqual(result, expected)

    def test_create_port_schedule(self):
        """Test create_port_schedule API method."""
        expected = {"id": "1", "name": "New Schedule"}
        self.mock_dashboard.switch.createNetworkSwitchPortSchedule.return_value = expected

        result = self.client.create_port_schedule("net-1", name="New Schedule")

        self.assertEqual(result, expected)

    def test_update_port_schedule(self):
        """Test update_port_schedule API method."""
        expected = {"id": "1", "name": "Updated Schedule"}
        self.mock_dashboard.switch.updateNetworkSwitchPortSchedule.return_value = expected

        result = self.client.update_port_schedule("net-1", "1", name="Updated Schedule")

        self.assertEqual(result, expected)

    def test_delete_port_schedule(self):
        """Test delete_port_schedule API method."""
        self.mock_dashboard.switch.deleteNetworkSwitchPortSchedule.return_value = None

        result = self.client.delete_port_schedule("net-1", "1")

        self.assertIsNone(result)

    # Story 13.5: LLDP/CDP
    def test_get_lldp_cdp(self):
        """Test get_lldp_cdp API method."""
        expected = {"ports": {"1": {"cdp": {"deviceId": "Switch1"}}}}
        self.mock_dashboard.devices.getDeviceLldpCdp.return_value = expected

        result = self.client.get_lldp_cdp("Q2XX-XXXX-XXXX")

        self.assertEqual(result, expected)

    # Story 13.7: NetFlow
    def test_get_netflow_settings(self):
        """Test get_netflow_settings API method."""
        expected = {"reportingEnabled": True, "collectorIp": "10.1.1.100"}
        self.mock_dashboard.networks.getNetworkNetflow.return_value = expected

        result = self.client.get_netflow_settings("net-1")

        self.assertEqual(result, expected)

    def test_update_netflow_settings(self):
        """Test update_netflow_settings API method."""
        expected = {"reportingEnabled": True}
        self.mock_dashboard.networks.updateNetworkNetflow.return_value = expected

        result = self.client.update_netflow_settings("net-1", reportingEnabled=True)

        self.assertEqual(result, expected)


class TestPhase2Wave1Discovery(unittest.TestCase):
    """Test discovery.py functions for Phase 2 Wave 1."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=MerakiClient)
        self.mock_client.org_id = "test-org"

    # Story 11.5: Policy Objects
    def test_discover_policy_objects(self):
        """Test discover_policy_objects function."""
        objects = [{"id": "1", "name": "Object1"}]
        groups = [{"id": "1", "name": "Group1"}]
        self.mock_client.safe_call.side_effect = [objects, groups]

        result = discovery.discover_policy_objects("test-org", self.mock_client)

        self.assertEqual(result["objects"], objects)
        self.assertEqual(result["groups"], groups)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["groups_count"], 1)

    # Story 11.2: Client VPN
    @patch('scripts.discovery.network_has_product')
    def test_discover_client_vpn(self, mock_has_product):
        """Test discover_client_vpn function."""
        mock_has_product.return_value = True
        expected = {"enabled": True, "subnet": "192.168.128.0/24"}
        self.mock_client.safe_call.return_value = expected

        result = discovery.discover_client_vpn("net-1", self.mock_client)

        self.assertEqual(result, expected)

    @patch('scripts.discovery.network_has_product')
    def test_discover_client_vpn_no_appliance(self, mock_has_product):
        """Test discover_client_vpn with no appliance."""
        mock_has_product.return_value = False

        result = discovery.discover_client_vpn("net-1", self.mock_client)

        self.assertEqual(result, {})

    # Story 12.3: Port Schedules
    @patch('scripts.discovery.network_has_product')
    def test_discover_port_schedules(self, mock_has_product):
        """Test discover_port_schedules function."""
        mock_has_product.return_value = True
        expected = [{"id": "1", "name": "After Hours"}]
        self.mock_client.safe_call.return_value = expected

        result = discovery.discover_port_schedules("net-1", self.mock_client)

        self.assertEqual(result, expected)

    @patch('scripts.discovery.network_has_product')
    def test_discover_port_schedules_no_switch(self, mock_has_product):
        """Test discover_port_schedules with no switch."""
        mock_has_product.return_value = False

        result = discovery.discover_port_schedules("net-1", self.mock_client)

        self.assertEqual(result, [])

    # Story 13.5: LLDP/CDP
    def test_discover_lldp_cdp(self):
        """Test discover_lldp_cdp function."""
        expected = {"ports": {"1": {"cdp": {"deviceId": "Switch1"}}}}
        self.mock_client.safe_call.return_value = expected

        result = discovery.discover_lldp_cdp("Q2XX-XXXX-XXXX", self.mock_client)

        self.assertEqual(result, expected)

    # Story 13.7: NetFlow
    def test_discover_netflow_config(self):
        """Test discover_netflow_config function."""
        expected = {"reportingEnabled": True, "collectorIp": "10.1.1.100"}
        self.mock_client.safe_call.return_value = expected

        result = discovery.discover_netflow_config("net-1", self.mock_client)

        self.assertEqual(result, expected)

    # Story 13.8: PoE Status
    def test_discover_poe_status(self):
        """Test discover_poe_status function."""
        ports = [
            {"portId": "1", "poe": {"enabled": True, "powerDraw": 15.4}},
            {"portId": "2", "poe": {"enabled": True, "powerDraw": 7.2}},
            {"portId": "3", "poe": {"enabled": False}},
        ]
        self.mock_client.safe_call.return_value = ports

        result = discovery.discover_poe_status("Q2XX-XXXX-XXXX", self.mock_client)

        self.assertAlmostEqual(result["total_poe_draw"], 22.6, places=1)
        self.assertEqual(result["total_poe_budget"], 370.0)
        self.assertEqual(len(result["poe_ports"]), 2)

    def test_discover_poe_status_no_poe(self):
        """Test discover_poe_status with no PoE ports."""
        ports = [
            {"portId": "1", "poe": {"enabled": False}},
        ]
        self.mock_client.safe_call.return_value = ports

        result = discovery.discover_poe_status("Q2XX-XXXX-XXXX", self.mock_client)

        self.assertEqual(result["total_poe_draw"], 0.0)
        self.assertEqual(len(result["poe_ports"]), 0)


class TestPhase2Wave1Config(unittest.TestCase):
    """Test config.py functions for Phase 2 Wave 1."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=MerakiClient)

    # Story 11.5: Policy Objects
    @patch('scripts.config.Path')
    def test_manage_policy_object_create(self, mock_path):
        """Test manage_policy_object create action."""
        mock_path.return_value.mkdir.return_value = None
        mock_path.return_value.write_text.return_value = None
        self.mock_client.get_policy_objects.return_value = []
        self.mock_client.create_policy_object.return_value = {"id": "1", "name": "Test"}

        result = config.manage_policy_object(
            org_id="test-org",
            action="create",
            name="Test",
            category="network",
            object_type="cidr",
            cidr="10.0.0.0/8",
            backup=True,
            client_name="test-client",
            client=self.mock_client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)

    # Story 11.2: Client VPN
    @patch('scripts.config.network_has_product')
    @patch('scripts.config.Path')
    def test_configure_client_vpn(self, mock_path, mock_has_product):
        """Test configure_client_vpn function."""
        mock_has_product.return_value = True
        mock_path.return_value.mkdir.return_value = None
        mock_path.return_value.write_text.return_value = None
        self.mock_client.safe_call.return_value = {"enabled": False}
        self.mock_client.update_client_vpn.return_value = {"enabled": True}

        result = config.configure_client_vpn(
            network_id="net-1",
            enabled=True,
            backup=True,
            client_name="test-client",
            client=self.mock_client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)

    @patch('scripts.config.network_has_product')
    def test_configure_client_vpn_no_appliance(self, mock_has_product):
        """Test configure_client_vpn with no appliance."""
        mock_has_product.return_value = False

        result = config.configure_client_vpn(
            network_id="net-1",
            enabled=True,
            client=self.mock_client
        )

        self.assertFalse(result.success)
        self.assertIn("missing_hardware", result.error)

    # Story 12.3: Port Schedules
    @patch('scripts.config.network_has_product')
    @patch('scripts.config.Path')
    def test_configure_port_schedule_create(self, mock_path, mock_has_product):
        """Test configure_port_schedule create action."""
        mock_has_product.return_value = True
        mock_path.return_value.mkdir.return_value = None
        mock_path.return_value.write_text.return_value = None
        self.mock_client.safe_call.return_value = []
        self.mock_client.create_port_schedule.return_value = {"id": "1", "name": "After Hours"}

        result = config.configure_port_schedule(
            network_id="net-1",
            action="create",
            name="After Hours",
            backup=True,
            client_name="test-client",
            client=self.mock_client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)

    # Story 13.7: NetFlow
    @patch('scripts.config.Path')
    def test_configure_netflow(self, mock_path):
        """Test configure_netflow function."""
        mock_path.return_value.mkdir.return_value = None
        mock_path.return_value.write_text.return_value = None
        self.mock_client.safe_call.return_value = {"reportingEnabled": False}
        self.mock_client.update_netflow_settings.return_value = {"reportingEnabled": True}

        result = config.configure_netflow(
            network_id="net-1",
            reporting_enabled=True,
            collector_ip="10.1.1.100",
            backup=True,
            client_name="test-client",
            client=self.mock_client
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)


class TestPhase2Wave1Registry(unittest.TestCase):
    """Test FUNCTION_REGISTRY entries for Phase 2 Wave 1."""

    def test_registry_policy_objects(self):
        """Test policy objects in FUNCTION_REGISTRY."""
        self.assertIn("discover_policy_objects", agent_router.FUNCTION_REGISTRY)
        self.assertIn("manage_policy_object", agent_router.FUNCTION_REGISTRY)

    def test_registry_client_vpn(self):
        """Test Client VPN in FUNCTION_REGISTRY."""
        self.assertIn("discover_client_vpn", agent_router.FUNCTION_REGISTRY)
        self.assertIn("configure_client_vpn", agent_router.FUNCTION_REGISTRY)

    def test_registry_port_schedules(self):
        """Test port schedules in FUNCTION_REGISTRY."""
        self.assertIn("discover_port_schedules", agent_router.FUNCTION_REGISTRY)
        self.assertIn("configure_port_schedule", agent_router.FUNCTION_REGISTRY)

    def test_registry_lldp_cdp(self):
        """Test LLDP/CDP in FUNCTION_REGISTRY."""
        self.assertIn("discover_lldp_cdp", agent_router.FUNCTION_REGISTRY)

    def test_registry_netflow(self):
        """Test NetFlow in FUNCTION_REGISTRY."""
        self.assertIn("discover_netflow_config", agent_router.FUNCTION_REGISTRY)
        self.assertIn("configure_netflow", agent_router.FUNCTION_REGISTRY)

    def test_registry_poe_status(self):
        """Test PoE status in FUNCTION_REGISTRY."""
        self.assertIn("discover_poe_status", agent_router.FUNCTION_REGISTRY)


class TestPhase2Wave1Safety(unittest.TestCase):
    """Test SAFETY_CLASSIFICATION entries for Phase 2 Wave 1."""

    def test_safety_policy_objects(self):
        """Test policy objects safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_policy_objects"], SafetyLevel.SAFE)
        self.assertEqual(safety.SAFETY_CLASSIFICATION["manage_policy_object"], SafetyLevel.MODERATE)

    def test_safety_client_vpn(self):
        """Test Client VPN safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_client_vpn"], SafetyLevel.SAFE)
        self.assertEqual(safety.SAFETY_CLASSIFICATION["configure_client_vpn"], SafetyLevel.MODERATE)

    def test_safety_port_schedules(self):
        """Test port schedules safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_port_schedules"], SafetyLevel.SAFE)
        self.assertEqual(safety.SAFETY_CLASSIFICATION["configure_port_schedule"], SafetyLevel.MODERATE)

    def test_safety_lldp_cdp(self):
        """Test LLDP/CDP safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_lldp_cdp"], SafetyLevel.SAFE)

    def test_safety_netflow(self):
        """Test NetFlow safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_netflow_config"], SafetyLevel.SAFE)
        self.assertEqual(safety.SAFETY_CLASSIFICATION["configure_netflow"], SafetyLevel.MODERATE)

    def test_safety_poe_status(self):
        """Test PoE status safety classification."""
        self.assertEqual(safety.SAFETY_CLASSIFICATION["discover_poe_status"], SafetyLevel.SAFE)


class TestPhase2Wave1Count(unittest.TestCase):
    """Test total count of new functions."""

    def test_total_registry_entries(self):
        """Test that all 11 new functions are registered."""
        new_functions = [
            "discover_policy_objects", "manage_policy_object",
            "discover_client_vpn", "configure_client_vpn",
            "discover_port_schedules", "configure_port_schedule",
            "discover_lldp_cdp",
            "discover_netflow_config", "configure_netflow",
            "discover_poe_status",
        ]
        for func in new_functions:
            self.assertIn(func, agent_router.FUNCTION_REGISTRY, f"Missing: {func}")

    def test_total_safety_entries(self):
        """Test that all 11 new functions have safety classification."""
        new_functions = [
            "discover_policy_objects", "manage_policy_object",
            "discover_client_vpn", "configure_client_vpn",
            "discover_port_schedules", "configure_port_schedule",
            "discover_lldp_cdp",
            "discover_netflow_config", "configure_netflow",
            "discover_poe_status",
        ]
        for func in new_functions:
            self.assertIn(func, safety.SAFETY_CLASSIFICATION, f"Missing: {func}")


if __name__ == "__main__":
    unittest.main()
