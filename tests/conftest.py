"""
Fixtures e configuracoes globais de teste.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_credentials_file(tmp_path):
    """Cria arquivo de credenciais temporario para testes."""
    creds_dir = tmp_path / ".meraki"
    creds_dir.mkdir()
    creds_file = creds_dir / "credentials"

    creds_file.write_text("""
[default]
api_key = test_default_api_key_12345678901234567890
org_id = 123456

[cliente-acme]
api_key = test_acme_api_key_12345678901234567890123
org_id = 789012
""")

    return creds_file


@pytest.fixture
def mock_env_credentials(monkeypatch):
    """Configura credenciais via variaveis de ambiente."""
    monkeypatch.setenv("MERAKI_API_KEY", "env_api_key_12345678901234567890123456")
    monkeypatch.setenv("MERAKI_ORG_ID", "env_org_123")
    monkeypatch.setenv("MERAKI_PROFILE", "env-profile")


@pytest.fixture
def mock_meraki_dashboard():
    """Mock do Meraki Dashboard API."""
    with patch("meraki.DashboardAPI") as mock:
        dashboard = MagicMock()

        # Mock organizations
        dashboard.organizations.getOrganizations.return_value = [
            {"id": "123456", "name": "Test Org 1"},
            {"id": "789012", "name": "Test Org 2"}
        ]
        dashboard.organizations.getOrganization.return_value = {
            "id": "123456",
            "name": "Test Org 1"
        }
        dashboard.organizations.getOrganizationNetworks.return_value = [
            {"id": "N_123", "name": "Network 1", "productTypes": ["switch"]},
            {"id": "N_456", "name": "Network 2", "productTypes": ["wireless"]}
        ]
        dashboard.organizations.getOrganizationDevicesStatuses.return_value = [
            {"serial": "Q2AB-1234-5678", "status": "online"},
            {"serial": "Q2AB-9012-3456", "status": "offline"}
        ]

        # Mock networks
        dashboard.networks.getNetwork.return_value = {
            "id": "N_123",
            "name": "Network 1"
        }
        dashboard.networks.getNetworkDevices.return_value = [
            {"serial": "Q2AB-1234-5678", "name": "Switch 1", "model": "MS120-8"},
            {"serial": "Q2AB-9012-3456", "name": "AP 1", "model": "MR33"}
        ]

        # Mock devices
        dashboard.devices.getDevice.return_value = {
            "serial": "Q2AB-1234-5678",
            "name": "Switch 1",
            "model": "MS120-8"
        }

        # Mock switch
        dashboard.switch.getDeviceSwitchPorts.return_value = [
            {"portId": "1", "name": "Port 1", "vlan": 1},
            {"portId": "2", "name": "Port 2", "vlan": 10}
        ]
        dashboard.switch.getNetworkSwitchAccessControlLists.return_value = {
            "rules": []
        }

        # Mock wireless
        dashboard.wireless.getNetworkWirelessSsids.return_value = [
            {"number": 0, "name": "Corp WiFi", "enabled": True},
            {"number": 1, "name": "Guest WiFi", "enabled": True}
        ]

        # Mock appliance
        dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules.return_value = {
            "rules": []
        }
        dashboard.appliance.getNetworkApplianceVlans.return_value = [
            {"id": "1", "name": "Default", "subnet": "192.168.1.0/24"}
        ]

        mock.return_value = dashboard
        yield mock


@pytest.fixture
def sample_network():
    """Network de exemplo para testes."""
    return {
        "id": "N_123456",
        "name": "Test Network",
        "organizationId": "123456",
        "productTypes": ["switch", "wireless"],
        "timeZone": "America/Sao_Paulo"
    }


@pytest.fixture
def sample_device():
    """Device de exemplo para testes."""
    return {
        "serial": "Q2AB-1234-5678",
        "name": "Core Switch",
        "model": "MS250-48",
        "networkId": "N_123456",
        "mac": "00:11:22:33:44:55",
        "lanIp": "192.168.1.1"
    }
