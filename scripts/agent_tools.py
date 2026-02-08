"""
Agent tool definitions for OpenAI function-calling.

Maps each agent's capabilities to structured tool schemas with:
- Parameter types and descriptions
- Required fields
- Enum constraints
- Safety classifications

All tools map to functions in FUNCTION_REGISTRY (agent_router.py).
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# ==================== Safety Classification ====================


class SafetyLevel(Enum):
    """Safety classification for tool calls."""

    SAFE = "safe"  # Read-only, no side effects
    MODERATE = "moderate"  # Reversible changes
    DANGEROUS = "dangerous"  # Disruptive, hard to reverse


# Tool safety classifications
TOOL_SAFETY = {
    # Safe (read-only)
    "full_discovery": SafetyLevel.SAFE,
    "discover_networks": SafetyLevel.SAFE,
    "discover_devices": SafetyLevel.SAFE,
    "discover_ssids": SafetyLevel.SAFE,
    "discover_vlans": SafetyLevel.SAFE,
    "discover_firewall_rules": SafetyLevel.SAFE,
    "discover_switch_ports": SafetyLevel.SAFE,
    "discover_switch_acls": SafetyLevel.SAFE,
    "find_issues": SafetyLevel.SAFE,
    "generate_suggestions": SafetyLevel.SAFE,
    "save_snapshot": SafetyLevel.SAFE,
    "compare_snapshots": SafetyLevel.SAFE,
    "list_workflows": SafetyLevel.SAFE,
    "generate_discovery_report": SafetyLevel.SAFE,
    # Moderate (reversible)
    "configure_ssid": SafetyLevel.MODERATE,
    "enable_ssid": SafetyLevel.MODERATE,
    "disable_ssid": SafetyLevel.MODERATE,
    "create_vlan": SafetyLevel.MODERATE,
    "update_vlan": SafetyLevel.MODERATE,
    "backup_config": SafetyLevel.SAFE,
    # Dangerous (disruptive)
    "delete_vlan": SafetyLevel.DANGEROUS,
    "add_firewall_rule": SafetyLevel.DANGEROUS,
    "remove_firewall_rule": SafetyLevel.DANGEROUS,
    "add_switch_acl": SafetyLevel.DANGEROUS,
    "rollback_config": SafetyLevel.MODERATE,
    # Workflow creation (safe - generates files only)
    "create_device_offline_handler": SafetyLevel.SAFE,
    "create_firmware_compliance_check": SafetyLevel.SAFE,
    "create_scheduled_report": SafetyLevel.SAFE,
    "create_security_alert_handler": SafetyLevel.SAFE,
    "save_workflow": SafetyLevel.SAFE,
    # Task executor support (Story 7.4)
    "detect_catalyst_mode": SafetyLevel.SAFE,
    "sgt_preflight_check": SafetyLevel.SAFE,
    "check_license": SafetyLevel.SAFE,
    "backup_current_state": SafetyLevel.SAFE,
}


def get_tool_safety(tool_name: str) -> SafetyLevel:
    """
    Get safety classification for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        SafetyLevel classification
    """
    return TOOL_SAFETY.get(tool_name, SafetyLevel.MODERATE)


def requires_confirmation(tool_name: str) -> bool:
    """
    Check if tool requires user confirmation.

    Args:
        tool_name: Name of the tool

    Returns:
        True if confirmation required
    """
    safety = get_tool_safety(tool_name)
    return safety in [SafetyLevel.MODERATE, SafetyLevel.DANGEROUS]


# ==================== Tool Definitions ====================

# Network Analyst Tools
NETWORK_ANALYST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "full_discovery",
            "description": "Run complete discovery of all networks, devices, SSIDs, VLANs, and firewall rules in the organization",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID (optional, uses profile default if not provided)",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_networks",
            "description": "Discover all networks in an organization",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID",
                    }
                },
                "required": ["org_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_devices",
            "description": "Discover all devices in a specific network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover devices from",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_ssids",
            "description": "Discover all SSIDs (wireless networks) in a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover SSIDs from",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_vlans",
            "description": "Discover all VLANs in a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover VLANs from",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_firewall_rules",
            "description": "Discover L3 and L7 firewall rules in a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover firewall rules from",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_switch_ports",
            "description": "Discover port configurations of a switch",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Serial number of the switch",
                    }
                },
                "required": ["serial"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_switch_acls",
            "description": "Discover switch ACL (Access Control List) rules in a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover switch ACLs from",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_issues",
            "description": "Analyze discovery results to identify network issues (offline devices, insecure SSIDs, etc)",
            "parameters": {
                "type": "object",
                "properties": {
                    "discovery_result": {
                        "type": "object",
                        "description": "Discovery result object from full_discovery",
                    }
                },
                "required": ["discovery_result"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_suggestions",
            "description": "Generate improvement suggestions based on identified issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "description": "List of issues from find_issues",
                        "items": {"type": "object"},
                    }
                },
                "required": ["issues"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_snapshot",
            "description": "Save discovery results as a snapshot for future comparison",
            "parameters": {
                "type": "object",
                "properties": {
                    "discovery_result": {
                        "type": "object",
                        "description": "Discovery result to save",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for organizing snapshots",
                    },
                },
                "required": ["discovery_result", "client_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_snapshots",
            "description": "Compare two discovery snapshots to identify changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_snapshot": {
                        "type": "object",
                        "description": "Older snapshot to compare",
                    },
                    "new_snapshot": {
                        "type": "object",
                        "description": "Newer snapshot to compare",
                    },
                },
                "required": ["old_snapshot", "new_snapshot"],
                "additionalProperties": False,
            },
        },
    },
]

# Meraki Specialist Tools
MERAKI_SPECIALIST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "configure_ssid",
            "description": "Configure SSID (wireless network) settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "ssid_number": {
                        "type": "integer",
                        "description": "SSID number (0-14)",
                        "minimum": 0,
                        "maximum": 14,
                    },
                    "name": {
                        "type": "string",
                        "description": "SSID name (optional)",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable or disable SSID (optional)",
                    },
                    "auth_mode": {
                        "type": "string",
                        "enum": ["open", "psk", "8021x-radius"],
                        "description": "Authentication mode (optional)",
                    },
                    "psk": {
                        "type": "string",
                        "description": "Pre-shared key if auth_mode is psk (optional)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "ssid_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enable_ssid",
            "description": "Enable a wireless SSID in the network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "ssid_number": {
                        "type": "integer",
                        "description": "SSID number (0-14)",
                        "minimum": 0,
                        "maximum": 14,
                    },
                    "name": {"type": "string", "description": "SSID name"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "ssid_number", "name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "disable_ssid",
            "description": "Disable a wireless SSID in the network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "ssid_number": {
                        "type": "integer",
                        "description": "SSID number (0-14)",
                        "minimum": 0,
                        "maximum": 14,
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "ssid_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_vlan",
            "description": "Create a new VLAN in a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "vlan_id": {"type": "integer", "description": "VLAN ID number"},
                    "name": {"type": "string", "description": "VLAN name"},
                    "subnet": {
                        "type": "string",
                        "description": "Subnet in CIDR format (e.g., 192.168.10.0/24)",
                    },
                    "appliance_ip": {
                        "type": "string",
                        "description": "Gateway IP address (e.g., 192.168.10.1)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "vlan_id", "name", "subnet", "appliance_ip"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_vlan",
            "description": "Update an existing VLAN configuration including DHCP and DNS settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "vlan_id": {"type": "string", "description": "VLAN ID"},
                    "name": {"type": "string", "description": "VLAN name (optional)"},
                    "subnet": {"type": "string", "description": "Subnet CIDR (optional)"},
                    "appliance_ip": {"type": "string", "description": "Gateway IP (optional)"},
                    "dhcpHandling": {
                        "type": "string",
                        "description": "DHCP handling mode",
                        "enum": ["Run a DHCP server", "Relay DHCP to another server", "Do not respond to DHCP requests"],
                    },
                    "dnsNameservers": {
                        "type": "string",
                        "description": "DNS nameservers (e.g., 'upstream_dns', 'google_dns', or custom IPs newline-separated)",
                    },
                    "dhcpOptions": {
                        "type": "array",
                        "description": "DHCP options list",
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "type": {"type": "string"},
                                "value": {"type": "string"},
                            },
                        },
                    },
                    "reservedIpRanges": {
                        "type": "array",
                        "description": "Reserved IP ranges for DHCP",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "string"},
                                "end": {"type": "string"},
                                "comment": {"type": "string"},
                            },
                        },
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "vlan_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_vlan",
            "description": "Delete a VLAN (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "vlan_id": {"type": "string", "description": "VLAN ID to delete"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "vlan_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_firewall_rule",
            "description": "Add a Layer 3 firewall rule (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "policy": {
                        "type": "string",
                        "enum": ["allow", "deny"],
                        "description": "Allow or deny traffic",
                    },
                    "protocol": {
                        "type": "string",
                        "enum": ["tcp", "udp", "icmp", "any"],
                        "description": "Protocol to match",
                    },
                    "src_cidr": {
                        "type": "string",
                        "description": "Source CIDR (e.g., 'any' or '192.168.1.0/24')",
                    },
                    "dest_cidr": {
                        "type": "string",
                        "description": "Destination CIDR (e.g., 'any' or '10.0.0.0/8')",
                    },
                    "dest_port": {
                        "type": "string",
                        "description": "Destination port (e.g., '80', '443', 'any')",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Descriptive comment for the rule",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": [
                    "network_id",
                    "policy",
                    "protocol",
                    "src_cidr",
                    "dest_cidr",
                    "dest_port",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_firewall_rule",
            "description": "Remove a Layer 3 firewall rule by index (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rule_index": {
                        "type": "integer",
                        "description": "Index of rule to remove (0-based)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "rule_index"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_switch_acl",
            "description": "Add a switch ACL rule (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "policy": {
                        "type": "string",
                        "enum": ["allow", "deny"],
                        "description": "Allow or deny traffic",
                    },
                    "protocol": {
                        "type": "string",
                        "enum": ["tcp", "udp", "any"],
                        "description": "Protocol to match",
                    },
                    "src_cidr": {
                        "type": "string",
                        "description": "Source CIDR (e.g., '192.168.1.0/24')",
                    },
                    "src_port": {
                        "type": "string",
                        "description": "Source port (e.g., 'any', '443')",
                    },
                    "dest_cidr": {
                        "type": "string",
                        "description": "Destination CIDR (e.g., '10.0.0.0/8')",
                    },
                    "dest_port": {
                        "type": "string",
                        "description": "Destination port (e.g., 'any', '80')",
                    },
                    "vlan": {
                        "type": "string",
                        "description": "VLAN ID or 'any' (default: 'any')",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Descriptive comment for the rule",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": [
                    "network_id",
                    "policy",
                    "protocol",
                    "src_cidr",
                    "src_port",
                    "dest_cidr",
                    "dest_port",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backup_config",
            "description": "Backup current network configuration before making changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup organization",
                    },
                    "resource_type": {
                        "type": "string",
                        "enum": ["full", "ssid", "vlan", "firewall", "acl"],
                        "description": "Type of resource to backup (default: 'full')",
                    },
                },
                "required": ["network_id", "client_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_config",
            "description": "Restore configuration from a backup file",
            "parameters": {
                "type": "object",
                "properties": {
                    "backup_path": {
                        "type": "string",
                        "description": "Path to backup file",
                    }
                },
                "required": ["backup_path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_catalyst_mode",
            "description": "Detect Catalyst switch management mode (native_meraki, managed, or monitored). Monitored mode blocks write operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Device serial number",
                    }
                },
                "required": ["serial"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sgt_preflight_check",
            "description": "Check switch port writeability for SGT/TrustSec restrictions. Returns count of writable vs read-only ports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Switch serial number",
                    }
                },
                "required": ["serial"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_license",
            "description": "Check device license level (enterprise, advanced, standard) and available features.",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Device serial number",
                    }
                },
                "required": ["serial"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backup_current_state",
            "description": "Create a backup of current configuration state before making changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "Type of resource to backup",
                        "enum": ["network", "ssid", "vlan", "firewall", "switch_acl"],
                    },
                    "targets": {
                        "type": "object",
                        "description": "Target parameters (e.g., network_id, vlan_id)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup directory",
                    },
                },
                "required": ["resource_type", "targets", "client_name"],
                "additionalProperties": False,
            },
        },
    },
]

# Workflow Creator Tools
WORKFLOW_CREATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_device_offline_handler",
            "description": "Create workflow to handle device offline events",
            "parameters": {
                "type": "object",
                "properties": {
                    "slack_channel": {
                        "type": "string",
                        "description": "Slack channel for notifications (e.g., '#network-alerts')",
                    },
                    "wait_minutes": {
                        "type": "integer",
                        "description": "Minutes to wait before notifying (default: 5)",
                    },
                },
                "required": ["slack_channel"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_firmware_compliance_check",
            "description": "Create workflow to check firmware compliance",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_version": {
                        "type": "string",
                        "description": "Target firmware version",
                    },
                    "email_recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses to receive compliance reports",
                    },
                },
                "required": ["target_version", "email_recipients"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_scheduled_report",
            "description": "Create workflow for scheduled reports",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["discovery", "compliance", "capacity"],
                        "description": "Type of report to generate",
                    },
                    "schedule_cron": {
                        "type": "string",
                        "description": "Cron expression for schedule (e.g., '0 8 * * 1' for Mondays at 8am)",
                    },
                    "email_recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses to receive reports",
                    },
                },
                "required": ["report_type", "schedule_cron", "email_recipients"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_security_alert_handler",
            "description": "Create workflow to handle security alerts",
            "parameters": {
                "type": "object",
                "properties": {
                    "slack_channel": {
                        "type": "string",
                        "description": "Slack channel for security alerts",
                    },
                    "pagerduty_enabled": {
                        "type": "boolean",
                        "description": "Whether to create PagerDuty incidents (default: false)",
                    },
                },
                "required": ["slack_channel"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_workflow",
            "description": "Save workflow JSON to client directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "object",
                        "description": "Workflow object to save",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for organizing workflows",
                    },
                },
                "required": ["workflow", "client_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_workflows",
            "description": "List all workflows for a client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "Client name",
                    }
                },
                "required": ["client_name"],
                "additionalProperties": False,
            },
        },
    },
]

# ==================== Tool Registry ====================

AGENT_TOOLS = {
    "network-analyst": NETWORK_ANALYST_TOOLS,
    "meraki-specialist": MERAKI_SPECIALIST_TOOLS,
    "workflow-creator": WORKFLOW_CREATOR_TOOLS,
}


def get_agent_tools(agent_name: str) -> list[dict]:
    """
    Get tool definitions for an agent.

    Args:
        agent_name: Name of agent (network-analyst, meraki-specialist, workflow-creator)

    Returns:
        List of tool definitions in OpenAI function-calling format

    Raises:
        ValueError: If agent not found
    """
    if agent_name not in AGENT_TOOLS:
        available = ", ".join(AGENT_TOOLS.keys())
        raise ValueError(
            f"Agent '{agent_name}' not found. Available: {available}"
        )

    tools = AGENT_TOOLS[agent_name]
    logger.debug(f"Retrieved {len(tools)} tools for agent: {agent_name}")
    return tools


def validate_tool_schema(tool: dict) -> tuple[bool, Optional[str]]:
    """
    Validate that tool definition follows OpenAI function-calling schema.

    Args:
        tool: Tool definition to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required top-level fields
    if "type" not in tool or tool["type"] != "function":
        return False, "Tool must have type='function'"

    if "function" not in tool:
        return False, "Tool must have 'function' field"

    func = tool["function"]

    # Check function fields
    if "name" not in func:
        return False, "Function must have 'name' field"

    if "description" not in func:
        return False, "Function must have 'description' field"

    if "parameters" not in func:
        return False, "Function must have 'parameters' field"

    params = func["parameters"]

    # Check parameters schema
    if "type" not in params or params["type"] != "object":
        return False, "Parameters must have type='object'"

    if "properties" not in params:
        return False, "Parameters must have 'properties' field"

    if "required" not in params:
        return False, "Parameters must have 'required' field"

    # Check additionalProperties is False for strict schema
    if params.get("additionalProperties", True) is not False:
        return False, "Parameters should have additionalProperties=False for strict validation"

    return True, None


# ==================== Main ====================

if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)s: %(message)s"
    )

    try:
        print("\n=== Testing agent_tools.py ===\n")

        # Test 1: Get tools for each agent
        print("1. Getting tools for each agent...")
        for agent in ["network-analyst", "meraki-specialist", "workflow-creator"]:
            tools = get_agent_tools(agent)
            print(f"  {agent}: {len(tools)} tools")

        # Test 2: Validate all tool schemas
        print("\n2. Validating tool schemas...")
        all_valid = True
        for agent_name, tools in AGENT_TOOLS.items():
            for tool in tools:
                valid, error = validate_tool_schema(tool)
                if not valid:
                    print(f"  ERROR in {agent_name}/{tool.get('function', {}).get('name')}: {error}")
                    all_valid = False

        if all_valid:
            print("  All tool schemas valid!")
        else:
            raise ValueError("Tool schema validation failed")

        # Test 3: Check safety classifications
        print("\n3. Checking safety classifications...")
        for tool_name, safety in TOOL_SAFETY.items():
            print(f"  {tool_name}: {safety.value}")

        # Test 4: Sample tool JSON
        print("\n4. Sample tool definition (full_discovery):")
        sample_tool = NETWORK_ANALYST_TOOLS[0]
        print(json.dumps(sample_tool, indent=2)[:500] + "...")

        print("\n=== All tests passed ===\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
