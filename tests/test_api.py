"""
Testes para scripts/api.py
"""

import pytest
from unittest.mock import patch, MagicMock

from scripts.api import MerakiClient, get_client


class TestMerakiClient:
    """Testes para a classe MerakiClient."""

    def test_client_initialization(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste inicializacao do cliente."""
        client = MerakiClient()

        assert client.profile is not None
        assert client.dashboard is not None

    def test_client_repr(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste representacao string do cliente."""
        client = MerakiClient()

        repr_str = repr(client)
        assert "MerakiClient" in repr_str

    def test_get_organizations(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de organizacoes."""
        client = MerakiClient()
        orgs = client.get_organizations()

        assert len(orgs) == 2
        assert orgs[0]["name"] == "Test Org 1"

    def test_get_networks(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de networks."""
        client = MerakiClient()
        # Precisa de org_id
        client.org_id = "123456"

        networks = client.get_networks()

        assert len(networks) == 2
        assert networks[0]["name"] == "Network 1"

    def test_get_networks_without_org_id_raises(self, mock_meraki_dashboard, mock_env_credentials, monkeypatch):
        """Teste que get_networks sem org_id levanta erro."""
        monkeypatch.delenv("MERAKI_ORG_ID", raising=False)

        client = MerakiClient()
        client.org_id = None

        with pytest.raises(ValueError, match="org_id"):
            client.get_networks()

    def test_get_network_devices(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de devices de uma network."""
        client = MerakiClient()

        devices = client.get_network_devices("N_123")

        assert len(devices) == 2
        assert devices[0]["serial"] == "Q2AB-1234-5678"

    def test_get_device(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste busca de device por serial."""
        client = MerakiClient()

        device = client.get_device("Q2AB-1234-5678")

        assert device["serial"] == "Q2AB-1234-5678"
        assert device["model"] == "MS120-8"

    def test_get_switch_ports(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de portas de switch."""
        client = MerakiClient()

        ports = client.get_switch_ports("Q2AB-1234-5678")

        assert len(ports) == 2
        assert ports[0]["portId"] == "1"

    def test_get_ssids(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de SSIDs."""
        client = MerakiClient()

        ssids = client.get_ssids("N_123")

        assert len(ssids) == 2
        assert ssids[0]["name"] == "Corp WiFi"

    def test_get_l3_firewall_rules(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste busca de regras L3 firewall."""
        client = MerakiClient()

        rules = client.get_l3_firewall_rules("N_123")

        assert "rules" in rules

    def test_get_vlans(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste listagem de VLANs."""
        client = MerakiClient()

        vlans = client.get_vlans("N_123")

        assert len(vlans) == 1
        assert vlans[0]["name"] == "Default"


class TestMerakiClientHelpers:
    """Testes para metodos helper do cliente."""

    def test_get_network_by_name_found(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste busca de network por nome."""
        client = MerakiClient()
        client.org_id = "123456"

        network = client.get_network_by_name("Network 1")

        assert network is not None
        assert network["id"] == "N_123"

    def test_get_network_by_name_not_found(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste busca de network inexistente."""
        client = MerakiClient()
        client.org_id = "123456"

        network = client.get_network_by_name("Nao Existe")

        assert network is None

    def test_get_network_by_name_case_insensitive(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste busca case-insensitive."""
        client = MerakiClient()
        client.org_id = "123456"

        network = client.get_network_by_name("NETWORK 1")

        assert network is not None
        assert network["id"] == "N_123"

    def test_safe_call_returns_default_on_404(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste safe_call retorna default em 404."""
        from meraki.exceptions import APIError

        client = MerakiClient()

        # Simular 404
        def raise_404():
            raise APIError(MagicMock(), MagicMock(status_code=404))

        result = client.safe_call(raise_404, default=[])

        assert result == []

    def test_safe_call_returns_default_on_400(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste safe_call retorna default em 400 (feature nao suportada)."""
        from meraki.exceptions import APIError

        client = MerakiClient()

        # Simular 400
        def raise_400():
            raise APIError(MagicMock(), MagicMock(status_code=400))

        result = client.safe_call(raise_400, default=None)

        assert result is None


class TestGetClient:
    """Testes para a funcao get_client (singleton)."""

    def test_get_client_returns_singleton(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste que get_client retorna mesma instancia."""
        # Reset singleton
        import scripts.api
        scripts.api._client_instance = None

        client1 = get_client()
        client2 = get_client()

        assert client1 is client2

    def test_get_client_force_new(self, mock_meraki_dashboard, mock_env_credentials):
        """Teste criacao de nova instancia com force_new."""
        # Reset singleton
        import scripts.api
        scripts.api._client_instance = None

        client1 = get_client()
        client2 = get_client(force_new=True)

        assert client1 is not client2
