"""
MCP Tool: meraki_list_networks

Lista networks de uma organização Meraki.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


async def meraki_list_networks(
    org_id: Optional[str] = None,
    profile: str = "default",
    include_devices: bool = False,
) -> dict[str, Any]:
    """
    Lista todas as networks de uma organização Meraki.

    Args:
        org_id: Organization ID (se None, usa o do profile)
        profile: Nome do profile de credenciais (default: "default")
        include_devices: Se True, inclui contagem de devices por network

    Returns:
        dict com lista de networks:
        {
            "success": bool,
            "org_id": str,
            "org_name": str,
            "networks_count": int,
            "networks": [
                {
                    "id": str,
                    "name": str,
                    "type": str,
                    "tags": list,
                    "timezone": str,
                    "devices_count": int | None
                },
                ...
            ]
        }

    Example:
        result = await meraki_list_networks(profile="acme-profile")
        for net in result["networks"]:
            print(f"{net['name']}: {net['type']}")
    """
    try:
        # Import dos módulos do projeto
        from scripts.api import MerakiClient

        # Criar cliente API
        api = MerakiClient(profile)

        # Usar org_id do profile se não especificado
        target_org_id = org_id or api.org_id

        # Obter informações da organização
        logger.info(f"Fetching networks for org {target_org_id}")

        # Listar networks
        networks_raw = api.dashboard.organizations.getOrganizationNetworks(target_org_id)

        # Processar networks
        networks = []
        for net in networks_raw:
            network_info = {
                "id": net.get("id"),
                "name": net.get("name"),
                "type": net.get("productTypes", []),
                "tags": net.get("tags", []),
                "timezone": net.get("timeZone"),
                "notes": net.get("notes", ""),
            }

            # Incluir contagem de devices se solicitado
            if include_devices:
                try:
                    devices = api.dashboard.networks.getNetworkDevices(net["id"])
                    network_info["devices_count"] = len(devices)
                except Exception:
                    network_info["devices_count"] = None

            networks.append(network_info)

        # Obter nome da organização
        try:
            org_info = api.dashboard.organizations.getOrganization(target_org_id)
            org_name = org_info.get("name", "Unknown")
        except Exception:
            org_name = "Unknown"

        response = {
            "success": True,
            "org_id": target_org_id,
            "org_name": org_name,
            "networks_count": len(networks),
            "networks": networks,
        }

        logger.info(f"Found {len(networks)} networks in {org_name}")
        return response

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/ modules are properly installed",
        }

    except Exception as e:
        logger.error(f"List networks failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_list_networks",
    "description": "List all networks in a Meraki organization with their types, tags, and optionally device counts.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "org_id": {
                "type": "string",
                "description": "Organization ID. If not provided, uses the one from the profile.",
            },
            "profile": {
                "type": "string",
                "description": "Credentials profile name from ~/.meraki/credentials",
                "default": "default",
            },
            "include_devices": {
                "type": "boolean",
                "description": "If true, includes device count for each network (slower)",
                "default": False,
            },
        },
        "required": [],
    },
}
