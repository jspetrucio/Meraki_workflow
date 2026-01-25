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

    try:
        networks_raw = client.get_networks(org_id)
        networks = [NetworkInfo.from_api(net) for net in networks_raw]
        logger.info(f"Encontradas {len(networks)} networks")
        return networks

    except APIError as e:
        logger.error(f"Erro ao descobrir networks: {e}")
        raise


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
        }

        # SSIDs (se wireless)
        if "wireless" in network.product_types:
            configs["ssids"] = [asdict(s) for s in discover_ssids(net_id, client)]

        # VLANs (se appliance)
        if "appliance" in network.product_types:
            configs["vlans"] = [asdict(v) for v in discover_vlans(net_id, client)]
            configs["firewall"] = discover_firewall_rules(net_id, client)

        # Switch ACLs (se switch)
        if "switch" in network.product_types:
            configs["switch_acls"] = discover_switch_acls(net_id, client)

            # Portas de cada switch
            for device in devices:
                if device.product_type == "switch":
                    ports = discover_switch_ports(device.serial, client)
                    configs["switch_ports"][device.serial] = ports

        configurations[net_id] = configs

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
