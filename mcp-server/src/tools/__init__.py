"""
MCP Tools para Meraki Workflow.

Tools disponíveis:
- meraki_discover: Executa discovery completo da rede
- meraki_list_networks: Lista networks da organização
- meraki_configure: Aplica configurações (SSID, Firewall, VLAN)
- meraki_create_workflow: Cria workflow de template (Clone + Patch)
- meraki_report: Gera relatórios HTML/PDF
- meraki_get_device_status: Status detalhado de device
"""

from .discovery import meraki_discover, TOOL_SCHEMA as DISCOVER_SCHEMA
from .network import meraki_list_networks, TOOL_SCHEMA as NETWORK_SCHEMA
from .config import meraki_configure, TOOL_SCHEMA as CONFIG_SCHEMA
from .workflow import meraki_create_workflow, TOOL_SCHEMA as WORKFLOW_SCHEMA
from .report import meraki_report, TOOL_SCHEMA as REPORT_SCHEMA
from .device import meraki_get_device_status, TOOL_SCHEMA as DEVICE_SCHEMA

__all__ = [
    # Tools
    "meraki_discover",
    "meraki_list_networks",
    "meraki_configure",
    "meraki_create_workflow",
    "meraki_report",
    "meraki_get_device_status",
    # Schemas
    "DISCOVER_SCHEMA",
    "NETWORK_SCHEMA",
    "CONFIG_SCHEMA",
    "CONFIGURE_SCHEMA",  # Alias
    "WORKFLOW_SCHEMA",
    "REPORT_SCHEMA",
    "DEVICE_SCHEMA",
    "ALL_TOOL_SCHEMAS",
]

# Alias para compatibilidade
CONFIGURE_SCHEMA = CONFIG_SCHEMA

# Lista de todos os schemas para facilitar registro
ALL_TOOL_SCHEMAS = [
    DISCOVER_SCHEMA,
    NETWORK_SCHEMA,
    CONFIG_SCHEMA,
    WORKFLOW_SCHEMA,
    REPORT_SCHEMA,
    DEVICE_SCHEMA,
]
