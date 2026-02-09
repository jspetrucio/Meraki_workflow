"""
Tests for safety.py - Safety Layer for CNL.

Tests cover:
- Safety classification for all operation types
- Confirmation flow (moderate and dangerous)
- Backup tracking and session management
- Undo/rollback mechanism
- Dry-run detection and execution
- Rate limiter pacing and per-org isolation
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.safety import (
    SAFETY_CLASSIFICATION,
    BackupInfo,
    RateLimiter,
    SafetyLevel,
    before_operation,
    classify_operation,
    detect_dry_run,
    execute_dry_run,
    execute_undo,
    generate_confirmation_request,
    get_rate_limiter,
    get_session_backups,
    get_undo_info,
    process_confirmation_response,
    track_operation,
)


# ==================== Fixtures ====================


@pytest.fixture
def temp_client_dir(tmp_path):
    """Create temporary client directory for backups."""
    client_dir = tmp_path / "clients" / "test-client"
    client_dir.mkdir(parents=True)
    return client_dir


# ==================== T7.1: Safety Classification ====================


def test_classify_safe_operations():
    """T7.1.1: Test classification of SAFE operations."""
    safe_functions = [
        "full_discovery",
        "discover_networks",
        "discover_devices",
        "find_issues",
        "list_networks",
        "generate_report",
        "compare_snapshots",
    ]

    for func_name in safe_functions:
        safety_check = classify_operation(func_name, {})

        assert safety_check.level == SafetyLevel.SAFE
        assert not safety_check.backup_required
        assert safety_check.confirmation_type == "none"
        assert func_name.replace("_", " ").title() in safety_check.action


def test_classify_moderate_operations():
    """T7.1.2: Test classification of MODERATE operations."""
    moderate_functions = [
        "configure_ssid",
        "enable_ssid",
        "disable_ssid",
        "create_vlan",
        "update_vlan",
    ]

    for func_name in moderate_functions:
        args = {"network_id": "N_123456", "name": "Test"}
        safety_check = classify_operation(func_name, args)

        assert safety_check.level == SafetyLevel.MODERATE
        assert safety_check.backup_required
        assert safety_check.confirmation_type == "confirm"
        assert "N_123456" in safety_check.preview


def test_classify_dangerous_operations():
    """T7.1.3: Test classification of DANGEROUS operations."""
    dangerous_functions = [
        "add_firewall_rule",
        "remove_firewall_rule",
        "add_switch_acl",
        "delete_vlan",
        "rollback_config",
    ]

    for func_name in dangerous_functions:
        args = {"network_id": "N_789", "vlan_id": "10"}
        safety_check = classify_operation(func_name, args)

        assert safety_check.level == SafetyLevel.DANGEROUS
        assert safety_check.backup_required
        assert safety_check.confirmation_type == "type_confirm"
        assert "DANGEROUS" in safety_check.preview


def test_classification_with_detailed_args():
    """T7.1.4: Test classification includes arg details in preview."""
    args = {
        "network_id": "N_123",
        "ssid_number": 0,
        "name": "Guest WiFi",
        "enabled": True,
    }

    safety_check = classify_operation("configure_ssid", args)

    assert "network_id: N_123" in safety_check.preview
    assert "ssid_number: 0" in safety_check.preview
    assert "name: Guest WiFi" in safety_check.preview
    assert "enabled: True" in safety_check.preview


# ==================== T7.2: Unclassified Functions ====================


def test_unclassified_function_defaults_to_dangerous():
    """T7.2: Test that unclassified functions default to DANGEROUS."""
    unknown_functions = [
        "unknown_function",
        "mystery_operation",
        "new_feature_not_classified",
    ]

    for func_name in unknown_functions:
        safety_check = classify_operation(func_name, {})

        assert safety_check.level == SafetyLevel.DANGEROUS
        assert safety_check.backup_required
        assert safety_check.confirmation_type == "type_confirm"


# ==================== T7.3: Moderate Confirmation ====================


def test_moderate_confirmation_flow():
    """T7.3: Test confirmation flow for MODERATE operations."""
    safety_check = classify_operation("configure_ssid", {"network_id": "N_123"})
    context = {
        "function_name": "configure_ssid",
        "session_id": "test-session",
    }

    # Generate confirmation request
    request = generate_confirmation_request(safety_check, context)

    assert request["type"] == "confirmation_request"
    assert request["safety_level"] == "moderate"
    assert not request["requires_typed"]
    assert "yes" in request["message"].lower()
    assert request["backup_will_be_created"]

    # Test approval
    request_id = request["request_id"]
    approved = process_confirmation_response(request_id, approved=True)
    assert approved

    # Test new request and denial
    request2 = generate_confirmation_request(safety_check, context)
    denied = process_confirmation_response(request2["request_id"], approved=False)
    assert not denied


def test_moderate_confirmation_missing_request():
    """T7.3.2: Test error when request_id not found."""
    with pytest.raises(ValueError, match="not found or expired"):
        process_confirmation_response("invalid-request-id", approved=True)


# ==================== T7.4: Dangerous Confirmation ====================


def test_dangerous_confirmation_flow():
    """T7.4: Test confirmation flow for DANGEROUS operations (typed CONFIRM)."""
    safety_check = classify_operation(
        "add_firewall_rule", {"network_id": "N_123", "protocol": "tcp", "port": 23}
    )
    context = {
        "function_name": "add_firewall_rule",
        "session_id": "test-session",
    }

    # Generate confirmation request
    request = generate_confirmation_request(safety_check, context)

    assert request["type"] == "confirmation_request"
    assert request["safety_level"] == "dangerous"
    assert request["requires_typed"]
    assert "CONFIRM" in request["message"]
    assert "⚠️" in request["message"]

    # Test with correct typed confirmation
    request_id = request["request_id"]
    approved = process_confirmation_response(
        request_id, approved=True, typed_confirm="CONFIRM"
    )
    assert approved


def test_dangerous_confirmation_wrong_typed():
    """T7.4.2: Test rejection when typed confirmation is wrong."""
    safety_check = classify_operation("delete_vlan", {})
    context = {"function_name": "delete_vlan", "session_id": "test"}

    request = generate_confirmation_request(safety_check, context)
    request_id = request["request_id"]

    # Wrong typed confirmation
    approved = process_confirmation_response(
        request_id, approved=True, typed_confirm="confirm"  # lowercase
    )
    assert not approved

    # Missing typed confirmation
    request2 = generate_confirmation_request(safety_check, context)
    approved2 = process_confirmation_response(
        request2["request_id"], approved=True, typed_confirm=None
    )
    assert not approved2


# ==================== T7.5: Backup Tracking ====================


def test_backup_tracking_max_10(tmp_path, monkeypatch):
    """T7.5: Test backup tracking with max 10 cap."""
    # Mock client directory
    client_dir = tmp_path / "clients" / "test-client"
    monkeypatch.chdir(tmp_path)

    session_id = "backup-test"

    # Create 15 backups (should keep only last 10)
    for i in range(15):
        result = before_operation(
            function_name=f"operation_{i}",
            args={"test": i},
            client_name="test-client",
            session_id=session_id,
        )

        assert result["backup_created"]
        assert "backup_path" in result

    # Check that only 10 are tracked
    backups = get_session_backups(session_id)
    assert len(backups) == 10

    # Check they are the most recent ones (10-14)
    backup_numbers = [
        int(b.function_name.split("_")[1]) for b in backups
    ]
    assert backup_numbers == list(range(14, 4, -1))  # 14, 13, ..., 5 (newest first)


def test_backup_not_created_for_safe_operations(tmp_path, monkeypatch):
    """T7.5.2: Test that SAFE operations don't create backups."""
    monkeypatch.chdir(tmp_path)

    result = before_operation(
        function_name="full_discovery",
        args={},
        client_name="test-client",
        session_id="test",
    )

    assert not result["backup_created"]
    assert "backup_path" not in result


def test_backup_metadata(tmp_path, monkeypatch):
    """T7.5.3: Test backup file contains correct metadata."""
    monkeypatch.chdir(tmp_path)

    args = {"network_id": "N_123", "vlan_id": 10}
    result = before_operation(
        function_name="create_vlan",
        args=args,
        client_name="test-client",
        session_id="test",
    )

    # Read backup file
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()

    backup_data = json.loads(backup_path.read_text())
    assert backup_data["function_name"] == "create_vlan"
    assert backup_data["args"] == args
    assert backup_data["client_name"] == "test-client"
    assert "timestamp" in backup_data


# ==================== T7.6: Undo/Rollback ====================


def test_undo_mechanism(tmp_path, monkeypatch):
    """T7.6: Test undo/rollback mechanism."""
    monkeypatch.chdir(tmp_path)
    session_id = "undo-test"

    # Execute operation with backup
    backup_result = before_operation(
        function_name="update_vlan",
        args={"vlan_id": 10},
        client_name="test-client",
        session_id=session_id,
    )

    # Track operation
    track_operation(
        session_id=session_id,
        function_name="update_vlan",
        args={"vlan_id": 10},
        backup_path=backup_result["backup_path"],
    )

    # Get undo info
    undo_info = get_undo_info(session_id)
    assert undo_info is not None
    assert undo_info["can_undo"]
    assert undo_info["operation"] == "update_vlan"
    assert backup_result["backup_path"] in undo_info["backup_path"]

    # Execute undo
    undo_result = execute_undo(session_id)
    assert undo_result["success"]
    assert backup_result["backup_path"] in undo_result["backup_path"]

    # Verify can't undo again (cleared after undo)
    undo_info_after = get_undo_info(session_id)
    assert undo_info_after is None


def test_undo_no_operation():
    """T7.6.2: Test undo when no operation was performed."""
    session_id = "empty-session"

    undo_info = get_undo_info(session_id)
    assert undo_info is None


def test_undo_operation_without_backup():
    """T7.6.3: Test undo info for operation without backup."""
    session_id = "no-backup"

    # Track operation without backup (e.g., safe operation)
    track_operation(
        session_id=session_id,
        function_name="full_discovery",
        args={},
        backup_path=None,
    )

    undo_info = get_undo_info(session_id)
    assert undo_info is not None
    assert not undo_info["can_undo"]
    assert "No backup available" in undo_info["reason"]


def test_undo_missing_backup_file(tmp_path, monkeypatch):
    """T7.6.4: Test undo fails when backup file is missing."""
    monkeypatch.chdir(tmp_path)
    session_id = "missing-backup"

    # Track operation with non-existent backup path
    track_operation(
        session_id=session_id,
        function_name="delete_vlan",
        args={},
        backup_path="/fake/path/backup.json",
    )

    # Attempt undo should fail
    with pytest.raises(ValueError, match="Backup file not found"):
        execute_undo(session_id)


# ==================== T7.7: Dry-Run Detection ====================


def test_dry_run_detection_patterns():
    """T7.7: Test dry-run detection for all patterns."""
    dry_run_messages = [
        "configure SSID --dry-run",
        "what would happen if I add a firewall rule",
        "preview the changes for VLAN 10",
        "simulate adding an ACL",
        "show me what configuring SSID would do",
        "can you do a dry run of this operation",
        "without actually doing it, what would happen",
    ]

    for message in dry_run_messages:
        assert detect_dry_run(message), f"Failed to detect dry-run in: {message}"

    # Non-dry-run messages
    normal_messages = [
        "add firewall rule to block port 23",
        "configure SSID for guests",
        "create VLAN 10",
    ]

    for message in normal_messages:
        assert not detect_dry_run(message), f"False positive for: {message}"


# ==================== T7.8: Dry-Run Execution ====================


def test_dry_run_execution():
    """T7.8: Test dry-run execution (no side effects)."""
    args = {
        "network_id": "N_123",
        "protocol": "tcp",
        "port": 23,
        "action": "deny",
    }

    result = execute_dry_run("add_firewall_rule", args)

    assert result["dry_run"]
    assert result["safety_level"] == "dangerous"
    assert result["backup_required"]
    assert "N_123" in result["networks_affected"]
    assert "tcp" in result["impact"].lower()
    assert "23" in result["impact"]
    assert result["api_calls_prevented"] >= 1


def test_dry_run_no_api_calls():
    """T7.8.2: Test that dry-run makes no actual API calls."""
    # This test verifies that execute_dry_run doesn't import or call
    # any Meraki API modules

    with patch("scripts.safety.classify_operation") as mock_classify:
        from scripts.safety import SafetyCheck, SafetyLevel

        mock_classify.return_value = SafetyCheck(
            level=SafetyLevel.MODERATE,
            action="Test action",
            preview="Test preview",
            backup_required=True,
            confirmation_type="confirm",
        )

        result = execute_dry_run("configure_ssid", {"network_id": "N_123"})

        # Verify result structure
        assert result["dry_run"]
        assert "impact" in result
        assert "networks_affected" in result

        # Mock should have been called (we're using it)
        mock_classify.assert_called_once()


def test_dry_run_different_safety_levels():
    """T7.8.3: Test dry-run for different safety levels."""
    test_cases = [
        ("full_discovery", {}, "safe"),
        ("configure_ssid", {"network_id": "N_123"}, "moderate"),
        ("delete_vlan", {"vlan_id": 10}, "dangerous"),
    ]

    for func_name, args, expected_level in test_cases:
        result = execute_dry_run(func_name, args)
        assert result["safety_level"] == expected_level


# ==================== T7.9: Rate Limiter Pacing ====================


@pytest.mark.asyncio
async def test_rate_limiter_8_rps_cap():
    """T7.9: Test rate limiter enforces 8 req/s cap."""
    limiter = RateLimiter(max_requests_per_second=8)
    org_id = "org_123"

    start_time = asyncio.get_event_loop().time()

    # Make 16 requests (should take ~2 seconds at 8 req/s)
    for i in range(16):
        await limiter.wait_for_capacity(org_id)

    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time

    # Should take at least 1 second (16 requests at 8 req/s = 2 seconds)
    # Allow some tolerance for timing
    assert elapsed >= 1.0, f"Too fast: {elapsed:.3f}s for 16 requests"
    assert elapsed < 3.0, f"Too slow: {elapsed:.3f}s for 16 requests"


@pytest.mark.asyncio
async def test_rate_limiter_burst():
    """T7.9.2: Test rate limiter handles burst requests correctly."""
    limiter = RateLimiter(max_requests_per_second=8)
    org_id = "org_456"

    # First 8 requests should be immediate
    start = asyncio.get_event_loop().time()
    for i in range(8):
        await limiter.wait_for_capacity(org_id)
    burst_time = asyncio.get_event_loop().time() - start

    # Should be nearly instant (< 0.1s)
    assert burst_time < 0.1

    # 9th request should wait
    start = asyncio.get_event_loop().time()
    await limiter.wait_for_capacity(org_id)
    wait_time = asyncio.get_event_loop().time() - start

    # Should wait around 1 second for the window to slide
    assert wait_time >= 0.9


@pytest.mark.asyncio
async def test_rate_limiter_pace_operations():
    """T7.9.3: Test rate limiter with pace_operations."""
    limiter = RateLimiter(max_requests_per_second=10)
    org_id = "org_789"

    # Mock operations
    call_count = 0

    async def mock_operation():
        nonlocal call_count
        call_count += 1
        return f"result_{call_count}"

    operations = [mock_operation for _ in range(15)]

    # Track progress
    progress_messages = []

    def progress_callback(message):
        progress_messages.append(message)

    # Execute with pacing
    start = asyncio.get_event_loop().time()
    results = await limiter.pace_operations(org_id, operations, progress_callback)
    elapsed = asyncio.get_event_loop().time() - start

    # Verify all operations executed
    assert len(results) == 15
    assert call_count == 15
    assert results == [f"result_{i}" for i in range(1, 16)]

    # Verify progress callbacks
    assert len(progress_messages) > 0
    assert any("Processing" in msg for msg in progress_messages)

    # Should take at least 1 second (15 requests at 10 req/s)
    assert elapsed >= 1.0


# ==================== T7.10: Rate Limiter Per-Org Isolation ====================


@pytest.mark.asyncio
async def test_rate_limiter_per_org_isolation():
    """T7.10: Test rate limiter isolates different organizations."""
    limiter = RateLimiter(max_requests_per_second=8)

    org1 = "org_alpha"
    org2 = "org_beta"

    # Fill org1's quota
    for i in range(8):
        await limiter.wait_for_capacity(org1)

    # org2 should still have capacity (independent)
    start = asyncio.get_event_loop().time()
    await limiter.wait_for_capacity(org2)
    elapsed = asyncio.get_event_loop().time() - start

    # Should be immediate (< 0.1s) since org2 is independent
    assert elapsed < 0.1

    # org1's 9th request should wait
    start = asyncio.get_event_loop().time()
    await limiter.wait_for_capacity(org1)
    wait_time = asyncio.get_event_loop().time() - start

    # Should wait around 1 second
    assert wait_time >= 0.9


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_orgs():
    """T7.10.2: Test rate limiter with concurrent requests from multiple orgs."""
    limiter = RateLimiter(max_requests_per_second=5)

    orgs = ["org_1", "org_2", "org_3"]

    async def make_requests(org_id, count):
        for _ in range(count):
            await limiter.wait_for_capacity(org_id)

    # Run concurrent requests for all orgs
    start = asyncio.get_event_loop().time()
    await asyncio.gather(
        make_requests(orgs[0], 10),
        make_requests(orgs[1], 10),
        make_requests(orgs[2], 10),
    )
    elapsed = asyncio.get_event_loop().time() - start

    # Each org makes 10 requests at 5 req/s = 2 seconds per org
    # Since they're concurrent and independent, each org can proceed at full rate
    # Actual time should be around 2 seconds (time for slowest org)
    # But due to asyncio timing, give more tolerance
    assert elapsed >= 1.0  # At least 1 second (some rate limiting occurred)
    assert elapsed < 3.0  # But not too slow


@pytest.mark.asyncio
async def test_rate_limiter_get_global_instance():
    """T7.10.3: Test global rate limiter instance."""
    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()

    # Should be same instance
    assert limiter1 is limiter2

    # Should work correctly
    org_id = "org_global"
    await limiter1.wait_for_capacity(org_id)
    # Should succeed without error


# ==================== Integration Tests ====================


def test_full_safety_workflow(tmp_path, monkeypatch):
    """Integration test: Full safety workflow from classification to undo."""
    monkeypatch.chdir(tmp_path)
    session_id = "integration-test"
    client_name = "test-client"

    # 1. Classify operation
    safety_check = classify_operation(
        "add_firewall_rule",
        {"network_id": "N_123", "protocol": "tcp", "port": 23},
    )
    assert safety_check.level == SafetyLevel.DANGEROUS

    # 2. Generate confirmation request
    context = {"function_name": "add_firewall_rule", "session_id": session_id}
    request = generate_confirmation_request(safety_check, context)
    assert request["requires_typed"]

    # 3. Process confirmation
    approved = process_confirmation_response(
        request["request_id"], approved=True, typed_confirm="CONFIRM"
    )
    assert approved

    # 4. Create backup before operation
    backup_result = before_operation(
        function_name="add_firewall_rule",
        args={"network_id": "N_123"},
        client_name=client_name,
        session_id=session_id,
    )
    assert backup_result["backup_created"]

    # 5. Track operation
    track_operation(
        session_id=session_id,
        function_name="add_firewall_rule",
        args={"network_id": "N_123"},
        backup_path=backup_result["backup_path"],
    )

    # 6. Get undo info
    undo_info = get_undo_info(session_id)
    assert undo_info["can_undo"]

    # 7. Execute undo
    undo_result = execute_undo(session_id)
    assert undo_result["success"]


def test_all_classified_functions_exist():
    """Test that all functions in SAFETY_CLASSIFICATION are accounted for."""
    # Count actual classifications
    counts = {level: 0 for level in SafetyLevel}
    for level in SAFETY_CLASSIFICATION.values():
        counts[level] += 1

    # Verify we have reasonable distribution
    assert counts[SafetyLevel.SAFE] > 0, "Should have safe operations"
    assert counts[SafetyLevel.MODERATE] > 0, "Should have moderate operations"
    assert counts[SafetyLevel.DANGEROUS] > 0, "Should have dangerous operations"

    # Verify specific counts match what's actually in SAFETY_CLASSIFICATION
    # Updated for Epic 8, Epic 9 & Epic 10:
    # SAFE: 51 (base 24 + Epic 8: 5 + Epic 9: 7 + Epic 10: 15)
    # MODERATE: 22 (base 6 + Epic 8: 7 + Epic 9: 4 + Epic 10: 5)
    # DANGEROUS: 15 (base 5 + Epic 8: 2 + Epic 9: 2 + Epic 10: 6)

    expected_counts = {
        SafetyLevel.SAFE: 51,
        SafetyLevel.MODERATE: 22,
        SafetyLevel.DANGEROUS: 15,
    }

    assert counts == expected_counts, (
        f"Classification counts don't match expected. "
        f"Expected: {expected_counts}, Got: {counts}"
    )
