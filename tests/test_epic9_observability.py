"""
Comprehensive tests for Epic 9: Alerts, Firmware & Observability.

Tests all 8 stories:
- 9.1: Alerts & Webhooks (configure_alerts, create_webhook_endpoint, test_webhook)
- 9.2: Firmware Upgrades (schedule_firmware_upgrade, cancel_firmware_upgrade, discover_firmware_status)
- 9.3: Live Tools - Ping (create_ping, get_ping_result)
- 9.4: Live Tools - Traceroute (N/A - no dedicated SDK method in most versions)
- 9.5: Live Tools - Cable Test (create_cable_test, get_cable_test_result)
- 9.6: SNMP Configuration (configure_snmp, discover_snmp_config)
- 9.7: Syslog Configuration (configure_syslog, discover_syslog_config)
- 9.8: Change Log Access (discover_recent_changes)
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path
from datetime import datetime
from meraki.exceptions import APIError

from scripts.api import MerakiClient
from scripts import discovery, config
from scripts.config import ConfigResult, ConfigAction


# ==================== Fixtures ====================


@pytest.fixture
def mock_client():
    """Mock MerakiClient for testing."""
    client = MagicMock(spec=MerakiClient)
    client.org_id = "org_123"
    return client


@pytest.fixture
def mock_api_error():
    """Factory for creating mock APIError responses."""
    def _make_error(status_code: int, message: str = "API Error"):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = message
        return APIError(
            metadata={
                "operation": "test_operation",
                "url": "https://api.meraki.com/test",
                "user_agent": "test",
                "tags": ["test"],
            },
            response=mock_response
        )
    return _make_error


# ==================== Story 9.1: Alerts & Webhooks ====================


def test_discover_alerts_success(mock_client):
    """Test discover_alerts with valid response."""
    mock_client.safe_call.return_value = {
        "alerts": [
            {"type": "gatewayDown", "enabled": True},
            {"type": "clientConnectivityChanged", "enabled": False}
        ],
        "defaultDestinations": {"emails": ["admin@example.com"]}
    }

    result = discovery.discover_alerts("N_123", mock_client)

    assert "alerts" in result
    assert len(result["alerts"]) == 2
    mock_client.safe_call.assert_called_once()


def test_discover_alerts_empty(mock_client):
    """Test discover_alerts with no alerts configured."""
    mock_client.safe_call.return_value = {}

    result = discovery.discover_alerts("N_123", mock_client)

    assert result == {}


def test_discover_webhooks_success(mock_client):
    """Test discover_webhooks with valid response."""
    mock_client.safe_call.return_value = [
        {"id": "wh_1", "name": "Slack Webhook", "url": "https://hooks.slack.com/services/..."},
        {"id": "wh_2", "name": "Teams Webhook", "url": "https://outlook.office.com/webhook/..."}
    ]

    result = discovery.discover_webhooks("N_123", mock_client)

    assert len(result) == 2
    assert result[0]["name"] == "Slack Webhook"


def test_configure_alerts_success(mock_client, tmp_path):
    """Test configure_alerts with backup."""
    mock_client.update_alert_settings.return_value = {
        "alerts": [{"type": "gatewayDown", "enabled": True}]
    }

    # Mock backup_config
    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.configure_alerts(
            network_id="N_123",
            alerts=[{"type": "gatewayDown", "enabled": True}],
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.UPDATE
    assert result.resource_type == "alerts"
    assert "Alertas configurados" in result.message
    mock_backup.assert_called_once()


def test_configure_alerts_error(mock_client, mock_api_error):
    """Test configure_alerts with API error."""
    mock_client.update_alert_settings.side_effect = mock_api_error(400, "Invalid alerts configuration")

    result = config.configure_alerts(
        network_id="N_123",
        alerts=[{"type": "invalid", "enabled": True}],
        backup=False,
        client=mock_client
    )

    assert not result.success
    assert "Falha ao configurar alertas" in result.message
    assert result.error is not None


def test_create_webhook_endpoint_success(mock_client, tmp_path):
    """Test create_webhook_endpoint."""
    mock_client.create_webhook_server.return_value = {
        "id": "wh_123",
        "name": "Slack",
        "url": "https://hooks.slack.com/test"
    }

    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.create_webhook_endpoint(
            network_id="N_123",
            name="Slack",
            url="https://hooks.slack.com/test",
            shared_secret="secret123",
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.CREATE
    assert result.resource_type == "webhook"
    assert "Webhook criado" in result.message


def test_create_webhook_endpoint_no_secret(mock_client):
    """Test create_webhook_endpoint without shared secret."""
    mock_client.create_webhook_server.return_value = {
        "id": "wh_123",
        "name": "Teams",
        "url": "https://outlook.office.com/test"
    }

    result = config.create_webhook_endpoint(
        network_id="N_123",
        name="Teams",
        url="https://outlook.office.com/test",
        backup=False,
        client=mock_client
    )

    assert result.success
    # Verify sharedSecret was not passed
    call_kwargs = mock_client.create_webhook_server.call_args[1]
    assert "sharedSecret" not in call_kwargs


# ==================== Story 9.2: Firmware Upgrades ====================


def test_discover_firmware_status_success(mock_client):
    """Test discover_firmware_status with valid response."""
    mock_client.safe_call.return_value = {
        "upgradeWindow": {"dayOfWeek": "Monday", "hourOfDay": "02:00"},
        "products": {
            "wireless": {
                "currentVersion": {"id": "v1.0", "shortName": "MR 28.5"},
                "nextUpgrade": {"id": "v1.1", "shortName": "MR 28.6"}
            }
        }
    }

    result = discovery.discover_firmware_status("N_123", mock_client)

    assert "upgradeWindow" in result
    assert "products" in result
    assert result["products"]["wireless"]["currentVersion"]["shortName"] == "MR 28.5"


def test_schedule_firmware_upgrade_success(mock_client, tmp_path):
    """Test schedule_firmware_upgrade (DANGEROUS)."""
    mock_client.update_firmware_upgrades.return_value = {
        "products": {"wireless": {"nextUpgrade": {"id": "v1.1"}}},
        "upgradeWindow": {"dayOfWeek": "Sunday", "hourOfDay": "03:00"}
    }

    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.schedule_firmware_upgrade(
            network_id="N_123",
            products={"wireless": {"nextUpgrade": {"id": "v1.1"}}},
            upgrade_window={"dayOfWeek": "Sunday", "hourOfDay": "03:00"},
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.UPDATE
    assert result.resource_type == "firmware"
    assert "Firmware upgrade agendado" in result.message


def test_schedule_firmware_upgrade_error(mock_client, mock_api_error):
    """Test schedule_firmware_upgrade with API error."""
    mock_client.update_firmware_upgrades.side_effect = mock_api_error(400, "Invalid upgrade window")

    result = config.schedule_firmware_upgrade(
        network_id="N_123",
        products={"wireless": {"nextUpgrade": {"id": "invalid"}}},
        upgrade_window={"dayOfWeek": "Invalid", "hourOfDay": "25:00"},
        backup=False,
        client=mock_client
    )

    assert not result.success
    assert "Falha ao agendar firmware upgrade" in result.message


def test_cancel_firmware_upgrade_success(mock_client, tmp_path):
    """Test cancel_firmware_upgrade (DANGEROUS)."""
    mock_client.get_firmware_upgrades.return_value = {
        "products": {
            "wireless": {"nextUpgrade": {"id": "v1.1"}},
            "switch": {"nextUpgrade": {"id": "v2.2"}}
        }
    }
    mock_client.update_firmware_upgrades.return_value = {
        "products": {
            "wireless": {"nextUpgrade": None},
            "switch": {"nextUpgrade": {"id": "v2.2"}}
        }
    }

    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.cancel_firmware_upgrade(
            network_id="N_123",
            products=["wireless"],
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.DELETE
    assert "cancelado" in result.message


def test_cancel_firmware_upgrade_multiple_products(mock_client):
    """Test cancel_firmware_upgrade with multiple products."""
    mock_client.get_firmware_upgrades.return_value = {
        "products": {
            "wireless": {"nextUpgrade": {"id": "v1"}},
            "switch": {"nextUpgrade": {"id": "v2"}},
            "appliance": {"nextUpgrade": {"id": "v3"}}
        }
    }
    mock_client.update_firmware_upgrades.return_value = {
        "products": {
            "wireless": {"nextUpgrade": None},
            "switch": {"nextUpgrade": None},
            "appliance": {"nextUpgrade": {"id": "v3"}}
        }
    }

    result = config.cancel_firmware_upgrade(
        network_id="N_123",
        products=["wireless", "switch"],
        backup=False,
        client=mock_client
    )

    assert result.success
    call_kwargs = mock_client.update_firmware_upgrades.call_args[1]
    assert call_kwargs["products"]["wireless"]["nextUpgrade"] is None
    assert call_kwargs["products"]["switch"]["nextUpgrade"] is None


# ==================== Story 9.3: Live Tools - Ping ====================


def test_api_create_ping():
    """Test api.py create_ping method."""
    mock_dashboard = MagicMock()
    mock_dashboard.devices.createDeviceLiveToolsPing.return_value = {
        "pingId": "ping_123",
        "status": "pending"
    }

    from scripts.api import MerakiClient
    client = MerakiClient.__new__(MerakiClient)
    client.dashboard = mock_dashboard

    result = client.create_ping("Q2XX-XXXX-XXXX", "8.8.8.8", count=10)

    assert result["pingId"] == "ping_123"
    mock_dashboard.devices.createDeviceLiveToolsPing.assert_called_with(
        "Q2XX-XXXX-XXXX", target="8.8.8.8", count=10
    )


def test_api_get_ping_result():
    """Test api.py get_ping_result method."""
    mock_dashboard = MagicMock()
    mock_dashboard.devices.getDeviceLiveToolsPing.return_value = {
        "pingId": "ping_123",
        "status": "complete",
        "results": {"sent": 10, "received": 10, "loss": "0%"}
    }

    from scripts.api import MerakiClient
    client = MerakiClient.__new__(MerakiClient)
    client.dashboard = mock_dashboard

    result = client.get_ping_result("Q2XX-XXXX-XXXX", "ping_123")

    assert result["status"] == "complete"
    assert result["results"]["loss"] == "0%"


# ==================== Story 9.5: Live Tools - Cable Test ====================


def test_api_create_cable_test():
    """Test api.py create_cable_test method."""
    mock_dashboard = MagicMock()
    mock_dashboard.devices.createDeviceLiveToolsCableTest.return_value = {
        "cableTestId": "ct_123",
        "status": "pending"
    }

    from scripts.api import MerakiClient
    client = MerakiClient.__new__(MerakiClient)
    client.dashboard = mock_dashboard

    result = client.create_cable_test("Q2XX-XXXX-XXXX", ["1", "2", "3"])

    assert result["cableTestId"] == "ct_123"
    mock_dashboard.devices.createDeviceLiveToolsCableTest.assert_called_with(
        "Q2XX-XXXX-XXXX", ports=["1", "2", "3"]
    )


def test_api_get_cable_test_result():
    """Test api.py get_cable_test_result method."""
    mock_dashboard = MagicMock()
    mock_dashboard.devices.getDeviceLiveToolsCableTest.return_value = {
        "cableTestId": "ct_123",
        "status": "complete",
        "results": [
            {"port": "1", "status": "OK", "length": 10},
            {"port": "2", "status": "Open", "length": 0}
        ]
    }

    from scripts.api import MerakiClient
    client = MerakiClient.__new__(MerakiClient)
    client.dashboard = mock_dashboard

    result = client.get_cable_test_result("Q2XX-XXXX-XXXX", "ct_123")

    assert result["status"] == "complete"
    assert len(result["results"]) == 2


# ==================== Story 9.6: SNMP Configuration ====================


def test_discover_snmp_config_success(mock_client):
    """Test discover_snmp_config with valid response."""
    mock_client.safe_call.return_value = {
        "access": "users",
        "users": [{"username": "snmp_user", "passphrase": "***"}]
    }

    result = discovery.discover_snmp_config("N_123", mock_client)

    assert result["access"] == "users"
    assert len(result["users"]) == 1


def test_discover_snmp_config_disabled(mock_client):
    """Test discover_snmp_config with SNMP disabled."""
    mock_client.safe_call.return_value = {"access": "none"}

    result = discovery.discover_snmp_config("N_123", mock_client)

    assert result["access"] == "none"


def test_configure_snmp_community(mock_client, tmp_path):
    """Test configure_snmp with community string (MODERATE)."""
    mock_client.update_snmp_settings.return_value = {
        "access": "community",
        "communityString": "public"
    }

    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.configure_snmp(
            network_id="N_123",
            access="community",
            community_string="public",
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.UPDATE
    assert result.resource_type == "snmp"
    assert "access=community" in result.message


def test_configure_snmp_users(mock_client):
    """Test configure_snmp with SNMPv3 users (MODERATE)."""
    mock_client.update_snmp_settings.return_value = {
        "access": "users",
        "users": [{"username": "admin", "passphrase": "***"}]
    }

    result = config.configure_snmp(
        network_id="N_123",
        access="users",
        users=[{"username": "admin", "passphrase": "secure123"}],
        backup=False,
        client=mock_client
    )

    assert result.success
    call_kwargs = mock_client.update_snmp_settings.call_args[1]
    assert "users" in call_kwargs
    assert len(call_kwargs["users"]) == 1


def test_configure_snmp_disable(mock_client):
    """Test configure_snmp to disable SNMP."""
    mock_client.update_snmp_settings.return_value = {"access": "none"}

    result = config.configure_snmp(
        network_id="N_123",
        access="none",
        backup=False,
        client=mock_client
    )

    assert result.success
    assert "access=none" in result.message


def test_configure_snmp_error(mock_client, mock_api_error):
    """Test configure_snmp with API error."""
    mock_client.update_snmp_settings.side_effect = mock_api_error(400, "Invalid SNMP configuration")

    result = config.configure_snmp(
        network_id="N_123",
        access="invalid",
        backup=False,
        client=mock_client
    )

    assert not result.success
    assert "Falha ao configurar SNMP" in result.message


# ==================== Story 9.7: Syslog Configuration ====================


def test_discover_syslog_config_success(mock_client):
    """Test discover_syslog_config with valid response."""
    mock_client.safe_call.return_value = {
        "servers": [
            {"host": "192.168.1.100", "port": 514, "roles": ["Wireless event log"]},
            {"host": "syslog.example.com", "port": 514, "roles": ["Appliance event log"]}
        ]
    }

    result = discovery.discover_syslog_config("N_123", mock_client)

    assert "servers" in result
    assert len(result["servers"]) == 2


def test_discover_syslog_config_empty(mock_client):
    """Test discover_syslog_config with no servers."""
    mock_client.safe_call.return_value = {"servers": []}

    result = discovery.discover_syslog_config("N_123", mock_client)

    assert result["servers"] == []


def test_configure_syslog_success(mock_client, tmp_path):
    """Test configure_syslog (MODERATE)."""
    mock_client.update_syslog_servers.return_value = {
        "servers": [
            {"host": "192.168.1.100", "port": 514, "roles": ["Wireless event log"]}
        ]
    }

    with patch("scripts.config.backup_config") as mock_backup:
        mock_backup.return_value = tmp_path / "backup.json"

        result = config.configure_syslog(
            network_id="N_123",
            servers=[
                {"host": "192.168.1.100", "port": 514, "roles": ["Wireless event log"]}
            ],
            backup=True,
            client_name="test-client",
            client=mock_client
        )

    assert result.success
    assert result.action == ConfigAction.UPDATE
    assert result.resource_type == "syslog"
    assert "1 servers" in result.message


def test_configure_syslog_multiple_servers(mock_client):
    """Test configure_syslog with multiple servers."""
    servers = [
        {"host": "192.168.1.100", "port": 514, "roles": ["Wireless event log"]},
        {"host": "192.168.1.101", "port": 514, "roles": ["Appliance event log"]},
        {"host": "syslog.example.com", "port": 514, "roles": ["Flows"]}
    ]
    mock_client.update_syslog_servers.return_value = {"servers": servers}

    result = config.configure_syslog(
        network_id="N_123",
        servers=servers,
        backup=False,
        client=mock_client
    )

    assert result.success
    assert "3 servers" in result.message


def test_configure_syslog_error(mock_client, mock_api_error):
    """Test configure_syslog with API error."""
    mock_client.update_syslog_servers.side_effect = mock_api_error(400, "Invalid syslog configuration")

    result = config.configure_syslog(
        network_id="N_123",
        servers=[{"host": "invalid", "port": 99999}],
        backup=False,
        client=mock_client
    )

    assert not result.success
    assert "Falha ao configurar syslog" in result.message


# ==================== Story 9.8: Change Log Access ====================


def test_discover_recent_changes_success(mock_client):
    """Test discover_recent_changes with valid response."""
    mock_client.safe_call.return_value = [
        {
            "ts": "2026-02-09T10:00:00Z",
            "adminName": "John Doe",
            "page": "Network-wide",
            "label": "SSID settings",
            "oldValue": "SSID_Old",
            "newValue": "SSID_New"
        },
        {
            "ts": "2026-02-09T09:00:00Z",
            "adminName": "Jane Smith",
            "page": "Firewall",
            "label": "L3 firewall rules",
            "oldValue": "...",
            "newValue": "..."
        }
    ]

    result = discovery.discover_recent_changes(org_id="org_123", timespan=3600, client=mock_client)

    assert len(result) == 2
    assert result[0]["adminName"] == "John Doe"
    assert result[1]["page"] == "Firewall"


def test_discover_recent_changes_empty(mock_client):
    """Test discover_recent_changes with no changes."""
    mock_client.safe_call.return_value = []

    result = discovery.discover_recent_changes(client=mock_client)

    assert result == []


def test_discover_recent_changes_custom_timespan(mock_client):
    """Test discover_recent_changes with custom timespan."""
    mock_client.safe_call.return_value = [{"ts": "2026-02-09T10:00:00Z", "page": "Test"}]

    result = discovery.discover_recent_changes(timespan=7200, client=mock_client)

    assert len(result) == 1
    # Verify timespan was passed correctly
    call_args = mock_client.safe_call.call_args
    # Check either positional or keyword argument
    assert call_args[1].get("timespan") == 7200 or (len(call_args[0]) > 2 and call_args[0][2] == 7200)


def test_api_get_config_changes():
    """Test api.py get_config_changes method."""
    mock_dashboard = MagicMock()
    mock_dashboard.organizations.getOrganizationConfigurationChanges.return_value = [
        {"ts": "2026-02-09T10:00:00Z", "page": "Wireless"}
    ]

    from scripts.api import MerakiClient
    client = MerakiClient.__new__(MerakiClient)
    client.dashboard = mock_dashboard
    client.org_id = "org_123"

    result = client.get_config_changes(timespan=3600)

    assert len(result) == 1
    mock_dashboard.organizations.getOrganizationConfigurationChanges.assert_called_with(
        "org_123", timespan=3600
    )


# ==================== Issue Detection ====================


def test_find_issues_no_alerts_configured():
    """Test find_issues detects networks without alerts."""
    from scripts.discovery import DiscoveryResult, NetworkInfo, find_issues

    discovery = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="org_123",
        org_name="Test Org",
        networks=[
            NetworkInfo(id="N_1", name="Net1", organization_id="org_123", product_types=["wireless"]),
            NetworkInfo(id="N_2", name="Net2", organization_id="org_123", product_types=["appliance"])
        ],
        devices=[],
        configurations={
            "N_1": {"alert_settings": {}},
            "N_2": {"alert_settings": {"alerts": []}}
        },
        issues=[],
        suggestions=[]
    )

    issues = find_issues(discovery)

    no_alerts_issue = next((i for i in issues if i["type"] == "no_alerts_configured"), None)
    assert no_alerts_issue is not None
    assert no_alerts_issue["count"] == 2
    assert no_alerts_issue["severity"] == "medium"


def test_find_issues_firmware_outdated():
    """Test find_issues detects outdated firmware."""
    from scripts.discovery import DiscoveryResult, NetworkInfo, find_issues

    discovery = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="org_123",
        org_name="Test Org",
        networks=[
            NetworkInfo(id="N_1", name="Net1", organization_id="org_123", product_types=["wireless"])
        ],
        devices=[],
        configurations={
            "N_1": {
                "firmware_status": {
                    "products": {
                        "wireless": {
                            "currentVersion": {"id": "v1.0", "shortName": "MR 28.5"},
                            "nextUpgrade": {"id": "v1.1", "shortName": "MR 28.6"}
                        }
                    }
                }
            }
        },
        issues=[],
        suggestions=[]
    )

    issues = find_issues(discovery)

    firmware_issue = next((i for i in issues if i["type"] == "firmware_outdated"), None)
    assert firmware_issue is not None
    assert firmware_issue["count"] == 1
    assert firmware_issue["severity"] == "low"


def test_find_issues_no_snmp_configured():
    """Test find_issues detects networks without SNMP."""
    from scripts.discovery import DiscoveryResult, NetworkInfo, find_issues

    discovery = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="org_123",
        org_name="Test Org",
        networks=[
            NetworkInfo(id="N_1", name="Net1", organization_id="org_123", product_types=["switch"])
        ],
        devices=[],
        configurations={
            "N_1": {"snmp_config": {"access": "none"}}
        },
        issues=[],
        suggestions=[]
    )

    issues = find_issues(discovery)

    snmp_issue = next((i for i in issues if i["type"] == "no_snmp_configured"), None)
    assert snmp_issue is not None
    assert snmp_issue["count"] == 1


def test_find_issues_no_syslog_configured():
    """Test find_issues detects networks without syslog."""
    from scripts.discovery import DiscoveryResult, NetworkInfo, find_issues

    discovery = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="org_123",
        org_name="Test Org",
        networks=[
            NetworkInfo(id="N_1", name="Net1", organization_id="org_123", product_types=["appliance"])
        ],
        devices=[],
        configurations={
            "N_1": {"syslog_config": {"servers": []}}
        },
        issues=[],
        suggestions=[]
    )

    issues = find_issues(discovery)

    syslog_issue = next((i for i in issues if i["type"] == "no_syslog_configured"), None)
    assert syslog_issue is not None
    assert syslog_issue["count"] == 1


# ==================== Safety Classifications ====================


def test_safety_classifications_epic9():
    """Verify all Epic 9 functions have safety classifications."""
    from scripts.agent_tools import TOOL_SAFETY, SafetyLevel

    # SAFE
    assert TOOL_SAFETY["discover_alerts"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["discover_webhooks"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["discover_firmware_status"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["discover_snmp_config"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["discover_syslog_config"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["discover_recent_changes"] == SafetyLevel.SAFE
    assert TOOL_SAFETY["test_webhook"] == SafetyLevel.SAFE

    # MODERATE
    assert TOOL_SAFETY["configure_alerts"] == SafetyLevel.MODERATE
    assert TOOL_SAFETY["create_webhook_endpoint"] == SafetyLevel.MODERATE
    assert TOOL_SAFETY["configure_snmp"] == SafetyLevel.MODERATE
    assert TOOL_SAFETY["configure_syslog"] == SafetyLevel.MODERATE

    # DANGEROUS
    assert TOOL_SAFETY["schedule_firmware_upgrade"] == SafetyLevel.DANGEROUS
    assert TOOL_SAFETY["cancel_firmware_upgrade"] == SafetyLevel.DANGEROUS


def test_safety_classifications_in_safety_module():
    """Verify safety.py has all Epic 9 classifications."""
    from scripts.safety import SAFETY_CLASSIFICATION, SafetyLevel

    # SAFE
    assert SAFETY_CLASSIFICATION["discover_alerts"] == SafetyLevel.SAFE
    assert SAFETY_CLASSIFICATION["test_webhook"] == SafetyLevel.SAFE

    # MODERATE
    assert SAFETY_CLASSIFICATION["configure_alerts"] == SafetyLevel.MODERATE
    assert SAFETY_CLASSIFICATION["create_webhook_endpoint"] == SafetyLevel.MODERATE

    # DANGEROUS
    assert SAFETY_CLASSIFICATION["schedule_firmware_upgrade"] == SafetyLevel.DANGEROUS
    assert SAFETY_CLASSIFICATION["cancel_firmware_upgrade"] == SafetyLevel.DANGEROUS


# ==================== Function Registry ====================


def test_function_registry_epic9():
    """Verify all Epic 9 functions are in FUNCTION_REGISTRY."""
    from scripts.agent_router import FUNCTION_REGISTRY

    # Discovery functions
    assert "discover_alerts" in FUNCTION_REGISTRY
    assert "discover_webhooks" in FUNCTION_REGISTRY
    assert "discover_firmware_status" in FUNCTION_REGISTRY
    assert "discover_snmp_config" in FUNCTION_REGISTRY
    assert "discover_syslog_config" in FUNCTION_REGISTRY
    assert "discover_recent_changes" in FUNCTION_REGISTRY

    # Config functions
    assert "configure_alerts" in FUNCTION_REGISTRY
    assert "create_webhook_endpoint" in FUNCTION_REGISTRY
    assert "schedule_firmware_upgrade" in FUNCTION_REGISTRY
    assert "cancel_firmware_upgrade" in FUNCTION_REGISTRY
    assert "configure_snmp" in FUNCTION_REGISTRY
    assert "configure_syslog" in FUNCTION_REGISTRY


# ==================== Tool Schema Validation ====================


def test_tool_schemas_valid():
    """Verify all Epic 9 tool schemas are valid."""
    from scripts.agent_tools import (
        NETWORK_ANALYST_TOOLS,
        MERAKI_SPECIALIST_TOOLS,
        validate_tool_schema
    )

    epic9_tools = [
        "discover_alerts",
        "discover_webhooks",
        "discover_firmware_status",
        "discover_snmp_config",
        "discover_syslog_config",
        "discover_recent_changes",
        "configure_alerts",
        "create_webhook_endpoint",
        "schedule_firmware_upgrade",
        "cancel_firmware_upgrade",
        "configure_snmp",
        "configure_syslog"
    ]

    all_tools = NETWORK_ANALYST_TOOLS + MERAKI_SPECIALIST_TOOLS

    for tool_name in epic9_tools:
        tool = next((t for t in all_tools if t["function"]["name"] == tool_name), None)
        assert tool is not None, f"Tool {tool_name} not found in agent tools"
        valid, error = validate_tool_schema(tool)
        assert valid, f"Tool {tool_name} has invalid schema: {error}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
