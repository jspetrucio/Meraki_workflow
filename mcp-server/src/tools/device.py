"""
MCP Tool: meraki_get_device_status

Obtém status detalhado de um device Meraki.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


async def meraki_get_device_status(
    serial: str,
    profile: str = "default",
    include_clients: bool = False,
    include_uplinks: bool = True,
) -> dict[str, Any]:
    """
    Obtém status detalhado de um device Meraki.

    Args:
        serial: Serial number do device (ex: "Q2XX-XXXX-XXXX")
        profile: Profile de credenciais (default: "default")
        include_clients: Se True, inclui lista de clientes conectados
        include_uplinks: Se True, inclui status dos uplinks

    Returns:
        dict com status do device:
        {
            "success": bool,
            "device": {
                "serial": str,
                "name": str,
                "model": str,
                "mac": str,
                "status": str,
                "network_id": str,
                "network_name": str,
                "lan_ip": str,
                "public_ip": str,
                "firmware": str,
                "last_reported": str,
                "tags": list
            },
            "uplinks": [...] | None,
            "clients_count": int | None,
            "clients": [...] | None
        }

    Example:
        result = await meraki_get_device_status(
            serial="Q2XX-XXXX-XXXX",
            include_clients=True
        )
        print(f"Device {result['device']['name']}: {result['device']['status']}")
    """
    try:
        # Import dos módulos do projeto
        from scripts.api import MerakiClient

        logger.info(f"Getting status for device {serial}")

        # Criar cliente API
        api = MerakiClient(profile)

        # Obter informações do device
        device = api.dashboard.devices.getDevice(serial)

        # Obter status do device na organização
        try:
            org_devices = api.dashboard.organizations.getOrganizationDevicesStatuses(
                api.org_id,
                serials=[serial]
            )
            device_status = org_devices[0] if org_devices else {}
        except Exception:
            device_status = {}

        # Obter informações da network
        network_id = device.get("networkId")
        network_name = "Unknown"
        if network_id:
            try:
                network = api.dashboard.networks.getNetwork(network_id)
                network_name = network.get("name", "Unknown")
            except Exception:
                pass

        # Formatar resposta do device
        device_info = {
            "serial": device.get("serial"),
            "name": device.get("name"),
            "model": device.get("model"),
            "mac": device.get("mac"),
            "status": device_status.get("status", "unknown"),
            "network_id": network_id,
            "network_name": network_name,
            "lan_ip": device.get("lanIp"),
            "public_ip": device_status.get("publicIp"),
            "firmware": device.get("firmware"),
            "last_reported": device_status.get("lastReportedAt"),
            "tags": device.get("tags", []),
            "address": device.get("address"),
            "notes": device.get("notes"),
            "product_type": device_status.get("productType"),
        }

        response = {
            "success": True,
            "device": device_info,
            "uplinks": None,
            "clients_count": None,
            "clients": None,
        }

        # Obter uplinks se solicitado
        if include_uplinks:
            try:
                # Para MX/appliances
                if device.get("model", "").startswith("MX"):
                    uplinks = api.dashboard.appliance.getDeviceApplianceUplinksSettings(serial)
                    response["uplinks"] = uplinks.get("interfaces", [])
                # Para switches
                elif device.get("model", "").startswith("MS"):
                    uplinks = api.dashboard.switch.getDeviceSwitchPorts(serial)
                    # Filtrar apenas uplink ports
                    response["uplinks"] = [
                        p for p in uplinks
                        if p.get("type") == "trunk" or "uplink" in p.get("name", "").lower()
                    ][:5]  # Limitar a 5
                else:
                    response["uplinks"] = []
            except Exception as e:
                logger.warning(f"Could not get uplinks: {e}")
                response["uplinks"] = []

        # Obter clientes se solicitado
        if include_clients and network_id:
            try:
                # Obter clientes do device
                clients = api.dashboard.devices.getDeviceClients(
                    serial,
                    timespan=86400  # Últimas 24 horas
                )
                response["clients_count"] = len(clients)
                # Limitar detalhes a 20 clientes
                response["clients"] = [
                    {
                        "mac": c.get("mac"),
                        "ip": c.get("ip"),
                        "description": c.get("description"),
                        "vlan": c.get("vlan"),
                        "usage": c.get("usage", {}).get("sent", 0) + c.get("usage", {}).get("recv", 0),
                    }
                    for c in clients[:20]
                ]
            except Exception as e:
                logger.warning(f"Could not get clients: {e}")
                response["clients_count"] = 0
                response["clients"] = []

        logger.info(f"Device {serial} status: {device_info['status']}")
        return response

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/ modules are properly installed",
        }

    except Exception as e:
        logger.error(f"Get device status failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "serial": serial,
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_get_device_status",
    "description": "Get detailed status of a Meraki device including uplinks and optionally connected clients.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "serial": {
                "type": "string",
                "description": "Device serial number (e.g., 'Q2XX-XXXX-XXXX')",
            },
            "profile": {
                "type": "string",
                "description": "Credentials profile name",
                "default": "default",
            },
            "include_clients": {
                "type": "boolean",
                "description": "Include list of connected clients (may be slow)",
                "default": False,
            },
            "include_uplinks": {
                "type": "boolean",
                "description": "Include uplink status information",
                "default": True,
            },
        },
        "required": ["serial"],
    },
}
