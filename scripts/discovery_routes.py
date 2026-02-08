"""
REST API routes for network discovery.

Endpoints:
- POST /api/v1/discovery/full - Run full discovery
- GET /api/v1/discovery/snapshots - List snapshots
- GET /api/v1/discovery/snapshots/{id} - Load specific snapshot
- POST /api/v1/discovery/compare - Compare two snapshots
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.api import get_client
from scripts.discovery import (
    full_discovery,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    compare_snapshots,
    DiscoveryResult
)
from scripts.path_validation import validate_path_within_base, validate_path_component

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


# ==================== Request/Response Models ====================


class DiscoveryRequest(BaseModel):
    """Request to run full discovery."""
    client_name: str
    profile: Optional[str] = None


class SnapshotInfo(BaseModel):
    """Snapshot metadata."""
    path: str
    timestamp: str
    filename: str


class SnapshotCompareRequest(BaseModel):
    """Request to compare two snapshots."""
    old_path: str
    new_path: str


# ==================== Endpoints ====================


@router.post("/full")
async def run_full_discovery(request: DiscoveryRequest):
    """
    Run full network discovery for a client.

    Discovers networks, devices, configurations, and identifies issues.
    Saves snapshot to clients/{client_name}/discovery/ directory.

    Args:
        request: Discovery request with client name and optional profile

    Returns:
        Discovery result with summary, issues, and suggestions

    Raises:
        400: Invalid profile or client name
        502: Meraki API error
    """
    try:
        validate_path_component(request.client_name, "client_name")

        # Get Meraki client
        client = await asyncio.to_thread(
            get_client,
            request.profile or "default",
            False
        )

        # Run discovery
        logger.info(f"Running full discovery for client: {request.client_name}")
        result = await asyncio.to_thread(
            full_discovery,
            client.org_id,
            client
        )

        # Save snapshot
        snapshot_path = await asyncio.to_thread(
            save_snapshot,
            result,
            request.client_name
        )

        logger.info(f"Discovery complete. Snapshot saved: {snapshot_path}")

        # Return result as dict
        return {
            "discovery": result.to_dict(),
            "summary": result.summary(),
            "snapshot_path": str(snapshot_path)
        }

    except Exception as e:
        logger.exception(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")


@router.get("/snapshots")
async def get_snapshots(client: str):
    """
    List all snapshots for a client.

    Args:
        client: Client name

    Returns:
        List of snapshot metadata (path, timestamp, filename)
    """
    try:
        validate_path_component(client, "client")

        # List snapshots
        snapshots = await asyncio.to_thread(list_snapshots, client)

        # Convert to response format
        snapshot_list = []
        for snapshot_path in snapshots:
            # Extract timestamp from filename (discovery_YYYYMMDD_HHMMSS.json)
            filename = snapshot_path.name
            timestamp_str = filename.replace("discovery_", "").replace(".json", "")

            snapshot_list.append(
                SnapshotInfo(
                    path=str(snapshot_path),
                    timestamp=timestamp_str,
                    filename=filename
                )
            )

        return {"snapshots": snapshot_list}

    except Exception as e:
        logger.exception(f"Failed to list snapshots: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: str, client: str):
    """
    Load a specific snapshot.

    Args:
        snapshot_id: Snapshot filename or timestamp (YYYYMMDD_HHMMSS)
        client: Client name

    Returns:
        Full discovery result from snapshot

    Raises:
        404: Snapshot not found
    """
    try:
        # Validate path components
        validate_path_component(client, "client")
        validate_path_component(
            snapshot_id if snapshot_id.endswith(".json") else f"discovery_{snapshot_id}.json",
            "snapshot_id"
        )

        # Construct snapshot path
        if not snapshot_id.endswith(".json"):
            snapshot_id = f"discovery_{snapshot_id}.json"

        snapshot_path = Path("clients") / client / "discovery" / snapshot_id
        # Validate resolved path stays within base
        validated_path = validate_path_within_base(str(snapshot_path))

        if not validated_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Snapshot not found."
            )

        # Load snapshot
        result = await asyncio.to_thread(load_snapshot, validated_path)

        return {
            "discovery": result.to_dict(),
            "summary": result.summary()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to load snapshot: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")


@router.post("/compare")
async def compare_discovery_snapshots(request: SnapshotCompareRequest):
    """
    Compare two discovery snapshots.

    Args:
        request: Paths to old and new snapshots

    Returns:
        Diff showing changes between snapshots

    Raises:
        404: Snapshot not found
    """
    try:
        old_path = validate_path_within_base(request.old_path)
        new_path = validate_path_within_base(request.new_path)

        if not old_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Old snapshot not found."
            )

        if not new_path.exists():
            raise HTTPException(
                status_code=404,
                detail="New snapshot not found."
            )

        # Load snapshots
        old_result = await asyncio.to_thread(load_snapshot, old_path)
        new_result = await asyncio.to_thread(load_snapshot, new_path)

        # Compare
        diff = await asyncio.to_thread(compare_snapshots, old_result, new_result)

        return {"comparison": diff}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to compare snapshots: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")
