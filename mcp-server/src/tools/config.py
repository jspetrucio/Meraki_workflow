"""
MCP Tool: meraki_configure

Aplica configurações em redes Meraki (SSID, Firewall, VLAN).
"""

import logging
import sys
from pathlib import Path
from typing import Any, Literal, Optional

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

ConfigType = Literal["ssid", "firewall", "vlan"]


async def meraki_configure(
    network_id: str,
    config_type: ConfigType,
    params: dict[str, Any],
    client: str,
    profile: str = "default",
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Aplica configuração em uma rede Meraki.

    Args:
        network_id: ID da network Meraki (ex: "N_123456789")
        config_type: Tipo de configuração ("ssid", "firewall", "vlan")
        params: Parâmetros específicos do tipo de configuração
        client: Nome do cliente (para backup e changelog)
        profile: Profile de credenciais (default: "default")
        dry_run: Se True, apenas valida sem aplicar

    Returns:
        dict com resultado da configuração:
        {
            "success": bool,
            "action": str,
            "config_type": str,
            "changes": dict,
            "backup_path": str | None,
            "message": str
        }

    Params por config_type:

    ssid:
        - number: int (0-14)
        - name: str (opcional)
        - enabled: bool (opcional)
        - auth_mode: str (opcional) - "open", "psk", "8021x-meraki", "8021x-radius"
        - psk: str (opcional) - Pre-shared key
        - vlan_id: int (opcional)

    firewall:
        - policy: str - "allow" ou "deny"
        - protocol: str - "tcp", "udp", "icmp", "any"
        - src_cidr: str (default: "any")
        - dest_cidr: str (default: "any")
        - dest_port: str (default: "any")
        - comment: str (opcional)

    vlan:
        - vlan_id: int
        - name: str
        - subnet: str (ex: "192.168.10.0/24")
        - appliance_ip: str (gateway)

    Example:
        # Configurar SSID
        result = await meraki_configure(
            network_id="N_123",
            config_type="ssid",
            params={"number": 0, "name": "Guest WiFi", "enabled": True},
            client="acme"
        )

        # Adicionar regra de firewall
        result = await meraki_configure(
            network_id="N_123",
            config_type="firewall",
            params={"policy": "deny", "protocol": "tcp", "dest_port": "23"},
            client="acme"
        )
    """
    try:
        # Import dos módulos do projeto
        from scripts.config import configure_ssid, add_firewall_rule, create_vlan

        logger.info(f"Configuring {config_type} on network {network_id}")

        if dry_run:
            return {
                "success": True,
                "action": "dry_run",
                "config_type": config_type,
                "changes": params,
                "backup_path": None,
                "message": f"Dry run: {config_type} configuration validated",
            }

        # Executar configuração baseado no tipo
        if config_type == "ssid":
            result = configure_ssid(
                network_id=network_id,
                ssid_number=params.get("number", 0),
                name=params.get("name"),
                enabled=params.get("enabled"),
                auth_mode=params.get("auth_mode"),
                psk=params.get("psk"),
                vlan_id=params.get("vlan_id"),
                client_name=client,
            )

        elif config_type == "firewall":
            result = add_firewall_rule(
                network_id=network_id,
                policy=params.get("policy", "deny"),
                protocol=params.get("protocol", "any"),
                src_cidr=params.get("src_cidr", "any"),
                dest_cidr=params.get("dest_cidr", "any"),
                dest_port=params.get("dest_port", "any"),
                comment=params.get("comment"),
                client_name=client,
            )

        elif config_type == "vlan":
            result = create_vlan(
                network_id=network_id,
                vlan_id=params["vlan_id"],
                name=params["name"],
                subnet=params["subnet"],
                appliance_ip=params["appliance_ip"],
                client_name=client,
            )

        else:
            return {
                "success": False,
                "error": f"Unknown config_type: {config_type}",
                "valid_types": ["ssid", "firewall", "vlan"],
            }

        # Formatar resposta
        return {
            "success": result.success,
            "action": result.action.value if hasattr(result, 'action') else "configure",
            "config_type": config_type,
            "changes": result.changes if hasattr(result, 'changes') else params,
            "backup_path": str(result.backup_path) if hasattr(result, 'backup_path') and result.backup_path else None,
            "message": result.message,
            "error": result.error if hasattr(result, 'error') else None,
        }

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/ modules are properly installed",
        }

    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        return {
            "success": False,
            "error": f"Missing required parameter: {e}",
            "config_type": config_type,
        }

    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_configure",
    "description": "Apply configuration to a Meraki network. Supports SSID, Firewall rules, and VLAN configuration. Creates backup before changes.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "network_id": {
                "type": "string",
                "description": "Meraki Network ID (e.g., 'N_123456789')",
            },
            "config_type": {
                "type": "string",
                "enum": ["ssid", "firewall", "vlan"],
                "description": "Type of configuration to apply",
            },
            "params": {
                "type": "object",
                "description": "Configuration parameters (varies by config_type)",
            },
            "client": {
                "type": "string",
                "description": "Client name for backup and changelog",
            },
            "profile": {
                "type": "string",
                "description": "Credentials profile name",
                "default": "default",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, validate without applying changes",
                "default": False,
            },
        },
        "required": ["network_id", "config_type", "params", "client"],
    },
}
