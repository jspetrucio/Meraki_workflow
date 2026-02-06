"""
Tests for scripts/settings.py and scripts/settings_routes.py
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.settings import Settings, SettingsManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a SettingsManager pointing at a temp directory."""
    return SettingsManager(config_dir=tmp_path)


@pytest.fixture
def populated_manager(temp_config_dir):
    """Manager with saved settings including an AI key."""
    s = Settings(ai_provider="openai", ai_model="gpt-4o", ai_api_key="sk-test-key-12345", theme="light")
    temp_config_dir.save(s)
    return temp_config_dir


# ---------------------------------------------------------------------------
# T1: Settings dataclass
# ---------------------------------------------------------------------------

class TestSettingsDefaults:
    def test_defaults(self):
        s = Settings()
        assert s.ai_provider == "anthropic"
        assert s.ai_model == "claude-sonnet"
        assert s.ai_api_key is None
        assert s.meraki_profile == "default"
        assert s.n8n_enabled is False
        assert s.n8n_url is None
        assert s.n8n_api_key is None
        assert s.theme == "dark"
        assert s.language == "en"
        assert s.port == 3141
        assert s.telemetry_enabled is False

    def test_custom_values(self):
        s = Settings(ai_provider="openai", theme="light", port=8080)
        assert s.ai_provider == "openai"
        assert s.theme == "light"
        assert s.port == 8080


# ---------------------------------------------------------------------------
# T1: SettingsManager load/save/update
# ---------------------------------------------------------------------------

class TestSettingsManager:
    def test_load_returns_defaults_when_no_file(self, temp_config_dir):
        s = temp_config_dir.load()
        assert s.ai_provider == "anthropic"
        assert s.theme == "dark"

    def test_save_creates_file(self, temp_config_dir):
        s = Settings()
        temp_config_dir.save(s)
        assert temp_config_dir.SETTINGS_FILE.exists()

    def test_save_load_roundtrip(self, temp_config_dir):
        original = Settings(ai_provider="openai", theme="light", language="pt")
        temp_config_dir.save(original)
        loaded = temp_config_dir.load()
        assert loaded.ai_provider == "openai"
        assert loaded.theme == "light"
        assert loaded.language == "pt"

    def test_update_partial(self, temp_config_dir):
        temp_config_dir.save(Settings())
        updated = temp_config_dir.update(theme="light", language="pt")
        assert updated.theme == "light"
        assert updated.language == "pt"
        assert updated.ai_provider == "anthropic"  # unchanged

    def test_update_persists(self, temp_config_dir):
        temp_config_dir.save(Settings())
        temp_config_dir.update(ai_provider="google")
        loaded = temp_config_dir.load()
        assert loaded.ai_provider == "google"

    def test_load_handles_corrupt_file(self, temp_config_dir):
        temp_config_dir._ensure_dir()
        temp_config_dir.SETTINGS_FILE.write_text("NOT JSON", encoding="utf-8")
        s = temp_config_dir.load()
        assert s.ai_provider == "anthropic"  # defaults

    def test_load_ignores_unknown_fields(self, temp_config_dir):
        temp_config_dir._ensure_dir()
        data = {"ai_provider": "openai", "unknown_field": "hello"}
        temp_config_dir.SETTINGS_FILE.write_text(json.dumps(data), encoding="utf-8")
        s = temp_config_dir.load()
        assert s.ai_provider == "openai"
        assert not hasattr(s, "unknown_field")

    def test_dir_auto_created(self, tmp_path):
        nested = tmp_path / "sub" / "dir"
        mgr = SettingsManager(config_dir=nested)
        mgr.save(Settings())
        assert nested.exists()


# ---------------------------------------------------------------------------
# T2: Encryption
# ---------------------------------------------------------------------------

class TestEncryption:
    def test_roundtrip(self, temp_config_dir):
        encrypted = temp_config_dir.encrypt_key("sk-test-key-12345")
        assert encrypted.startswith("enc:")
        decrypted = temp_config_dir.decrypt_key(encrypted)
        assert decrypted == "sk-test-key-12345"

    def test_encrypt_empty_returns_empty(self, temp_config_dir):
        assert temp_config_dir.encrypt_key("") == ""
        assert temp_config_dir.encrypt_key(None) is None

    def test_decrypt_non_prefixed_returns_as_is(self, temp_config_dir):
        assert temp_config_dir.decrypt_key("plain-text") == "plain-text"

    def test_decrypt_bad_token_returns_none(self, temp_config_dir):
        result = temp_config_dir.decrypt_key("enc:totally-invalid-token")
        assert result is None

    def test_keys_encrypted_on_save(self, temp_config_dir):
        s = Settings(ai_api_key="sk-my-secret")
        temp_config_dir.save(s)
        raw = json.loads(temp_config_dir.SETTINGS_FILE.read_text())
        assert raw["ai_api_key"].startswith("enc:")

    def test_keys_decrypted_on_load(self, temp_config_dir):
        s = Settings(ai_api_key="sk-my-secret")
        temp_config_dir.save(s)
        loaded = temp_config_dir.load()
        assert loaded.ai_api_key == "sk-my-secret"

    def test_n8n_key_encrypted(self, temp_config_dir):
        s = Settings(n8n_api_key="n8n-secret-key")
        temp_config_dir.save(s)
        raw = json.loads(temp_config_dir.SETTINGS_FILE.read_text())
        assert raw["n8n_api_key"].startswith("enc:")
        loaded = temp_config_dir.load()
        assert loaded.n8n_api_key == "n8n-secret-key"


# ---------------------------------------------------------------------------
# T1.7: Onboarding
# ---------------------------------------------------------------------------

class TestOnboarding:
    def test_incomplete_no_key(self, temp_config_dir):
        temp_config_dir.save(Settings())
        assert temp_config_dir.is_onboarding_complete() is False

    def test_incomplete_when_profile_missing(self, temp_config_dir):
        temp_config_dir.save(Settings(ai_api_key="sk-key"))
        with patch("scripts.auth.load_profile", side_effect=Exception("not found")):
            assert temp_config_dir.is_onboarding_complete() is False

    def test_complete(self, temp_config_dir):
        temp_config_dir.save(Settings(ai_api_key="sk-key"))
        mock_profile = MagicMock()
        with patch("scripts.auth.load_profile", return_value=mock_profile):
            assert temp_config_dir.is_onboarding_complete() is True


# ---------------------------------------------------------------------------
# T4: Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_get_active_meraki_profile_delegates_to_auth(self, temp_config_dir):
        temp_config_dir.save(Settings(meraki_profile="cliente-acme"))
        mock_profile = MagicMock()
        with patch("scripts.auth.load_profile", return_value=mock_profile) as mock_load:
            result = temp_config_dir.get_active_meraki_profile()
            mock_load.assert_called_once_with("cliente-acme")
            assert result is mock_profile

    def test_settings_never_modifies_meraki_credentials(self, temp_config_dir, tmp_path):
        creds_file = tmp_path / ".meraki" / "credentials"
        creds_file.parent.mkdir(parents=True)
        creds_file.write_text("[default]\napi_key = ORIGINAL\norg_id = 123\n")
        original_content = creds_file.read_text()

        # Perform various settings operations
        temp_config_dir.save(Settings(meraki_profile="default"))
        temp_config_dir.update(meraki_profile="other")
        temp_config_dir.load()

        assert creds_file.read_text() == original_content


# ---------------------------------------------------------------------------
# T3: Credential validation
# ---------------------------------------------------------------------------

class TestCredentialValidation:
    def test_validate_meraki_success(self, temp_config_dir):
        with patch("meraki.DashboardAPI") as mock_api:
            mock_dash = MagicMock()
            mock_dash.organizations.getOrganizations.return_value = [
                {"id": "123", "name": "TestOrg"}
            ]
            mock_api.return_value = mock_dash
            valid, msg = temp_config_dir.validate_meraki_credentials("valid-key")
            assert valid is True
            assert "TestOrg" in msg

    def test_validate_meraki_failure(self, temp_config_dir):
        with patch("meraki.DashboardAPI", side_effect=Exception("unauthorized")):
            valid, msg = temp_config_dir.validate_meraki_credentials("bad-key")
            assert valid is False

    def test_validate_ai_no_litellm(self, temp_config_dir):
        with patch.dict("sys.modules", {"litellm": None}):
            import importlib
            valid, msg = temp_config_dir.validate_ai_credentials("anthropic", "sk-key")
            # Will fail with import error or LiteLLM message
            assert valid is False

    def test_validate_n8n_success(self, temp_config_dir):
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"data": [{"id": 1}, {"id": 2}]}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp
            valid, msg = temp_config_dir.validate_n8n_connection("http://localhost:5678")
            assert valid is True
            assert "2 workflows" in msg

    def test_validate_n8n_failure(self, temp_config_dir):
        with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
            valid, msg = temp_config_dir.validate_n8n_connection("http://localhost:9999")
            assert valid is False


# ---------------------------------------------------------------------------
# T5: REST API endpoints
# ---------------------------------------------------------------------------

class TestSettingsRoutes:
    @pytest.fixture(autouse=True)
    def setup_routes(self, temp_config_dir):
        """Patch the singleton manager in routes module."""
        from scripts import settings_routes
        self._original_manager = settings_routes._manager
        settings_routes._manager = temp_config_dir
        yield
        settings_routes._manager = self._original_manager

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from scripts.settings_routes import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_get_settings_defaults(self, client):
        resp = client.get("/api/v1/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_provider"] == "anthropic"
        assert data["has_ai_key"] is False
        assert data["theme"] == "dark"

    def test_get_settings_masks_keys(self, client, temp_config_dir):
        temp_config_dir.save(Settings(ai_api_key="sk-secret-key"))
        resp = client.get("/api/v1/settings")
        data = resp.json()
        assert data["has_ai_key"] is True
        assert "sk-secret" not in json.dumps(data)

    def test_patch_settings(self, client):
        resp = client.patch("/api/v1/settings", json={"theme": "light", "language": "pt"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] == "light"
        assert data["language"] == "pt"

    def test_patch_settings_invalid_provider(self, client):
        resp = client.patch("/api/v1/settings", json={"ai_provider": "unknown"})
        assert resp.status_code == 422

    def test_patch_settings_invalid_theme(self, client):
        resp = client.patch("/api/v1/settings", json={"theme": "rainbow"})
        assert resp.status_code == 422

    def test_patch_settings_empty(self, client):
        resp = client.patch("/api/v1/settings", json={})
        assert resp.status_code == 400

    def test_list_providers(self, client):
        resp = client.get("/api/v1/credentials/providers")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "anthropic" in names
        assert "openai" in names

    def test_save_provider_key(self, client):
        resp = client.post(
            "/api/v1/credentials/provider/anthropic",
            json={"api_key": "sk-ant-key"},
        )
        assert resp.status_code == 200
        assert resp.json()["has_ai_key"] is True
        assert resp.json()["ai_provider"] == "anthropic"

    def test_save_provider_key_invalid(self, client):
        resp = client.post(
            "/api/v1/credentials/provider/badprovider",
            json={"api_key": "sk-key"},
        )
        assert resp.status_code == 400

    def test_validate_endpoint_missing_fields(self, client):
        resp = client.post("/api/v1/credentials/validate", json={"type": "meraki"})
        assert resp.status_code == 400

    def test_validate_endpoint_invalid_type(self, client):
        resp = client.post("/api/v1/credentials/validate", json={"type": "invalid"})
        assert resp.status_code == 422

    def test_onboarding_status_incomplete(self, client):
        resp = client.get("/api/v1/settings/onboarding-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["complete"] is False
        assert "ai_api_key" in data["missing"]

    def test_onboarding_status_complete(self, client, temp_config_dir):
        temp_config_dir.save(Settings(ai_api_key="sk-key"))
        with patch("scripts.auth.load_profile", return_value=MagicMock()):
            resp = client.get("/api/v1/settings/onboarding-status")
            data = resp.json()
            assert data["complete"] is True
            assert data["missing"] == []
