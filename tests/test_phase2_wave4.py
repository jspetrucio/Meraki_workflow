"""
Tests for Phase 2 Wave 4: Floor Plans, Group Policies, Packet Capture, Static Routes.

Stories:
- 13.3: Floor Plans (3 SP, SAFE/MODERATE)
- 13.4: Group Policies (3 SP, MODERATE)
- 13.6: Packet Capture (3 SP, MODERATE)
- 13.9: Static Routes (Appliance) (3 SP, MODERATE)

Total: 4 stories, 12 SP
"""

import pytest
from unittest.mock import MagicMock, patch
from scripts.api import MerakiClient
from scripts import discovery, config
from scripts.config import ConfigResult, ConfigAction
from scripts.agent_router import _build_function_registry
from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel


# All API method tests use the pattern:
# mock_db = mock_meraki_dashboard.return_value
# then configure and assert on mock_db


class TestStory13_3_FloorPlans:
    """Story 13.3: Floor Plans (3 SP, SAFE/MODERATE)"""

    def test_get_floor_plans(self, mock_meraki_dashboard, mock_env_credentials):
        """Test get_floor_plans API method"""
        mock_db = mock_meraki_dashboard.return_value
        network_id = "N_test123"
        mock_db.networks.getNetworkFloorPlans.return_value = [
            {"floorPlanId": "fp1", "name": "Floor 1"},
            {"floorPlanId": "fp2", "name": "Floor 2"},
        ]

        client = MerakiClient()
        result = client.get_floor_plans(network_id)

        assert len(result) == 2
        mock_db.networks.getNetworkFloorPlans.assert_called_once_with(network_id)

    @patch("scripts.discovery.get_client")
    def test_discover_floor_plans_success(self, mock_get_client):
        """Test discover_floor_plans with data"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.safe_call.return_value = [
            {"floorPlanId": "fp1", "name": "Floor 1"},
            {"floorPlanId": "fp2", "name": "Floor 2"},
        ]

        result = discovery.discover_floor_plans(network_id)

        assert result["plan_count"] == 2
        assert len(result["floor_plans"]) == 2


class TestStory13_4_GroupPolicies:
    """Story 13.4: Group Policies (3 SP, MODERATE)"""

    def test_get_group_policies(self, mock_meraki_dashboard, mock_env_credentials):
        """Test get_group_policies API method"""
        mock_db = mock_meraki_dashboard.return_value
        network_id = "N_test123"
        mock_db.networks.getNetworkGroupPolicies.return_value = [
            {"groupPolicyId": "gp1", "name": "Policy 1"},
        ]

        client = MerakiClient()
        result = client.get_group_policies(network_id)

        assert len(result) == 1
        mock_db.networks.getNetworkGroupPolicies.assert_called_once_with(network_id)

    @patch("scripts.discovery.get_client")
    def test_discover_group_policies_success(self, mock_get_client):
        """Test discover_group_policies with data"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.safe_call.return_value = [
            {"groupPolicyId": "gp1", "name": "Policy 1"},
        ]

        result = discovery.discover_group_policies(network_id)

        assert result["policy_count"] == 1
        assert len(result["policies"]) == 1

    @patch("scripts.config.backup_config")
    @patch("scripts.config.get_client")
    def test_configure_group_policy_create_success(self, mock_get_client, mock_backup):
        """Test configure_group_policy create action"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"
        mock_client.create_group_policy.return_value = {
            "groupPolicyId": "gp_new",
            "name": "New Policy",
        }

        result = config.configure_group_policy(
            network_id,
            action="create",
            name="New Policy",
        )

        assert result.success
        assert result.action == ConfigAction.CREATE
        assert result.resource_type == "group_policy"
        assert result.resource_id == "gp_new"

    @patch("scripts.config.get_client")
    def test_configure_group_policy_create_missing_name(self, mock_get_client):
        """Test configure_group_policy create without name"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.configure_group_policy(
            network_id,
            action="create",
        )

        assert not result.success
        assert "name is required" in result.message


class TestStory13_6_PacketCapture:
    """Story 13.6: Packet Capture (3 SP, MODERATE)"""

    def test_create_packet_capture(self, mock_meraki_dashboard, mock_env_credentials):
        """Test create_packet_capture API method"""
        mock_db = mock_meraki_dashboard.return_value
        device_serial = "Q234-ABCD-5678"
        mock_db.devices.createDeviceLiveToolsPcap.return_value = {
            "pcapId": "pcap1",
            "status": "initiated",
        }

        client = MerakiClient()
        result = client.create_packet_capture(device_serial, duration=60)

        assert result["pcapId"] == "pcap1"
        mock_db.devices.createDeviceLiveToolsPcap.assert_called_once_with(
            device_serial, duration=60
        )


class TestStory13_9_StaticRoutes:
    """Story 13.9: Static Routes (Appliance) (3 SP, MODERATE)"""

    def test_get_static_routes(self, mock_meraki_dashboard, mock_env_credentials):
        """Test get_static_routes API method"""
        mock_db = mock_meraki_dashboard.return_value
        network_id = "N_test123"
        mock_db.appliance.getNetworkApplianceStaticRoutes.return_value = [
            {"id": "sr1", "subnet": "192.168.100.0/24", "gatewayIp": "192.168.1.1"},
        ]

        client = MerakiClient()
        result = client.get_static_routes(network_id)

        assert len(result) == 1
        mock_db.appliance.getNetworkApplianceStaticRoutes.assert_called_once_with(
            network_id
        )

    @patch("scripts.api.network_has_product", return_value=True)
    def test_discover_static_routes_success(self, mock_has_product):
        """Test discover_static_routes with appliance"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_client.safe_call.return_value = [
            {"id": "sr1", "subnet": "192.168.100.0/24", "gatewayIp": "192.168.1.1"},
        ]

        result = discovery.discover_static_routes(network_id, client=mock_client)

        assert result["route_count"] == 1
        assert len(result["routes"]) == 1

    @patch("scripts.api.network_has_product", return_value=False)
    def test_discover_static_routes_no_appliance(self, mock_has_product):
        """Test discover_static_routes without appliance"""
        network_id = "N_test123"
        mock_client = MagicMock()

        result = discovery.discover_static_routes(network_id, client=mock_client)

        assert result["route_count"] == 0
        assert result["routes"] == []
        mock_client.safe_call.assert_not_called()

    @patch("scripts.api.network_has_product", return_value=True)
    @patch("scripts.config.backup_config")
    @patch("scripts.config.get_client")
    def test_manage_static_route_create_success(self, mock_get_client, mock_backup, mock_has_product):
        """Test manage_static_route create action"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_backup.return_value = "/tmp/backup.json"
        mock_client.create_static_route.return_value = {
            "id": "sr_new",
            "subnet": "192.168.200.0/24",
            "gatewayIp": "192.168.1.1",
        }

        result = config.manage_static_route(
            network_id,
            action="create",
            subnet="192.168.200.0/24",
            gateway_ip="192.168.1.1",
        )

        assert result.success
        assert result.action == ConfigAction.CREATE
        assert result.resource_type == "static_route"
        assert result.resource_id == "sr_new"

    @patch("scripts.api.network_has_product", return_value=False)
    @patch("scripts.config.get_client")
    def test_manage_static_route_no_appliance(self, mock_get_client, mock_has_product):
        """Test manage_static_route without appliance hardware"""
        network_id = "N_test123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = config.manage_static_route(
            network_id,
            action="create",
            subnet="192.168.200.0/24",
            gateway_ip="192.168.1.1",
        )

        assert not result.success
        assert "appliance" in result.message.lower()


class TestWave4Registry:
    """Test that all Wave 4 functions are registered"""

    def test_registry_has_all_wave4_functions(self):
        """Test all Wave 4 functions in registry"""
        registry = _build_function_registry()

        # Floor Plans
        assert "discover_floor_plans" in registry
        assert "create_floor_plan" in registry
        assert "update_floor_plan" in registry
        assert "delete_floor_plan" in registry

        # Group Policies
        assert "discover_group_policies" in registry
        assert "configure_group_policy" in registry

        # Packet Capture
        assert "create_packet_capture" in registry
        assert "get_packet_capture_status" in registry

        # Static Routes
        assert "discover_static_routes" in registry
        assert "manage_static_route" in registry


class TestWave4Safety:
    """Test safety classifications for Wave 4"""

    def test_all_wave4_safety_levels(self):
        """Test all Wave 4 function safety levels"""
        # Floor Plans
        assert SAFETY_CLASSIFICATION["discover_floor_plans"] == SafetyLevel.SAFE
        assert SAFETY_CLASSIFICATION["create_floor_plan"] == SafetyLevel.MODERATE
        assert SAFETY_CLASSIFICATION["update_floor_plan"] == SafetyLevel.MODERATE
        assert SAFETY_CLASSIFICATION["delete_floor_plan"] == SafetyLevel.MODERATE

        # Group Policies
        assert SAFETY_CLASSIFICATION["discover_group_policies"] == SafetyLevel.SAFE
        assert SAFETY_CLASSIFICATION["configure_group_policy"] == SafetyLevel.MODERATE

        # Packet Capture
        assert SAFETY_CLASSIFICATION["create_packet_capture"] == SafetyLevel.MODERATE
        assert SAFETY_CLASSIFICATION["get_packet_capture_status"] == SafetyLevel.SAFE

        # Static Routes
        assert SAFETY_CLASSIFICATION["discover_static_routes"] == SafetyLevel.SAFE
        assert SAFETY_CLASSIFICATION["manage_static_route"] == SafetyLevel.MODERATE

    def test_wave4_safety_counts(self):
        """Test that Wave 4 adds correct number of entries"""
        safe_count = sum(
            1 for level in SAFETY_CLASSIFICATION.values()
            if level == SafetyLevel.SAFE
        )
        moderate_count = sum(
            1 for level in SAFETY_CLASSIFICATION.values()
            if level == SafetyLevel.MODERATE
        )
        dangerous_count = sum(
            1 for level in SAFETY_CLASSIFICATION.values()
            if level == SafetyLevel.DANGEROUS
        )

        # After Wave 4: SAFE=78, MODERATE=36, DANGEROUS=22
        assert safe_count == 78
        assert moderate_count == 36
        assert dangerous_count == 22
