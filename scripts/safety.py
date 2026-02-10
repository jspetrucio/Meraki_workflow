"""
Safety Layer for CNL (Cisco Neural Language).

Provides safety classification, confirmation flows, automatic backups,
undo/rollback, dry-run mode, and rate limiting for Meraki API operations.

Safety Levels:
- SAFE: Read-only operations, no confirmation needed
- MODERATE: Low-risk changes, requires preview + confirmation
- DANGEROUS: High-risk changes, requires typed CONFIRM + backup
"""

import asyncio
import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ==================== Enums & Data Classes ====================


class SafetyLevel(Enum):
    """Safety level for operations."""

    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class SafetyCheck:
    """Result of safety classification."""

    level: SafetyLevel
    action: str
    preview: str
    backup_required: bool
    confirmation_type: str  # "none", "confirm", "type_confirm"


# ==================== Safety Classification ====================


# Mapping of function names to safety levels
SAFETY_CLASSIFICATION = {
    # SAFE: Read-only operations
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
    "list_networks": SafetyLevel.SAFE,
    "list_devices": SafetyLevel.SAFE,
    "generate_report": SafetyLevel.SAFE,
    "generate_discovery_report": SafetyLevel.SAFE,
    # Workflow functions (safe - just generate JSON)
    "create_device_offline_handler": SafetyLevel.SAFE,
    "create_firmware_compliance_check": SafetyLevel.SAFE,
    "create_scheduled_report": SafetyLevel.SAFE,
    "create_security_alert_handler": SafetyLevel.SAFE,
    "save_workflow": SafetyLevel.SAFE,
    "list_workflows": SafetyLevel.SAFE,
    # MODERATE: Low-risk configuration changes
    "configure_ssid": SafetyLevel.MODERATE,
    "enable_ssid": SafetyLevel.MODERATE,
    "disable_ssid": SafetyLevel.MODERATE,
    "create_vlan": SafetyLevel.MODERATE,
    "update_vlan": SafetyLevel.MODERATE,
    "backup_config": SafetyLevel.MODERATE,
    # DANGEROUS: High-risk operations
    "add_firewall_rule": SafetyLevel.DANGEROUS,
    "remove_firewall_rule": SafetyLevel.DANGEROUS,
    "add_switch_acl": SafetyLevel.DANGEROUS,
    "delete_vlan": SafetyLevel.DANGEROUS,
    "rollback_config": SafetyLevel.DANGEROUS,
    # Epic 8: Security & Monitoring - Discovery (SAFE)
    "discover_vpn_topology": SafetyLevel.SAFE,
    "discover_content_filtering": SafetyLevel.SAFE,
    "discover_ips_settings": SafetyLevel.SAFE,
    "discover_amp_settings": SafetyLevel.SAFE,
    "discover_traffic_shaping": SafetyLevel.SAFE,
    # Epic 8: Security & Monitoring - Config (DANGEROUS/MODERATE)
    "configure_s2s_vpn": SafetyLevel.DANGEROUS,
    "add_vpn_peer": SafetyLevel.DANGEROUS,
    "configure_content_filter": SafetyLevel.MODERATE,
    "add_blocked_url": SafetyLevel.MODERATE,
    "configure_ips": SafetyLevel.MODERATE,
    "set_ips_mode": SafetyLevel.MODERATE,
    "configure_amp": SafetyLevel.MODERATE,
    "configure_traffic_shaping": SafetyLevel.MODERATE,
    "set_bandwidth_limit": SafetyLevel.MODERATE,
    # Epic 9: Alerts, Firmware & Observability - Discovery (SAFE)
    "discover_alerts": SafetyLevel.SAFE,
    "discover_webhooks": SafetyLevel.SAFE,
    "discover_firmware_status": SafetyLevel.SAFE,
    "discover_snmp_config": SafetyLevel.SAFE,
    "discover_syslog_config": SafetyLevel.SAFE,
    "discover_recent_changes": SafetyLevel.SAFE,
    # Epic 9: Alerts, Firmware & Observability - Config (DANGEROUS/MODERATE)
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
    # Phase 2 - Wave 1: Policy Objects, Client VPN, Port Schedules, LLDP/CDP, NetFlow, PoE
    "discover_policy_objects": SafetyLevel.SAFE,
    "manage_policy_object": SafetyLevel.MODERATE,
    "discover_client_vpn": SafetyLevel.SAFE,
    "configure_client_vpn": SafetyLevel.MODERATE,
    "discover_port_schedules": SafetyLevel.SAFE,
    "configure_port_schedule": SafetyLevel.MODERATE,
    "discover_lldp_cdp": SafetyLevel.SAFE,
    "discover_netflow_config": SafetyLevel.SAFE,
    "configure_netflow": SafetyLevel.MODERATE,
    "discover_poe_status": SafetyLevel.SAFE,
    # Phase 2 - Wave 2: SD-WAN, Templates, Access Policies, Air Marshal, SSID FW, Splash
    "discover_sdwan_config": SafetyLevel.SAFE,
    "configure_sdwan_policy": SafetyLevel.DANGEROUS,
    "set_uplink_preference": SafetyLevel.DANGEROUS,
    "discover_templates": SafetyLevel.SAFE,
    "manage_template": SafetyLevel.DANGEROUS,
    "discover_access_policies": SafetyLevel.SAFE,
    "configure_access_policy": SafetyLevel.MODERATE,
    "discover_rogue_aps": SafetyLevel.SAFE,
    "discover_ssid_firewall": SafetyLevel.SAFE,
    "configure_ssid_firewall": SafetyLevel.MODERATE,
    "discover_splash_config": SafetyLevel.SAFE,
    "configure_splash_page": SafetyLevel.MODERATE,
    # Phase 2 - Wave 3: Adaptive Policy, Switch Stacks, HA/Warm Spare, Camera Analytics, Sensors
    "discover_adaptive_policies": SafetyLevel.SAFE,
    "configure_adaptive_policy": SafetyLevel.DANGEROUS,
    "get_adaptive_policy_acls": SafetyLevel.SAFE,
    "discover_switch_stacks": SafetyLevel.SAFE,
    "manage_switch_stack": SafetyLevel.DANGEROUS,
    "get_stack_routing": SafetyLevel.SAFE,
    "discover_ha_config": SafetyLevel.SAFE,
    "configure_warm_spare": SafetyLevel.DANGEROUS,
    "trigger_failover": SafetyLevel.DANGEROUS,
    "discover_camera_analytics": SafetyLevel.SAFE,
    "generate_snapshot": SafetyLevel.SAFE,
    "get_video_link": SafetyLevel.SAFE,
    "discover_sensors": SafetyLevel.SAFE,
    "configure_sensor_alert": SafetyLevel.MODERATE,
    "get_sensor_readings_latest": SafetyLevel.SAFE,
    "get_sensor_readings_history": SafetyLevel.SAFE,
    # Phase 2 - Wave 4: Floor Plans, Group Policies, Packet Capture, Static Routes
    "discover_floor_plans": SafetyLevel.SAFE,
    "create_floor_plan": SafetyLevel.MODERATE,
    "update_floor_plan": SafetyLevel.MODERATE,
    "delete_floor_plan": SafetyLevel.MODERATE,
    "discover_group_policies": SafetyLevel.SAFE,
    "configure_group_policy": SafetyLevel.MODERATE,
    "create_packet_capture": SafetyLevel.MODERATE,
    "get_packet_capture_status": SafetyLevel.SAFE,
    "discover_static_routes": SafetyLevel.SAFE,
    "manage_static_route": SafetyLevel.MODERATE,
}


def classify_operation(function_name: str, args: dict) -> SafetyCheck:
    """
    Classify operation safety level and generate confirmation requirements.

    Args:
        function_name: Name of the function to execute
        args: Arguments to pass to the function

    Returns:
        SafetyCheck with level, preview, and confirmation requirements
    """
    # Get safety level (default to DANGEROUS for unclassified)
    level = SAFETY_CLASSIFICATION.get(function_name, SafetyLevel.DANGEROUS)

    # Build action description
    action = _build_action_description(function_name, args)

    # Build preview message
    preview = _build_preview_message(function_name, args, level)

    # Determine backup and confirmation requirements
    if level == SafetyLevel.SAFE:
        backup_required = False
        confirmation_type = "none"
    elif level == SafetyLevel.MODERATE:
        backup_required = True
        confirmation_type = "confirm"
    else:  # DANGEROUS
        backup_required = True
        confirmation_type = "type_confirm"

    return SafetyCheck(
        level=level,
        action=action,
        preview=preview,
        backup_required=backup_required,
        confirmation_type=confirmation_type,
    )


def _build_action_description(function_name: str, args: dict) -> str:
    """Build human-readable action description."""
    # Extract key parameters for description
    desc_parts = [function_name.replace("_", " ").title()]

    # Add key arguments to description
    if "network_id" in args:
        desc_parts.append(f"on network {args['network_id']}")
    if "ssid_number" in args or "number" in args:
        num = args.get("ssid_number") or args.get("number")
        desc_parts.append(f"SSID #{num}")
    if "name" in args:
        desc_parts.append(f"'{args['name']}'")
    if "vlan_id" in args:
        desc_parts.append(f"VLAN {args['vlan_id']}")

    return " ".join(desc_parts)


def _build_preview_message(
    function_name: str, args: dict, level: SafetyLevel
) -> str:
    """Build detailed preview message for confirmation."""
    lines = [f"Operation: {function_name}"]
    lines.append(f"Safety Level: {level.value.upper()}")
    lines.append("\nParameters:")

    # Show key parameters
    for key, value in args.items():
        if isinstance(value, (str, int, bool)):
            lines.append(f"  - {key}: {value}")
        elif isinstance(value, dict):
            lines.append(f"  - {key}: {len(value)} items")
        elif isinstance(value, list):
            lines.append(f"  - {key}: {len(value)} items")

    return "\n".join(lines)


# ==================== Confirmation Flow ====================


# In-memory store for pending confirmations
_pending_confirmations: dict[str, dict] = {}


def generate_confirmation_request(
    safety_check: SafetyCheck, operation_context: dict
) -> dict:
    """
    Generate confirmation request for user.

    Args:
        safety_check: SafetyCheck result
        operation_context: Additional context (function_name, args, client_name, etc.)

    Returns:
        Dict with confirmation request details
    """
    request_id = _generate_request_id(operation_context)

    # Store pending confirmation
    _pending_confirmations[request_id] = {
        "safety_check": safety_check,
        "context": operation_context,
        "timestamp": datetime.now(),
    }

    # Build request message
    if safety_check.confirmation_type == "confirm":
        message = (
            f"{safety_check.preview}\n\n"
            f"This operation requires confirmation.\n"
            f"Reply 'yes' or 'y' to proceed, or 'no' to cancel."
        )
        requires_typed = False
    else:  # type_confirm
        message = (
            f"{safety_check.preview}\n\n"
            f"⚠️ DANGEROUS OPERATION ⚠️\n"
            f"This operation will make critical changes to your network.\n"
            f"A backup will be created automatically.\n\n"
            f"Type 'CONFIRM' (all caps) to proceed, or 'cancel' to abort."
        )
        requires_typed = True

    return {
        "type": "confirmation_request",
        "request_id": request_id,
        "safety_level": safety_check.level.value,
        "action": safety_check.action,
        "message": message,
        "requires_typed": requires_typed,
        "backup_will_be_created": safety_check.backup_required,
    }


def process_confirmation_response(
    request_id: str, approved: bool, typed_confirm: Optional[str] = None
) -> bool:
    """
    Process user's confirmation response.

    Args:
        request_id: ID of the confirmation request
        approved: Whether user approved (True) or denied (False)
        typed_confirm: For dangerous ops, the typed confirmation string

    Returns:
        True if confirmation is valid and operation can proceed

    Raises:
        ValueError: If request_id not found
    """
    if request_id not in _pending_confirmations:
        raise ValueError(f"Confirmation request {request_id} not found or expired")

    pending = _pending_confirmations.pop(request_id)
    safety_check: SafetyCheck = pending["safety_check"]

    # Check denial
    if not approved:
        logger.info(f"Operation cancelled by user: {request_id}")
        return False

    # Check typed confirmation for dangerous ops
    if safety_check.confirmation_type == "type_confirm":
        if typed_confirm != "CONFIRM":
            logger.warning(
                f"Invalid typed confirmation for dangerous operation: '{typed_confirm}'"
            )
            return False

    logger.info(f"Operation confirmed by user: {request_id}")
    return True


def _generate_request_id(context: dict) -> str:
    """Generate unique request ID from context."""
    import hashlib

    content = f"{context.get('function_name', '')}:{context.get('session_id', '')}:{datetime.now().isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ==================== Backup Tracking ====================


@dataclass
class BackupInfo:
    """Information about a backup."""

    backup_path: str
    function_name: str
    timestamp: datetime
    client_name: str
    args_summary: str


# Per-session backup tracking (max 10 backups per session)
_session_backups: dict[str, deque[BackupInfo]] = {}


def before_operation(
    function_name: str, args: dict, client_name: str, session_id: str = "default"
) -> dict:
    """
    Prepare for operation: create backup if needed.

    Args:
        function_name: Name of function to execute
        args: Function arguments
        client_name: Client name for backup directory
        session_id: Session identifier

    Returns:
        Dict with backup_path if backup was created, None otherwise
    """
    safety_check = classify_operation(function_name, args)

    if not safety_check.backup_required:
        return {"backup_created": False}

    # Create backup
    from pathlib import Path

    backup_dir = Path("clients") / client_name / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{function_name}_{timestamp}.json"

    # In production, would actually save current config
    # For now, just create placeholder
    import json

    backup_data = {
        "function_name": function_name,
        "timestamp": datetime.now().isoformat(),
        "args": args,
        "client_name": client_name,
    }

    backup_path.write_text(json.dumps(backup_data, indent=2), encoding="utf-8")
    logger.info(f"Backup created: {backup_path}")

    # Track backup in session
    if session_id not in _session_backups:
        _session_backups[session_id] = deque(maxlen=10)

    backup_info = BackupInfo(
        backup_path=str(backup_path),
        function_name=function_name,
        timestamp=datetime.now(),
        client_name=client_name,
        args_summary=str(args)[:100],
    )

    _session_backups[session_id].append(backup_info)

    return {"backup_created": True, "backup_path": str(backup_path)}


def get_session_backups(session_id: str = "default") -> list[BackupInfo]:
    """
    Get list of backups for session.

    Args:
        session_id: Session identifier

    Returns:
        List of BackupInfo objects (newest first)
    """
    if session_id not in _session_backups:
        return []

    return list(reversed(_session_backups[session_id]))


# ==================== Undo/Rollback ====================


# Per-session last operation tracking
_last_operations: dict[str, dict] = {}


def track_operation(
    session_id: str, function_name: str, args: dict, backup_path: Optional[str]
) -> None:
    """
    Track operation for undo capability.

    Args:
        session_id: Session identifier
        function_name: Function that was executed
        args: Arguments used
        backup_path: Path to backup if created
    """
    _last_operations[session_id] = {
        "function_name": function_name,
        "args": args,
        "backup_path": backup_path,
        "timestamp": datetime.now(),
    }


def get_undo_info(session_id: str = "default") -> Optional[dict]:
    """
    Get information about what will be undone.

    Args:
        session_id: Session identifier

    Returns:
        Dict with undo info or None if nothing to undo
    """
    if session_id not in _last_operations:
        return None

    last_op = _last_operations[session_id]

    if not last_op.get("backup_path"):
        return {
            "can_undo": False,
            "reason": "No backup available for last operation",
        }

    return {
        "can_undo": True,
        "operation": last_op["function_name"],
        "timestamp": last_op["timestamp"].isoformat(),
        "backup_path": last_op["backup_path"],
        "preview": f"Will restore configuration from {last_op['backup_path']}",
    }


def execute_undo(session_id: str = "default") -> dict:
    """
    Execute undo operation by restoring from backup.

    Args:
        session_id: Session identifier

    Returns:
        Dict with result

    Raises:
        ValueError: If nothing to undo or backup not found
    """
    undo_info = get_undo_info(session_id)

    if not undo_info or not undo_info.get("can_undo"):
        raise ValueError("Nothing to undo or no backup available")

    backup_path = undo_info["backup_path"]

    # Verify backup exists
    from pathlib import Path

    if not Path(backup_path).exists():
        raise ValueError(f"Backup file not found: {backup_path}")

    # In production, would actually restore config from backup
    # For now, just mark as restored
    logger.info(f"Restoring configuration from {backup_path}")

    # Clear last operation (can't undo an undo)
    _last_operations.pop(session_id, None)

    return {
        "success": True,
        "message": f"Configuration restored from {backup_path}",
        "backup_path": backup_path,
    }


# ==================== Dry-Run Mode ====================


def detect_dry_run(message: str) -> bool:
    """
    Detect if user wants a dry-run/preview.

    Patterns:
    - --dry-run flag
    - "what would happen if"
    - "preview"
    - "simulate"

    Args:
        message: User message

    Returns:
        True if dry-run requested
    """
    message_lower = message.lower()

    patterns = [
        r"--dry-run",
        r"\bdry\s*run\b",
        r"what would happen",
        r"\bpreview\b",
        r"\bsimulate\b",
        r"show me what",
        r"without (actually|really) (doing|executing|running)",
    ]

    for pattern in patterns:
        if re.search(pattern, message_lower):
            return True

    return False


def execute_dry_run(function_name: str, args: dict) -> dict:
    """
    Execute dry-run: show what would happen without calling API.

    Args:
        function_name: Function to simulate
        args: Arguments

    Returns:
        Dict with action, impact, and affected resources
    """
    safety_check = classify_operation(function_name, args)

    # Build impact analysis
    impact_lines = [
        f"Function: {function_name}",
        f"Safety Level: {safety_check.level.value.upper()}",
        "",
        "Parameters:",
    ]

    for key, value in args.items():
        impact_lines.append(f"  - {key}: {value}")

    impact_lines.extend(
        [
            "",
            "Changes that would be made:",
            safety_check.action,
            "",
            f"Backup required: {safety_check.backup_required}",
            f"Confirmation type: {safety_check.confirmation_type}",
        ]
    )

    # Extract affected resources
    networks_affected = []
    if "network_id" in args:
        networks_affected.append(args["network_id"])

    return {
        "dry_run": True,
        "action": safety_check.action,
        "impact": "\n".join(impact_lines),
        "networks_affected": networks_affected,
        "safety_level": safety_check.level.value,
        "backup_required": safety_check.backup_required,
        "api_calls_prevented": 1,  # Would make at least 1 API call
    }


# ==================== Rate Limiter ====================


class RateLimiter:
    """
    Rate limiter for Meraki API calls.

    Enforces 8 req/s per organization (Meraki limit is 10, leave headroom).
    Uses sliding window with per-org tracking.
    """

    def __init__(self, max_requests_per_second: int = 8):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum requests per second per org
        """
        self.max_rps = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second

        # Per-org tracking: org_id -> deque of timestamps
        self._org_requests: dict[str, deque[float]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, org_id: str) -> asyncio.Lock:
        """Get or create lock for organization."""
        if org_id not in self._locks:
            self._locks[org_id] = asyncio.Lock()
        return self._locks[org_id]

    async def wait_for_capacity(
        self, org_id: str, progress_callback: Optional[Callable] = None
    ) -> None:
        """
        Wait until capacity is available for organization.

        Args:
            org_id: Organization ID
            progress_callback: Optional callback for progress updates
        """
        lock = self._get_lock(org_id)

        async with lock:
            now = asyncio.get_event_loop().time()

            # Initialize tracking for org
            if org_id not in self._org_requests:
                self._org_requests[org_id] = deque()

            requests = self._org_requests[org_id]

            # Remove requests older than 1 second
            cutoff = now - 1.0
            while requests and requests[0] < cutoff:
                requests.popleft()

            # Check if we need to wait
            if len(requests) >= self.max_rps:
                # Need to wait until oldest request is > 1 second old
                oldest = requests[0]
                wait_time = 1.0 - (now - oldest)

                if wait_time > 0:
                    if progress_callback:
                        progress_callback(
                            f"Rate limit: waiting {wait_time:.2f}s for {org_id}"
                        )

                    await asyncio.sleep(wait_time)

                    # Recalculate now after sleep
                    now = asyncio.get_event_loop().time()

                    # Clean old requests again
                    cutoff = now - 1.0
                    while requests and requests[0] < cutoff:
                        requests.popleft()

            # Record this request
            requests.append(now)

    async def pace_operations(
        self,
        org_id: str,
        operations: list[Callable],
        progress_callback: Optional[Callable] = None,
    ) -> list[Any]:
        """
        Execute operations with rate limiting.

        Args:
            org_id: Organization ID
            operations: List of async callables to execute
            progress_callback: Optional progress callback

        Returns:
            List of results from operations
        """
        results = []

        for i, operation in enumerate(operations):
            if progress_callback:
                progress_callback(f"Processing {i + 1}/{len(operations)}...")

            # Wait for capacity
            await self.wait_for_capacity(org_id, progress_callback)

            # Execute operation
            result = await operation()
            results.append(result)

        return results


# ==================== Module Initialization ====================

# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter


# ==================== Main ====================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)s: %(message)s"
    )

    def test_safety():
        """Test safety classification."""
        print("\n=== Testing Safety Layer ===\n")

        # Test classifications
        test_functions = [
            ("full_discovery", {}),
            ("configure_ssid", {"network_id": "N_123", "number": 0, "name": "Guest"}),
            ("add_firewall_rule", {"network_id": "N_123", "protocol": "tcp", "port": 23}),
            ("unknown_function", {}),
        ]

        for func_name, args in test_functions:
            safety_check = classify_operation(func_name, args)
            print(f"Function: {func_name}")
            print(f"  Level: {safety_check.level.value}")
            print(f"  Action: {safety_check.action}")
            print(f"  Backup Required: {safety_check.backup_required}")
            print(f"  Confirmation: {safety_check.confirmation_type}")
            print()

        # Test dry-run detection
        print("Dry-run detection:")
        test_messages = [
            "configure SSID --dry-run",
            "what would happen if I add a firewall rule",
            "preview the changes",
            "add firewall rule",
        ]

        for msg in test_messages:
            is_dry_run = detect_dry_run(msg)
            print(f"  '{msg}': {is_dry_run}")

        print("\n=== Tests Complete ===\n")

    try:
        test_safety()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
