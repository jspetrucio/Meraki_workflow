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

    # ==================== Policy Objects (Org-level) ====================

    @log_api_call
    def get_policy_objects(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna todos os policy objects da org."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationPolicyObjects(org)

    @log_api_call
    def create_policy_object(self, org_id: Optional[str] = None, **kwargs) -> dict:
        """Cria policy object (CIDR, FQDN, port range)."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.createOrganizationPolicyObject(org, **kwargs)

    @log_api_call
    def update_policy_object(self, org_id: Optional[str] = None, policy_object_id: str = "", **kwargs) -> dict:
        """Atualiza policy object."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.updateOrganizationPolicyObject(org, policy_object_id, **kwargs)

    @log_api_call
    def delete_policy_object(self, org_id: Optional[str] = None, policy_object_id: str = "") -> None:
        """Remove policy object."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.deleteOrganizationPolicyObject(org, policy_object_id)

    @log_api_call
    def get_policy_object_groups(self, org_id: Optional[str] = None) -> list[dict]:
        """Retorna grupos de policy objects."""
        org = org_id or self.org_id
        if not org:
            raise ValueError("org_id nao definido")
        return self.dashboard.organizations.getOrganizationPolicyObjectsGroups(org)

    # ==================== Client VPN ====================

    @log_api_call
    def get_client_vpn(self, network_id: str) -> dict:
        """Retorna configuracao Client VPN."""
        return self.dashboard.appliance.getNetworkApplianceVpn(network_id)

    @log_api_call
    def update_client_vpn(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracao Client VPN."""
        return self.dashboard.appliance.updateNetworkApplianceVpn(network_id, **kwargs)

    # ==================== Port Schedules ====================

    @log_api_call
    def get_port_schedules(self, network_id: str) -> list[dict]:
        """Retorna port schedules da network."""
        return self.dashboard.switch.getNetworkSwitchPortSchedules(network_id)

    @log_api_call
    def create_port_schedule(self, network_id: str, **kwargs) -> dict:
        """Cria port schedule."""
        return self.dashboard.switch.createNetworkSwitchPortSchedule(network_id, **kwargs)

    @log_api_call
    def update_port_schedule(self, network_id: str, port_schedule_id: str, **kwargs) -> dict:
        """Atualiza port schedule."""
        return self.dashboard.switch.updateNetworkSwitchPortSchedule(network_id, port_schedule_id, **kwargs)

    @log_api_call
    def delete_port_schedule(self, network_id: str, port_schedule_id: str) -> None:
        """Remove port schedule."""
        return self.dashboard.switch.deleteNetworkSwitchPortSchedule(network_id, port_schedule_id)

    # ==================== LLDP/CDP ====================

    @log_api_call
    def get_lldp_cdp(self, serial: str) -> dict:
        """Retorna dados LLDP/CDP de um device."""
        return self.dashboard.devices.getDeviceLldpCdp(serial)

    # ==================== NetFlow ====================

    @log_api_call
    def get_netflow_settings(self, network_id: str) -> dict:
        """Retorna configuracoes NetFlow."""
        return self.dashboard.networks.getNetworkNetflow(network_id)

    @log_api_call
    def update_netflow_settings(self, network_id: str, **kwargs) -> dict:
        """Atualiza configuracoes NetFlow."""
        return self.dashboard.networks.updateNetworkNetflow(network_id, **kwargs)

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

    # ==================== Phase 2 - Wave 2: SD-WAN / Uplink ====================

    @log_api_call
    def get_uplink_selection(self, network_id: str) -> dict:
        """Get uplink selection settings for an MX network."""
        return self.dashboard.appliance.getNetworkApplianceTrafficShapingUplinkSelection(network_id)

    @log_api_call
    def update_uplink_selection(self, network_id: str, **kwargs) -> dict:
        """Update uplink selection settings for an MX network."""
        return self.dashboard.appliance.updateNetworkApplianceTrafficShapingUplinkSelection(network_id, **kwargs)

    @log_api_call
    def get_uplink_statuses(self, org_id: str) -> list:
        """Get uplink statuses for all MX devices in an organization."""
        return self.dashboard.appliance.getOrganizationApplianceUplinkStatuses(org_id)

    @log_api_call
    def get_vpn_exclusions(self, network_id: str) -> dict:
        """Get VPN exclusions for an MX network."""
        return self.dashboard.appliance.getNetworkApplianceTrafficShapingVpnExclusions(network_id)

    # ==================== Phase 2 - Wave 2: Config Templates ====================

    @log_api_call
    def get_config_templates(self, org_id: str) -> list:
        """Get all configuration templates in an organization."""
        return self.dashboard.organizations.getOrganizationConfigTemplates(org_id)

    @log_api_call
    def create_config_template(self, org_id: str, **kwargs) -> dict:
        """Create a new configuration template."""
        return self.dashboard.organizations.createOrganizationConfigTemplate(org_id, **kwargs)

    @log_api_call
    def update_config_template(self, org_id: str, template_id: str, **kwargs) -> dict:
        """Update an existing configuration template."""
        return self.dashboard.organizations.updateOrganizationConfigTemplate(org_id, template_id, **kwargs)

    @log_api_call
    def delete_config_template(self, org_id: str, template_id: str) -> None:
        """Delete a configuration template."""
        return self.dashboard.organizations.deleteOrganizationConfigTemplate(org_id, template_id)

    @log_api_call
    def bind_network(self, network_id: str, template_id: str, **kwargs) -> dict:
        """Bind a network to a configuration template."""
        return self.dashboard.networks.bindNetwork(network_id, configTemplateId=template_id, **kwargs)

    @log_api_call
    def unbind_network(self, network_id: str) -> dict:
        """Unbind a network from its configuration template."""
        return self.dashboard.networks.unbindNetwork(network_id)

    # ==================== Phase 2 - Wave 2: 802.1X Access Policies ====================

    @log_api_call
    def get_access_policies(self, network_id: str) -> list:
        """Get 802.1X access policies for a switch network."""
        return self.dashboard.switch.getNetworkSwitchAccessPolicies(network_id)

    @log_api_call
    def create_access_policy(self, network_id: str, **kwargs) -> dict:
        """Create a new 802.1X access policy."""
        return self.dashboard.switch.createNetworkSwitchAccessPolicy(network_id, **kwargs)

    @log_api_call
    def update_access_policy(self, network_id: str, access_policy_number: str, **kwargs) -> dict:
        """Update an existing 802.1X access policy."""
        return self.dashboard.switch.updateNetworkSwitchAccessPolicy(network_id, access_policy_number, **kwargs)

    @log_api_call
    def delete_access_policy(self, network_id: str, access_policy_number: str) -> None:
        """Delete an 802.1X access policy."""
        return self.dashboard.switch.deleteNetworkSwitchAccessPolicy(network_id, access_policy_number)

    # ==================== Phase 2 - Wave 2: Air Marshal ====================

    @log_api_call
    def get_air_marshal(self, network_id: str) -> list:
        """Get Air Marshal rogue access point detection data."""
        return self.dashboard.wireless.getNetworkWirelessAirMarshal(network_id)

    # ==================== Phase 2 - Wave 2: SSID Firewall ====================

    @log_api_call
    def get_ssid_l3_firewall(self, network_id: str, number: int) -> dict:
        """Get L3 firewall rules for a specific SSID."""
        return self.dashboard.wireless.getNetworkWirelessSsidFirewallL3FirewallRules(network_id, number)

    @log_api_call
    def update_ssid_l3_firewall(self, network_id: str, number: int, **kwargs) -> dict:
        """Update L3 firewall rules for a specific SSID."""
        return self.dashboard.wireless.updateNetworkWirelessSsidFirewallL3FirewallRules(network_id, number, **kwargs)

    @log_api_call
    def get_ssid_l7_firewall(self, network_id: str, number: int) -> dict:
        """Get L7 firewall rules for a specific SSID."""
        return self.dashboard.wireless.getNetworkWirelessSsidFirewallL7FirewallRules(network_id, number)

    @log_api_call
    def update_ssid_l7_firewall(self, network_id: str, number: int, **kwargs) -> dict:
        """Update L7 firewall rules for a specific SSID."""
        return self.dashboard.wireless.updateNetworkWirelessSsidFirewallL7FirewallRules(network_id, number, **kwargs)

    # ==================== Phase 2 - Wave 2: Splash Pages ====================

    @log_api_call
    def get_splash_settings(self, network_id: str, number: int) -> dict:
        """Get splash page settings for a specific SSID."""
        return self.dashboard.wireless.getNetworkWirelessSsidSplashSettings(network_id, number)

    @log_api_call
    def update_splash_settings(self, network_id: str, number: int, **kwargs) -> dict:
        """Update splash page settings for a specific SSID."""
        return self.dashboard.wireless.updateNetworkWirelessSsidSplashSettings(network_id, number, **kwargs)

    # ===== Phase 2 - Wave 3 =====

    # Story 11.3: Adaptive Policy / SGT
    @log_api_call
    def get_adaptive_policies(self, org_id: str) -> list:
        """Get all adaptive policies for organization."""
        return self.dashboard.organizations.getOrganizationAdaptivePolicyPolicies(org_id)

    @log_api_call
    def create_adaptive_policy(self, org_id: str, **kwargs) -> dict:
        """Create adaptive policy in organization."""
        return self.dashboard.organizations.createOrganizationAdaptivePolicyPolicy(org_id, **kwargs)

    @log_api_call
    def get_adaptive_policy_acls(self, org_id: str) -> list:
        """Get all adaptive policy ACLs for organization."""
        return self.dashboard.organizations.getOrganizationAdaptivePolicyAcls(org_id)

    # Story 12.1: Switch Stacks
    @log_api_call
    def get_switch_stacks(self, network_id: str) -> list:
        """Get all switch stacks in network."""
        return self.dashboard.switch.getNetworkSwitchStacks(network_id)

    @log_api_call
    def create_switch_stack(self, network_id: str, name: str, serials: list) -> dict:
        """Create a new switch stack."""
        return self.dashboard.switch.createNetworkSwitchStack(network_id, name=name, serials=serials)

    @log_api_call
    def add_to_stack(self, network_id: str, stack_id: str, serial: str) -> dict:
        """Add a switch to an existing stack."""
        return self.dashboard.switch.addNetworkSwitchStack(network_id, stack_id, serial=serial)

    @log_api_call
    def remove_from_stack(self, network_id: str, stack_id: str, serial: str) -> dict:
        """Remove a switch from a stack."""
        return self.dashboard.switch.removeNetworkSwitchStack(network_id, stack_id, serial=serial)

    @log_api_call
    def get_stack_routing(self, network_id: str, stack_id: str) -> list:
        """Get routing interfaces for a switch stack."""
        return self.dashboard.switch.getNetworkSwitchStackRoutingInterfaces(network_id, stack_id)

    # Story 12.4: HA / Warm Spare
    @log_api_call
    def get_warm_spare(self, network_id: str) -> dict:
        """Get warm spare configuration for network."""
        return self.dashboard.appliance.getNetworkApplianceWarmSpare(network_id)

    @log_api_call
    def update_warm_spare(self, network_id: str, enabled: bool, spare_serial: str = None,
                          uplink_mode: str = None, virtual_ip1: str = None, virtual_ip2: str = None) -> dict:
        """Update warm spare configuration."""
        kwargs = {"enabled": enabled}
        if spare_serial is not None:
            kwargs["spareSerial"] = spare_serial
        if uplink_mode is not None:
            kwargs["uplinkMode"] = uplink_mode
        if virtual_ip1 is not None:
            kwargs["virtualIp1"] = virtual_ip1
        if virtual_ip2 is not None:
            kwargs["virtualIp2"] = virtual_ip2
        return self.dashboard.appliance.updateNetworkApplianceWarmSpare(network_id, **kwargs)

    @log_api_call
    def swap_warm_spare(self, network_id: str) -> dict:
        """Swap primary and warm spare appliances."""
        return self.dashboard.appliance.swapNetworkApplianceWarmSpare(network_id)

    # Story 13.1: Camera Analytics & Snapshots
    @log_api_call
    def get_camera_analytics_overview(self, serial: str) -> dict:
        """Get analytics overview for a camera."""
        return self.dashboard.camera.getDeviceCameraAnalyticsOverview(serial)

    @log_api_call
    def get_camera_analytics_zones(self, serial: str) -> list:
        """Get analytics zones configured on a camera."""
        return self.dashboard.camera.getDeviceCameraAnalyticsZones(serial)

    @log_api_call
    def get_camera_analytics_history(self, serial: str, zone_id: str) -> list:
        """Get analytics history for a specific zone."""
        return self.dashboard.camera.getDeviceCameraAnalyticsZoneHistory(serial, zoneId=zone_id)

    @log_api_call
    def generate_snapshot(self, serial: str, timestamp: str = None) -> dict:
        """Generate a snapshot from a camera."""
        if timestamp:
            return self.dashboard.camera.generateDeviceCameraSnapshot(serial, timestamp=timestamp)
        return self.dashboard.camera.generateDeviceCameraSnapshot(serial)

    @log_api_call
    def get_video_link(self, serial: str, timestamp: str = None) -> dict:
        """Get video link for camera footage."""
        if timestamp:
            return self.dashboard.camera.getDeviceCameraVideoLink(serial, timestamp=timestamp)
        return self.dashboard.camera.getDeviceCameraVideoLink(serial)

    # Story 13.2: Sensor Readings & Alerts
    @log_api_call
    def get_sensor_readings_latest(self, org_id: str, serials: list = None) -> list:
        """Get latest sensor readings for organization."""
        return self.dashboard.sensor.getOrganizationSensorReadingsLatest(org_id, serials=serials)

    @log_api_call
    def get_sensor_readings_history(self, org_id: str, serials: list = None, t0: str = None, t1: str = None) -> list:
        """Get historical sensor readings."""
        kwargs = {}
        if serials:
            kwargs["serials"] = serials
        if t0:
            kwargs["t0"] = t0
        if t1:
            kwargs["t1"] = t1
        return self.dashboard.sensor.getOrganizationSensorReadingsHistory(org_id, **kwargs)

    @log_api_call
    def get_sensor_alert_profiles(self, network_id: str) -> list:
        """Get sensor alert profiles for network."""
        return self.dashboard.sensor.getNetworkSensorAlertsProfiles(network_id)

    @log_api_call
    def create_sensor_alert(self, network_id: str, name: str, conditions: list, recipients: list = None) -> dict:
        """Create sensor alert profile."""
        kwargs = {"name": name, "conditions": conditions}
        if recipients:
            kwargs["recipients"] = recipients
        return self.dashboard.sensor.createNetworkSensorAlertsProfile(network_id, **kwargs)

    # ===== Phase 2 - Wave 4 =====

    @log_api_call
    def get_floor_plans(self, network_id: str) -> list:
        """Get all floor plans for a network."""
        return self.dashboard.networks.getNetworkFloorPlans(network_id)

    @log_api_call
    def create_floor_plan(self, network_id: str, name: str, **kwargs) -> dict:
        """Create a new floor plan."""
        return self.dashboard.networks.createNetworkFloorPlan(
            network_id, name=name, **kwargs
        )

    @log_api_call
    def update_floor_plan(self, network_id: str, floor_plan_id: str, **kwargs) -> dict:
        """Update an existing floor plan."""
        return self.dashboard.networks.updateNetworkFloorPlan(
            network_id, floor_plan_id, **kwargs
        )

    @log_api_call
    def delete_floor_plan(self, network_id: str, floor_plan_id: str) -> dict:
        """Delete a floor plan."""
        return self.dashboard.networks.deleteNetworkFloorPlan(
            network_id, floor_plan_id
        )

    @log_api_call
    def get_group_policies(self, network_id: str) -> list:
        """Get all group policies for a network."""
        return self.dashboard.networks.getNetworkGroupPolicies(network_id)

    @log_api_call
    def create_group_policy(self, network_id: str, name: str, **kwargs) -> dict:
        """Create a new group policy."""
        return self.dashboard.networks.createNetworkGroupPolicy(
            network_id, name=name, **kwargs
        )

    @log_api_call
    def update_group_policy(self, network_id: str, group_policy_id: str, **kwargs) -> dict:
        """Update an existing group policy."""
        return self.dashboard.networks.updateNetworkGroupPolicy(
            network_id, group_policy_id, **kwargs
        )

    @log_api_call
    def delete_group_policy(self, network_id: str, group_policy_id: str) -> dict:
        """Delete a group policy."""
        return self.dashboard.networks.deleteNetworkGroupPolicy(
            network_id, group_policy_id
        )

    @log_api_call
    def create_packet_capture(self, device_serial: str, **kwargs) -> dict:
        """Initiate a packet capture on a device."""
        return self.dashboard.devices.createDeviceLiveToolsPcap(
            device_serial, **kwargs
        )

    @log_api_call
    def get_packet_capture_status(self, device_serial: str, capture_id: str) -> dict:
        """Get status of a packet capture."""
        return self.dashboard.devices.getDeviceLiveToolsPcap(
            device_serial, capture_id
        )

    @log_api_call
    def get_static_routes(self, network_id: str) -> list:
        """Get all static routes for an appliance network."""
        return self.dashboard.appliance.getNetworkApplianceStaticRoutes(network_id)

    @log_api_call
    def create_static_route(
        self, network_id: str, subnet: str, gateway_ip: str, name: str = None
    ) -> dict:
        """Create a new static route."""
        return self.dashboard.appliance.createNetworkApplianceStaticRoute(
            network_id, subnet=subnet, gatewayIp=gateway_ip, name=name
        )

    @log_api_call
    def update_static_route(self, network_id: str, route_id: str, **kwargs) -> dict:
        """Update an existing static route."""
        return self.dashboard.appliance.updateNetworkApplianceStaticRoute(
            network_id, route_id, **kwargs
        )

    @log_api_call
    def delete_static_route(self, network_id: str, route_id: str) -> dict:
        """Delete a static route."""
        return self.dashboard.appliance.deleteNetworkApplianceStaticRoute(
            network_id, route_id
        )


# ==================== Product Type Helpers ====================

_network_product_cache: dict[str, list[str]] = {}


def get_network_product_types(network_id: str, client: "MerakiClient") -> list[str] | None:
    """Return the product types for a network, with caching.

    Returns None when the product types cannot be determined (e.g. mock
    client in tests, API error).  Callers should treat None as "unknown –
    proceed normally".
    """
    if network_id in _network_product_cache:
        return _network_product_cache[network_id]

    try:
        network = client.get_network(network_id)
        # MagicMock / non-dict → cannot determine
        if not isinstance(network, dict):
            return None
        product_types = network.get("productTypes")
        if not isinstance(product_types, list):
            return None  # key missing or wrong type → unknown
        _network_product_cache[network_id] = product_types
        return product_types
    except Exception:
        return None


def network_has_product(network_id: str, required_type: str, client: "MerakiClient") -> bool | None:
    """Check whether *network_id* includes *required_type* hardware.

    Returns:
        True  – network has the required hardware
        False – network definitely lacks the required hardware
        None  – cannot determine (mock client, API error) → caller should proceed
    """
    types = get_network_product_types(network_id, client)
    if types is None:
        return None
    return required_type in types


def clear_product_type_cache() -> None:
    """Clear the network product-type cache (for tests)."""
    _network_product_cache.clear()


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
