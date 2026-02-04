"""
MCP Tool: meraki_discover

Executa discovery completo de uma rede Meraki.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


async def meraki_discover(
    client: str,
    full: bool = True,
    save: bool = True,
    profile: str = "default",
) -> dict[str, Any]:
    """
    Executa discovery completo da rede Meraki.

    Args:
        client: Nome do cliente (ex: "acme")
        full: Se True, executa discovery completo. Se False, apenas resumo.
        save: Se True, salva snapshot em clients/{client}/discovery/
        profile: Nome do profile de credenciais (default: "default")

    Returns:
        dict com resultados do discovery:
        {
            "success": bool,
            "org_name": str,
            "networks_count": int,
            "devices_count": int,
            "devices_online": int,
            "devices_offline": int,
            "issues_count": int,
            "issues": [...],
            "suggestions": [...],
            "snapshot_path": str | None
        }

    Example:
        result = await meraki_discover(client="acme", full=True)
        print(f"Found {result['networks_count']} networks")
    """
    try:
        # Import dos módulos do projeto
        from scripts.api import MerakiClient
        from scripts.discovery import full_discovery, save_snapshot

        # Criar cliente API
        api = MerakiClient(profile)

        # Executar discovery
        logger.info(f"Starting discovery for client '{client}' with profile '{profile}'")
        result = full_discovery(api.org_id, api)

        # Preparar resposta
        response = {
            "success": True,
            "org_name": result.org_name,
            "org_id": api.org_id,
            "networks_count": len(result.networks),
            "devices_count": len(result.devices),
            "devices_online": sum(1 for d in result.devices if d.get("status") == "online"),
            "devices_offline": sum(1 for d in result.devices if d.get("status") != "online"),
            "issues_count": len(result.issues),
            "issues": result.issues[:10],  # Limitar para não sobrecarregar
            "suggestions_count": len(result.suggestions),
            "suggestions": result.suggestions[:5],
            "snapshot_path": None,
        }

        # Salvar snapshot se solicitado
        if save:
            path = save_snapshot(result, client)
            response["snapshot_path"] = str(path)
            logger.info(f"Snapshot saved to {path}")

        # Resumo para log
        logger.info(
            f"Discovery complete: {response['networks_count']} networks, "
            f"{response['devices_count']} devices ({response['devices_online']} online)"
        )

        return response

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/ modules are properly installed",
        }

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_discover",
    "description": "Execute complete network discovery for a Meraki organization. Returns network topology, device status, and identified issues.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "client": {
                "type": "string",
                "description": "Client name for organizing results (e.g., 'acme')",
            },
            "full": {
                "type": "boolean",
                "description": "If true, performs full discovery. If false, only summary.",
                "default": True,
            },
            "save": {
                "type": "boolean",
                "description": "If true, saves snapshot to clients/{client}/discovery/",
                "default": True,
            },
            "profile": {
                "type": "string",
                "description": "Credentials profile name from ~/.meraki/credentials",
                "default": "default",
            },
        },
        "required": ["client"],
    },
}
