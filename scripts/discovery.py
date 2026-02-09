"""
Discovery e analise de redes Meraki.

Este modulo realiza:
- Discovery completo de networks, devices, SSIDs, VLANs, firewall rules
- Identificacao de problemas (devices offline, SSIDs inseguros, etc)
- Geracao de sugestoes para melhorias
- Salvamento e comparacao de snapshots

Uso:
    from scripts.discovery import full_discovery, save_snapshot

    # Discovery completo
    result = full_discovery(org_id="123456")

    # Ver problemas encontrados
    for issue in result.issues:
        print(f"{issue['severity']}: {issue['type']}")

    # Salvar snapshot
    save_snapshot(result, "cliente-acme")
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from meraki.exceptions import APIError

from .api import MerakiClient, get_client

logger = logging.getLogger(__name__)


# ==================== Dataclasses ====================


@dataclass
class NetworkInfo:
    """Informacoes de uma network Meraki."""

    id: str
    name: str
    organization_id: str
    product_types: list[str]
    tags: list[str] = field(default_factory=list)
    time_zone: Optional[str] = None
    enrollment_string: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "NetworkInfo":
        """Cria NetworkInfo a partir de resposta da API."""
        return cls(
            id=data["id"],
            name=data["name"],
            organization_id=data["organizationId"],
            product_types=data.get("productTypes", []),
            tags=data.get("tags", []),
            time_zone=data.get("timeZone"),
            enrollment_string=data.get("enrollmentString"),
            url=data.get("url"),
            notes=data.get("notes"),
        )


@dataclass
class DeviceInfo:
    """Informacoes de um device Meraki."""

    serial: str
    name: Optional[str]
    model: str
    network_id: str
    mac: Optional[str] = None
    lan_ip: Optional[str] = None
    firmware: Optional[str] = None
    product_type: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    status: Optional[str] = None  # online, offline, dormant, alerting
    public_ip: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    @classmethod
    def from_api(cls, data: dict) -> "DeviceInfo":
        """Cria DeviceInfo a partir de resposta da API."""
        return cls(
            serial=data["serial"],
            name=data.get("name"),
            model=data["model"],
            network_id=data["networkId"],
            mac=data.get("mac"),
            lan_ip=data.get("lanIp"),
            firmware=data.get("firmware"),
            product_type=data.get("productType"),
            tags=data.get("tags", []),
            status=data.get("status"),
            public_ip=data.get("publicIp"),
            lat=data.get("lat"),
            lng=data.get("lng"),
        )


@dataclass
class SSIDInfo:
    """Informacoes de um SSID wireless."""

    number: int
    name: str
    enabled: bool
    network_id: str
    auth_mode: Optional[str] = None
    encryption_mode: Optional[str] = None
    wpa_encryption_mode: Optional[str] = None
    splash_page: Optional[str] = None
    radius_servers: list[dict] = field(default_factory=list)
    visible: bool = True
    available_on_all_aps: bool = True
    bands_steering_enabled: bool = False

    @classmethod
    def from_api(cls, data: dict, network_id: str) -> "SSIDInfo":
        """Cria SSIDInfo a partir de resposta da API."""
        return cls(
            number=data["number"],
            name=data["name"],
            enabled=data.get("enabled", False),
            network_id=network_id,
            auth_mode=data.get("authMode"),
            encryption_mode=data.get("encryptionMode"),
            wpa_encryption_mode=data.get("wpaEncryptionMode"),
            splash_page=data.get("splashPage"),
            radius_servers=data.get("radiusServers", []),
            visible=data.get("visible", True),
            available_on_all_aps=data.get("availableOnAllAps", True),
            bands_steering_enabled=data.get("bandSelection") == "Dual band operation with Band Steering",
        )


@dataclass
class VLANInfo:
    """Informacoes de uma VLAN."""

    id: str
    name: str
    network_id: str
    subnet: Optional[str] = None
    appliance_ip: Optional[str] = None
    dhcp_handling: Optional[str] = None
    dhcp_lease_time: Optional[str] = None
    dhcp_boot_options_enabled: bool = False
    reserved_ip_ranges: list[dict] = field(default_factory=list)
    dns_nameservers: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict, network_id: str) -> "VLANInfo":
        """Cria VLANInfo a partir de resposta da API."""
        return cls(
            id=str(data["id"]),
            name=data["name"],
            network_id=network_id,
            subnet=data.get("subnet"),
            appliance_ip=data.get("applianceIp"),
            dhcp_handling=data.get("dhcpHandling"),
            dhcp_lease_time=data.get("dhcpLeaseTime"),
            dhcp_boot_options_enabled=data.get("dhcpBootOptionsEnabled", False),
            reserved_ip_ranges=data.get("reservedIpRanges", []),
            dns_nameservers=data.get("dnsNameservers"),
        )


@dataclass
class DiscoveryResult:
    """
    Resultado completo de discovery de uma organizacao.

    Attributes:
        timestamp: Quando o discovery foi realizado
        org_id: ID da organizacao
        org_name: Nome da organizacao
        networks: Lista de networks encontradas
        devices: Lista de devices encontrados
        configurations: Configuracoes por network_id
        issues: Problemas identificados
        suggestions: Sugestoes de melhorias
    """

    timestamp: datetime
    org_id: str
    org_name: str
    networks: list[NetworkInfo]
    devices: list[DeviceInfo]
    configurations: dict[str, dict]  # network_id -> {vlans, ssids, firewall, etc}
    issues: list[dict]
    suggestions: list[dict]

    def to_dict(self) -> dict:
        """Converte para dicionario (para serializar em JSON)."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "org_id": self.org_id,
            "org_name": self.org_name,
            "networks": [asdict(n) for n in self.networks],
            "devices": [asdict(d) for d in self.devices],
            "configurations": self.configurations,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiscoveryResult":
        """Cria DiscoveryResult a partir de dicionario."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            org_id=data["org_id"],
            org_name=data["org_name"],
            networks=[NetworkInfo(**n) for n in data["networks"]],
            devices=[DeviceInfo(**d) for d in data["devices"]],
            configurations=data["configurations"],
            issues=data["issues"],
            suggestions=data["suggestions"],
        )

    def summary(self) -> dict:
        """Retorna resumo do discovery."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "organization": f"{self.org_name} ({self.org_id})",
            "networks_count": len(self.networks),
            "devices_count": len(self.devices),
            "devices_by_status": self._count_devices_by_status(),
            "issues_count": len(self.issues),
            "issues_by_severity": self._count_issues_by_severity(),
        }

    def _count_devices_by_status(self) -> dict[str, int]:
        """Conta devices por status."""
        counts: dict[str, int] = {}
        for device in self.devices:
            status = device.status or "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _count_issues_by_severity(self) -> dict[str, int]:
        """Conta issues por severidade."""
        counts: dict[str, int] = {}
        for issue in self.issues:
            severity = issue.get("severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts


# ==================== Discovery Functions ====================


def discover_networks(org_id: str, client: MerakiClient) -> list[NetworkInfo]:
    """
    Descobre todas as networks de uma organizacao.

    Args:
        org_id: ID da organizacao
        client: Cliente Meraki autenticado

    Returns:
        Lista de NetworkInfo
    """
    logger.info(f"Descobrindo networks da org {org_id}")

    # Meraki API can return transient 404s — retry with backoff
    last_error = None
    for attempt in range(3):
        try:
            networks_raw = client.get_networks(org_id)
            networks = [NetworkInfo.from_api(net) for net in networks_raw]
            logger.info(f"Encontradas {len(networks)} networks")
            return networks
        except APIError as e:
            last_error = e
            if e.status == 404 and attempt < 2:
                import time
                wait = 2 ** attempt  # 1s, 2s
                logger.warning(f"Transient 404 on discover_networks (attempt {attempt + 1}/3), retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Erro ao descobrir networks: {e}")
                raise

    raise last_error


def discover_devices(network_id: str, client: MerakiClient) -> list[DeviceInfo]:
    """
    Descobre todos os devices de uma network.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado

    Returns:
        Lista de DeviceInfo
    """
    logger.debug(f"Descobrindo devices da network {network_id}")

    try:
        devices_raw = client.get_network_devices(network_id)
        devices = [DeviceInfo.from_api(dev) for dev in devices_raw]
        logger.debug(f"Encontrados {len(devices)} devices")
        return devices

    except APIError as e:
        logger.warning(f"Erro ao descobrir devices da network {network_id}: {e}")
        return []


def discover_ssids(network_id: str, client: MerakiClient) -> list[SSIDInfo]:
    """
    Descobre SSIDs de uma network wireless.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado

    Returns:
        Lista de SSIDInfo (vazia se network nao tem wireless)
    """
    logger.debug(f"Descobrindo SSIDs da network {network_id}")

    ssids_raw = client.safe_call(client.get_ssids, network_id, default=[])

    if not ssids_raw:
        logger.debug("Network nao tem wireless ou erro ao buscar SSIDs")
        return []

    ssids = [SSIDInfo.from_api(ssid, network_id) for ssid in ssids_raw]
    logger.debug(f"Encontrados {len(ssids)} SSIDs")
    return ssids


def discover_vlans(network_id: str, client: MerakiClient) -> list[VLANInfo]:
    """
    Descobre VLANs de uma network appliance.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado

    Returns:
        Lista de VLANInfo (vazia se network nao tem appliance)
    """
    logger.debug(f"Descobrindo VLANs da network {network_id}")

    vlans_raw = client.safe_call(client.get_vlans, network_id, default=[])

    if not vlans_raw:
        logger.debug("Network nao tem VLANs habilitadas ou erro ao buscar")
        return []

    vlans = [VLANInfo.from_api(vlan, network_id) for vlan in vlans_raw]
    logger.debug(f"Encontradas {len(vlans)} VLANs")
    return vlans


def discover_firewall_rules(network_id: str, client: MerakiClient) -> dict:
    """
    Descobre regras de firewall L3 e L7.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado

    Returns:
        Dict com l3_rules e l7_rules
    """
    logger.debug(f"Descobrindo firewall rules da network {network_id}")

    result = {
        "l3_rules": [],
        "l7_rules": [],
    }

    # L3 Rules
    l3_data = client.safe_call(client.get_l3_firewall_rules, network_id, default={})
    if l3_data:
        result["l3_rules"] = l3_data.get("rules", [])

    # L7 Rules
    l7_data = client.safe_call(client.get_l7_firewall_rules, network_id, default={})
    if l7_data:
        result["l7_rules"] = l7_data.get("rules", [])

    logger.debug(
        f"Encontradas {len(result['l3_rules'])} L3 rules "
        f"e {len(result['l7_rules'])} L7 rules"
    )

    return result


def discover_switch_ports(serial: str, client: MerakiClient) -> list[dict]:
    """
    Descobre portas de um switch.

    Args:
        serial: Serial do switch
        client: Cliente Meraki autenticado

    Returns:
        Lista de configuracoes de portas
    """
    logger.debug(f"Descobrindo portas do switch {serial}")

    ports = client.safe_call(client.get_switch_ports, serial, default=[])
    logger.debug(f"Encontradas {len(ports)} portas")

    return ports


def discover_switch_acls(network_id: str, client: MerakiClient) -> dict:
    """
    Descobre ACLs de switch.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado

    Returns:
        Dict com regras de ACL
    """
    logger.debug(f"Descobrindo switch ACLs da network {network_id}")

    acls = client.safe_call(client.get_switch_acls, network_id, default={})

    if acls:
        rules_count = len(acls.get("rules", []))
        logger.debug(f"Encontradas {rules_count} regras de ACL")

    return acls


def discover_clients(network_id: str, client: MerakiClient, timespan: int = 3600) -> list[dict]:
    """
    Descobre clientes conectados a uma network com dados de uso de banda.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado
        timespan: Janela de tempo em segundos (default: 1 hora)

    Returns:
        Lista de clientes com uso de banda (sorted by usage desc)
    """
    logger.debug(f"Descobrindo clientes da network {network_id} (timespan={timespan}s)")

    clients = client.safe_call(
        client.get_network_clients, network_id, timespan=timespan, default=[]
    )

    # Sort by total usage (sent + recv) descending
    for c in clients:
        c["total_usage"] = (c.get("usage", {}).get("sent", 0) or 0) + (c.get("usage", {}).get("recv", 0) or 0)

    clients.sort(key=lambda c: c.get("total_usage", 0), reverse=True)
    logger.debug(f"Encontrados {len(clients)} clientes")

    return clients


def discover_traffic(network_id: str, client: MerakiClient, timespan: int = 3600) -> list[dict]:
    """
    Descobre trafego da network por aplicacao.

    Args:
        network_id: ID da network
        client: Cliente Meraki autenticado
        timespan: Janela de tempo em segundos (default: 1 hora)

    Returns:
        Lista de aplicacoes com trafego (sorted by usage desc)
    """
    logger.debug(f"Descobrindo trafego da network {network_id}")

    traffic = client.safe_call(
        client.get_network_traffic, network_id, timespan=timespan, default=[]
    )

    logger.debug(f"Encontradas {len(traffic)} aplicacoes com trafego")
    return traffic


def discover_vpn_topology(org_id: Optional[str] = None, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre topologia Site-to-Site VPN.

    Args:
        org_id: ID da organizacao (usa do profile se None)
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracoes VPN e status
    """
    client = client or get_client()
    org_id = org_id or client.org_id
    if not org_id:
        raise ValueError("org_id deve ser fornecido ou definido no profile")

    logger.debug(f"Descobrindo VPN topology da org {org_id}")

    # Get all networks
    networks = client.safe_call(client.get_networks, org_id, default=[])

    # Filter MX networks
    mx_networks = [n for n in networks if "appliance" in n.get("productTypes", [])]

    # Get VPN config for each MX network
    vpn_configs = {}
    for network in mx_networks:
        net_id = network["id"]
        config = client.safe_call(client.get_vpn_config, net_id, default={})
        if config:
            vpn_configs[net_id] = config

    # Get org-level VPN statuses
    vpn_statuses = client.safe_call(client.get_vpn_statuses, org_id, default=[])

    logger.debug(
        f"Encontradas {len(vpn_configs)} configuracoes VPN, "
        f"{len(vpn_statuses)} status entries"
    )

    return {
        "vpn_configs": vpn_configs,
        "vpn_statuses": vpn_statuses,
        "mx_networks": mx_networks,
    }


def discover_content_filtering(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracao de Content Filtering.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracao de content filtering
    """
    client = client or get_client()
    logger.debug(f"Descobrindo content filtering da network {network_id}")

    result = client.safe_call(client.get_content_filtering, network_id, default={})
    logger.debug(f"Content filtering: {len(result.get('blockedUrlPatterns', []))} blocked URLs")

    return result


def discover_ips_settings(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracoes de IPS/IDS.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracoes de IPS
    """
    client = client or get_client()
    logger.debug(f"Descobrindo IPS settings da network {network_id}")

    result = client.safe_call(client.get_intrusion_settings, network_id, default={})
    logger.debug(f"IPS mode: {result.get('mode', 'unknown')}")

    return result


def discover_amp_settings(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracoes de AMP/Malware Protection.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracoes de AMP
    """
    client = client or get_client()
    logger.debug(f"Descobrindo AMP settings da network {network_id}")

    result = client.safe_call(client.get_malware_settings, network_id, default={})
    logger.debug(f"AMP mode: {result.get('mode', 'unknown')}")

    return result


def discover_traffic_shaping(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracao de Traffic Shaping.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com regras de traffic shaping
    """
    client = client or get_client()
    logger.debug(f"Descobrindo traffic shaping da network {network_id}")

    result = client.safe_call(client.get_traffic_shaping, network_id, default={})
    logger.debug(f"Traffic shaping: {len(result.get('rules', []))} rules")

    return result


def discover_alerts(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracoes de alertas.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracoes de alertas
    """
    client = client or get_client()
    logger.debug(f"Descobrindo alert settings da network {network_id}")

    result = client.safe_call(client.get_alert_settings, network_id, default={})
    # Ensure result is a dict
    if not isinstance(result, dict):
        result = {}
    logger.debug(f"Alertas: {len(result.get('alerts', []))} configured")

    return result


def discover_webhooks(network_id: str, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre servidores webhook configurados.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Lista de webhooks
    """
    client = client or get_client()
    logger.debug(f"Descobrindo webhooks da network {network_id}")

    result = client.safe_call(client.get_webhook_servers, network_id, default=[])
    logger.debug(f"Webhooks: {len(result)} servers")

    return result


def discover_firmware_status(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre status de firmware da network.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com status de firmware
    """
    client = client or get_client()
    logger.debug(f"Descobrindo firmware status da network {network_id}")

    result = client.safe_call(client.get_firmware_upgrades, network_id, default={})
    if isinstance(result, dict):
        logger.debug(f"Firmware upgrade policy: {result.get('upgradeWindow', {}).get('dayOfWeek', 'unknown')}")

    return result


def discover_snmp_config(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracao SNMP.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracao SNMP
    """
    client = client or get_client()
    logger.debug(f"Descobrindo SNMP config da network {network_id}")

    result = client.safe_call(client.get_snmp_settings, network_id, default={})
    logger.debug(f"SNMP access: {result.get('access', 'unknown')}")

    return result


def discover_syslog_config(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracao de syslog.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracao de syslog
    """
    client = client or get_client()
    logger.debug(f"Descobrindo syslog config da network {network_id}")

    result = client.safe_call(client.get_syslog_servers, network_id, default={})
    servers = result.get("servers", [])
    logger.debug(f"Syslog: {len(servers)} servers")

    return result


def discover_recent_changes(org_id: Optional[str] = None, timespan: int = 86400, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre mudancas recentes de configuracao.

    Args:
        org_id: ID da organizacao (opcional)
        timespan: Janela de tempo em segundos (default: 86400 = 24h)
        client: Cliente Meraki (opcional)

    Returns:
        Lista de mudancas
    """
    client = client or get_client()
    org_id = org_id or client.org_id
    if not org_id:
        raise ValueError("org_id deve ser fornecido ou definido no profile")

    logger.debug(f"Descobrindo config changes da org {org_id} (timespan={timespan}s)")

    result = client.safe_call(client.get_config_changes, org_id, timespan=timespan, default=[])
    logger.debug(f"Config changes: {len(result)} entries")

    return result


def discover_switch_routing(serial: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracoes de routing L3 de um switch.

    Args:
        serial: Serial do switch
        client: Cliente Meraki (opcional)

    Returns:
        Dict com interfaces e rotas estaticas
    """
    client = client or get_client()
    logger.debug(f"Descobrindo switch routing para {serial}")

    result = {
        "interfaces": client.safe_call(client.get_switch_routing_interfaces, serial, default=[]),
        "static_routes": client.safe_call(client.get_switch_static_routes, serial, default=[]),
    }

    logger.debug(f"Encontradas {len(result['interfaces'])} interfaces L3, {len(result['static_routes'])} rotas estaticas")
    return result


def discover_stp_config(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre configuracao STP da network.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com configuracao STP
    """
    client = client or get_client()
    logger.debug(f"Descobrindo STP config da network {network_id}")

    result = client.safe_call(client.get_stp_settings, network_id, default={})
    logger.debug(f"STP enabled: {result.get('stpBridgePriority', 'unknown')}")

    return result


def discover_nat_rules(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre regras NAT (1:1 e 1:Many).

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com regras 1:1 e 1:Many
    """
    client = client or get_client()
    logger.debug(f"Descobrindo NAT rules da network {network_id}")

    result = {
        "1to1_nat": client.safe_call(client.get_1to1_nat, network_id, default={"rules": []}),
        "1tomany_nat": client.safe_call(client.get_1tomany_nat, network_id, default={"rules": []}),
    }

    logger.debug(f"Found {len(result['1to1_nat'].get('rules', []))} 1:1 NAT, {len(result['1tomany_nat'].get('rules', []))} 1:Many NAT")
    return result


def discover_port_forwarding(network_id: str, client: Optional[MerakiClient] = None) -> dict:
    """
    Descobre regras de port forwarding.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Dict com regras de port forwarding
    """
    client = client or get_client()
    logger.debug(f"Descobrindo port forwarding da network {network_id}")

    result = client.safe_call(client.get_port_forwarding, network_id, default={"rules": []})
    logger.debug(f"Port forwarding: {len(result.get('rules', []))} rules")

    return result


def discover_rf_profiles(network_id: str, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre RF profiles da network.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Lista de RF profiles
    """
    client = client or get_client()
    logger.debug(f"Descobrindo RF profiles da network {network_id}")

    result = client.safe_call(client.get_rf_profiles, network_id, default=[])
    logger.debug(f"RF profiles: {len(result)} profiles")

    return result


def discover_wireless_health(network_id: str, client: Optional[MerakiClient] = None, timespan: int = 3600) -> dict:
    """
    Descobre metricas de saude wireless.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)
        timespan: Janela de tempo em segundos (default: 3600 = 1h)

    Returns:
        Dict com metricas de saude wireless
    """
    client = client or get_client()
    logger.debug(f"Descobrindo wireless health da network {network_id}")

    result = {
        "connection_stats": client.safe_call(client.get_wireless_connection_stats, network_id, timespan=timespan, default={}),
        "latency_stats": client.safe_call(client.get_wireless_latency_stats, network_id, timespan=timespan, default={}),
        "signal_quality": client.safe_call(client.get_wireless_signal_quality, network_id, timespan=timespan, default=[]),
        "channel_utilization": client.safe_call(client.get_channel_utilization, network_id, timespan=timespan, default=[]),
        "failed_connections": client.safe_call(client.get_failed_connections, network_id, timespan=timespan, default=[]),
    }

    logger.debug(f"Wireless health: {len(result['failed_connections'])} failed connections")
    return result


def discover_qos_config(network_id: str, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre configuracao QoS do switch.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Lista de regras QoS
    """
    client = client or get_client()
    logger.debug(f"Descobrindo QoS config da network {network_id}")

    result = client.safe_call(client.get_qos_rules, network_id, default=[])
    logger.debug(f"QoS rules: {len(result)} rules")

    return result


def discover_org_admins(org_id: Optional[str] = None, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre administradores da organizacao.

    Args:
        org_id: ID da organizacao (opcional)
        client: Cliente Meraki (opcional)

    Returns:
        Lista de admins com roles e 2FA
    """
    client = client or get_client()
    org_id = org_id or client.org_id
    if not org_id:
        raise ValueError("org_id deve ser fornecido ou definido no profile")

    logger.debug(f"Descobrindo org admins da org {org_id}")

    result = client.safe_call(client.get_admins, org_id, default=[])
    logger.debug(f"Org admins: {len(result)} admins")

    return result


def discover_inventory(org_id: Optional[str] = None, client: Optional[MerakiClient] = None) -> list[dict]:
    """
    Descobre inventario completo da org.

    Args:
        org_id: ID da organizacao (opcional)
        client: Cliente Meraki (opcional)

    Returns:
        Lista de devices no inventario
    """
    client = client or get_client()
    org_id = org_id or client.org_id
    if not org_id:
        raise ValueError("org_id deve ser fornecido ou definido no profile")

    logger.debug(f"Descobrindo inventory da org {org_id}")

    result = client.safe_call(client.get_inventory, org_id, default=[])
    logger.debug(f"Inventory: {len(result)} devices")

    return result


def full_discovery(
    org_id: Optional[str] = None,
    client: Optional[MerakiClient] = None,
) -> DiscoveryResult:
    """
    Executa discovery completo de uma organizacao Meraki.

    Coleta:
    - Networks
    - Devices (com status)
    - SSIDs (wireless)
    - VLANs (appliance)
    - Firewall rules (L3 e L7)
    - Switch ports e ACLs

    Analisa:
    - Identifica problemas
    - Gera sugestoes

    Args:
        org_id: ID da organizacao (usa do profile se None)
        client: Cliente Meraki (cria novo se None)

    Returns:
        DiscoveryResult com todas as informacoes
    """
    # Inicializar cliente se necessario
    if client is None:
        client = get_client()

    # Usar org_id do profile se nao fornecido
    if org_id is None:
        org_id = client.org_id
        if not org_id:
            raise ValueError("org_id deve ser fornecido ou definido no profile")

    logger.info(f"Iniciando discovery completo da org {org_id}")
    start_time = datetime.now()

    # Coletar dados da organizacao
    org_data = client.get_organization(org_id)
    org_name = org_data["name"]

    logger.info(f"Organizacao: {org_name}")

    # Descobrir networks
    networks = discover_networks(org_id, client)

    # Descobrir devices e configuracoes por network
    all_devices: list[DeviceInfo] = []
    configurations: dict[str, dict] = {}

    for network in networks:
        net_id = network.id
        logger.info(f"Analisando network '{network.name}' ({net_id})")

        # Devices
        devices = discover_devices(net_id, client)
        all_devices.extend(devices)

        # Configuracoes
        configs: dict[str, Any] = {
            "ssids": [],
            "vlans": [],
            "firewall": {"l3_rules": [], "l7_rules": []},
            "switch_acls": {},
            "switch_ports": {},
            "content_filtering": {},
            "ips_settings": {},
            "amp_settings": {},
            "traffic_shaping": {},
            "alert_settings": {},
            "webhooks": [],
            "firmware_status": {},
            "snmp_config": {},
            "syslog_config": {},
        }

        # SSIDs (se wireless)
        if "wireless" in network.product_types:
            configs["ssids"] = [asdict(s) for s in discover_ssids(net_id, client)]

        # VLANs (se appliance)
        if "appliance" in network.product_types:
            configs["vlans"] = [asdict(v) for v in discover_vlans(net_id, client)]
            configs["firewall"] = discover_firewall_rules(net_id, client)
            configs["content_filtering"] = discover_content_filtering(net_id, client)
            configs["ips_settings"] = discover_ips_settings(net_id, client)
            configs["amp_settings"] = discover_amp_settings(net_id, client)
            configs["traffic_shaping"] = discover_traffic_shaping(net_id, client)

        # Epic 9: Alerts, Firmware, SNMP, Syslog (all networks)
        configs["alert_settings"] = discover_alerts(net_id, client)
        configs["webhooks"] = discover_webhooks(net_id, client)
        configs["firmware_status"] = discover_firmware_status(net_id, client)
        configs["snmp_config"] = discover_snmp_config(net_id, client)
        configs["syslog_config"] = discover_syslog_config(net_id, client)

        # Switch ACLs (se switch)
        if "switch" in network.product_types:
            configs["switch_acls"] = discover_switch_acls(net_id, client)

            # Portas de cada switch
            for device in devices:
                if device.product_type == "switch":
                    ports = discover_switch_ports(device.serial, client)
                    configs["switch_ports"][device.serial] = ports

        configurations[net_id] = configs

    # Discover VPN topology (org-level)
    logger.info("Descobrindo topologia VPN")
    vpn_topology = discover_vpn_topology(org_id, client)
    configurations["vpn_topology"] = vpn_topology

    # Buscar status atualizado dos devices
    logger.info("Buscando status dos devices")
    try:
        device_statuses = client.get_device_status(org_id)
        status_map = {d["serial"]: d.get("status") for d in device_statuses}

        # Atualizar status nos devices
        for device in all_devices:
            if device.serial in status_map:
                device.status = status_map[device.serial]

    except APIError as e:
        logger.warning(f"Nao foi possivel buscar status dos devices: {e}")

    # Criar resultado
    result = DiscoveryResult(
        timestamp=start_time,
        org_id=org_id,
        org_name=org_name,
        networks=networks,
        devices=all_devices,
        configurations=configurations,
        issues=[],
        suggestions=[],
    )

    # Analisar problemas
    logger.info("Analisando problemas")
    result.issues = find_issues(result)

    # Gerar sugestoes
    logger.info("Gerando sugestoes")
    result.suggestions = generate_suggestions(result.issues)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Discovery completo em {elapsed:.2f}s: "
        f"{len(networks)} networks, {len(all_devices)} devices, "
        f"{len(result.issues)} issues"
    )

    return result


# ==================== Analysis Functions ====================


def find_issues(discovery: DiscoveryResult) -> list[dict]:
    """
    Identifica problemas na rede.

    Detecta:
    - Devices offline
    - Networks sem devices
    - SSIDs habilitados sem autenticacao
    - Firewall rules muito permissivas

    Args:
        discovery: Resultado do discovery

    Returns:
        Lista de issues encontrados
    """
    issues: list[dict] = []

    # 1. Devices offline
    offline_devices = [d for d in discovery.devices if d.status == "offline"]
    if offline_devices:
        issues.append({
            "type": "devices_offline",
            "severity": "high",
            "message": f"{len(offline_devices)} device(s) offline",
            "count": len(offline_devices),
            "devices": [
                {"serial": d.serial, "name": d.name, "model": d.model}
                for d in offline_devices
            ],
        })

    # 2. Devices com status alerting
    alerting_devices = [d for d in discovery.devices if d.status == "alerting"]
    if alerting_devices:
        issues.append({
            "type": "devices_alerting",
            "severity": "medium",
            "message": f"{len(alerting_devices)} device(s) em estado de alerta",
            "count": len(alerting_devices),
            "devices": [
                {"serial": d.serial, "name": d.name, "model": d.model}
                for d in alerting_devices
            ],
        })

    # 3. Networks sem devices
    networks_without_devices = []
    devices_by_network: dict[str, int] = {}

    for device in discovery.devices:
        net_id = device.network_id
        devices_by_network[net_id] = devices_by_network.get(net_id, 0) + 1

    for network in discovery.networks:
        if network.id not in devices_by_network:
            networks_without_devices.append(network)

    if networks_without_devices:
        issues.append({
            "type": "networks_without_devices",
            "severity": "low",
            "message": f"{len(networks_without_devices)} network(s) sem devices",
            "count": len(networks_without_devices),
            "networks": [
                {"id": n.id, "name": n.name}
                for n in networks_without_devices
            ],
        })

    # 4. SSIDs habilitados sem autenticacao
    insecure_ssids = []

    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        for ssid_data in configs.get("ssids", []):
            if ssid_data["enabled"] and ssid_data.get("auth_mode") == "open":
                network = next((n for n in discovery.networks if n.id == net_id), None)
                insecure_ssids.append({
                    "network_id": net_id,
                    "network_name": network.name if network else "unknown",
                    "ssid_number": ssid_data["number"],
                    "ssid_name": ssid_data["name"],
                })

    if insecure_ssids:
        issues.append({
            "type": "insecure_ssids",
            "severity": "high",
            "message": f"{len(insecure_ssids)} SSID(s) habilitado(s) sem autenticacao",
            "count": len(insecure_ssids),
            "ssids": insecure_ssids,
        })

    # 5. Firewall rules muito permissivas (any any allow)
    permissive_rules = []

    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        firewall = configs.get("firewall", {})
        l3_rules = firewall.get("l3_rules", [])

        network = next((n for n in discovery.networks if n.id == net_id), None)

        for rule in l3_rules:
            # Verificar se e uma regra "any any allow"
            if (
                rule.get("policy") == "allow"
                and rule.get("srcCidr") in ["Any", "any"]
                and rule.get("destCidr") in ["Any", "any"]
            ):
                permissive_rules.append({
                    "network_id": net_id,
                    "network_name": network.name if network else "unknown",
                    "rule": rule.get("comment", "sem comentario"),
                })

    if permissive_rules:
        issues.append({
            "type": "permissive_firewall_rules",
            "severity": "medium",
            "message": f"{len(permissive_rules)} regra(s) de firewall muito permissiva(s)",
            "count": len(permissive_rules),
            "rules": permissive_rules,
        })

    # 6. VPN peer down (check if configurations dict has vpn_topology)
    vpn_topology = discovery.configurations.get("vpn_topology", {})
    vpn_statuses = vpn_topology.get("vpn_statuses", []) if isinstance(vpn_topology, dict) else []
    peers_down = [s for s in vpn_statuses if s.get("vpnMode") == "spoke" and s.get("status", {}).get("metaNetworkName") and "offline" in str(s.get("status", {}).get("uplinks", [])).lower()]

    if peers_down:
        issues.append({
            "type": "vpn_peer_down",
            "severity": "high",
            "message": f"{len(peers_down)} VPN peer(s) offline",
            "count": len(peers_down),
            "peers": [{"network": p.get("networkName"), "mode": p.get("vpnMode")} for p in peers_down],
        })

    # 7. Content filtering permissive
    content_filter_permissive = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        content_filter = configs.get("content_filtering", {})
        url_category_list_size = content_filter.get("urlCategoryListSize", "topSites")
        blocked_categories = content_filter.get("blockedUrlCategories", [])

        # If topSites (minimal filtering) and no blocked categories
        if url_category_list_size == "topSites" and len(blocked_categories) == 0:
            network = next((n for n in discovery.networks if n.id == net_id), None)
            content_filter_permissive.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if content_filter_permissive:
        issues.append({
            "type": "content_filter_permissive",
            "severity": "medium",
            "message": f"{len(content_filter_permissive)} network(s) com content filtering muito permissivo",
            "count": len(content_filter_permissive),
            "networks": content_filter_permissive,
        })

    # 8. IPS disabled
    ips_disabled = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        ips_settings = configs.get("ips_settings", {})
        if ips_settings.get("mode") == "disabled":
            network = next((n for n in discovery.networks if n.id == net_id), None)
            ips_disabled.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if ips_disabled:
        issues.append({
            "type": "ips_disabled",
            "severity": "medium",
            "message": f"{len(ips_disabled)} network(s) com IPS desabilitado",
            "count": len(ips_disabled),
            "networks": ips_disabled,
        })

    # 9. AMP disabled
    amp_disabled = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        amp_settings = configs.get("amp_settings", {})
        if amp_settings.get("mode") == "disabled":
            network = next((n for n in discovery.networks if n.id == net_id), None)
            amp_disabled.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if amp_disabled:
        issues.append({
            "type": "amp_disabled",
            "severity": "medium",
            "message": f"{len(amp_disabled)} network(s) com AMP desabilitado",
            "count": len(amp_disabled),
            "networks": amp_disabled,
        })

    # 10. No alerts configured (Epic 9)
    no_alerts = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        alert_settings = configs.get("alert_settings", {})
        alerts = alert_settings.get("alerts", [])
        if len(alerts) == 0 or not alert_settings:
            network = next((n for n in discovery.networks if n.id == net_id), None)
            no_alerts.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if no_alerts:
        issues.append({
            "type": "no_alerts_configured",
            "severity": "medium",
            "message": f"{len(no_alerts)} network(s) sem alertas configurados",
            "count": len(no_alerts),
            "networks": no_alerts,
        })

    # 11. Firmware outdated (Epic 9)
    firmware_outdated = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        firmware_status = configs.get("firmware_status", {})
        products = firmware_status.get("products", {})
        for product_type, product_config in products.items():
            current_version = product_config.get("currentVersion", {})
            if current_version.get("id") and current_version.get("id") != product_config.get("nextUpgrade", {}).get("id"):
                network = next((n for n in discovery.networks if n.id == net_id), None)
                firmware_outdated.append({
                    "network_id": net_id,
                    "network_name": network.name if network else "unknown",
                    "product_type": product_type,
                    "current": current_version.get("shortName", "unknown"),
                })
                break  # One entry per network

    if firmware_outdated:
        issues.append({
            "type": "firmware_outdated",
            "severity": "low",
            "message": f"{len(firmware_outdated)} network(s) com firmware desatualizado",
            "count": len(firmware_outdated),
            "networks": firmware_outdated,
        })

    # 12. No SNMP configured (Epic 9)
    no_snmp = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        snmp_config = configs.get("snmp_config", {})
        if snmp_config.get("access") == "none" or not snmp_config:
            network = next((n for n in discovery.networks if n.id == net_id), None)
            no_snmp.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if no_snmp:
        issues.append({
            "type": "no_snmp_configured",
            "severity": "low",
            "message": f"{len(no_snmp)} network(s) sem SNMP configurado",
            "count": len(no_snmp),
            "networks": no_snmp,
        })

    # 13. No syslog configured (Epic 9)
    no_syslog = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        syslog_config = configs.get("syslog_config", {})
        servers = syslog_config.get("servers", [])
        if len(servers) == 0:
            network = next((n for n in discovery.networks if n.id == net_id), None)
            no_syslog.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
            })

    if no_syslog:
        issues.append({
            "type": "no_syslog_configured",
            "severity": "low",
            "message": f"{len(no_syslog)} network(s) sem syslog configurado",
            "count": len(no_syslog),
            "networks": no_syslog,
        })

    # 14. STP inconsistency (Epic 10)
    stp_inconsistent = []
    for net_id, configs in discovery.configurations.items():
        if not isinstance(configs, dict):
            continue
        stp_config = configs.get("stp_config", {})
        if stp_config.get("stpBridgePriority") and stp_config.get("rstpEnabled") is False:
            network = next((n for n in discovery.networks if n.id == net_id), None)
            stp_inconsistent.append({
                "network_id": net_id,
                "network_name": network.name if network else "unknown",
                "reason": "STP enabled but RSTP disabled",
            })

    if stp_inconsistent:
        issues.append({
            "type": "stp_inconsistency",
            "severity": "medium",
            "message": f"{len(stp_inconsistent)} network(s) with STP inconsistency",
            "count": len(stp_inconsistent),
            "networks": stp_inconsistent,
        })

    return issues


def generate_suggestions(issues: list[dict]) -> list[dict]:
    """
    Gera sugestoes baseadas nos issues encontrados.

    Args:
        issues: Lista de issues do discovery

    Returns:
        Lista de sugestoes
    """
    suggestions: list[dict] = []

    for issue in issues:
        issue_type = issue["type"]

        if issue_type == "devices_offline":
            suggestions.append({
                "issue_type": issue_type,
                "priority": "high",
                "action": "Verificar dispositivos offline",
                "description": (
                    "Dispositivos offline podem indicar problemas de conectividade, "
                    "energia ou hardware. Verifique os dispositivos listados."
                ),
                "automated": False,
            })

        elif issue_type == "devices_alerting":
            suggestions.append({
                "issue_type": issue_type,
                "priority": "medium",
                "action": "Investigar alertas dos dispositivos",
                "description": (
                    "Dispositivos em estado de alerta podem ter problemas de "
                    "performance, uplink ou configuracao. Revise os alertas no Dashboard."
                ),
                "automated": False,
            })

        elif issue_type == "networks_without_devices":
            suggestions.append({
                "issue_type": issue_type,
                "priority": "low",
                "action": "Remover networks vazias ou adicionar devices",
                "description": (
                    "Networks sem devices podem ser removidas para simplificar "
                    "o gerenciamento ou receber devices se forem necessarias."
                ),
                "automated": False,
            })

        elif issue_type == "insecure_ssids":
            suggestions.append({
                "issue_type": issue_type,
                "priority": "high",
                "action": "Configurar autenticacao nos SSIDs abertos",
                "description": (
                    "SSIDs sem autenticacao representam um risco de seguranca. "
                    "Configure WPA2/WPA3 Enterprise ou PSK."
                ),
                "automated": True,
                "workflow_template": "secure_ssid",
            })

        elif issue_type == "permissive_firewall_rules":
            suggestions.append({
                "issue_type": issue_type,
                "priority": "medium",
                "action": "Revisar regras de firewall permissivas",
                "description": (
                    "Regras 'any any allow' comprometem a seguranca da rede. "
                    "Aplique o principio de menor privilegio especificando "
                    "origem, destino e portas."
                ),
                "automated": False,
            })

    return suggestions


# ==================== Snapshot Functions ====================


def get_snapshot_dir(client_name: str) -> Path:
    """
    Retorna o diretorio de snapshots para um cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Path do diretorio de snapshots
    """
    snapshot_dir = Path("clients") / client_name / "discovery"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def save_snapshot(discovery: DiscoveryResult, client_name: str) -> Path:
    """
    Salva um snapshot do discovery em JSON.

    Args:
        discovery: Resultado do discovery
        client_name: Nome do cliente

    Returns:
        Path do arquivo salvo
    """
    snapshot_dir = get_snapshot_dir(client_name)

    # Formato: discovery_YYYYMMDD_HHMMSS.json
    timestamp_str = discovery.timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"discovery_{timestamp_str}.json"
    filepath = snapshot_dir / filename

    logger.info(f"Salvando snapshot em {filepath}")

    # Serializar para JSON
    data = discovery.to_dict()

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Snapshot salvo com sucesso")

    # Criar symlink para latest
    latest_link = snapshot_dir / "latest.json"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(filename)

    return filepath


def load_snapshot(path: Path) -> DiscoveryResult:
    """
    Carrega um snapshot do disco.

    Args:
        path: Caminho do arquivo JSON

    Returns:
        DiscoveryResult
    """
    logger.info(f"Carregando snapshot de {path}")

    with open(path, "r") as f:
        data = json.load(f)

    return DiscoveryResult.from_dict(data)


def list_snapshots(client_name: str) -> list[Path]:
    """
    Lista todos os snapshots de um cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Lista de paths dos snapshots (ordenado por data, mais recente primeiro)
    """
    snapshot_dir = get_snapshot_dir(client_name)
    snapshots = sorted(
        snapshot_dir.glob("discovery_*.json"),
        reverse=True,
    )
    return snapshots


def compare_snapshots(old: DiscoveryResult, new: DiscoveryResult) -> dict:
    """
    Compara dois snapshots e retorna as diferencas.

    Args:
        old: Snapshot antigo
        new: Snapshot novo

    Returns:
        Dict com as diferencas encontradas
    """
    logger.info(
        f"Comparando snapshots: {old.timestamp.isoformat()} vs {new.timestamp.isoformat()}"
    )

    diff: dict[str, Any] = {
        "old_timestamp": old.timestamp.isoformat(),
        "new_timestamp": new.timestamp.isoformat(),
        "networks": {"added": [], "removed": [], "changed": []},
        "devices": {"added": [], "removed": [], "changed_status": []},
        "issues": {"resolved": [], "new": []},
    }

    # Networks
    old_net_ids = {n.id for n in old.networks}
    new_net_ids = {n.id for n in new.networks}

    added_net_ids = new_net_ids - old_net_ids
    removed_net_ids = old_net_ids - new_net_ids

    diff["networks"]["added"] = [
        {"id": n.id, "name": n.name}
        for n in new.networks
        if n.id in added_net_ids
    ]

    diff["networks"]["removed"] = [
        {"id": n.id, "name": n.name}
        for n in old.networks
        if n.id in removed_net_ids
    ]

    # Devices
    old_device_map = {d.serial: d for d in old.devices}
    new_device_map = {d.serial: d for d in new.devices}

    old_serials = set(old_device_map.keys())
    new_serials = set(new_device_map.keys())

    added_serials = new_serials - old_serials
    removed_serials = old_serials - new_serials

    diff["devices"]["added"] = [
        {"serial": d.serial, "name": d.name, "model": d.model}
        for d in new.devices
        if d.serial in added_serials
    ]

    diff["devices"]["removed"] = [
        {"serial": d.serial, "name": d.name, "model": d.model}
        for d in old.devices
        if d.serial in removed_serials
    ]

    # Devices com mudanca de status
    for serial in old_serials & new_serials:
        old_device = old_device_map[serial]
        new_device = new_device_map[serial]

        if old_device.status != new_device.status:
            diff["devices"]["changed_status"].append({
                "serial": serial,
                "name": new_device.name,
                "old_status": old_device.status,
                "new_status": new_device.status,
            })

    # Issues
    old_issue_types = {i["type"] for i in old.issues}
    new_issue_types = {i["type"] for i in new.issues}

    resolved_types = old_issue_types - new_issue_types
    new_types = new_issue_types - old_issue_types

    diff["issues"]["resolved"] = [
        i for i in old.issues if i["type"] in resolved_types
    ]

    diff["issues"]["new"] = [
        i for i in new.issues if i["type"] in new_types
    ]

    logger.info(
        f"Comparacao completa: "
        f"{len(diff['devices']['added'])} devices adicionados, "
        f"{len(diff['devices']['removed'])} removidos, "
        f"{len(diff['issues']['new'])} novos issues"
    )

    return diff


# ==================== Main ====================


if __name__ == "__main__":
    import sys
    from rich.console import Console
    from rich.table import Table

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    console = Console()

    try:
        # Discovery completo
        console.print("\n[bold]Iniciando Discovery Meraki[/bold]\n")
        result = full_discovery()

        # Resumo
        summary = result.summary()
        console.print(f"[green]Organizacao:[/green] {summary['organization']}")
        console.print(f"[green]Networks:[/green] {summary['networks_count']}")
        console.print(f"[green]Devices:[/green] {summary['devices_count']}")

        # Status dos devices
        console.print("\n[bold]Status dos Devices:[/bold]")
        for status, count in summary["devices_by_status"].items():
            console.print(f"  {status}: {count}")

        # Issues
        if result.issues:
            console.print(f"\n[bold red]Issues Encontrados:[/bold red] {len(result.issues)}")

            table = Table(show_header=True)
            table.add_column("Severidade")
            table.add_column("Tipo")
            table.add_column("Mensagem")

            for issue in result.issues:
                severity = issue["severity"]
                color = "red" if severity == "high" else "yellow" if severity == "medium" else "blue"
                table.add_row(
                    f"[{color}]{severity}[/{color}]",
                    issue["type"],
                    issue["message"],
                )

            console.print(table)

        # Sugestoes
        if result.suggestions:
            console.print(f"\n[bold]Sugestoes:[/bold] {len(result.suggestions)}")
            for i, suggestion in enumerate(result.suggestions, 1):
                console.print(f"  {i}. [{suggestion['priority']}] {suggestion['action']}")

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        logger.exception("Erro no discovery")
        sys.exit(1)
