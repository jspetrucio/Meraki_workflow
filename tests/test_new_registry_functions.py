"""
Tests for Story 7.4: New FUNCTION_REGISTRY Entries.

Covers:
- detect_catalyst_mode()
- sgt_preflight_check()
- check_license()
- backup_current_state()
- FUNCTION_REGISTRY registration
- Tool schemas in agent_tools.py
- Safety classifications
"""

from unittest.mock import MagicMock, patch

import pytest

from scripts.config import (
    detect_catalyst_mode,
    sgt_preflight_check,
    check_license,
    backup_current_state,
)
from scripts.agent_tools import TOOL_SAFETY, SafetyLevel, MERAKI_SPECIALIST_TOOLS


# ==================== detect_catalyst_mode Tests ====================


class TestDetectCatalystMode:
    @patch("scripts.config.requests")
    @patch("scripts.config.get_client")
    def test_native_meraki_device(self, mock_get_client, mock_requests):
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "MR46",
            "firmware": "wireless-29-0",
            "serial": "Q2XX-1234",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        result = detect_catalyst_mode("Q2XX-1234")
        assert result["serial"] == "Q2XX-1234"
        assert result["mode"] == "native_meraki"
        assert result["writable"] is True

    @patch("scripts.config.requests")
    @patch("scripts.config.get_client")
    def test_catalyst_managed(self, mock_get_client, mock_requests):
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "C9300-48P",
            "firmware": "catalyst-17.9",
            "serial": "FCW-1234",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        result = detect_catalyst_mode("FCW-1234")
        assert result["mode"] == "managed"
        assert result["writable"] is True

    @patch("scripts.config.requests")
    @patch("scripts.config.get_client")
    def test_catalyst_monitored(self, mock_get_client, mock_requests):
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "C9300-48P",
            "firmware": "monitor-mode-17.9",
            "serial": "FCW-5678",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        result = detect_catalyst_mode("FCW-5678")
        assert result["mode"] == "monitored"
        assert result["writable"] is False

    @patch("scripts.config.get_client")
    def test_api_failure(self, mock_get_client):
        mock_get_client.side_effect = Exception("Connection refused")

        result = detect_catalyst_mode("BAD-SERIAL")
        assert result["mode"] == "unknown"
        assert result["writable"] is False
        assert "error" in result


# ==================== sgt_preflight_check Tests ====================


class TestSgtPreflightCheck:
    @patch("scripts.config.check_switch_port_writeability")
    def test_no_sgt_restriction(self, mock_check):
        mock_preflight = MagicMock()
        mock_preflight.has_sgt_restriction = False
        mock_preflight.writable_ports = ["1", "2", "3"]
        mock_preflight.read_only_ports = []
        mock_preflight.writable_ratio = 1.0
        mock_check.return_value = mock_preflight

        result = sgt_preflight_check("Q2XX-1234")
        assert result["serial"] == "Q2XX-1234"
        assert result["has_sgt_restriction"] is False
        assert result["writable_ports"] == 3
        assert result["read_only_ports"] == 0
        assert "warning" not in result

    @patch("scripts.config.check_switch_port_writeability")
    def test_sgt_restriction_with_warning(self, mock_check):
        mock_preflight = MagicMock()
        mock_preflight.has_sgt_restriction = True
        mock_preflight.writable_ports = ["1"]
        mock_preflight.read_only_ports = [{"portId": "2"}, {"portId": "3"}, {"portId": "4"}]
        mock_preflight.writable_ratio = 0.25
        mock_check.return_value = mock_preflight

        result = sgt_preflight_check("FCW-1234")
        assert result["has_sgt_restriction"] is True
        assert result["writable_ratio"] == 0.25
        assert "warning" in result
        assert "SGT-locked" in result["warning"]

    @patch("scripts.config.check_switch_port_writeability")
    def test_api_failure(self, mock_check):
        mock_check.side_effect = Exception("API error")

        result = sgt_preflight_check("BAD-SERIAL")
        assert result["has_sgt_restriction"] is False
        assert "error" in result


# ==================== check_license Tests ====================


class TestCheckLicense:
    @patch("scripts.config.get_client")
    def test_unknown_license_no_org(self, mock_get_client):
        mock_client = MagicMock()
        # Remove org_id attribute
        del mock_client.org_id
        mock_get_client.return_value = mock_client

        result = check_license("Q2XX-1234")
        assert result["license_type"] == "unknown"
        assert result["features_available"] == []

    @patch("scripts.config.get_client")
    def test_api_failure(self, mock_get_client):
        mock_get_client.side_effect = Exception("Auth error")

        result = check_license("BAD-SERIAL")
        assert result["license_type"] == "unknown"
        assert "error" in result


# ==================== backup_current_state Tests ====================


class TestBackupCurrentState:
    @patch("scripts.config.backup_config")
    def test_successful_backup(self, mock_backup):
        mock_backup.return_value = "/clients/test/backups/backup.json"

        result = backup_current_state(
            resource_type="vlan",
            targets={"network_id": "N_123"},
            client_name="test-client",
        )

        assert result["resource_type"] == "vlan"
        assert result["backup_path"] == "/clients/test/backups/backup.json"
        assert "timestamp" in result
        assert result["targets"] == {"network_id": "N_123"}

    @patch("scripts.config.backup_config")
    def test_backup_failure(self, mock_backup):
        mock_backup.side_effect = Exception("Disk full")

        result = backup_current_state(
            resource_type="firewall",
            targets={"network_id": "N_456"},
            client_name="test-client",
        )

        assert result["backup_path"] == ""
        assert "error" in result
        assert "Disk full" in result["error"]


# ==================== FUNCTION_REGISTRY Tests ====================


class TestFunctionRegistry:
    def test_new_functions_registered(self):
        from scripts.agent_router import FUNCTION_REGISTRY

        assert "detect_catalyst_mode" in FUNCTION_REGISTRY
        assert "sgt_preflight_check" in FUNCTION_REGISTRY
        assert "check_license" in FUNCTION_REGISTRY
        assert "backup_current_state" in FUNCTION_REGISTRY

    def test_new_functions_callable(self):
        from scripts.agent_router import FUNCTION_REGISTRY

        for name in ["detect_catalyst_mode", "sgt_preflight_check", "check_license", "backup_current_state"]:
            assert callable(FUNCTION_REGISTRY[name])

    def test_existing_functions_preserved(self):
        from scripts.agent_router import FUNCTION_REGISTRY

        assert "full_discovery" in FUNCTION_REGISTRY
        assert "configure_ssid" in FUNCTION_REGISTRY
        assert "update_vlan" in FUNCTION_REGISTRY


# ==================== Safety Classification Tests ====================


class TestSafetyClassifications:
    def test_new_functions_safe(self):
        assert TOOL_SAFETY["detect_catalyst_mode"] == SafetyLevel.SAFE
        assert TOOL_SAFETY["sgt_preflight_check"] == SafetyLevel.SAFE
        assert TOOL_SAFETY["check_license"] == SafetyLevel.SAFE
        assert TOOL_SAFETY["backup_current_state"] == SafetyLevel.SAFE


# ==================== Schema Tests ====================


class TestToolSchemas:
    def _get_schema(self, name: str) -> dict:
        for tool in MERAKI_SPECIALIST_TOOLS:
            if tool["function"]["name"] == name:
                return tool
        return None

    def test_detect_catalyst_schema(self):
        schema = self._get_schema("detect_catalyst_mode")
        assert schema is not None
        assert schema["type"] == "function"
        params = schema["function"]["parameters"]
        assert "serial" in params["properties"]
        assert "serial" in params["required"]

    def test_sgt_preflight_schema(self):
        schema = self._get_schema("sgt_preflight_check")
        assert schema is not None
        assert "serial" in schema["function"]["parameters"]["required"]

    def test_check_license_schema(self):
        schema = self._get_schema("check_license")
        assert schema is not None
        assert "serial" in schema["function"]["parameters"]["required"]

    def test_backup_current_state_schema(self):
        schema = self._get_schema("backup_current_state")
        assert schema is not None
        params = schema["function"]["parameters"]
        assert "resource_type" in params["properties"]
        assert "targets" in params["properties"]
        assert "client_name" in params["properties"]
        assert "resource_type" in params["required"]

    def test_update_vlan_schema_complete(self):
        """Story 7.7 AC#8: update_vlan schema includes DHCP/DNS fields."""
        schema = self._get_schema("update_vlan")
        assert schema is not None
        props = schema["function"]["parameters"]["properties"]
        assert "dhcpHandling" in props
        assert "dnsNameservers" in props
        assert "dhcpOptions" in props
        assert "reservedIpRanges" in props

    def test_schemas_openai_format(self):
        """All schemas follow OpenAI function-calling format."""
        for tool in MERAKI_SPECIALIST_TOOLS:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            params = func["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
