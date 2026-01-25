"""
Wrapper da Meraki Dashboard API.

Fornece uma interface simplificada para interacao com a API Meraki,
com tratamento de rate limiting, retry automatico e logging.

Uso:
    from scripts.api import MerakiClient

    client = MerakiClient()  # usa profile default
    client = MerakiClient(profile="cliente-acme")

    networks = client.get_networks()
    devices = client.get_devices(network_id)
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

import meraki
from meraki.exceptions import APIError

from .auth import MerakiProfile, load_profile

logger = logging.getLogger(__name__)


# Singleton instance
_client_instance: Optional["MerakiClient"] = None


def get_client(profile: str = "default", force_new: bool = False) -> "MerakiClient":
    """
    Retorna instancia singleton do MerakiClient.

    Args:
        profile: Nome do profile a usar
        force_new: Se True, cria nova instancia

    Returns:
        MerakiClient
    """
    global _client_instance

    if _client_instance is None or force_new:
        _client_instance = MerakiClient(profile=profile)

    return _client_instance


def log_api_call(func: Callable) -> Callable:
    """Decorator para logging de chamadas API."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func_name = func.__name__

        logger.debug(f"API call: {func_name}")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"API call {func_name} completed in {elapsed:.2f}s")
            return result

        except APIError as e:
            elapsed = time.time() - start
            logger.error(f"API error in {func_name} after {elapsed:.2f}s: {e}")
            raise

    return wrapper


class MerakiClient:
    """
    Cliente wrapper para Meraki Dashboard API.

    Fornece:
    - Rate limit handling automatico
    - Retry em erros transientes
    - Logging estruturado
    - Interface simplificada

    Attributes:
        profile: MerakiProfile usado
        dashboard: Instancia do DashboardAPI
        org_id: ID da organizacao (se definido no profile)
    """

    def __init__(self, profile: str = "default"):
        """
        Inicializa o cliente Meraki.

        Args:
            profile: Nome do profile de credenciais a usar
        """
        self.profile = load_profile(profile)
        self.dashboard = meraki.DashboardAPI(
            self.profile.api_key,
            output_log=False,
            suppress_logging=True,
            wait_on_rate_limit=True,  # Auto-retry on 429
            retry_4xx_error=True,
            retry_4xx_error_wait_time=2,
            maximum_retries=3
        )
        self.org_id = self.profile.org_id
        logger.info(f"MerakiClient inicializado com profile '{self.profile.name}'")

    def __repr__(self) -> str:
        return f"MerakiClient(profile='{self.profile.name}', org_id='{self.org_id}')"

    # ==================== Organizations ====================

    @log_api_call
    def get_organizations(self) -> list[dict]:
        """Lista todas as organizacoes acessiveis."""
        return self.dashboard.organizations.getOrganizations()

    @log_api_call
    def get_organization(self, org_id: Optional[str] = None) -> dict:
        """Retorna detalhes de uma organizacao."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganization(org)

    # ==================== Networks ====================

    @log_api_call
    def get_networks(self, org_id: Optional[str] = None) -> list[dict]:
        """Lista todas as networks da organizacao."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationNetworks(org)

    @log_api_call
    def get_network(self, network_id: str) -> dict:
        """Retorna detalhes de uma network."""
        return self.dashboard.networks.getNetwork(network_id)

    @log_api_call
    def get_network_devices(self, network_id: str) -> list[dict]:
        """Lista devices de uma network."""
        return self.dashboard.networks.getNetworkDevices(network_id)

    # ==================== Devices ====================

    @log_api_call
    def get_device(self, serial: str) -> dict:
        """Retorna detalhes de um device por serial."""
        return self.dashboard.devices.getDevice(serial)

    @log_api_call
    def get_device_status(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna status de todos os devices da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationDevicesStatuses(org)

    # ==================== Switch ====================

    @log_api_call
    def get_switch_ports(self, serial: str) -> list[dict]:
        """Lista portas de um switch."""
        return self.dashboard.switch.getDeviceSwitchPorts(serial)

    @log_api_call
    def update_switch_port(self, serial: str, port_id: str, **kwargs) -> dict:
        """Atualiza configuracao de uma porta de switch."""
        return self.dashboard.switch.updateDeviceSwitchPort(serial, port_id, **kwargs)

    @log_api_call
    def get_switch_acls(self, network_id: str) -> dict:
        """Retorna ACLs de switch da network."""
        return self.dashboard.switch.getNetworkSwitchAccessControlLists(network_id)

    @log_api_call
    def update_switch_acls(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza ACLs de switch."""
        return self.dashboard.switch.updateNetworkSwitchAccessControlLists(
            network_id, rules=rules
        )

    # ==================== Wireless ====================

    @log_api_call
    def get_ssids(self, network_id: str) -> list[dict]:
        """Lista SSIDs de uma network wireless."""
        return self.dashboard.wireless.getNetworkWirelessSsids(network_id)

    @log_api_call
    def get_ssid(self, network_id: str, number: int) -> dict:
        """Retorna detalhes de um SSID."""
        return self.dashboard.wireless.getNetworkWirelessSsid(network_id, number)

    @log_api_call
    def update_ssid(self, network_id: str, number: int, **kwargs) -> dict:
        """Atualiza configuracao de um SSID."""
        return self.dashboard.wireless.updateNetworkWirelessSsid(
            network_id, number, **kwargs
        )

    @log_api_call
    def enable_ssid(self, network_id: str, number: int, name: str) -> dict:
        """Habilita um SSID com nome especificado."""
        return self.update_ssid(network_id, number, enabled=True, name=name)

    @log_api_call
    def disable_ssid(self, network_id: str, number: int) -> dict:
        """Desabilita um SSID."""
        return self.update_ssid(network_id, number, enabled=False)

    # ==================== Appliance (MX Firewall) ====================

    @log_api_call
    def get_l3_firewall_rules(self, network_id: str) -> dict:
        """Retorna regras L3 firewall."""
        return self.dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(
            network_id
        )

    @log_api_call
    def update_l3_firewall_rules(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza regras L3 firewall."""
        return self.dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
            network_id, rules=rules
        )

    @log_api_call
    def get_l7_firewall_rules(self, network_id: str) -> dict:
        """Retorna regras L7 firewall."""
        return self.dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
            network_id
        )

    @log_api_call
    def update_l7_firewall_rules(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza regras L7 firewall."""
        return self.dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(
            network_id, rules=rules
        )

    # ==================== VLANs ====================

    @log_api_call
    def get_vlans(self, network_id: str) -> list[dict]:
        """Lista VLANs de uma network."""
        return self.dashboard.appliance.getNetworkApplianceVlans(network_id)

    @log_api_call
    def get_vlan(self, network_id: str, vlan_id: str) -> dict:
        """Retorna detalhes de uma VLAN."""
        return self.dashboard.appliance.getNetworkApplianceVlan(network_id, vlan_id)

    @log_api_call
    def create_vlan(self, network_id: str, vlan_id: int, name: str, subnet: str, appliance_ip: str) -> dict:
        """Cria uma nova VLAN."""
        return self.dashboard.appliance.createNetworkApplianceVlan(
            network_id,
            id=vlan_id,
            name=name,
            subnet=subnet,
            applianceIp=appliance_ip
        )

    @log_api_call
    def update_vlan(self, network_id: str, vlan_id: str, **kwargs) -> dict:
        """Atualiza uma VLAN."""
        return self.dashboard.appliance.updateNetworkApplianceVlan(
            network_id, vlan_id, **kwargs
        )

    @log_api_call
    def delete_vlan(self, network_id: str, vlan_id: str) -> None:
        """Remove uma VLAN."""
        return self.dashboard.appliance.deleteNetworkApplianceVlan(network_id, vlan_id)

    # ==================== Camera (MV) ====================

    @log_api_call
    def get_camera_quality(self, serial: str) -> dict:
        """Retorna configuracao de qualidade da camera."""
        return self.dashboard.camera.getDeviceCameraQualityAndRetention(serial)

    @log_api_call
    def update_camera_quality(self, serial: str, **kwargs) -> dict:
        """Atualiza configuracao de qualidade da camera."""
        return self.dashboard.camera.updateDeviceCameraQualityAndRetention(serial, **kwargs)

    # ==================== Helpers ====================

    def get_network_by_name(self, name: str, org_id: Optional[str] = None) -> Optional[dict]:
        """Busca network por nome (case-insensitive)."""
        networks = self.get_networks(org_id)
        name_lower = name.lower()

        for network in networks:
            if network.get("name", "").lower() == name_lower:
                return network

        return None

    def get_device_by_name(self, name: str, network_id: str) -> Optional[dict]:
        """Busca device por nome em uma network."""
        devices = self.get_network_devices(network_id)
        name_lower = name.lower()

        for device in devices:
            if device.get("name", "").lower() == name_lower:
                return device

        return None

    def safe_call(self, func: Callable, *args, default: Any = None, **kwargs) -> Any:
        """
        Executa chamada API com tratamento de erro.

        Retorna default em caso de erro (util para discovery
        onde alguns endpoints podem nao existir).
        """
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.status == 400:
                # Feature nao suportada nesta network
                logger.debug(f"Feature nao suportada: {e}")
                return default
            elif e.status == 404:
                # Recurso nao encontrado
                logger.debug(f"Recurso nao encontrado: {e}")
                return default
            else:
                raise


if __name__ == "__main__":
    # Teste rapido
    import sys

    logging.basicConfig(level=logging.DEBUG)

    try:
        client = MerakiClient()
        print(f"Cliente: {client}")

        orgs = client.get_organizations()
        print(f"Organizacoes: {len(orgs)}")

        for org in orgs:
            print(f"  - {org['name']} ({org['id']})")

    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
