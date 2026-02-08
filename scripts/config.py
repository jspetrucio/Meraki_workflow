"""
Aplicacao de configuracoes em redes Meraki.

Fornece funcoes para:
- Configurar SSIDs (criar, atualizar, habilitar/desabilitar)
- Configurar VLANs (criar, atualizar, deletar)
- Configurar Firewall L3 (adicionar/remover regras)
- Configurar ACLs de switch
- Fazer backup automatico antes de mudancas
- Suportar rollback

Uso:
    from scripts.config import configure_ssid, add_firewall_rule

    result = configure_ssid(
        network_id="N_123",
        ssid_number=0,
        name="Guest WiFi",
        enabled=True
    )
    print(f"SSID: {result.message}")
"""

import json
import logging
import requests
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from meraki.exceptions import APIError

from .api import MerakiClient, get_client

logger = logging.getLogger(__name__)


def _mask_serial(serial: str) -> str:
    """Mask a device serial for safe logging (e.g. 'Q2XX-XXXX-XXXX' → 'Q2XX...XXXX')."""
    return f"{serial[:4]}...{serial[-4:]}" if len(serial) > 8 else "****"


class ConfigAction(Enum):
    """Tipo de acao de configuracao."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ENABLE = "enable"
    DISABLE = "disable"


@dataclass
class ConfigResult:
    """Resultado de uma operacao de configuracao."""
    success: bool
    action: ConfigAction
    resource_type: str  # ssid, vlan, firewall, acl
    resource_id: str
    message: str
    backup_path: Optional[Path] = None
    changes: dict = field(default_factory=dict)
    error: Optional[str] = None

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"ConfigResult({status}, {self.action.value} {self.resource_type} "
            f"{self.resource_id}: {self.message})"
        )


# ==================== Backup & Rollback ====================

def backup_config(
    network_id: str,
    client_name: str,
    resource_type: str = "full",
    client: Optional[MerakiClient] = None
) -> Path:
    """
    Faz backup da configuracao atual da network.

    Args:
        network_id: ID da network
        client_name: Nome do cliente (para organizar backups)
        resource_type: Tipo de recurso (full, ssid, vlan, firewall, acl)
        client: Cliente Meraki (opcional)

    Returns:
        Path para o arquivo de backup criado
    """
    client = client or get_client()

    # Criar diretorio de backups
    backup_dir = Path("clients") / client_name / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Coletar configuracoes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_data = {
        "timestamp": timestamp,
        "network_id": network_id,
        "resource_type": resource_type
    }

    try:
        if resource_type in ["full", "ssid"]:
            backup_data["ssids"] = client.safe_call(
                client.get_ssids, network_id, default=[]
            )

        if resource_type in ["full", "vlan"]:
            backup_data["vlans"] = client.safe_call(
                client.get_vlans, network_id, default=[]
            )

        if resource_type in ["full", "firewall"]:
            backup_data["l3_firewall"] = client.safe_call(
                client.get_l3_firewall_rules, network_id, default={"rules": []}
            )
            backup_data["l7_firewall"] = client.safe_call(
                client.get_l7_firewall_rules, network_id, default={"rules": []}
            )

        if resource_type in ["full", "acl"]:
            backup_data["switch_acls"] = client.safe_call(
                client.get_switch_acls, network_id, default={"rules": []}
            )

        # Salvar backup
        backup_file = backup_dir / f"backup_{resource_type}_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"Backup criado: {backup_file}")
        return backup_file

    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        raise


def rollback_config(
    backup_path: Path,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Restaura configuracao a partir de um backup.

    Args:
        backup_path: Path para o arquivo de backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()

    try:
        # Ler backup
        with open(backup_path) as f:
            backup_data = json.load(f)

        network_id = backup_data["network_id"]
        resource_type = backup_data["resource_type"]
        changes = {}

        # Restaurar SSIDs
        if "ssids" in backup_data:
            for ssid in backup_data["ssids"]:
                number = ssid["number"]
                # Remover campos read-only
                update_data = {k: v for k, v in ssid.items()
                              if k not in ["number", "radiusServers", "radiusAccountingServers"]}
                client.update_ssid(network_id, number, **update_data)
                changes[f"ssid_{number}"] = "restored"

        # Restaurar VLANs
        if "vlans" in backup_data:
            # Get current VLANs
            current_vlans = client.safe_call(client.get_vlans, network_id, default=[])
            current_ids = {v["id"] for v in current_vlans}

            for vlan in backup_data["vlans"]:
                vlan_id = vlan["id"]
                # Remover campos read-only
                update_data = {k: v for k, v in vlan.items() if k != "id"}

                if vlan_id in current_ids:
                    client.update_vlan(network_id, str(vlan_id), **update_data)
                    changes[f"vlan_{vlan_id}"] = "updated"
                # Note: Nao recriamos VLANs deletadas automaticamente

        # Restaurar Firewall L3
        if "l3_firewall" in backup_data:
            rules = backup_data["l3_firewall"].get("rules", [])
            client.update_l3_firewall_rules(network_id, rules)
            changes["l3_firewall"] = f"{len(rules)} rules restored"

        # Restaurar Firewall L7
        if "l7_firewall" in backup_data:
            rules = backup_data["l7_firewall"].get("rules", [])
            client.update_l7_firewall_rules(network_id, rules)
            changes["l7_firewall"] = f"{len(rules)} rules restored"

        # Restaurar Switch ACLs
        if "switch_acls" in backup_data:
            rules = backup_data["switch_acls"].get("rules", [])
            client.update_switch_acls(network_id, rules)
            changes["switch_acls"] = f"{len(rules)} rules restored"

        return ConfigResult(
            success=True,
            action=ConfigAction.UPDATE,
            resource_type=resource_type,
            resource_id=network_id,
            message=f"Configuracao restaurada de {backup_path.name}",
            backup_path=backup_path,
            changes=changes
        )

    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.UPDATE,
            resource_type="rollback",
            resource_id=str(backup_path),
            message="Falha ao restaurar backup",
            error=str(e)
        )


# ==================== SSID Configuration ====================

def configure_ssid(
    network_id: str,
    ssid_number: int,
    name: Optional[str] = None,
    enabled: Optional[bool] = None,
    auth_mode: Optional[str] = None,
    psk: Optional[str] = None,
    vlan_id: Optional[int] = None,
    ip_assignment_mode: Optional[str] = None,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Configura um SSID wireless.

    Args:
        network_id: ID da network
        ssid_number: Numero do SSID (0-14)
        name: Nome do SSID (opcional)
        enabled: Habilitar/desabilitar (opcional)
        auth_mode: Modo de autenticacao (open, psk, 8021x-radius, etc)
        psk: Pre-shared key se auth_mode=psk
        vlan_id: ID da VLAN para tagging
        ip_assignment_mode: bridge, nat, etc
        backup: Fazer backup antes de aplicar (default: True)
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "ssid", client)

        # Preparar update
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if enabled is not None:
            update_data["enabled"] = enabled
        if auth_mode is not None:
            update_data["authMode"] = auth_mode
        if psk is not None:
            update_data["psk"] = psk
        if vlan_id is not None:
            update_data["defaultVlanId"] = vlan_id
        if ip_assignment_mode is not None:
            update_data["ipAssignmentMode"] = ip_assignment_mode

        # Aplicar
        result = client.update_ssid(network_id, ssid_number, **update_data)

        return ConfigResult(
            success=True,
            action=ConfigAction.UPDATE,
            resource_type="ssid",
            resource_id=f"{network_id}/ssid_{ssid_number}",
            message=f"SSID {ssid_number} configurado: {result.get('name')}",
            backup_path=backup_path,
            changes=update_data
        )

    except APIError as e:
        logger.error(f"Erro ao configurar SSID: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.UPDATE,
            resource_type="ssid",
            resource_id=f"{network_id}/ssid_{ssid_number}",
            message="Falha ao configurar SSID",
            error=str(e)
        )


def enable_ssid(
    network_id: str,
    ssid_number: int,
    name: str,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """Habilita um SSID."""
    return configure_ssid(
        network_id=network_id,
        ssid_number=ssid_number,
        name=name,
        enabled=True,
        backup=backup,
        client_name=client_name,
        client=client
    )


def disable_ssid(
    network_id: str,
    ssid_number: int,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """Desabilita um SSID."""
    return configure_ssid(
        network_id=network_id,
        ssid_number=ssid_number,
        enabled=False,
        backup=backup,
        client_name=client_name,
        client=client
    )


# ==================== VLAN Configuration ====================

def create_vlan(
    network_id: str,
    vlan_id: int,
    name: str,
    subnet: str,
    appliance_ip: str,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Cria uma nova VLAN.

    Args:
        network_id: ID da network
        vlan_id: ID numerico da VLAN
        name: Nome da VLAN
        subnet: Subnet em formato CIDR (ex: 192.168.10.0/24)
        appliance_ip: IP do appliance/gateway (ex: 192.168.10.1)
        backup: Fazer backup antes de aplicar
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "vlan", client)

        # Criar VLAN
        result = client.create_vlan(network_id, vlan_id, name, subnet, appliance_ip)

        return ConfigResult(
            success=True,
            action=ConfigAction.CREATE,
            resource_type="vlan",
            resource_id=str(vlan_id),
            message=f"VLAN {vlan_id} criada: {name} ({subnet})",
            backup_path=backup_path,
            changes={"vlan_id": vlan_id, "name": name, "subnet": subnet}
        )

    except APIError as e:
        logger.error(f"Erro ao criar VLAN: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.CREATE,
            resource_type="vlan",
            resource_id=str(vlan_id),
            message="Falha ao criar VLAN",
            error=str(e)
        )


def update_vlan(
    network_id: str,
    vlan_id: str,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None,
    **kwargs
) -> ConfigResult:
    """
    Atualiza uma VLAN existente.

    Args:
        network_id: ID da network
        vlan_id: ID da VLAN
        backup: Fazer backup antes de aplicar
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)
        **kwargs: Parametros a atualizar (name, subnet, applianceIp, etc)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "vlan", client)

        # Atualizar
        result = client.update_vlan(network_id, vlan_id, **kwargs)

        return ConfigResult(
            success=True,
            action=ConfigAction.UPDATE,
            resource_type="vlan",
            resource_id=vlan_id,
            message=f"VLAN {vlan_id} atualizada",
            backup_path=backup_path,
            changes=kwargs
        )

    except APIError as e:
        logger.error(f"Erro ao atualizar VLAN: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.UPDATE,
            resource_type="vlan",
            resource_id=vlan_id,
            message="Falha ao atualizar VLAN",
            error=str(e)
        )


def delete_vlan(
    network_id: str,
    vlan_id: str,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Remove uma VLAN.

    Args:
        network_id: ID da network
        vlan_id: ID da VLAN
        backup: Fazer backup antes de remover
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "vlan", client)

        # Deletar
        client.delete_vlan(network_id, vlan_id)

        return ConfigResult(
            success=True,
            action=ConfigAction.DELETE,
            resource_type="vlan",
            resource_id=vlan_id,
            message=f"VLAN {vlan_id} removida",
            backup_path=backup_path
        )

    except APIError as e:
        logger.error(f"Erro ao deletar VLAN: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.DELETE,
            resource_type="vlan",
            resource_id=vlan_id,
            message="Falha ao deletar VLAN",
            error=str(e)
        )


# ==================== Firewall L3 Configuration ====================

def get_firewall_rules(
    network_id: str,
    client: Optional[MerakiClient] = None
) -> list[dict]:
    """
    Retorna regras de firewall L3 atuais.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Lista de regras de firewall
    """
    client = client or get_client()
    try:
        result = client.get_l3_firewall_rules(network_id)
        return result.get("rules", [])
    except APIError as e:
        logger.error(f"Erro ao obter regras de firewall: {e}")
        return []


def add_firewall_rule(
    network_id: str,
    policy: str,
    protocol: str,
    src_cidr: str,
    dest_cidr: str,
    dest_port: str = "any",
    comment: Optional[str] = None,
    position: Optional[int] = None,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Adiciona uma regra de firewall L3.

    Args:
        network_id: ID da network
        policy: allow ou deny
        protocol: tcp, udp, icmp, ou any
        src_cidr: CIDR de origem (ex: "any" ou "192.168.1.0/24")
        dest_cidr: CIDR de destino
        dest_port: Porta de destino (ex: "80", "443", "any")
        comment: Comentario descritivo
        position: Posicao na lista (None = append no final)
        backup: Fazer backup antes de aplicar
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "firewall", client)

        # Obter regras atuais
        current_rules = get_firewall_rules(network_id, client)

        # Criar nova regra
        new_rule = {
            "policy": policy,
            "protocol": protocol,
            "srcCidr": src_cidr,
            "destCidr": dest_cidr,
            "destPort": dest_port
        }
        if comment:
            new_rule["comment"] = comment

        # Inserir na posicao correta
        if position is not None:
            current_rules.insert(position, new_rule)
        else:
            # Adicionar antes da regra default (ultima)
            if current_rules and current_rules[-1].get("policy") == "default deny":
                current_rules.insert(-1, new_rule)
            else:
                current_rules.append(new_rule)

        # Aplicar
        client.update_l3_firewall_rules(network_id, current_rules)

        return ConfigResult(
            success=True,
            action=ConfigAction.CREATE,
            resource_type="firewall",
            resource_id=network_id,
            message=f"Regra de firewall adicionada: {policy} {protocol} {src_cidr} -> {dest_cidr}:{dest_port}",
            backup_path=backup_path,
            changes=new_rule
        )

    except APIError as e:
        logger.error(f"Erro ao adicionar regra de firewall: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.CREATE,
            resource_type="firewall",
            resource_id=network_id,
            message="Falha ao adicionar regra de firewall",
            error=str(e)
        )


def remove_firewall_rule(
    network_id: str,
    rule_index: int,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Remove uma regra de firewall L3 por indice.

    Args:
        network_id: ID da network
        rule_index: Indice da regra (0-based)
        backup: Fazer backup antes de remover
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "firewall", client)

        # Obter regras atuais
        current_rules = get_firewall_rules(network_id, client)

        if rule_index < 0 or rule_index >= len(current_rules):
            return ConfigResult(
                success=False,
                action=ConfigAction.DELETE,
                resource_type="firewall",
                resource_id=network_id,
                message=f"Indice {rule_index} fora do range (0-{len(current_rules)-1})",
                error="Invalid index"
            )

        # Remover regra
        removed_rule = current_rules.pop(rule_index)

        # Aplicar
        client.update_l3_firewall_rules(network_id, current_rules)

        return ConfigResult(
            success=True,
            action=ConfigAction.DELETE,
            resource_type="firewall",
            resource_id=network_id,
            message=f"Regra de firewall removida: {removed_rule.get('comment', 'sem comentario')}",
            backup_path=backup_path,
            changes={"removed_rule": removed_rule}
        )

    except APIError as e:
        logger.error(f"Erro ao remover regra de firewall: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.DELETE,
            resource_type="firewall",
            resource_id=network_id,
            message="Falha ao remover regra de firewall",
            error=str(e)
        )


# ==================== Switch ACL Configuration ====================

def add_switch_acl(
    network_id: str,
    policy: str,
    protocol: str,
    src_cidr: str,
    src_port: str,
    dest_cidr: str,
    dest_port: str,
    vlan: str = "any",
    comment: Optional[str] = None,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None
) -> ConfigResult:
    """
    Adiciona uma regra de ACL de switch.

    Args:
        network_id: ID da network
        policy: allow ou deny
        protocol: tcp, udp, ou any
        src_cidr: CIDR de origem
        src_port: Porta de origem
        dest_cidr: CIDR de destino
        dest_port: Porta de destino
        vlan: VLAN ID ou "any"
        comment: Comentario descritivo
        backup: Fazer backup antes de aplicar
        client_name: Nome do cliente para backup
        client: Cliente Meraki (opcional)

    Returns:
        ConfigResult com resultado da operacao
    """
    client = client or get_client()
    backup_path = None

    try:
        # Backup
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "acl", client)

        # Obter ACLs atuais
        current_acls = client.get_switch_acls(network_id)
        current_rules = current_acls.get("rules", [])

        # Criar nova regra
        new_rule = {
            "policy": policy,
            "ipVersion": "ipv4",
            "protocol": protocol,
            "srcCidr": src_cidr,
            "srcPort": src_port,
            "destCidr": dest_cidr,
            "destPort": dest_port,
            "vlan": vlan
        }
        if comment:
            new_rule["comment"] = comment

        # Adicionar regra
        current_rules.append(new_rule)

        # Aplicar
        client.update_switch_acls(network_id, current_rules)

        return ConfigResult(
            success=True,
            action=ConfigAction.CREATE,
            resource_type="acl",
            resource_id=network_id,
            message=f"ACL adicionada: {policy} {protocol} {src_cidr}:{src_port} -> {dest_cidr}:{dest_port}",
            backup_path=backup_path,
            changes=new_rule
        )

    except APIError as e:
        logger.error(f"Erro ao adicionar ACL: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.CREATE,
            resource_type="acl",
            resource_id=network_id,
            message="Falha ao adicionar ACL",
            error=str(e)
        )


# ==================== Switch Port Configuration ====================

@dataclass
class SwitchPortPreflight:
    """Result of a switch port writeability pre-flight check."""
    serial: str
    total_ports: int
    writable_ports: list[str]
    read_only_ports: list[dict]  # [{"portId": "4", "error": "Peer SGT capable is read-only"}]
    has_sgt_restriction: bool
    writable_ratio: float  # 0.0 to 1.0

    @property
    def fully_writable(self) -> bool:
        return len(self.read_only_ports) == 0

    @property
    def fully_locked(self) -> bool:
        return len(self.writable_ports) == 0

    def summary(self) -> str:
        if self.fully_writable:
            return f"All {self.total_ports} ports are writable via API."
        if self.fully_locked:
            return (
                f"ALL {self.total_ports} ports are READ-ONLY. "
                "TrustSec/SGT policy prevents API modifications."
            )
        ro_ids = [p["portId"] for p in self.read_only_ports]
        return (
            f"{len(self.writable_ports)}/{self.total_ports} ports writable, "
            f"{len(self.read_only_ports)} read-only (SGT). "
            f"Writable: {self.writable_ports}. "
            f"Read-only: {ro_ids}."
        )

    def is_port_writable(self, port_id: str) -> bool:
        return port_id in self.writable_ports


def check_switch_port_writeability(
    serial: str,
    client: Optional[MerakiClient] = None
) -> SwitchPortPreflight:
    """
    Pre-flight check: probe which switch ports are writable vs read-only.

    Some Catalyst switches (e.g. C9300) with Cisco ISE/TrustSec integration
    have ports locked as read-only via SGT peering. The Meraki Dashboard API
    returns "Peer SGT capable is read-only" when attempting to modify them.

    This function probes each port with a no-op name write to detect the
    restriction before the user attempts a real change.

    Args:
        serial: Switch serial number
        client: MerakiClient instance (optional, uses default)

    Returns:
        SwitchPortPreflight with writeability map
    """
    import requests

    client = client or get_client()
    api_key = client.api_key

    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json",
    }

    # Get all ports
    r = requests.get(
        f"https://api.meraki.com/api/v1/devices/{serial}/switch/ports",
        headers=headers,
    )
    r.raise_for_status()
    ports = r.json()

    writable = []
    read_only = []
    has_sgt = False

    for port in ports:
        pid = port["portId"]
        current_name = port.get("name", "")

        # Probe: try to set name back to itself (no actual change).
        # Always send the original value to avoid unintended modifications.
        probe = requests.put(
            f"https://api.meraki.com/api/v1/devices/{serial}/switch/ports/{pid}",
            headers=headers,
            json={"name": current_name},
        )

        if probe.status_code == 200:
            writable.append(pid)
        else:
            errors = probe.json().get("errors", [probe.text])
            error_msg = errors[0] if errors else "Unknown error"
            read_only.append({"portId": pid, "error": error_msg})
            if "SGT" in error_msg or "read-only" in error_msg.lower():
                has_sgt = True

    total = len(ports)
    ratio = len(writable) / total if total > 0 else 0.0

    result = SwitchPortPreflight(
        serial=serial,
        total_ports=total,
        writable_ports=writable,
        read_only_ports=read_only,
        has_sgt_restriction=has_sgt,
        writable_ratio=ratio,
    )

    logger.info(
        f"Switch {_mask_serial(serial)} preflight: {len(writable)}/{total} writable, "
        f"SGT restriction: {has_sgt}"
    )

    return result


def update_switch_port(
    serial: str,
    port_id: str,
    preflight: Optional[SwitchPortPreflight] = None,
    client: Optional[MerakiClient] = None,
    **kwargs,
) -> ConfigResult:
    """
    Update a switch port with pre-flight SGT/read-only check.

    Args:
        serial: Switch serial number
        port_id: Port ID to update
        preflight: Optional pre-computed preflight result
        client: MerakiClient instance (optional)
        **kwargs: Port fields to update (name, vlan, type, enabled, etc.)

    Returns:
        ConfigResult with outcome
    """
    client = client or get_client()

    # Run preflight if not provided
    if preflight is None:
        logger.info(f"Running preflight check for switch {_mask_serial(serial)}...")
        preflight = check_switch_port_writeability(serial, client)

    # Check if target port is writable
    if not preflight.is_port_writable(port_id):
        ro_entry = next(
            (p for p in preflight.read_only_ports if p["portId"] == port_id),
            None,
        )
        error_detail = ro_entry["error"] if ro_entry else "Port is read-only"

        return ConfigResult(
            success=False,
            action=ConfigAction.UPDATE,
            resource_type="switch_port",
            resource_id=f"{serial}/port_{port_id}",
            message=(
                f"Port {port_id} is READ-ONLY: {error_detail}. "
                f"This switch has TrustSec/SGT restrictions. "
                f"Writable ports: {preflight.writable_ports}"
            ),
            error=error_detail,
        )

    # Port is writable — apply change
    try:
        import requests

        headers = {
            "X-Cisco-Meraki-API-Key": client.api_key,
            "Content-Type": "application/json",
        }
        r = requests.put(
            f"https://api.meraki.com/api/v1/devices/{serial}/switch/ports/{port_id}",
            headers=headers,
            json=kwargs,
        )
        r.raise_for_status()

        return ConfigResult(
            success=True,
            action=ConfigAction.UPDATE,
            resource_type="switch_port",
            resource_id=f"{serial}/port_{port_id}",
            message=f"Port {port_id} updated successfully",
            changes=kwargs,
        )

    except Exception as e:
        logger.error(f"Failed to update port {port_id}: {e}")
        return ConfigResult(
            success=False,
            action=ConfigAction.UPDATE,
            resource_type="switch_port",
            resource_id=f"{serial}/port_{port_id}",
            message=f"Failed to update port {port_id}",
            error=str(e),
        )


# ==================== Helpers ====================

def validate_config_params(
    network_id: str,
    client: Optional[MerakiClient] = None
) -> tuple[bool, str]:
    """
    Valida se a network suporta configuracao.

    Args:
        network_id: ID da network
        client: Cliente Meraki (opcional)

    Returns:
        Tupla (valido: bool, mensagem: str)
    """
    client = client or get_client()

    try:
        network = client.get_network(network_id)
        return True, f"Network validada: {network.get('name')}"
    except APIError as e:
        return False, f"Network invalida: {e}"


# ==================== Task Executor Support Functions (Story 7.4) ====================


def detect_catalyst_mode(
    serial: str,
    client: Optional[MerakiClient] = None,
) -> dict:
    """
    Detect Catalyst switch management mode.

    Queries device info to determine if it's native Meraki, managed, or monitored.
    Monitored mode blocks write operations.

    Args:
        serial: Device serial number
        client: MerakiClient instance (optional, uses default)

    Returns:
        Dict with serial, mode, writable, and optional error
    """
    try:
        client = client or get_client()
        api_key = client.api_key
        headers = {
            "X-Cisco-Meraki-API-Key": api_key,
            "Content-Type": "application/json",
        }

        r = requests.get(
            f"https://api.meraki.com/api/v1/devices/{serial}",
            headers=headers,
        )
        r.raise_for_status()
        device = r.json()

        model = device.get("model", "").upper()
        firmware = device.get("firmware", "")

        # Classification logic
        if model.startswith("C9") or model.startswith("CAT"):
            # Catalyst models
            if "monitor" in firmware.lower() or device.get("tags", []) and "monitor-only" in device.get("tags", []):
                mode = "monitored"
                writable = False
            else:
                mode = "managed"
                writable = True
        else:
            mode = "native_meraki"
            writable = True

        return {"serial": serial, "mode": mode, "writable": writable}

    except Exception as exc:
        logger.warning(f"detect_catalyst_mode failed for {_mask_serial(serial)}: {exc}")
        return {"serial": serial, "mode": "unknown", "writable": False, "error": str(exc)}


def sgt_preflight_check(
    serial: str,
    client: Optional[MerakiClient] = None,
) -> dict:
    """
    SGT preflight check — wrapper over check_switch_port_writeability.

    Returns a simplified dict with writeability summary.

    Args:
        serial: Switch serial number
        client: MerakiClient instance (optional, uses default)

    Returns:
        Dict with serial, has_sgt_restriction, writable/read-only counts, ratio
    """
    try:
        preflight = check_switch_port_writeability(serial, client=client)

        result = {
            "serial": serial,
            "has_sgt_restriction": preflight.has_sgt_restriction,
            "writable_ports": len(preflight.writable_ports),
            "read_only_ports": len(preflight.read_only_ports),
            "writable_ratio": preflight.writable_ratio,
        }

        if preflight.has_sgt_restriction and preflight.writable_ratio < 0.5:
            result["warning"] = "Most ports are SGT-locked"

        return result

    except Exception as exc:
        logger.warning(f"sgt_preflight_check failed for {_mask_serial(serial)}: {exc}")
        return {
            "serial": serial,
            "has_sgt_restriction": False,
            "writable_ports": 0,
            "read_only_ports": 0,
            "writable_ratio": 0.0,
            "error": str(exc),
        }


def check_license(
    serial: str,
    client: Optional[MerakiClient] = None,
) -> dict:
    """
    Check device license level.

    Args:
        serial: Device serial number
        client: MerakiClient instance (optional, uses default)

    Returns:
        Dict with serial, license_type, features_available
    """
    try:
        client = client or get_client()
        api_key = client.api_key
        org_id = client.org_id if hasattr(client, "org_id") else None

        if not org_id:
            return {
                "serial": serial,
                "license_type": "unknown",
                "features_available": [],
                "error": "No org_id available",
            }

        headers = {
            "X-Cisco-Meraki-API-Key": api_key,
            "Content-Type": "application/json",
        }

        r = requests.get(
            f"https://api.meraki.com/api/v1/organizations/{org_id}/licensing/coterm/licenses",
            headers=headers,
        )

        if r.status_code == 200:
            licenses = r.json()
            # Find license matching this device
            device_license = None
            for lic in licenses:
                counts = lic.get("counts", [])
                for count in counts:
                    if serial in str(count.get("model", "")):
                        device_license = lic
                        break

            if device_license:
                edition = device_license.get("editions", [{}])[0].get("edition", "standard").lower()
                if "enterprise" in edition:
                    license_type = "enterprise"
                elif "advanced" in edition:
                    license_type = "advanced"
                else:
                    license_type = "standard"

                features = [e.get("edition", "") for e in device_license.get("editions", [])]
                return {
                    "serial": serial,
                    "license_type": license_type,
                    "features_available": features,
                }

        return {
            "serial": serial,
            "license_type": "unknown",
            "features_available": [],
        }

    except Exception as exc:
        logger.warning(f"check_license failed for {_mask_serial(serial)}: {exc}")
        return {
            "serial": serial,
            "license_type": "unknown",
            "features_available": [],
            "error": str(exc),
        }


def backup_current_state(
    resource_type: str,
    targets: dict,
    client_name: str,
    client: Optional[MerakiClient] = None,
) -> dict:
    """
    Generic backup wrapper over backup_config.

    Args:
        resource_type: Type of resource (network, ssid, vlan, firewall, switch_acl)
        targets: Target parameters (e.g., {"network_id": "N_123"})
        client_name: Client name for backup directory
        client: MerakiClient instance (optional)

    Returns:
        Dict with backup_path, resource_type, timestamp, targets
    """
    from datetime import datetime as _dt

    network_id = targets.get("network_id", "unknown")

    try:
        backup_path = backup_config(
            network_id=network_id,
            client_name=client_name,
            resource_type=resource_type,
            client=client,
        )

        return {
            "backup_path": str(backup_path),
            "resource_type": resource_type,
            "timestamp": _dt.now().isoformat(),
            "targets": targets,
        }
    except Exception as exc:
        logger.warning(f"backup_current_state failed: {exc}")
        return {
            "backup_path": "",
            "resource_type": resource_type,
            "timestamp": _dt.now().isoformat(),
            "targets": targets,
            "error": str(exc),
        }


if __name__ == "__main__":
    # Teste rapido
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    try:
        # Listar redes disponiveis
        client = get_client()
        orgs = client.get_organizations()

        if not orgs:
            print("Nenhuma organizacao encontrada")
            sys.exit(1)

        org_id = orgs[0]["id"]
        networks = client.get_networks(org_id)

        print(f"\n=== Networks Disponiveis ===")
        for i, net in enumerate(networks):
            print(f"{i}: {net['name']} ({net['id']})")

        print("\nPara testar configuracoes, use:")
        print("  python -m scripts.config <network_id>")

    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
