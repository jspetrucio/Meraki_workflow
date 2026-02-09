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

    # ==================== VPN ====================

    @log_api_call
    def get_vpn_config(self, network_id: str) -> dict:
        """Retorna configuracao Site-to-Site VPN."""
        return self.dashboard.appliance.getNetworkApplianceSiteToSiteVpn(network_id)

    @log_api_call
    def update_vpn_config(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracao Site-to-Site VPN."""
        return self.dashboard.appliance.updateNetworkApplianceSiteToSiteVpn(network_id, **kwargs)

    @log_api_call
    def get_vpn_statuses(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna status VPN de todas as networks da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.appliance.getOrganizationApplianceVpnStatuses(org)

    # ==================== Content Filtering ====================

    @log_api_call
    def get_content_filtering(self, network_id: str) -> dict:
        """Retorna configuracao de Content Filtering."""
        return self.dashboard.appliance.getNetworkApplianceContentFiltering(network_id)

    @log_api_call
    def update_content_filtering(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracao de Content Filtering."""
        return self.dashboard.appliance.updateNetworkApplianceContentFiltering(network_id, **kwargs)

    @log_api_call
    def get_content_categories(self, network_id: str) -> dict:
        """Retorna categorias de conteudo disponiveis."""
        return self.dashboard.appliance.getNetworkApplianceContentFilteringCategories(network_id)

    # ==================== IPS (Intrusion Prevention) ====================

    @log_api_call
    def get_intrusion_settings(self, network_id: str) -> dict:
        """Retorna configuracoes de IPS/IDS."""
        return self.dashboard.appliance.getNetworkApplianceSecurityIntrusion(network_id)

    @log_api_call
    def update_intrusion_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes de IPS/IDS."""
        return self.dashboard.appliance.updateNetworkApplianceSecurityIntrusion(network_id, **kwargs)

    # ==================== AMP (Malware Protection) ====================

    @log_api_call
    def get_malware_settings(self, network_id: str) -> dict:
        """Retorna configuracoes de AMP/Malware Protection."""
        return self.dashboard.appliance.getNetworkApplianceSecurityMalware(network_id)

    @log_api_call
    def update_malware_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes de AMP/Malware Protection."""
        return self.dashboard.appliance.updateNetworkApplianceSecurityMalware(network_id, **kwargs)

    # ==================== Traffic Shaping ====================

    @log_api_call
    def get_traffic_shaping(self, network_id: str) -> dict:
        """Retorna regras de Traffic Shaping."""
        return self.dashboard.appliance.getNetworkApplianceTrafficShapingRules(network_id)

    @log_api_call
    def update_traffic_shaping(self, network_id: str, **kwargs) -> dict:
        """Atualiza regras de Traffic Shaping."""
        return self.dashboard.appliance.updateNetworkApplianceTrafficShapingRules(network_id, **kwargs)

    @log_api_call
    def get_uplink_bandwidth(self, network_id: str) -> dict:
        """Retorna configuracao de banda de uplink."""
        return self.dashboard.appliance.getNetworkApplianceTrafficShapingUplinkBandwidth(network_id)

    # ==================== Alerts & Webhooks ====================

    @log_api_call
    def get_alert_settings(self, network_id: str) -> dict:
        """Retorna configuracoes de alertas."""
        return self.dashboard.networks.getNetworkAlertsSettings(network_id)

    @log_api_call
    def update_alert_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes de alertas."""
        return self.dashboard.networks.updateNetworkAlertsSettings(network_id, **kwargs)

    @log_api_call
    def get_webhook_servers(self, network_id: str) -> list[dict]:
        """Retorna servidores webhook."""
        return self.dashboard.networks.getNetworkWebhooksHttpServers(network_id)

    @log_api_call
    def create_webhook_server(self, network_id: str, **kwargs) -> dict:
        """Cria servidor webhook."""
        return self.dashboard.networks.createNetworkWebhooksHttpServer(network_id, **kwargs)

    @log_api_call
    def test_webhook(self, network_id: str, url: str) -> dict:
        """Testa webhook."""
        return self.dashboard.networks.createNetworkWebhooksWebhookTest(network_id, url=url)

    # ==================== Firmware ====================

    @log_api_call
    def get_firmware_upgrades(self, network_id: str) -> dict:
        """Retorna configuracao de firmware upgrades."""
        return self.dashboard.networks.getNetworkFirmwareUpgrades(network_id)

    @log_api_call
    def update_firmware_upgrades(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracao de firmware upgrades."""
        return self.dashboard.networks.updateNetworkFirmwareUpgrades(network_id, **kwargs)

    @log_api_call
    def get_firmware_by_device(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna firmware status por device (org-level)."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationFirmwareUpgradesByDevice(org)

    # ==================== Live Tools ====================

    @log_api_call
    def create_ping(self, serial: str, target: str, count: int = 5) -> dict:
        """Cria ping test."""
        return self.dashboard.devices.createDeviceLiveToolsPing(serial, target=target, count=count)

    @log_api_call
    def get_ping_result(self, serial: str, ping_id: str) -> dict:
        """Retorna resultado de ping test."""
        return self.dashboard.devices.getDeviceLiveToolsPing(serial, ping_id)

    @log_api_call
    def create_cable_test(self, serial: str, ports: list[str]) -> dict:
        """Cria cable test."""
        return self.dashboard.devices.createDeviceLiveToolsCableTest(serial, ports=ports)

    @log_api_call
    def get_cable_test_result(self, serial: str, cable_test_id: str) -> dict:
        """Retorna resultado de cable test."""
        return self.dashboard.devices.getDeviceLiveToolsCableTest(serial, cable_test_id)

    # ==================== SNMP ====================

    @log_api_call
    def get_snmp_settings(self, network_id: str) -> dict:
        """Retorna configuracoes SNMP."""
        return self.dashboard.networks.getNetworkSnmp(network_id)

    @log_api_call
    def update_snmp_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes SNMP."""
        return self.dashboard.networks.updateNetworkSnmp(network_id, **kwargs)

    # ==================== Syslog ====================

    @log_api_call
    def get_syslog_servers(self, network_id: str) -> dict:
        """Retorna configuracoes de syslog."""
        return self.dashboard.networks.getNetworkSyslogServers(network_id)

    @log_api_call
    def update_syslog_servers(self, network_id: str, servers: list[dict]) -> dict:
        """Atualiza servidores syslog."""
        return self.dashboard.networks.updateNetworkSyslogServers(network_id, servers=servers)

    # ==================== Change Log ====================

    @log_api_call
    def get_config_changes(self, org_id: Optional[str] = None, timespan: int = 86400) -> list[dict]:
        """Retorna mudancas de configuracao (org-level)."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationConfigurationChanges(org, timespan=timespan)

    # ==================== Switch Routing (L3) ====================

    @log_api_call
    def get_switch_routing_interfaces(self, serial: str) -> list[dict]:
        """Retorna interfaces L3 de routing do switch."""
        return self.dashboard.switch.getDeviceSwitchRoutingInterfaces(serial)

    @log_api_call
    def create_routing_interface(self, serial: str, **kwargs) -> dict:
        """Cria interface L3 de routing."""
        return self.dashboard.switch.createDeviceSwitchRoutingInterface(serial, **kwargs)

    @log_api_call
    def update_routing_interface(self, serial: str, interface_id: str, **kwargs) -> dict:
        """Atualiza interface L3 de routing."""
        return self.dashboard.switch.updateDeviceSwitchRoutingInterface(serial, interface_id, **kwargs)

    @log_api_call
    def delete_routing_interface(self, serial: str, interface_id: str) -> None:
        """Remove interface L3 de routing."""
        return self.dashboard.switch.deleteDeviceSwitchRoutingInterface(serial, interface_id)

    @log_api_call
    def get_switch_static_routes(self, serial: str) -> list[dict]:
        """Retorna rotas estaticas do switch."""
        return self.dashboard.switch.getDeviceSwitchRoutingStaticRoutes(serial)

    # ==================== STP ====================

    @log_api_call
    def get_stp_settings(self, network_id: str) -> dict:
        """Retorna configuracoes STP da network."""
        return self.dashboard.switch.getNetworkSwitchStp(network_id)

    @log_api_call
    def update_stp_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes STP."""
        return self.dashboard.switch.updateNetworkSwitchStp(network_id, **kwargs)

    # ==================== Device Management ====================

    @log_api_call
    def reboot_device(self, serial: str) -> dict:
        """Reinicia um device."""
        return self.dashboard.devices.rebootDevice(serial)

    @log_api_call
    def blink_leds(self, serial: str, duration: int = 20, **kwargs) -> dict:
        """Pisca LEDs de um device para identificacao."""
        return self.dashboard.devices.blinkDeviceLeds(serial, duration=duration, **kwargs)

    # ==================== NAT & Port Forwarding ====================

    @log_api_call
    def get_1to1_nat(self, network_id: str) -> dict:
        """Retorna regras 1:1 NAT."""
        return self.dashboard.appliance.getNetworkApplianceFirewallOneToOneNatRules(network_id)

    @log_api_call
    def update_1to1_nat(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza regras 1:1 NAT."""
        return self.dashboard.appliance.updateNetworkApplianceFirewallOneToOneNatRules(network_id, rules=rules)

    @log_api_call
    def get_1tomany_nat(self, network_id: str) -> dict:
        """Retorna regras 1:Many NAT."""
        return self.dashboard.appliance.getNetworkApplianceFirewallOneToManyNatRules(network_id)

    @log_api_call
    def update_1tomany_nat(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza regras 1:Many NAT."""
        return self.dashboard.appliance.updateNetworkApplianceFirewallOneToManyNatRules(network_id, rules=rules)

    @log_api_call
    def get_port_forwarding(self, network_id: str) -> dict:
        """Retorna regras de port forwarding."""
        return self.dashboard.appliance.getNetworkApplianceFirewallPortForwardingRules(network_id)

    @log_api_call
    def update_port_forwarding(self, network_id: str, rules: list[dict]) -> dict:
        """Atualiza regras de port forwarding."""
        return self.dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules(network_id, rules=rules)

    # ==================== RF Profiles ====================

    @log_api_call
    def get_rf_profiles(self, network_id: str) -> list[dict]:
        """Retorna RF profiles da network."""
        return self.dashboard.wireless.getNetworkWirelessRfProfiles(network_id)

    @log_api_call
    def create_rf_profile(self, network_id: str, **kwargs) -> dict:
        """Cria RF profile."""
        return self.dashboard.wireless.createNetworkWirelessRfProfile(network_id, **kwargs)

    @log_api_call
    def update_rf_profile(self, network_id: str, rf_profile_id: str, **kwargs) -> dict:
        """Atualiza RF profile."""
        return self.dashboard.wireless.updateNetworkWirelessRfProfile(network_id, rf_profile_id, **kwargs)

    @log_api_call
    def delete_rf_profile(self, network_id: str, rf_profile_id: str) -> None:
        """Remove RF profile."""
        return self.dashboard.wireless.deleteNetworkWirelessRfProfile(network_id, rf_profile_id)

    # ==================== Wireless Health ====================

    @log_api_call
    def get_wireless_connection_stats(self, network_id: str, timespan: int = 3600) -> dict:
        """Retorna estatisticas de conexao wireless."""
        return self.dashboard.wireless.getNetworkWirelessConnectionStats(network_id, timespan=timespan)

    @log_api_call
    def get_wireless_latency_stats(self, network_id: str, timespan: int = 3600) -> dict:
        """Retorna estatisticas de latencia wireless."""
        return self.dashboard.wireless.getNetworkWirelessLatencyStats(network_id, timespan=timespan)

    @log_api_call
    def get_wireless_signal_quality(self, network_id: str, timespan: int = 3600) -> dict:
        """Retorna qualidade de sinal wireless."""
        return self.dashboard.wireless.getNetworkWirelessSignalQualityHistory(network_id, timespan=timespan)

    @log_api_call
    def get_channel_utilization(self, network_id: str, timespan: int = 3600) -> list[dict]:
        """Retorna utilizacao de canal wireless."""
        return self.dashboard.wireless.getNetworkWirelessChannelUtilizationHistory(network_id, timespan=timespan)

    @log_api_call
    def get_failed_connections(self, network_id: str, timespan: int = 3600) -> list[dict]:
        """Retorna conexoes wireless falhas."""
        return self.dashboard.wireless.getNetworkWirelessFailedConnections(network_id, timespan=timespan)

    # ==================== Switch QoS ====================

    @log_api_call
    def get_qos_rules(self, network_id: str) -> list[dict]:
        """Retorna regras QoS do switch."""
        return self.dashboard.switch.getNetworkSwitchQosRules(network_id)

    @log_api_call
    def create_qos_rule(self, network_id: str, **kwargs) -> dict:
        """Cria regra QoS."""
        return self.dashboard.switch.createNetworkSwitchQosRule(network_id, **kwargs)

    @log_api_call
    def update_qos_rule(self, network_id: str, qos_rule_id: str, **kwargs) -> dict:
        """Atualiza regra QoS."""
        return self.dashboard.switch.updateNetworkSwitchQosRule(network_id, qos_rule_id, **kwargs)

    @log_api_call
    def delete_qos_rule(self, network_id: str, qos_rule_id: str) -> None:
        """Remove regra QoS."""
        return self.dashboard.switch.deleteNetworkSwitchQosRule(network_id, qos_rule_id)

    # ==================== Org Admins ====================

    @log_api_call
    def get_admins(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna administradores da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationAdmins(org)

    @log_api_call
    def create_admin(self, org_id: Optional[str] = None, **kwargs) -> dict:
        """Cria administrador."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.createOrganizationAdmin(org, **kwargs)

    @log_api_call
    def update_admin(self, org_id: Optional[str] = None, admin_id: str = "", **kwargs) -> dict:
        """Atualiza administrador."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.updateOrganizationAdmin(org, admin_id, **kwargs)

    @log_api_call
    def delete_admin(self, org_id: Optional[str] = None, admin_id: str = "") -> None:
        """Remove administrador."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.deleteOrganizationAdmin(org, admin_id)

    # ==================== Inventory ====================

    @log_api_call
    def get_inventory(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna inventario completo da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationInventoryDevices(org)

    @log_api_call
    def claim_device(self, org_id: Optional[str] = None, serials: list[str] = None) -> dict:
        """Faz claim de devices na org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.claimIntoOrganizationInventory(org, serials=serials or [])

    @log_api_call
    def release_device(self, org_id: Optional[str] = None, serials: list[str] = None) -> dict:
        """Release devices da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.releaseFromOrganizationInventory(org, serials=serials or [])

    # ==================== Camera (MV) ====================

    @log_api_call
    def get_camera_quality(self, serial: str) -> dict:
        """Retorna configuracao de qualidade da camera."""
        return self.dashboard.camera.getDeviceCameraQualityAndRetention(serial)

    @log_api_call
    def update_camera_quality(self, serial: str, **kwargs) -> dict:
        """Atualiza configuracao de qualidade da camera."""
        return self.dashboard.camera.updateDeviceCameraQualityAndRetention(serial, **kwargs)

    # ==================== Clients & Traffic ====================

    @log_api_call
    def get_network_clients(self, network_id: str, timespan: int = 3600, per_page: int = 50) -> list[dict]:
        """Lista clientes conectados com uso de banda."""
        return self.dashboard.networks.getNetworkClients(
            network_id, timespan=timespan, perPage=per_page, total_pages=1
        )

    @log_api_call
    def get_network_clients_bandwidth_usage(self, network_id: str, timespan: int = 3600, per_page: int = 10) -> list[dict]:
        """Historico de uso de banda por cliente."""
        return self.dashboard.networks.getNetworkClientsBandwidthUsageHistory(
            network_id, timespan=timespan, perPage=per_page, total_pages=1
        )

    @log_api_call
    def get_network_clients_overview(self, network_id: str, timespan: int = 3600) -> dict:
        """Resumo geral dos clientes da rede."""
        return self.dashboard.networks.getNetworkClientsOverview(
            network_id, timespan=timespan
        )

    @log_api_call
    def get_network_traffic(self, network_id: str, timespan: int = 3600) -> list[dict]:
        """Analise de trafego da rede por aplicacao."""
        return self.dashboard.networks.getNetworkTraffic(
            network_id, timespan=timespan
        )

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
