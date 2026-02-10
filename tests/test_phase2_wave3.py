"""
Comprehensive tests for Phase 2 Wave 3.

Stories covered:
- 11.3: Adaptive Policy / SGT (8 SP, DANGEROUS)
- 12.1: Switch Stacks (5 SP, DANGEROUS)
- 12.4: HA / Warm Spare (5 SP, DANGEROUS)
- 13.1: Camera Analytics & Snapshots (5 SP, SAFE)
- 13.2: Sensor Readings & Alerts (5 SP, SAFE/MODERATE)
"""

import unittest
from unittest.mock import patch, MagicMock
from scripts.config import ConfigAction


class TestStory11_3_AdaptivePolicy(unittest.TestCase):
    """Story 11.3: Adaptive Policy / SGT."""

    def test_api_get_adaptive_policies(self):
        """Test get_adaptive_policies API method exists."""
        from scripts.api import MerakiClient

        # Just verify the method exists on the class
        self.assertTrue(hasattr(MerakiClient, "get_adaptive_policies"))

    def test_api_create_adaptive_policy(self):
        """Test create_adaptive_policy API method exists."""
        from scripts.api import MerakiClient

        # Just verify the method exists on the class
        self.assertTrue(hasattr(MerakiClient, "create_adaptive_policy"))

    def test_api_get_adaptive_policy_acls(self):
        """Test get_adaptive_policy_acls API method exists."""
        from scripts.api import MerakiClient

        # Just verify the method exists on the class
        self.assertTrue(hasattr(MerakiClient, "get_adaptive_policy_acls"))

    @patch("scripts.discovery.get_client")
    def test_discover_adaptive_policies(self, mock_get_client):
        """Test discover_adaptive_policies function."""
        from scripts.discovery import discover_adaptive_policies

        mock_client = MagicMock()
        mock_client.safe_call.side_effect = [
            {"organizationId": "org123"},  # get_network
            [{"policyId": "1"}],  # get_adaptive_policies
            [{"aclId": "acl1"}],  # get_adaptive_policy_acls
        ]
        mock_get_client.return_value = mock_client

        result = discover_adaptive_policies("net123")

        self.assertEqual(result["policy_count"], 1)
        self.assertEqual(result["acl_count"], 1)

    @patch("scripts.config.get_client")
    @patch("scripts.config.backup_config")
    def test_configure_adaptive_policy(self, mock_backup, mock_get_client):
        """Test configure_adaptive_policy function."""
        from scripts.config import configure_adaptive_policy

        mock_client = MagicMock()
        mock_client.create_adaptive_policy.return_value = {"policyId": "new123"}
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"

        result = configure_adaptive_policy("org123", "10", "20", acl_ids=["acl1"])

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)
        self.assertEqual(result.resource_type, "adaptive_policy")

    def test_adaptive_policy_safety_classification(self):
        """Test safety classifications for adaptive policy functions."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        self.assertEqual(SAFETY_CLASSIFICATION["discover_adaptive_policies"], SafetyLevel.SAFE)
        self.assertEqual(SAFETY_CLASSIFICATION["configure_adaptive_policy"], SafetyLevel.DANGEROUS)

    def test_adaptive_policy_registry_entries(self):
        """Test function registry has adaptive policy entries."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        self.assertIn("discover_adaptive_policies", registry)
        self.assertIn("configure_adaptive_policy", registry)


class TestStory12_1_SwitchStacks(unittest.TestCase):
    """Story 12.1: Switch Stacks."""

    def test_api_get_switch_stacks(self):
        """Test get_switch_stacks API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_switch_stacks"))

    def test_api_create_switch_stack(self):
        """Test create_switch_stack API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "create_switch_stack"))

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.discovery.get_client")
    def test_discover_switch_stacks(self, mock_get_client, mock_has_product):
        """Test discover_switch_stacks function."""
        from scripts.discovery import discover_switch_stacks

        mock_client = MagicMock()
        # Return values in sequence: get_switch_stacks, then get_stack_routing
        mock_client.safe_call.side_effect = [
            [{"id": "stack1"}],  # get_switch_stacks returns list of stacks
            [{"interface": "vlan1"}],  # get_stack_routing returns list of interfaces
        ]
        mock_get_client.return_value = mock_client

        result = discover_switch_stacks("net123")

        self.assertEqual(result["stack_count"], 1)
        self.assertIn("stack1", result["routing_interfaces"])

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.discovery.get_client")
    def test_discover_switch_stacks_no_hardware(self, mock_get_client, mock_has_product):
        """Test discover_switch_stacks with no switch hardware."""
        from scripts.discovery import discover_switch_stacks

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discover_switch_stacks("net123")

        self.assertEqual(result["stack_count"], 0)
        # safe_call should NOT be called when hardware is missing
        mock_client.safe_call.assert_not_called()

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.get_client")
    @patch("scripts.config.backup_config")
    def test_manage_switch_stack_create(self, mock_backup, mock_get_client, mock_has_product):
        """Test manage_switch_stack - create action."""
        from scripts.config import manage_switch_stack

        mock_client = MagicMock()
        mock_client.create_switch_stack.return_value = {"id": "stack1"}
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"

        result = manage_switch_stack(
            "net123",
            action="create",
            name="Test Stack",
            serials=["S1", "S2"]
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)
        self.assertEqual(result.resource_type, "switch_stack")

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.config.get_client")
    def test_manage_switch_stack_no_hardware(self, mock_get_client, mock_has_product):
        """Test manage_switch_stack with no switch hardware."""
        from scripts.config import manage_switch_stack

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = manage_switch_stack(
            "net123",
            action="create",
            name="Test",
            serials=["S1"]
        )

        self.assertFalse(result.success)
        self.assertIn("switch", result.message.lower())

    def test_switch_stacks_safety_classification(self):
        """Test safety classifications for switch stacks."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        self.assertEqual(SAFETY_CLASSIFICATION["discover_switch_stacks"], SafetyLevel.SAFE)
        self.assertEqual(SAFETY_CLASSIFICATION["manage_switch_stack"], SafetyLevel.DANGEROUS)

    def test_switch_stacks_registry_entries(self):
        """Test function registry has switch stack entries."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        self.assertIn("discover_switch_stacks", registry)
        self.assertIn("manage_switch_stack", registry)


class TestStory12_4_WarmSpare(unittest.TestCase):
    """Story 12.4: HA / Warm Spare."""

    def test_api_get_warm_spare(self):
        """Test get_warm_spare API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_warm_spare"))

    def test_api_update_warm_spare(self):
        """Test update_warm_spare API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "update_warm_spare"))

    def test_api_swap_warm_spare(self):
        """Test swap_warm_spare API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "swap_warm_spare"))

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.discovery.get_client")
    def test_discover_ha_config(self, mock_get_client, mock_has_product):
        """Test discover_ha_config function."""
        from scripts.discovery import discover_ha_config

        mock_client = MagicMock()
        mock_client.safe_call.return_value = {
            "enabled": True,
            "spareSerial": "SPARE123"
        }
        mock_get_client.return_value = mock_client

        result = discover_ha_config("net123")

        self.assertTrue(result["enabled"])
        self.assertEqual(result["spare_serial"], "SPARE123")

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.discovery.get_client")
    def test_discover_ha_config_no_hardware(self, mock_get_client, mock_has_product):
        """Test discover_ha_config with no appliance hardware."""
        from scripts.discovery import discover_ha_config

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discover_ha_config("net123")

        self.assertFalse(result["enabled"])
        mock_client.safe_call.assert_not_called()

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.get_client")
    @patch("scripts.config.backup_config")
    def test_configure_warm_spare(self, mock_backup, mock_get_client, mock_has_product):
        """Test configure_warm_spare function."""
        from scripts.config import configure_warm_spare

        mock_client = MagicMock()
        mock_client.update_warm_spare.return_value = {"enabled": True}
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"

        result = configure_warm_spare(
            "net123",
            enabled=True,
            spare_serial="SPARE123"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)
        self.assertEqual(result.resource_type, "warm_spare")

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.config.get_client")
    def test_configure_warm_spare_no_hardware(self, mock_get_client, mock_has_product):
        """Test configure_warm_spare with no appliance hardware."""
        from scripts.config import configure_warm_spare

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = configure_warm_spare("net123", enabled=True)

        self.assertFalse(result.success)
        self.assertIn("appliance", result.message.lower())

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.get_client")
    @patch("scripts.config.backup_config")
    def test_trigger_failover_with_confirmation(self, mock_backup, mock_get_client, mock_has_product):
        """Test trigger_failover with correct confirmation."""
        from scripts.config import trigger_failover

        mock_client = MagicMock()
        mock_client.swap_warm_spare.return_value = {"status": "swapped"}
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"

        result = trigger_failover("net123", confirm_text="CONFIRM")

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.UPDATE)
        self.assertEqual(result.resource_type, "failover")

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.get_client")
    def test_trigger_failover_without_confirmation(self, mock_get_client, mock_has_product):
        """Test trigger_failover without confirmation fails."""
        from scripts.config import trigger_failover

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = trigger_failover("net123")

        self.assertFalse(result.success)
        self.assertIn("confirmacao", result.message.lower())

    def test_warm_spare_safety_classification(self):
        """Test safety classifications for warm spare functions."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        self.assertEqual(SAFETY_CLASSIFICATION["discover_ha_config"], SafetyLevel.SAFE)
        self.assertEqual(SAFETY_CLASSIFICATION["configure_warm_spare"], SafetyLevel.DANGEROUS)
        self.assertEqual(SAFETY_CLASSIFICATION["trigger_failover"], SafetyLevel.DANGEROUS)

    def test_warm_spare_registry_entries(self):
        """Test function registry has warm spare entries."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        self.assertIn("discover_ha_config", registry)
        self.assertIn("configure_warm_spare", registry)
        self.assertIn("trigger_failover", registry)


class TestStory13_1_CameraAnalytics(unittest.TestCase):
    """Story 13.1: Camera Analytics & Snapshots."""

    def test_api_get_camera_analytics_overview(self):
        """Test get_camera_analytics_overview API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_camera_analytics_overview"))

    def test_api_generate_snapshot(self):
        """Test generate_snapshot API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "generate_snapshot"))

    def test_api_get_video_link(self):
        """Test get_video_link API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_video_link"))

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.discovery.get_client")
    def test_discover_camera_analytics(self, mock_get_client, mock_has_product):
        """Test discover_camera_analytics function."""
        from scripts.discovery import discover_camera_analytics

        mock_client = MagicMock()
        # Return values in sequence: get_devices, then get_camera_analytics_overview
        mock_client.safe_call.side_effect = [
            [{"serial": "MV1", "model": "MV12"}],  # get_devices
            {"zones": 2},  # get_camera_analytics_overview
        ]
        mock_get_client.return_value = mock_client

        result = discover_camera_analytics("net123")

        self.assertEqual(result["camera_count"], 1)
        self.assertIn("MV1", result["analytics_data"])

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.discovery.get_client")
    def test_discover_camera_analytics_no_hardware(self, mock_get_client, mock_has_product):
        """Test discover_camera_analytics with no camera hardware."""
        from scripts.discovery import discover_camera_analytics

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discover_camera_analytics("net123")

        self.assertEqual(result["camera_count"], 0)
        mock_client.safe_call.assert_not_called()

    def test_camera_analytics_safety_classification(self):
        """Test safety classifications for camera analytics."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        self.assertEqual(SAFETY_CLASSIFICATION["discover_camera_analytics"], SafetyLevel.SAFE)

    def test_camera_analytics_registry_entries(self):
        """Test function registry has camera analytics entries."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        self.assertIn("discover_camera_analytics", registry)


class TestStory13_2_Sensors(unittest.TestCase):
    """Story 13.2: Sensor Readings & Alerts."""

    def test_api_get_sensor_readings_latest(self):
        """Test get_sensor_readings_latest API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_sensor_readings_latest"))

    def test_api_get_sensor_alert_profiles(self):
        """Test get_sensor_alert_profiles API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "get_sensor_alert_profiles"))

    def test_api_create_sensor_alert(self):
        """Test create_sensor_alert API method exists."""
        from scripts.api import MerakiClient

        self.assertTrue(hasattr(MerakiClient, "create_sensor_alert"))

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.discovery.get_client")
    def test_discover_sensors(self, mock_get_client, mock_has_product):
        """Test discover_sensors function."""
        from scripts.discovery import discover_sensors

        mock_client = MagicMock()
        # Return values in sequence: get_devices, then get_sensor_alert_profiles
        mock_client.safe_call.side_effect = [
            [{"serial": "MT1", "model": "MT10"}],  # get_devices
            [{"profileId": "1"}],  # get_sensor_alert_profiles
        ]
        mock_get_client.return_value = mock_client

        result = discover_sensors("net123")

        self.assertEqual(result["sensor_count"], 1)
        self.assertEqual(len(result["alert_profiles"]), 1)

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.discovery.get_client")
    def test_discover_sensors_no_hardware(self, mock_get_client, mock_has_product):
        """Test discover_sensors with no sensor hardware."""
        from scripts.discovery import discover_sensors

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = discover_sensors("net123")

        self.assertEqual(result["sensor_count"], 0)
        mock_client.safe_call.assert_not_called()

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.get_client")
    @patch("scripts.config.backup_config")
    def test_configure_sensor_alert(self, mock_backup, mock_get_client, mock_has_product):
        """Test configure_sensor_alert function."""
        from scripts.config import configure_sensor_alert

        mock_client = MagicMock()
        mock_client.create_sensor_alert.return_value = {"profileId": "new123"}
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"

        result = configure_sensor_alert(
            "net123",
            name="Test Alert",
            conditions=[{"metric": "temperature", "threshold": 30}]
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action, ConfigAction.CREATE)
        self.assertEqual(result.resource_type, "sensor_alert")

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.config.get_client")
    def test_configure_sensor_alert_no_hardware(self, mock_get_client, mock_has_product):
        """Test configure_sensor_alert with no sensor hardware."""
        from scripts.config import configure_sensor_alert

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = configure_sensor_alert(
            "net123",
            name="Test",
            conditions=[]
        )

        self.assertFalse(result.success)
        self.assertIn("sensor", result.message.lower())

    def test_sensor_safety_classification(self):
        """Test safety classifications for sensor functions."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        self.assertEqual(SAFETY_CLASSIFICATION["discover_sensors"], SafetyLevel.SAFE)
        self.assertEqual(SAFETY_CLASSIFICATION["configure_sensor_alert"], SafetyLevel.MODERATE)

    def test_sensor_registry_entries(self):
        """Test function registry has sensor entries."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        self.assertIn("discover_sensors", registry)
        self.assertIn("configure_sensor_alert", registry)


class TestWave3Integration(unittest.TestCase):
    """Integration tests for Wave 3."""

    def test_all_wave3_functions_in_registry(self):
        """Verify all Wave 3 functions are in registry."""
        from scripts.agent_router import _build_function_registry

        registry = _build_function_registry()

        expected = [
            # Story 11.3
            "discover_adaptive_policies",
            "configure_adaptive_policy",
            # Story 12.1
            "discover_switch_stacks",
            "manage_switch_stack",
            # Story 12.4
            "discover_ha_config",
            "configure_warm_spare",
            "trigger_failover",
            # Story 13.1
            "discover_camera_analytics",
            # Story 13.2
            "discover_sensors",
            "configure_sensor_alert",
        ]

        for func_name in expected:
            self.assertIn(func_name, registry, f"Missing {func_name} in registry")

    def test_wave3_safety_counts(self):
        """Verify Wave 3 adds correct number of safety entries."""
        from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

        safe = [k for k, v in SAFETY_CLASSIFICATION.items() if v == SafetyLevel.SAFE]
        moderate = [k for k, v in SAFETY_CLASSIFICATION.items() if v == SafetyLevel.MODERATE]
        dangerous = [k for k, v in SAFETY_CLASSIFICATION.items() if v == SafetyLevel.DANGEROUS]

        # After Wave 3: SAFE=74, MODERATE=30, DANGEROUS=22
        # After Wave 4 (note: this test now validates total counts including Wave 4):
        # SAFE=78, MODERATE=36, DANGEROUS=22
        self.assertEqual(len(safe), 78, f"Expected 78 SAFE (includes Wave 4), got {len(safe)}")
        self.assertEqual(len(moderate), 36, f"Expected 36 MODERATE (includes Wave 4), got {len(moderate)}")
        self.assertEqual(len(dangerous), 22, f"Expected 22 DANGEROUS, got {len(dangerous)}")


if __name__ == "__main__":
    unittest.main()
