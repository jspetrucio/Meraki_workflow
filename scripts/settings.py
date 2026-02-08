"""
Gestao de configuracoes e credenciais AI para o CNL.

Armazena configuracoes em ~/.cnl/settings.json.
Chaves de API sao criptografadas em repouso usando Fernet.

Credenciais Meraki continuam em ~/.meraki/credentials (gerenciadas por auth.py).
Este modulo armazena APENAS o nome do profile ativo.
"""

import hashlib
import json
import logging
import os
import socket
from base64 import urlsafe_b64encode
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Encryption prefix for stored keys
_ENC_PREFIX = "enc:"


@dataclass
class Settings:
    """Configuracoes da aplicacao CNL."""

    # AI Provider
    ai_provider: str = "anthropic"
    ai_model: str = "claude-sonnet"
    ai_api_key: Optional[str] = None

    # Meraki
    meraki_profile: str = "default"

    # N8N (optional)
    n8n_enabled: bool = False
    n8n_url: Optional[str] = None
    n8n_api_key: Optional[str] = None

    # UI
    theme: str = "dark"
    language: str = "en"

    # Server
    port: int = 3141

    # Privacy
    telemetry_enabled: bool = False

    # Feature Flags
    use_modular_tasks: bool = True


class SettingsManager:
    """Gerencia carregamento, salvamento e criptografia de configuracoes."""

    CONFIG_DIR = Path.home() / ".cnl"
    SETTINGS_FILE = CONFIG_DIR / "settings.json"

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is not None:
            self.CONFIG_DIR = config_dir
            self.SETTINGS_FILE = config_dir / "settings.json"

    def _ensure_dir(self) -> None:
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Encryption
    # ------------------------------------------------------------------

    def _derive_fernet_key(self) -> bytes:
        """Derive a Fernet key from machine-specific data."""
        hostname = socket.gethostname()
        username = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        raw = f"{hostname}:{username}".encode()
        digest = hashlib.sha256(raw).digest()
        return urlsafe_b64encode(digest)

    def _get_fernet(self):
        """Return a Fernet instance. Import lazily to avoid hard dependency at module level."""
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logger.warning("cryptography package not installed — keys will NOT be encrypted")
            return None
        return Fernet(self._derive_fernet_key())

    def encrypt_key(self, key: str) -> str:
        """Encrypt a plaintext key. Returns enc:-prefixed string or original if crypto unavailable."""
        if not key:
            return key
        fernet = self._get_fernet()
        if fernet is None:
            return key
        token = fernet.encrypt(key.encode()).decode()
        return f"{_ENC_PREFIX}{token}"

    def decrypt_key(self, encrypted: str) -> Optional[str]:
        """Decrypt an enc:-prefixed string. Returns None on failure."""
        if not encrypted or not encrypted.startswith(_ENC_PREFIX):
            return encrypted
        fernet = self._get_fernet()
        if fernet is None:
            return None
        try:
            token = encrypted[len(_ENC_PREFIX):]
            return fernet.decrypt(token.encode()).decode()
        except Exception:
            logger.warning("Decryption failed (machine changed?) — clearing stored key")
            return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> Settings:
        """Load settings from disk. Returns defaults if file missing."""
        if not self.SETTINGS_FILE.exists():
            return Settings()

        try:
            data = json.loads(self.SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read settings file, using defaults: %s", exc)
            return Settings()

        # Decrypt encrypted fields
        for key_field in ("ai_api_key", "n8n_api_key"):
            raw = data.get(key_field)
            if raw and isinstance(raw, str) and raw.startswith(_ENC_PREFIX):
                data[key_field] = self.decrypt_key(raw)

        # Filter to known fields only
        known = {f.name for f in Settings.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return Settings(**filtered)

    def save(self, settings: Settings) -> None:
        """Save settings to disk with encrypted keys."""
        self._ensure_dir()
        data = asdict(settings)

        # Encrypt sensitive fields
        for key_field in ("ai_api_key", "n8n_api_key"):
            value = data.get(key_field)
            if value and not value.startswith(_ENC_PREFIX):
                data[key_field] = self.encrypt_key(value)

        self.SETTINGS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update(self, **kwargs) -> Settings:
        """Partial update: load, merge, save, return new settings."""
        settings = self.load()
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        self.save(settings)
        return settings

    def is_onboarding_complete(self) -> bool:
        """Check if minimum configuration is done (AI key + Meraki profile exists)."""
        settings = self.load()
        if not settings.ai_api_key:
            return False
        try:
            from scripts.auth import load_profile
            load_profile(settings.meraki_profile)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Meraki helpers
    # ------------------------------------------------------------------

    def get_active_meraki_profile(self):
        """Load the active Meraki profile via auth module."""
        from scripts.auth import load_profile
        settings = self.load()
        return load_profile(settings.meraki_profile)

    # ------------------------------------------------------------------
    # Credential validation
    # ------------------------------------------------------------------

    def validate_meraki_credentials(self, api_key: str, org_id: Optional[str] = None) -> tuple[bool, str]:
        """Validate Meraki credentials by calling the API."""
        try:
            import meraki
            dashboard = meraki.DashboardAPI(api_key, suppress_logging=True, output_log=False)
            orgs = dashboard.organizations.getOrganizations()
            if org_id:
                org_ids = [o["id"] for o in orgs]
                if org_id not in org_ids:
                    return False, f"org_id '{org_id}' not found. Available: {org_ids}"
            org_names = ", ".join(o["name"] for o in orgs[:3])
            return True, f"Connected to org(s): {org_names}"
        except Exception as exc:
            return False, f"Invalid API key: {exc}"

    def validate_ai_credentials(self, provider: str, api_key: str) -> tuple[bool, str]:
        """Validate AI provider credentials via LiteLLM test completion."""
        try:
            import litellm
        except ImportError:
            return False, "LiteLLM not installed — install with: pip install litellm"
        try:
            model_map = {
                "anthropic": "claude-sonnet-4-5-20250929",
                "openai": "gpt-4o-mini",
                "google": "gemini/gemini-2.0-flash",
            }
            model = model_map.get(provider, provider)
            litellm.completion(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                api_key=api_key,
                max_tokens=5,
            )
            return True, f"Connected to {provider}"
        except Exception as exc:
            return False, f"{exc}"

    def validate_n8n_connection(self, url: str, api_key: Optional[str] = None) -> tuple[bool, str]:
        """Validate N8N connection by hitting the workflows endpoint."""
        import urllib.request
        import urllib.error

        target = f"{url.rstrip('/')}/api/v1/workflows"
        req = urllib.request.Request(target, method="GET")
        if api_key:
            req.add_header("X-N8N-API-KEY", api_key)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                count = len(data.get("data", []))
                return True, f"N8N connected: {count} workflows"
        except Exception as exc:
            return False, f"{exc}"
