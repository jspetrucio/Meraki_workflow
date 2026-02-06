"""
REST API routes for Meraki profile management.

Endpoints:
- GET /api/v1/profiles - List all profiles
- GET /api/v1/profiles/{name} - Get profile details (masked)
- POST /api/v1/profiles/{name}/activate - Set active profile
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.auth import (
    load_profile,
    list_profiles,
    validate_credentials,
    CredentialsNotFoundError,
    InvalidProfileError
)
from scripts.settings import SettingsManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


# ==================== Response Models ====================


class ProfileResponse(BaseModel):
    """Profile details response (masked)."""
    name: str
    has_api_key: bool
    has_org_id: bool
    api_key_preview: Optional[str] = None  # First 8 chars only


class ProfileListResponse(BaseModel):
    """List of profiles response."""
    profiles: list[str]
    active: str


# ==================== Endpoints ====================


@router.get("", response_model=ProfileListResponse)
async def get_profiles():
    """
    List all available Meraki profiles.

    Returns list of profile names and the currently active profile.
    """
    # Run sync function in thread
    profiles = await asyncio.to_thread(list_profiles)

    # Get active profile from settings
    manager = SettingsManager()
    settings = manager.load()
    active_profile = settings.meraki_profile

    return ProfileListResponse(
        profiles=profiles,
        active=active_profile
    )


@router.get("/{name}", response_model=ProfileResponse)
async def get_profile(name: str):
    """
    Get profile details (with masked credentials).

    Args:
        name: Profile name

    Returns:
        Profile details with masked API key

    Raises:
        404: Profile not found
        400: Invalid profile
    """
    try:
        # Load profile in thread
        profile = await asyncio.to_thread(load_profile, name)

        # Mask API key (show first 8 chars only)
        api_key_preview = None
        if profile.api_key and len(profile.api_key) >= 8:
            api_key_preview = f"{profile.api_key[:8]}..."

        return ProfileResponse(
            name=profile.name,
            has_api_key=bool(profile.api_key),
            has_org_id=bool(profile.org_id),
            api_key_preview=api_key_preview
        )

    except CredentialsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidProfileError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{name}/activate", response_model=ProfileResponse)
async def activate_profile(name: str):
    """
    Set a profile as the active profile.

    Args:
        name: Profile name to activate

    Returns:
        Activated profile details

    Raises:
        404: Profile not found
        400: Invalid profile or validation failed
    """
    try:
        # Verify profile exists and load it
        profile = await asyncio.to_thread(load_profile, name)

        # Validate credentials
        valid, message = await asyncio.to_thread(validate_credentials, profile)
        if not valid:
            raise HTTPException(
                status_code=400,
                detail=f"Profile validation failed: {message}"
            )

        # Update settings
        manager = SettingsManager()
        manager.update(meraki_profile=name)

        logger.info(f"Activated profile: {name}")

        # Return profile details
        api_key_preview = None
        if profile.api_key and len(profile.api_key) >= 8:
            api_key_preview = f"{profile.api_key[:8]}..."

        return ProfileResponse(
            name=profile.name,
            has_api_key=bool(profile.api_key),
            has_org_id=bool(profile.org_id),
            api_key_preview=api_key_preview
        )

    except CredentialsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidProfileError as e:
        raise HTTPException(status_code=400, detail=str(e))
