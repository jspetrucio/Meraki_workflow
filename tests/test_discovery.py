"""
Testes unitarios para o modulo discovery.

Testa:
- Parsing de dados da API
- Identificacao de issues
- Geracao de sugestoes
- Salvamento e carregamento de snapshots
- Comparacao de snapshots
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.discovery import (
    NetworkInfo,
    DeviceInfo,
    SSIDInfo,
    VLANInfo,
    DiscoveryResult,
    find_issues,
    generate_suggestions,
    save_snapshot,
    load_snapshot,
    compare_snapshots,
    discover_networks,
    discover_devices,
    discover_ssids,
    discover_vlans,
    full_discovery,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_client():
    """Cria um cliente Meraki mockado."""
    client = Mock()
    client.org_id = "123456"
    return client


@pytest.fixture
def sample_network_data():
    """Dados de exemplo de uma network."""
    return {
        "id": "N_12345",
        "name": "Main Office",
        "organizationId": "123456",
        "productTypes": ["switch", "wireless", "appliance"],
        "tags": ["production", "main"],
        "timeZone": "America/Los_Angeles",
    }


@pytest.fixture
def sample_device_data():
    """Dados de exemplo de um device."""
    return {
        "serial": "Q2XX-AAAA-BBBB",
        "name": "Switch-Core",
        "model": "MS250-48",
        "networkId": "N_12345",
        "mac": "00:11:22:33:44:55",
        "lanIp": "192.168.1.1",
        "firmware": "MS 15.21",
        "productType": "switch",
        "status": "online",
    }


@pytest.fixture
def sample_ssid_data():
    """Dados de exemplo de um SSID."""
    return {
        "number": 0,
        "name": "Corporate-WiFi",
        "enabled": True,
        "authMode": "8021x-radius",
        "encryptionMode": "wpa",
        "wpaEncryptionMode": "WPA2 only",
    }


@pytest.fixture
def sample_vlan_data():
    """Dados de exemplo de uma VLAN."""
    return {
        "id": 10,
        "name": "Data",
        "subnet": "192.168.10.0/24",
        "applianceIp": "192.168.10.1",
        "dhcpHandling": "Run a DHCP server",
    }


@pytest.fixture
def sample_discovery_result():
    """DiscoveryResult de exemplo."""
    return DiscoveryResult(
        timestamp=datetime(2024, 1, 24, 14, 30, 0),
        org_id="123456",
        org_name="ACME Corp",
        networks=[
            NetworkInfo(
                id="N_12345",
                name="Main Office",
                organization_id="123456",
                product_types=["switch", "wireless"],
            )
        ],
        devices=[
            DeviceInfo(
                serial="Q2XX-AAAA-BBBB",
                name="Switch-Core",
                model="MS250",
                network_id="N_12345",
                status="online",
            ),
            DeviceInfo(
                serial="Q2XX-CCCC-DDDD",
                name="Switch-Access",
                model="MS120",
                network_id="N_12345",
                status="offline",
            ),
        ],
        configurations={
            "N_12345": {
                "ssids": [],
                "vlans": [],
                "firewall": {"l3_rules": [], "l7_rules": []},
                "switch_acls": {},
                "switch_ports": {},
            }
        },
        issues=[],
        suggestions=[],
    )


# ==================== Tests: Dataclasses ====================


def test_network_info_from_api(sample_network_data):
    """Testa criacao de NetworkInfo a partir de dados da API."""
    network = NetworkInfo.from_api(sample_network_data)

    assert network.id == "N_12345"
    assert network.name == "Main Office"
    assert network.organization_id == "123456"
    assert "switch" in network.product_types
    assert "production" in network.tags


def test_device_info_from_api(sample_device_data):
    """Testa criacao de DeviceInfo a partir de dados da API."""
    device = DeviceInfo.from_api(sample_device_data)

    assert device.serial == "Q2XX-AAAA-BBBB"
    assert device.name == "Switch-Core"
    assert device.model == "MS250-48"
    assert device.status == "online"


def test_ssid_info_from_api(sample_ssid_data):
    """Testa criacao de SSIDInfo a partir de dados da API."""
    ssid = SSIDInfo.from_api(sample_ssid_data, "N_12345")

    assert ssid.number == 0
    assert ssid.name == "Corporate-WiFi"
    assert ssid.enabled is True
    assert ssid.auth_mode == "8021x-radius"
    assert ssid.network_id == "N_12345"


def test_vlan_info_from_api(sample_vlan_data):
    """Testa criacao de VLANInfo a partir de dados da API."""
    vlan = VLANInfo.from_api(sample_vlan_data, "N_12345")

    assert vlan.id == "10"
    assert vlan.name == "Data"
    assert vlan.subnet == "192.168.10.0/24"
    assert vlan.network_id == "N_12345"


def test_discovery_result_to_dict(sample_discovery_result):
    """Testa serializacao de DiscoveryResult para dict."""
    data = sample_discovery_result.to_dict()

    assert data["org_id"] == "123456"
    assert data["org_name"] == "ACME Corp"
    assert len(data["networks"]) == 1
    assert len(data["devices"]) == 2
    assert isinstance(data["timestamp"], str)


def test_discovery_result_from_dict(sample_discovery_result):
    """Testa desserializacao de DiscoveryResult de dict."""
    data = sample_discovery_result.to_dict()
    result = DiscoveryResult.from_dict(data)

    assert result.org_id == sample_discovery_result.org_id
    assert result.org_name == sample_discovery_result.org_name
    assert len(result.networks) == len(sample_discovery_result.networks)
    assert len(result.devices) == len(sample_discovery_result.devices)


def test_discovery_result_summary(sample_discovery_result):
    """Testa geracao de resumo."""
    summary = sample_discovery_result.summary()

    assert summary["networks_count"] == 1
    assert summary["devices_count"] == 2
    assert "online" in summary["devices_by_status"]
    assert "offline" in summary["devices_by_status"]


# ==================== Tests: Discovery Functions ====================


def test_discover_networks(mock_client):
    """Testa discovery de networks."""
    mock_client.get_networks.return_value = [
        {
            "id": "N_1",
            "name": "Network 1",
            "organizationId": "123456",
            "productTypes": ["switch"],
        },
        {
            "id": "N_2",
            "name": "Network 2",
            "organizationId": "123456",
            "productTypes": ["wireless"],
        },
    ]

    networks = discover_networks("123456", mock_client)

    assert len(networks) == 2
    assert networks[0].id == "N_1"
    assert networks[1].id == "N_2"
    mock_client.get_networks.assert_called_once_with("123456")


def test_discover_devices(mock_client):
    """Testa discovery de devices."""
    mock_client.get_network_devices.return_value = [
        {
            "serial": "Q2XX-1111-1111",
            "name": "Device 1",
            "model": "MS250",
            "networkId": "N_1",
        },
    ]

    devices = discover_devices("N_1", mock_client)

    assert len(devices) == 1
    assert devices[0].serial == "Q2XX-1111-1111"
    mock_client.get_network_devices.assert_called_once_with("N_1")


def test_discover_ssids(mock_client):
    """Testa discovery de SSIDs."""
    mock_client.safe_call.return_value = [
        {
            "number": 0,
            "name": "SSID 1",
            "enabled": True,
            "authMode": "psk",
        },
    ]

    ssids = discover_ssids("N_1", mock_client)

    assert len(ssids) == 1
    assert ssids[0].name == "SSID 1"


def test_discover_ssids_no_wireless(mock_client):
    """Testa discovery de SSIDs em network sem wireless."""
    mock_client.safe_call.return_value = []

    ssids = discover_ssids("N_1", mock_client)

    assert len(ssids) == 0


def test_discover_vlans(mock_client):
    """Testa discovery de VLANs."""
    mock_client.safe_call.return_value = [
        {
            "id": 10,
            "name": "Data VLAN",
            "subnet": "192.168.10.0/24",
        },
    ]

    vlans = discover_vlans("N_1", mock_client)

    assert len(vlans) == 1
    assert vlans[0].name == "Data VLAN"


# ==================== Tests: Issue Detection ====================


def test_find_issues_devices_offline():
    """Testa deteccao de devices offline."""
    result = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="online"
            ),
            DeviceInfo(
                serial="Q2", name="D2", model="MS120",
                network_id="N1", status="offline"
            ),
            DeviceInfo(
                serial="Q3", name="D3", model="MR44",
                network_id="N1", status="offline"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    issues = find_issues(result)

    offline_issue = next(
        (i for i in issues if i["type"] == "devices_offline"),
        None
    )

    assert offline_issue is not None
    assert offline_issue["severity"] == "high"
    assert offline_issue["count"] == 2
    assert len(offline_issue["devices"]) == 2


def test_find_issues_devices_alerting():
    """Testa deteccao de devices em alerta."""
    result = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="alerting"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    issues = find_issues(result)

    alerting_issue = next(
        (i for i in issues if i["type"] == "devices_alerting"),
        None
    )

    assert alerting_issue is not None
    assert alerting_issue["severity"] == "medium"
    assert alerting_issue["count"] == 1


def test_find_issues_insecure_ssids():
    """Testa deteccao de SSIDs sem autenticacao."""
    result = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[
            NetworkInfo(
                id="N1", name="Network 1",
                organization_id="123",
                product_types=["wireless"]
            ),
        ],
        devices=[],
        configurations={
            "N1": {
                "ssids": [
                    {
                        "number": 0,
                        "name": "Guest WiFi",
                        "enabled": True,
                        "auth_mode": "open",
                        "network_id": "N1",
                    }
                ],
                "vlans": [],
                "firewall": {},
            }
        },
        issues=[],
        suggestions=[],
    )

    issues = find_issues(result)

    ssid_issue = next(
        (i for i in issues if i["type"] == "insecure_ssids"),
        None
    )

    assert ssid_issue is not None
    assert ssid_issue["severity"] == "high"
    assert ssid_issue["count"] == 1


def test_find_issues_permissive_firewall():
    """Testa deteccao de regras de firewall permissivas."""
    result = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[
            NetworkInfo(
                id="N1", name="Network 1",
                organization_id="123",
                product_types=["appliance"]
            ),
        ],
        devices=[],
        configurations={
            "N1": {
                "firewall": {
                    "l3_rules": [
                        {
                            "policy": "allow",
                            "srcCidr": "any",
                            "destCidr": "any",
                            "comment": "Allow all",
                        }
                    ],
                }
            }
        },
        issues=[],
        suggestions=[],
    )

    issues = find_issues(result)

    fw_issue = next(
        (i for i in issues if i["type"] == "permissive_firewall_rules"),
        None
    )

    assert fw_issue is not None
    assert fw_issue["severity"] == "medium"


# ==================== Tests: Suggestions ====================


def test_generate_suggestions():
    """Testa geracao de sugestoes."""
    issues = [
        {
            "type": "devices_offline",
            "severity": "high",
            "count": 2,
        },
        {
            "type": "insecure_ssids",
            "severity": "high",
            "count": 1,
        },
    ]

    suggestions = generate_suggestions(issues)

    assert len(suggestions) == 2

    offline_suggestion = next(
        (s for s in suggestions if s["issue_type"] == "devices_offline"),
        None
    )
    assert offline_suggestion["priority"] == "high"
    assert offline_suggestion["automated"] is False

    ssid_suggestion = next(
        (s for s in suggestions if s["issue_type"] == "insecure_ssids"),
        None
    )
    assert ssid_suggestion["priority"] == "high"
    assert ssid_suggestion["automated"] is True


# ==================== Tests: Snapshots ====================


def test_save_and_load_snapshot(sample_discovery_result, tmp_path):
    """Testa salvamento e carregamento de snapshot."""
    # Usar diretorio temporario
    with patch("scripts.discovery.get_snapshot_dir") as mock_dir:
        snapshot_dir = tmp_path / "discovery"
        snapshot_dir.mkdir()
        mock_dir.return_value = snapshot_dir

        # Salvar
        path = save_snapshot(sample_discovery_result, "test-client")
        assert path.exists()

        # Carregar
        loaded = load_snapshot(path)

        assert loaded.org_id == sample_discovery_result.org_id
        assert loaded.org_name == sample_discovery_result.org_name
        assert len(loaded.networks) == len(sample_discovery_result.networks)
        assert len(loaded.devices) == len(sample_discovery_result.devices)


def test_compare_snapshots_devices_added():
    """Testa comparacao com devices adicionados."""
    old = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="online"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    new = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="online"
            ),
            DeviceInfo(
                serial="Q2", name="D2", model="MR44",
                network_id="N1", status="online"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    diff = compare_snapshots(old, new)

    assert len(diff["devices"]["added"]) == 1
    assert diff["devices"]["added"][0]["serial"] == "Q2"


def test_compare_snapshots_status_changed():
    """Testa comparacao com mudanca de status."""
    old = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="online"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    new = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="123",
        org_name="Test",
        networks=[],
        devices=[
            DeviceInfo(
                serial="Q1", name="D1", model="MS250",
                network_id="N1", status="offline"
            ),
        ],
        configurations={},
        issues=[],
        suggestions=[],
    )

    diff = compare_snapshots(old, new)

    assert len(diff["devices"]["changed_status"]) == 1
    assert diff["devices"]["changed_status"][0]["serial"] == "Q1"
    assert diff["devices"]["changed_status"][0]["old_status"] == "online"
    assert diff["devices"]["changed_status"][0]["new_status"] == "offline"


# ==================== Tests: Integration ====================


@patch("scripts.discovery.get_client")
def test_full_discovery_integration(mock_get_client):
    """Testa discovery completo (integration test)."""
    # Mock client
    mock_client = Mock()
    mock_client.org_id = "123456"

    # Mock organization
    mock_client.get_organization.return_value = {
        "id": "123456",
        "name": "Test Org",
    }

    # Mock networks
    mock_client.get_networks.return_value = [
        {
            "id": "N_1",
            "name": "Network 1",
            "organizationId": "123456",
            "productTypes": ["switch"],
        }
    ]

    # Mock devices
    mock_client.get_network_devices.return_value = [
        {
            "serial": "Q1",
            "name": "Device 1",
            "model": "MS250",
            "networkId": "N_1",
        }
    ]

    # Mock device status
    mock_client.get_device_status.return_value = [
        {"serial": "Q1", "status": "online"}
    ]

    # Mock safe_call (para SSIDs, VLANs, etc)
    mock_client.safe_call.return_value = []

    mock_get_client.return_value = mock_client

    # Execute discovery
    result = full_discovery()

    assert result.org_name == "Test Org"
    assert len(result.networks) == 1
    assert len(result.devices) == 1
    assert result.devices[0].status == "online"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
