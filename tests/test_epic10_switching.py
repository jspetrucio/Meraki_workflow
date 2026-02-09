"""
Tests for Epic 10: Advanced Switching, Wireless & Platform.

Covers:
- Story 10.1: Switch Routing L3 (DANGEROUS)
- Story 10.2: STP Configuration (DANGEROUS)
- Story 10.3: Device Reboot & LED Blink (DANGEROUS/SAFE)
- Story 10.4: NAT & Port Forwarding (MODERATE)
- Story 10.5: RF Profiles (MODERATE)
- Story 10.6: Wireless Health Monitoring (SAFE)
- Story 10.7: Switch QoS (MODERATE)
- Story 10.8: Org Admins Management (DANGEROUS)
- Story 10.9: Inventory Management (MODERATE/DANGEROUS)
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from meraki.exceptions import APIError

from scripts import api, discovery, config
from scripts.agent_router import FUNCTION_REGISTRY
from scripts.agent_tools import get_agent_tools, TOOL_SAFETY, SafetyLevel
from scripts.safety import SAFETY_CLASSIFICATION
from scripts.config import ConfigResult, ConfigAction


# ==================== Fixtures ====================


@pytest.fixture
def mock_client():
    """Mock MerakiClient for testing."""
    client = MagicMock(spec=api.MerakiClient)
    client.org_id = "123456"
    client.api_key = "test_key"
    # Create nested dashboard mock
    client.dashboard = MagicMock()
    return client


@pytest.fixture
def mock_api_response():
    """Mock API response for error testing."""
    response = MagicMock()
    response.status_code = 400
    response.text = "API Error"
    return response


# ==================== Story 10.1: Switch Routing L3 Tests ====================


def test_get_switch_routing_interfaces(mock_client):
    """Test api.get_switch_routing_interfaces."""
    expected_result = [
        {"interfaceId": "1", "name": "Vlan10", "subnet": "192.168.10.0/24"}
    ]
    mock_client.get_switch_routing_interfaces.return_value = expected_result

    result = mock_client.get_switch_routing_interfaces("Q2XX-AAAA-BBBB")

    assert len(result) == 1
    assert result[0]["name"] == "Vlan10"
    mock_client.get_switch_routing_interfaces.assert_called_once_with("Q2XX-AAAA-BBBB")


def test_create_routing_interface(mock_client):
    """Test api.create_routing_interface."""
    expected_result = {
        "interfaceId": "2",
        "name": "Vlan20",
    }
    mock_client.create_routing_interface.return_value = expected_result

    result = mock_client.create_routing_interface(
        "Q2XX-AAAA-BBBB", name="Vlan20", subnet="192.168.20.0/24"
    )

    assert result["name"] == "Vlan20"
    mock_client.create_routing_interface.assert_called_once()


def test_discover_switch_routing(mock_client):
    """Test discovery.discover_switch_routing."""
    mock_client.safe_call.side_effect = [
        [{"interfaceId": "1", "name": "Vlan10"}],  # interfaces
        [{"staticRouteId": "1", "subnet": "10.0.0.0/8"}],  # static_routes
    ]

    result = discovery.discover_switch_routing("Q2XX-AAAA-BBBB", client=mock_client)

    assert "interfaces" in result
    assert "static_routes" in result
    assert len(result["interfaces"]) == 1
    assert len(result["static_routes"]) == 1


def test_configure_switch_l3_interface_success(mock_client):
    """Test config.configure_switch_l3_interface success."""
    mock_client.get_device.return_value = {"networkId": "N_123", "serial": "Q2XX-AAAA-BBBB"}
    mock_client.create_routing_interface.return_value = {
        "interfaceId": "2",
        "name": "Vlan30",
    }

    result = config.configure_switch_l3_interface(
        serial="Q2XX-AAAA-BBBB",
        name="Vlan30",
        subnet="192.168.30.0/24",
        interface_ip="192.168.30.1",
        vlan_id=30,
        backup=False,
        client=mock_client,
    )

    assert result.success is True
    assert "Vlan30" in result.message


def test_configure_switch_l3_interface_dry_run(mock_client):
    """Test config.configure_switch_l3_interface dry-run."""
    result = config.configure_switch_l3_interface(
        serial="Q2XX-AAAA-BBBB",
        name="Vlan40",
        dry_run=True,
        client=mock_client,
    )

    assert result.success is True
    assert "[DRY-RUN]" in result.message
    mock_client.create_routing_interface.assert_not_called()


def test_configure_switch_l3_interface_api_error(mock_client, mock_api_response):
    """Test config.configure_switch_l3_interface API error."""
    mock_client.get_device.return_value = {"networkId": "N_123"}
    mock_client.create_routing_interface.side_effect = APIError(
        metadata={
            "operation": "createDeviceSwitchRoutingInterface",
            "url": "https://api.meraki.com/api/v1/test",
            "user_agent": "test",
            "tags": ["switch", "routing"],
        },
        response=mock_api_response,
    )

    result = config.configure_switch_l3_interface(
        serial="Q2XX-AAAA-BBBB",
        name="Vlan50",
        backup=False,
        client=mock_client,
    )

    assert result.success is False
    assert "Falha" in result.message


# ==================== Story 10.2: STP Tests ====================


def test_get_stp_settings(mock_client):
    """Test api.get_stp_settings."""
    expected_result = {
        "rstpEnabled": True,
        "stpBridgePriority": [{"switchId": "Q2XX-AAAA-BBBB", "priority": 32768}],
    }
    mock_client.get_stp_settings.return_value = expected_result

    result = mock_client.get_stp_settings("N_123")

    assert result["rstpEnabled"] is True
    mock_client.get_stp_settings.assert_called_once_with("N_123")


def test_discover_stp_config(mock_client):
    """Test discovery.discover_stp_config."""
    mock_client.safe_call.return_value = {"rstpEnabled": False}

    result = discovery.discover_stp_config("N_123", client=mock_client)

    assert "rstpEnabled" in result


def test_configure_stp_success(mock_client):
    """Test config.configure_stp success."""
    mock_client.update_stp_settings.return_value = {"rstpEnabled": True}

    result = config.configure_stp(
        network_id="N_123",
        rstp_enabled=True,
        backup=False,
        client=mock_client,
    )

    assert result.success is True


def test_configure_stp_dry_run(mock_client):
    """Test config.configure_stp dry-run."""
    result = config.configure_stp(
        network_id="N_123",
        rstp_enabled=True,
        dry_run=True,
        client=mock_client,
    )

    assert result.success is True
    assert "[DRY-RUN]" in result.message
    mock_client.update_stp_settings.assert_not_called()


def test_stp_inconsistency_issue_detection():
    """Test find_issues detects STP inconsistency."""
    from scripts.discovery import DiscoveryResult, NetworkInfo, find_issues

    # Create mock discovery result
    networks = [
        NetworkInfo(
            id="N_123",
            name="Test Network",
            organization_id="123456",
            product_types=["switch"],
        )
    ]

    configurations = {
        "N_123": {
            "stp_config": {"stpBridgePriority": [{"switchId": "Q2XX"}], "rstpEnabled": False}
        }
    }

    discovery_result = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123456",
        org_name="Test Org",
        networks=networks,
        devices=[],
        configurations=configurations,
        issues=[],
        suggestions=[],
    )

    issues = find_issues(discovery_result)

    stp_issues = [i for i in issues if i["type"] == "stp_inconsistency"]
    assert len(stp_issues) == 1
    assert stp_issues[0]["severity"] == "medium"


# ==================== Story 10.3: Device Management Tests ====================


def test_reboot_device(mock_client):
    """Test api.reboot_device."""
    expected_result = {"success": True}
    mock_client.reboot_device.return_value = expected_result

    result = mock_client.reboot_device("Q2XX-AAAA-BBBB")

    assert result["success"] is True
    mock_client.reboot_device.assert_called_once_with("Q2XX-AAAA-BBBB")


def test_blink_leds(mock_client):
    """Test api.blink_leds."""
    expected_result = {"success": True}
    mock_client.blink_leds.return_value = expected_result

    result = mock_client.blink_leds("Q2XX-AAAA-BBBB", duration=30)

    assert result["success"] is True
    mock_client.blink_leds.assert_called_once_with("Q2XX-AAAA-BBBB", duration=30)


# ==================== Story 10.4: NAT & Port Forwarding Tests ====================


def test_get_1to1_nat(mock_client):
    """Test api.get_1to1_nat."""
    expected_result = {
        "rules": [{"name": "Rule1", "publicIp": "1.2.3.4"}]
    }
    mock_client.get_1to1_nat.return_value = expected_result

    result = mock_client.get_1to1_nat("N_123")

    assert len(result["rules"]) == 1
    mock_client.get_1to1_nat.assert_called_once_with("N_123")


def test_discover_nat_rules(mock_client):
    """Test discovery.discover_nat_rules."""
    mock_client.safe_call.side_effect = [
        {"rules": [{"name": "1to1"}]},
        {"rules": [{"name": "1tomany"}]},
    ]

    result = discovery.discover_nat_rules("N_123", client=mock_client)

    assert "1to1_nat" in result
    assert "1tomany_nat" in result


def test_configure_1to1_nat_success(mock_client):
    """Test config.configure_1to1_nat success."""
    mock_client.update_1to1_nat.return_value = {"rules": []}

    result = config.configure_1to1_nat(
        network_id="N_123",
        rules=[{"name": "Test", "publicIp": "1.2.3.4", "lanIp": "192.168.1.1"}],
        backup=False,
        client=mock_client,
    )

    assert result.success is True


def test_configure_port_forwarding_success(mock_client):
    """Test config.configure_port_forwarding success."""
    mock_client.update_port_forwarding.return_value = {"rules": []}

    result = config.configure_port_forwarding(
        network_id="N_123",
        rules=[{"name": "SSH", "publicPort": "22", "localIp": "192.168.1.10", "localPort": "22"}],
        backup=False,
        client=mock_client,
    )

    assert result.success is True


# ==================== Story 10.5: RF Profiles Tests ====================


def test_get_rf_profiles(mock_client):
    """Test api.get_rf_profiles."""
    expected_result = [{"id": "1", "name": "Default"}]
    mock_client.get_rf_profiles.return_value = expected_result

    result = mock_client.get_rf_profiles("N_123")

    assert len(result) == 1
    mock_client.get_rf_profiles.assert_called_once_with("N_123")


def test_discover_rf_profiles(mock_client):
    """Test discovery.discover_rf_profiles."""
    mock_client.safe_call.return_value = [{"id": "1", "name": "Default"}]

    result = discovery.discover_rf_profiles("N_123", client=mock_client)

    assert len(result) == 1


def test_configure_rf_profile_success(mock_client):
    """Test config.configure_rf_profile success."""
    mock_client.create_rf_profile.return_value = {"id": "2", "name": "Custom"}

    result = config.configure_rf_profile(
        network_id="N_123",
        name="Custom",
        band_selection_type="ap",
        backup=False,
        client=mock_client,
    )

    assert result.success is True


# ==================== Story 10.6: Wireless Health Tests ====================


def test_get_wireless_connection_stats(mock_client):
    """Test api.get_wireless_connection_stats."""
    expected_result = {
        "connectionStats": {"assoc": 100, "auth": 95}
    }
    mock_client.get_wireless_connection_stats.return_value = expected_result

    result = mock_client.get_wireless_connection_stats("N_123", timespan=7200)

    assert "connectionStats" in result
    mock_client.get_wireless_connection_stats.assert_called_once_with("N_123", timespan=7200)


def test_discover_wireless_health(mock_client):
    """Test discovery.discover_wireless_health."""
    mock_client.safe_call.side_effect = [
        {"connectionStats": {}},
        {"latencyStats": {}},
        [],
        [],
        [],
    ]

    result = discovery.discover_wireless_health("N_123", client=mock_client, timespan=3600)

    assert "connection_stats" in result
    assert "latency_stats" in result
    assert "signal_quality" in result
    assert "channel_utilization" in result
    assert "failed_connections" in result


# ==================== Story 10.7: Switch QoS Tests ====================


def test_get_qos_rules(mock_client):
    """Test api.get_qos_rules."""
    expected_result = [{"id": "1", "vlan": 10, "dscp": 46}]
    mock_client.get_qos_rules.return_value = expected_result

    result = mock_client.get_qos_rules("N_123")

    assert len(result) == 1
    mock_client.get_qos_rules.assert_called_once_with("N_123")


def test_discover_qos_config(mock_client):
    """Test discovery.discover_qos_config."""
    mock_client.safe_call.return_value = [{"id": "1", "vlan": 10}]

    result = discovery.discover_qos_config("N_123", client=mock_client)

    assert len(result) == 1


def test_configure_qos_success(mock_client):
    """Test config.configure_qos success."""
    mock_client.create_qos_rule.return_value = {"id": "2", "vlan": 20}

    result = config.configure_qos(
        network_id="N_123",
        rules=[{"vlan": 20, "dscp": 46}],
        backup=False,
        client=mock_client,
    )

    assert result.success is True


# ==================== Story 10.8: Org Admins Tests ====================


def test_get_admins(mock_client):
    """Test api.get_admins."""
    expected_result = [{"id": "1", "email": "admin@test.com", "orgAccess": "full"}]
    mock_client.get_admins.return_value = expected_result

    result = mock_client.get_admins("123456")

    assert len(result) == 1
    mock_client.get_admins.assert_called_once_with("123456")


def test_discover_org_admins(mock_client):
    """Test discovery.discover_org_admins."""
    mock_client.safe_call.return_value = [
        {"id": "1", "email": "admin@test.com"}
    ]

    result = discovery.discover_org_admins(org_id="123456", client=mock_client)

    assert len(result) == 1


def test_manage_admin_create_success(mock_client):
    """Test config.manage_admin create success."""
    mock_client.create_admin.return_value = {"id": "2", "email": "new@test.com"}

    result = config.manage_admin(
        org_id="123456",
        action="create",
        email="new@test.com",
        name="New Admin",
        org_access="read-only",
        backup=False,
        client=mock_client,
    )

    assert result.success is True


def test_manage_admin_delete_last_admin_guard_rail(mock_client):
    """Test config.manage_admin cannot delete last admin."""
    mock_client.get_admins.return_value = [{"id": "1", "email": "last@test.com"}]

    result = config.manage_admin(
        org_id="123456",
        action="delete",
        admin_id="1",
        backup=False,
        client=mock_client,
    )

    assert result.success is False
    assert "last admin" in result.message.lower()


def test_manage_admin_delete_success(mock_client):
    """Test config.manage_admin delete success."""
    mock_client.get_admins.return_value = [
        {"id": "1", "email": "admin1@test.com"},
        {"id": "2", "email": "admin2@test.com"},
    ]
    mock_client.delete_admin.return_value = None

    result = config.manage_admin(
        org_id="123456",
        action="delete",
        admin_id="2",
        backup=False,
        client=mock_client,
    )

    assert result.success is True


# ==================== Story 10.9: Inventory Tests ====================


def test_get_inventory(mock_client):
    """Test api.get_inventory."""
    expected_result = [{"serial": "Q2XX-AAAA-BBBB", "model": "MS120-8"}]
    mock_client.get_inventory.return_value = expected_result

    result = mock_client.get_inventory("123456")

    assert len(result) == 1
    mock_client.get_inventory.assert_called_once_with("123456")


def test_discover_inventory(mock_client):
    """Test discovery.discover_inventory."""
    mock_client.safe_call.return_value = [
        {"serial": "Q2XX-AAAA-BBBB", "model": "MS120-8"}
    ]

    result = discovery.discover_inventory(org_id="123456", client=mock_client)

    assert len(result) == 1


def test_claim_device(mock_client):
    """Test api.claim_device."""
    expected_result = {"serials": ["Q2XX-AAAA-BBBB"]}
    mock_client.claim_device.return_value = expected_result

    result = mock_client.claim_device(org_id="123456", serials=["Q2XX-AAAA-BBBB"])

    assert "serials" in result
    mock_client.claim_device.assert_called_once_with(org_id="123456", serials=["Q2XX-AAAA-BBBB"])


def test_release_device(mock_client):
    """Test api.release_device."""
    expected_result = {"serials": ["Q2XX-AAAA-BBBB"]}
    mock_client.release_device.return_value = expected_result

    result = mock_client.release_device(org_id="123456", serials=["Q2XX-AAAA-BBBB"])

    assert "serials" in result
    mock_client.release_device.assert_called_once_with(org_id="123456", serials=["Q2XX-AAAA-BBBB"])


# ==================== FUNCTION_REGISTRY Tests ====================


def test_epic10_function_registry_entries():
    """Test all Epic 10 functions are in FUNCTION_REGISTRY."""
    # Discovery functions
    assert "discover_switch_routing" in FUNCTION_REGISTRY
    assert "discover_stp_config" in FUNCTION_REGISTRY
    assert "discover_nat_rules" in FUNCTION_REGISTRY
    assert "discover_port_forwarding" in FUNCTION_REGISTRY
    assert "discover_rf_profiles" in FUNCTION_REGISTRY
    assert "discover_wireless_health" in FUNCTION_REGISTRY
    assert "discover_qos_config" in FUNCTION_REGISTRY
    assert "discover_org_admins" in FUNCTION_REGISTRY
    assert "discover_inventory" in FUNCTION_REGISTRY

    # Config functions
    assert "configure_switch_l3_interface" in FUNCTION_REGISTRY
    assert "add_switch_static_route" in FUNCTION_REGISTRY
    assert "configure_stp" in FUNCTION_REGISTRY
    assert "configure_1to1_nat" in FUNCTION_REGISTRY
    assert "configure_port_forwarding" in FUNCTION_REGISTRY
    assert "configure_rf_profile" in FUNCTION_REGISTRY
    assert "configure_qos" in FUNCTION_REGISTRY
    assert "manage_admin" in FUNCTION_REGISTRY

    # Direct API actions
    assert "reboot_device" in FUNCTION_REGISTRY
    assert "blink_leds" in FUNCTION_REGISTRY
    assert "claim_device" in FUNCTION_REGISTRY
    assert "release_device" in FUNCTION_REGISTRY


# ==================== Tool Schema Tests ====================


def test_epic10_tool_schemas_valid():
    """Test all Epic 10 tool schemas are valid."""
    from scripts.agent_tools import validate_tool_schema, AGENT_TOOLS

    epic10_tools = [
        # Network analyst (wireless health + inventory)
        "discover_wireless_health",
        "get_wireless_connection_stats",
        "get_wireless_latency_stats",
        "get_wireless_signal_quality",
        "get_channel_utilization",
        "get_failed_connections",
        "discover_inventory",
        # Meraki specialist (config + actions)
        "discover_switch_routing",
        "configure_switch_l3_interface",
        "add_switch_static_route",
        "discover_stp_config",
        "configure_stp",
        "reboot_device",
        "blink_leds",
        "discover_nat_rules",
        "discover_port_forwarding",
        "configure_1to1_nat",
        "configure_port_forwarding",
        "discover_rf_profiles",
        "configure_rf_profile",
        "discover_qos_config",
        "configure_qos",
        "discover_org_admins",
        "manage_admin",
        "claim_device",
        "release_device",
    ]

    for agent_name, tools in AGENT_TOOLS.items():
        for tool in tools:
            func_name = tool["function"]["name"]
            if func_name in epic10_tools:
                valid, error = validate_tool_schema(tool)
                assert valid, f"Tool schema invalid for {func_name}: {error}"

                # Check additionalProperties is False
                params = tool["function"]["parameters"]
                assert (
                    params.get("additionalProperties") is False
                ), f"Tool {func_name} should have additionalProperties=False"


# ==================== Safety Classification Tests ====================


def test_epic10_safety_classifications():
    """Test all Epic 10 functions have safety classifications."""
    epic10_functions = {
        # SAFE
        "discover_switch_routing": SafetyLevel.SAFE,
        "discover_stp_config": SafetyLevel.SAFE,
        "discover_nat_rules": SafetyLevel.SAFE,
        "discover_port_forwarding": SafetyLevel.SAFE,
        "discover_rf_profiles": SafetyLevel.SAFE,
        "discover_wireless_health": SafetyLevel.SAFE,
        "get_wireless_connection_stats": SafetyLevel.SAFE,
        "get_wireless_latency_stats": SafetyLevel.SAFE,
        "get_wireless_signal_quality": SafetyLevel.SAFE,
        "get_channel_utilization": SafetyLevel.SAFE,
        "get_failed_connections": SafetyLevel.SAFE,
        "discover_qos_config": SafetyLevel.SAFE,
        "discover_org_admins": SafetyLevel.SAFE,
        "discover_inventory": SafetyLevel.SAFE,
        "blink_leds": SafetyLevel.SAFE,
        # MODERATE
        "configure_1to1_nat": SafetyLevel.MODERATE,
        "configure_port_forwarding": SafetyLevel.MODERATE,
        "configure_rf_profile": SafetyLevel.MODERATE,
        "configure_qos": SafetyLevel.MODERATE,
        "claim_device": SafetyLevel.MODERATE,
        # DANGEROUS
        "configure_switch_l3_interface": SafetyLevel.DANGEROUS,
        "add_switch_static_route": SafetyLevel.DANGEROUS,
        "configure_stp": SafetyLevel.DANGEROUS,
        "reboot_device": SafetyLevel.DANGEROUS,
        "manage_admin": SafetyLevel.DANGEROUS,
        "release_device": SafetyLevel.DANGEROUS,
    }

    for func_name, expected_level in epic10_functions.items():
        # Check TOOL_SAFETY
        assert (
            func_name in TOOL_SAFETY
        ), f"{func_name} missing from TOOL_SAFETY"
        assert (
            TOOL_SAFETY[func_name] == expected_level
        ), f"{func_name} has wrong TOOL_SAFETY level"

        # Check SAFETY_CLASSIFICATION
        assert (
            func_name in SAFETY_CLASSIFICATION
        ), f"{func_name} missing from SAFETY_CLASSIFICATION"
        assert (
            SAFETY_CLASSIFICATION[func_name] == expected_level
        ), f"{func_name} has wrong SAFETY_CLASSIFICATION level"
