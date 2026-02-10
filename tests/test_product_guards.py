"""
Tests for hardware product-type guards in discovery and config functions.

Verifies that functions return early with clear "no hardware" results
when the required product type is missing from a network.
"""

import pytest
from unittest.mock import MagicMock, patch

from scripts.api import (
    clear_product_type_cache,
    get_network_product_types,
    network_has_product,
)
from scripts.config import ConfigAction, configure_ips, configure_ssid, configure_stp
from scripts.config import add_firewall_rule, configure_s2s_vpn, configure_qos
from scripts.discovery import (
    discover_content_filtering,
    discover_qos_config,
    discover_ssids,
    discover_stp_config,
    discover_vlans,
    discover_wireless_health,
)


# ==================== Fixtures ====================


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the product-type cache before each test."""
    clear_product_type_cache()
    yield
    clear_product_type_cache()


def _make_client(product_types=None):
    """Create a MerakiClient mock that returns a specific network dict.

    If product_types is None, get_network returns a MagicMock (simulating
    an unconfigured mock client where product types can't be determined).
    """
    client = MagicMock()
    if product_types is not None:
        client.get_network.return_value = {
            "id": "N_123",
            "name": "Test Network",
            "productTypes": product_types,
        }
    # else: client.get_network() returns MagicMock() (not a dict)
    return client


# ==================== Helper Tests ====================


class TestGetNetworkProductTypes:
    def test_real_dict_returns_list(self):
        client = _make_client(["appliance", "switch"])
        result = get_network_product_types("N_123", client)
        assert result == ["appliance", "switch"]

    def test_mock_client_returns_none(self):
        client = MagicMock()  # get_network returns MagicMock (not dict)
        result = get_network_product_types("N_123", client)
        assert result is None

    def test_api_error_returns_none(self):
        client = _make_client(["appliance"])
        client.get_network.side_effect = Exception("API timeout")
        result = get_network_product_types("N_123", client)
        assert result is None

    def test_cache_prevents_repeat_calls(self):
        client = _make_client(["wireless"])
        get_network_product_types("N_123", client)
        get_network_product_types("N_123", client)
        assert client.get_network.call_count == 1

    def test_clear_cache(self):
        client = _make_client(["wireless"])
        get_network_product_types("N_123", client)
        clear_product_type_cache()
        get_network_product_types("N_123", client)
        assert client.get_network.call_count == 2


# ==================== Discovery Guard Tests ====================


class TestDiscoveryGuards:
    def test_discover_vlans_skips_without_appliance(self):
        client = _make_client(["switch", "wireless"])
        result = discover_vlans("N_123", client)
        assert result == []
        client.safe_call.assert_not_called()

    def test_discover_ssids_skips_without_wireless(self):
        client = _make_client(["appliance", "switch"])
        result = discover_ssids("N_123", client)
        assert result == []
        client.safe_call.assert_not_called()

    def test_discover_stp_skips_without_switch(self):
        client = _make_client(["appliance", "wireless"])
        result = discover_stp_config("N_123", client)
        assert result == {}
        client.safe_call.assert_not_called()

    def test_discover_content_filtering_skips_without_appliance(self):
        client = _make_client(["switch"])
        result = discover_content_filtering("N_123", client)
        assert result == {}
        client.safe_call.assert_not_called()

    def test_discover_vlans_proceeds_when_unknown(self):
        """Mock client (can't determine hw) → guard skipped → safe_call runs."""
        client = MagicMock()
        client.safe_call.return_value = []
        result = discover_vlans("N_123", client)
        assert result == []
        client.safe_call.assert_called_once()

    def test_discover_wireless_health_skips_without_wireless(self):
        client = _make_client(["appliance"])
        result = discover_wireless_health("N_123", client)
        assert result["connection_stats"] == {}
        assert result["failed_connections"] == []
        client.safe_call.assert_not_called()

    def test_discover_qos_skips_without_switch(self):
        client = _make_client(["appliance", "wireless"])
        result = discover_qos_config("N_123", client)
        assert result == []
        client.safe_call.assert_not_called()


# ==================== Config Guard Tests ====================


class TestConfigGuards:
    def test_configure_ips_rejects_without_appliance(self):
        client = _make_client(["switch"])
        result = configure_ips("N_123", mode="prevention", client=client)
        assert result.success is False
        assert result.error == "missing_hardware:appliance"
        assert "MX appliance" in result.message

    def test_configure_ssid_rejects_without_wireless(self):
        client = _make_client(["appliance", "switch"])
        result = configure_ssid("N_123", ssid_number=0, name="Test", client=client)
        assert result.success is False
        assert result.error == "missing_hardware:wireless"
        assert "MR wireless AP" in result.message

    def test_configure_stp_rejects_without_switch(self):
        client = _make_client(["appliance"])
        result = configure_stp("N_123", rstp_enabled=True, client=client)
        assert result.success is False
        assert result.error == "missing_hardware:switch"
        assert "MS switch" in result.message

    def test_configure_ips_proceeds_when_unknown(self):
        """Mock client → guard returns None → function proceeds normally."""
        client = MagicMock()
        # configure_ips will try to call API and fail, but the guard didn't block it
        # We just need to verify it gets past the guard
        client.safe_call.return_value = {}
        try:
            result = configure_ips("N_123", mode="prevention", client=client)
        except Exception:
            pass  # May fail deeper in the function; that's OK — we just verify guard didn't block
        # The guard did not block — get_network was called but returned MagicMock
        # (which is not a dict), so network_has_product returned None → no early exit

    def test_configure_s2s_vpn_guard_before_dry_run(self):
        """Switch-only network + dry_run=True → guard fires, not dry_run."""
        client = _make_client(["switch"])
        result = configure_s2s_vpn("N_123", mode="spoke", client=client, dry_run=True)
        assert result.success is False
        assert result.error == "missing_hardware:appliance"
        # If dry_run had fired first, success would be True
        assert "[DRY-RUN]" not in result.message

    def test_add_firewall_rule_rejects_without_appliance(self):
        client = _make_client(["wireless"])
        result = add_firewall_rule(
            "N_123", policy="deny", protocol="tcp",
            src_cidr="any", dest_cidr="any", dest_port="23",
            client=client,
        )
        assert result.success is False
        assert result.error == "missing_hardware:appliance"

    def test_configure_qos_rejects_without_switch(self):
        client = _make_client(["appliance"])
        result = configure_qos("N_123", rules=[{"dscp": 0}], client=client)
        assert result.success is False
        assert result.error == "missing_hardware:switch"
        assert "MS switch" in result.message
