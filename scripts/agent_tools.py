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
from typing import Optional

# Import SafetyLevel from safety module (canonical definition)
from scripts.safety import SafetyLevel

logger = logging.getLogger(__name__)

# ==================== Safety Classification ====================


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
    "discover_clients": SafetyLevel.SAFE,
    "discover_traffic": SafetyLevel.SAFE,
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
    # Epic 8: Security & Monitoring
    "discover_vpn_topology": SafetyLevel.SAFE,
    "discover_content_filtering": SafetyLevel.SAFE,
    "discover_ips_settings": SafetyLevel.SAFE,
    "discover_amp_settings": SafetyLevel.SAFE,
    "discover_traffic_shaping": SafetyLevel.SAFE,
    "configure_s2s_vpn": SafetyLevel.DANGEROUS,
    "add_vpn_peer": SafetyLevel.DANGEROUS,
    "configure_content_filter": SafetyLevel.MODERATE,
    "add_blocked_url": SafetyLevel.MODERATE,
    "configure_ips": SafetyLevel.MODERATE,
    "set_ips_mode": SafetyLevel.MODERATE,
    "configure_amp": SafetyLevel.MODERATE,
    "configure_traffic_shaping": SafetyLevel.MODERATE,
    "set_bandwidth_limit": SafetyLevel.MODERATE,
    # Epic 9: Alerts, Firmware, Observability
    "discover_alerts": SafetyLevel.SAFE,
    "discover_webhooks": SafetyLevel.SAFE,
    "discover_firmware_status": SafetyLevel.SAFE,
    "discover_snmp_config": SafetyLevel.SAFE,
    "discover_syslog_config": SafetyLevel.SAFE,
    "discover_recent_changes": SafetyLevel.SAFE,
    "configure_alerts": SafetyLevel.MODERATE,
    "create_webhook_endpoint": SafetyLevel.MODERATE,
    "test_webhook": SafetyLevel.SAFE,
    "schedule_firmware_upgrade": SafetyLevel.DANGEROUS,
    "cancel_firmware_upgrade": SafetyLevel.DANGEROUS,
    "configure_snmp": SafetyLevel.MODERATE,
    "configure_syslog": SafetyLevel.MODERATE,
    # Epic 10: Advanced Switching, Wireless & Platform
    "discover_switch_routing": SafetyLevel.SAFE,
    "configure_switch_l3_interface": SafetyLevel.DANGEROUS,
    "add_switch_static_route": SafetyLevel.DANGEROUS,
    "discover_stp_config": SafetyLevel.SAFE,
    "configure_stp": SafetyLevel.DANGEROUS,
    "reboot_device": SafetyLevel.DANGEROUS,
    "blink_leds": SafetyLevel.SAFE,
    "discover_nat_rules": SafetyLevel.SAFE,
    "discover_port_forwarding": SafetyLevel.SAFE,
    "configure_1to1_nat": SafetyLevel.MODERATE,
    "configure_port_forwarding": SafetyLevel.MODERATE,
    "discover_rf_profiles": SafetyLevel.SAFE,
    "configure_rf_profile": SafetyLevel.MODERATE,
    "discover_wireless_health": SafetyLevel.SAFE,
    "get_wireless_connection_stats": SafetyLevel.SAFE,
    "get_wireless_latency_stats": SafetyLevel.SAFE,
    "get_wireless_signal_quality": SafetyLevel.SAFE,
    "get_channel_utilization": SafetyLevel.SAFE,
    "get_failed_connections": SafetyLevel.SAFE,
    "discover_qos_config": SafetyLevel.SAFE,
    "configure_qos": SafetyLevel.MODERATE,
    "discover_org_admins": SafetyLevel.SAFE,
    "manage_admin": SafetyLevel.DANGEROUS,
    "discover_inventory": SafetyLevel.SAFE,
    "claim_device": SafetyLevel.MODERATE,
    "release_device": SafetyLevel.DANGEROUS,
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
            "name": "discover_clients",
            "description": "Discover connected clients in a network with bandwidth usage data, sorted by usage (highest first). Use this to find which devices are consuming the most bandwidth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to discover clients from",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour, max: 2592000 = 30 days)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_traffic",
            "description": "Discover network traffic by application. Shows which applications are consuming the most bandwidth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to get traffic data from",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
                    },
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
    {
        "type": "function",
        "function": {
            "name": "discover_vpn_topology",
            "description": "Discover Site-to-Site VPN topology and peer status",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID (optional, uses profile default)",
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
            "name": "discover_content_filtering",
            "description": "Discover content filtering rules and settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_ips_settings",
            "description": "Discover IPS/IDS intrusion prevention settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_amp_settings",
            "description": "Discover AMP/Malware Protection settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_traffic_shaping",
            "description": "Discover traffic shaping rules and bandwidth limits",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_alerts",
            "description": "Discover alert settings for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_webhooks",
            "description": "Discover webhook endpoints configured for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_firmware_status",
            "description": "Discover firmware status and upgrade schedule for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_snmp_config",
            "description": "Discover SNMP configuration for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_syslog_config",
            "description": "Discover syslog server configuration for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_recent_changes",
            "description": "Discover recent configuration changes in the organization",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID (optional, uses profile default)",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 86400 = 24h)",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Wireless Health Monitoring
    {
        "type": "function",
        "function": {
            "name": "discover_wireless_health",
            "description": "Discover wireless health metrics including connection stats, latency, signal quality, channel utilization, and failed connections",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
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
            "name": "get_wireless_connection_stats",
            "description": "Get wireless connection statistics for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
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
            "name": "get_wireless_latency_stats",
            "description": "Get wireless latency statistics for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
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
            "name": "get_wireless_signal_quality",
            "description": "Get wireless signal quality metrics for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
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
            "name": "get_channel_utilization",
            "description": "Get wireless channel utilization data for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
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
            "name": "get_failed_connections",
            "description": "Get failed wireless connection attempts for a network",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time window in seconds (default: 3600 = 1 hour)",
                    }
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Inventory Management
    {
        "type": "function",
        "function": {
            "name": "discover_inventory",
            "description": "Discover inventory devices (claimed, unclaimed) in the organization",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID (optional, uses profile default)",
                    }
                },
                "required": [],
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
    {
        "type": "function",
        "function": {
            "name": "configure_s2s_vpn",
            "description": "Configure Site-to-Site VPN (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "mode": {
                        "type": "string",
                        "enum": ["none", "spoke", "hub"],
                        "description": "VPN mode",
                    },
                    "hubs": {
                        "type": "array",
                        "description": "Hub configurations (for spoke mode)",
                        "items": {"type": "object"},
                    },
                    "subnets": {
                        "type": "array",
                        "description": "Subnets to announce",
                        "items": {"type": "object"},
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Simulate without applying changes",
                    },
                },
                "required": ["network_id", "mode"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_vpn_peer",
            "description": "Add third-party VPN peer (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "name": {"type": "string", "description": "Peer name"},
                    "public_ip": {"type": "string", "description": "Peer public IP"},
                    "private_subnets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Peer private subnets",
                    },
                    "secret": {"type": "string", "description": "Pre-shared secret"},
                    "ike_version": {
                        "type": "integer",
                        "description": "IKE version (1 or 2, default: 2)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "name", "public_ip", "private_subnets", "secret"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_content_filter",
            "description": "Configure content filtering (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "blocked_url_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Blocked URL patterns",
                    },
                    "allowed_url_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Allowed URL patterns",
                    },
                    "blocked_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Blocked content categories",
                    },
                    "url_category_list_size": {
                        "type": "string",
                        "enum": ["topSites", "fullList"],
                        "description": "Category list size",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_blocked_url",
            "description": "Add blocked URL to content filter (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "url": {"type": "string", "description": "URL to block"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_ips",
            "description": "Configure IPS/IDS intrusion prevention (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "mode": {
                        "type": "string",
                        "enum": ["disabled", "detection", "prevention"],
                        "description": "IPS mode",
                    },
                    "ids_rulesets": {
                        "type": "string",
                        "enum": ["connectivity", "balanced", "security"],
                        "description": "IDS rulesets",
                    },
                    "protected_networks": {
                        "type": "object",
                        "description": "Protected networks configuration",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_ips_mode",
            "description": "Set IPS mode (convenience wrapper, MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "mode": {
                        "type": "string",
                        "enum": ["disabled", "detection", "prevention"],
                        "description": "IPS mode",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "mode"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_amp",
            "description": "Configure AMP/Malware Protection (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "mode": {
                        "type": "string",
                        "enum": ["disabled", "enabled"],
                        "description": "AMP mode",
                    },
                    "allowed_files": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Allowed file hashes (sha256, comment)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_traffic_shaping",
            "description": "Configure traffic shaping rules (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rules": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Traffic shaping rules",
                    },
                    "default_rules_enabled": {
                        "type": "boolean",
                        "description": "Enable default rules",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_bandwidth_limit",
            "description": "Set uplink bandwidth limits (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "wan1_up": {"type": "integer", "description": "WAN1 upload Mbps"},
                    "wan1_down": {"type": "integer", "description": "WAN1 download Mbps"},
                    "wan2_up": {"type": "integer", "description": "WAN2 upload Mbps"},
                    "wan2_down": {"type": "integer", "description": "WAN2 download Mbps"},
                    "cellular_up": {"type": "integer", "description": "Cellular upload Mbps"},
                    "cellular_down": {"type": "integer", "description": "Cellular download Mbps"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_alerts",
            "description": "Configure network alert settings (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "alerts": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of alert configurations",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "alerts"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_webhook_endpoint",
            "description": "Create webhook endpoint for alerts (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "name": {"type": "string", "description": "Webhook name"},
                    "url": {"type": "string", "description": "Webhook URL"},
                    "shared_secret": {"type": "string", "description": "Shared secret (optional)"},
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "name", "url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_firmware_upgrade",
            "description": "Schedule firmware upgrade (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "products": {
                        "type": "object",
                        "description": "Products and versions to upgrade",
                    },
                    "upgrade_window": {
                        "type": "object",
                        "description": "Upgrade window (dayOfWeek, hourOfDay)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "products", "upgrade_window"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_firmware_upgrade",
            "description": "Cancel scheduled firmware upgrade (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "products": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Products to cancel (e.g., ['wireless', 'switch'])",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "products"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_snmp",
            "description": "Configure SNMP settings (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "access": {
                        "type": "string",
                        "enum": ["none", "community", "users"],
                        "description": "SNMP access mode",
                    },
                    "community_string": {
                        "type": "string",
                        "description": "Community string (for community mode)",
                    },
                    "users": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "SNMPv3 users (for users mode)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "access"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_syslog",
            "description": "Configure syslog servers (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "servers": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Syslog servers (host, port, roles)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for backup (optional)",
                    },
                },
                "required": ["network_id", "servers"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Switch Routing L3
    {
        "type": "function",
        "function": {
            "name": "discover_switch_routing",
            "description": "Discover switch L3 routing interfaces and static routes",
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
            "name": "configure_switch_l3_interface",
            "description": "Create L3 routing interface on switch (DANGEROUS - requires confirmation, supports dry-run)",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Switch serial number"},
                    "name": {"type": "string", "description": "Interface name"},
                    "subnet": {"type": "string", "description": "Subnet (e.g., '192.168.10.0/24')"},
                    "interface_ip": {"type": "string", "description": "Interface IP address"},
                    "vlan_id": {"type": "integer", "description": "VLAN ID"},
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                    "dry_run": {"type": "boolean", "description": "Dry-run mode (default: false)"},
                },
                "required": ["serial", "name", "subnet", "interface_ip", "vlan_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_switch_static_route",
            "description": "Add static route to switch (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Switch serial number"},
                    "subnet": {"type": "string", "description": "Destination subnet (e.g., '10.0.0.0/8')"},
                    "next_hop_ip": {"type": "string", "description": "Next hop IP address"},
                    "name": {"type": "string", "description": "Route name (optional)"},
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["serial", "subnet", "next_hop_ip"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: STP Configuration
    {
        "type": "function",
        "function": {
            "name": "discover_stp_config",
            "description": "Discover Spanning Tree Protocol configuration",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "configure_stp",
            "description": "Configure Spanning Tree Protocol settings (DANGEROUS - requires confirmation, supports dry-run)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rstp_enabled": {"type": "boolean", "description": "Enable RSTP (default: true)"},
                    "stp_bridge_priority": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "STP bridge priority per VLAN",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                    "dry_run": {"type": "boolean", "description": "Dry-run mode (default: false)"},
                },
                "required": ["network_id"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Device Management
    {
        "type": "function",
        "function": {
            "name": "reboot_device",
            "description": "Reboot a Meraki device (DANGEROUS - requires confirmation)",
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
            "name": "blink_leds",
            "description": "Blink device LEDs for identification (SAFE)",
            "parameters": {
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Device serial number",
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Blink duration in seconds (default: 20)",
                    }
                },
                "required": ["serial"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: NAT & Port Forwarding
    {
        "type": "function",
        "function": {
            "name": "discover_nat_rules",
            "description": "Discover 1:1 NAT and 1:Many NAT rules",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "discover_port_forwarding",
            "description": "Discover port forwarding rules",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "configure_1to1_nat",
            "description": "Configure 1:1 NAT rules (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rules": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "NAT rules (name, publicIp, lanIp, uplink, allowedInbound)",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["network_id", "rules"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_port_forwarding",
            "description": "Configure port forwarding rules (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rules": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Port forwarding rules (name, protocol, publicPort, localIp, localPort)",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["network_id", "rules"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: RF Profiles
    {
        "type": "function",
        "function": {
            "name": "discover_rf_profiles",
            "description": "Discover wireless RF profiles",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "configure_rf_profile",
            "description": "Create or update RF profile (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "name": {"type": "string", "description": "RF profile name"},
                    "band_selection_type": {
                        "type": "string",
                        "enum": ["dual", "5ghz", "ssid"],
                        "description": "Band selection type",
                    },
                    "ap_band_settings": {
                        "type": "object",
                        "description": "AP band settings (bandOperationMode, bandSteeringEnabled)",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["network_id", "name", "band_selection_type"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Switch QoS
    {
        "type": "function",
        "function": {
            "name": "discover_qos_config",
            "description": "Discover switch QoS rules",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID",
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
            "name": "configure_qos",
            "description": "Configure switch QoS rules (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "rules": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "QoS rules (vlan, dscp, srcPort, dstPort, protocol)",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["network_id", "rules"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Org Admins Management
    {
        "type": "function",
        "function": {
            "name": "discover_org_admins",
            "description": "Discover organization administrators",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "Organization ID (optional, uses profile default)",
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
            "name": "manage_admin",
            "description": "Create, update, or delete organization admin (DANGEROUS - requires confirmation, has guard-rails)",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Organization ID (optional)"},
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "delete"],
                        "description": "Action to perform",
                    },
                    "admin_id": {"type": "string", "description": "Admin ID (required for update/delete)"},
                    "email": {"type": "string", "description": "Admin email (required for create)"},
                    "name": {"type": "string", "description": "Admin name (required for create)"},
                    "org_access": {
                        "type": "string",
                        "enum": ["full", "read-only", "none"],
                        "description": "Organization access level",
                    },
                    "client_name": {"type": "string", "description": "Client name for backup (optional)"},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },
    # Epic 10: Inventory Management
    {
        "type": "function",
        "function": {
            "name": "claim_device",
            "description": "Claim device to network (MODERATE - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "serial": {"type": "string", "description": "Device serial number"},
                },
                "required": ["network_id", "serial"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "release_device",
            "description": "Release device from network (DANGEROUS - requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"},
                    "serial": {"type": "string", "description": "Device serial number"},
                },
                "required": ["network_id", "serial"],
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
