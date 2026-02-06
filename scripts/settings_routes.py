"""
REST API routes for settings and credential management.

Provides endpoints for:
- GET/PATCH settings
- Credential provider listing and saving
- Credential validation
- Onboarding status

This router is mounted by server.py (Story 1.1).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from scripts.settings import Settings, SettingsManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["settings"])

# Singleton manager — shared across all requests
_manager = SettingsManager()

VALID_PROVIDERS = {"anthropic", "openai", "google", "ollama"}
VALID_THEMES = {"dark", "light"}


# ---------------------------------------------------------------------------
# Response / Request models
# ---------------------------------------------------------------------------

class SettingsResponse(BaseModel):
    ai_provider: str
    ai_model: str
    has_ai_key: bool
    meraki_profile: str
    n8n_enabled: bool
    n8n_url: Optional[str] = None
    has_n8n_key: bool
    theme: str
    language: str
    port: int

    @classmethod
    def from_settings(cls, s: Settings) -> "SettingsResponse":
        return cls(
            ai_provider=s.ai_provider,
            ai_model=s.ai_model,
            has_ai_key=bool(s.ai_api_key),
            meraki_profile=s.meraki_profile,
            n8n_enabled=s.n8n_enabled,
            n8n_url=s.n8n_url,
            has_n8n_key=bool(s.n8n_api_key),
            theme=s.theme,
            language=s.language,
            port=s.port,
        )


class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    meraki_profile: Optional[str] = None
    n8n_enabled: Optional[bool] = None
    n8n_url: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None

    @field_validator("ai_provider")
    @classmethod
    def validate_provider(cls, v):
        if v is not None and v not in VALID_PROVIDERS:
            raise ValueError(f"Unknown provider '{v}'. Valid: {sorted(VALID_PROVIDERS)}")
        return v

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v):
        if v is not None and v not in VALID_THEMES:
            raise ValueError(f"Unknown theme '{v}'. Valid: {sorted(VALID_THEMES)}")
        return v


class CredentialSaveRequest(BaseModel):
    api_key: str


class ProviderInfo(BaseModel):
    name: str
    has_key: bool


class ValidationRequest(BaseModel):
    type: str  # "meraki", "ai", "n8n"
    api_key: Optional[str] = None
    org_id: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("meraki", "ai", "n8n"):
            raise ValueError("type must be 'meraki', 'ai', or 'n8n'")
        return v


class ValidationResponse(BaseModel):
    valid: bool
    message: str


class OnboardingStatusResponse(BaseModel):
    complete: bool
    missing: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    settings = _manager.load()
    return SettingsResponse.from_settings(settings)


@router.patch("/settings", response_model=SettingsResponse)
async def update_settings(req: SettingsUpdateRequest):
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    settings = _manager.update(**updates)
    return SettingsResponse.from_settings(settings)


@router.get("/credentials/providers", response_model=list[ProviderInfo])
async def list_providers():
    settings = _manager.load()
    providers = []
    for name in sorted(VALID_PROVIDERS):
        has_key = bool(settings.ai_api_key) if name == settings.ai_provider else False
        providers.append(ProviderInfo(name=name, has_key=has_key))
    return providers


@router.post("/credentials/provider/{name}", response_model=SettingsResponse)
async def save_provider_key(name: str, req: CredentialSaveRequest):
    if name not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{name}'. Valid: {sorted(VALID_PROVIDERS)}")
    settings = _manager.update(ai_provider=name, ai_api_key=req.api_key)
    return SettingsResponse.from_settings(settings)


@router.post("/credentials/validate", response_model=ValidationResponse)
async def validate_credentials(req: ValidationRequest):
    if req.type == "meraki":
        if not req.api_key:
            raise HTTPException(status_code=400, detail="api_key required for Meraki validation")
        valid, msg = _manager.validate_meraki_credentials(req.api_key, req.org_id)
    elif req.type == "ai":
        if not req.api_key or not req.provider:
            raise HTTPException(status_code=400, detail="api_key and provider required for AI validation")
        valid, msg = _manager.validate_ai_credentials(req.provider, req.api_key)
    elif req.type == "n8n":
        if not req.url:
            raise HTTPException(status_code=400, detail="url required for N8N validation")
        valid, msg = _manager.validate_n8n_connection(req.url, req.api_key)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown validation type: {req.type}")

    return ValidationResponse(valid=valid, message=msg)


@router.get("/settings/onboarding-status", response_model=OnboardingStatusResponse)
async def onboarding_status():
    settings = _manager.load()
    missing = []
    if not settings.ai_api_key:
        missing.append("ai_api_key")
    try:
        from scripts.auth import load_profile
        load_profile(settings.meraki_profile)
    except Exception:
        missing.append("meraki_profile")
    return OnboardingStatusResponse(complete=len(missing) == 0, missing=missing)
