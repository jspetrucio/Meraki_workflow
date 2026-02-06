"""
REST API routes for network configuration.

Endpoints:
- POST /api/v1/config/ssid - Configure SSID
- POST /api/v1/config/firewall - Add firewall rule
- POST /api/v1/config/acl - Add switch ACL
- POST /api/v1/config/vlan - Create VLAN
- POST /api/v1/config/rollback - Rollback configuration
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.api import get_client
from scripts.config import (
    configure_ssid,
    add_firewall_rule,
    add_switch_acl,
    create_vlan,
    rollback_config,
    backup_config,
    ConfigResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


# ==================== Request Models ====================


class SSIDConfigRequest(BaseModel):
    """Request to configure SSID."""
    network_id: str
    client_name: str
    ssid_number: int = 0
    name: Optional[str] = None
    enabled: Optional[bool] = None
    auth_mode: Optional[str] = None
    psk: Optional[str] = None
    vlan_id: Optional[int] = None
    ip_assignment_mode: Optional[str] = None


class FirewallRuleRequest(BaseModel):
    """Request to add firewall rule."""
    network_id: str
    client_name: str
    policy: str  # allow or deny
    protocol: str  # tcp, udp, icmp, any
    src_cidr: str = "any"
    dest_cidr: str = "any"
    dest_port: str = "any"
    comment: Optional[str] = None
    position: Optional[int] = None


class ACLRequest(BaseModel):
    """Request to add switch ACL."""
    network_id: str
    client_name: str
    policy: str  # allow or deny
    protocol: str  # tcp, udp, any
    src_cidr: str
    src_port: str
    dest_cidr: str
    dest_port: str
    vlan: str = "any"
    comment: Optional[str] = None


class VLANRequest(BaseModel):
    """Request to create VLAN."""
    network_id: str
    client_name: str
    vlan_id: int
    name: str
    subnet: str
    appliance_ip: str


class RollbackRequest(BaseModel):
    """Request to rollback configuration."""
    backup_path: str
    client_name: str


# ==================== Helper Functions ====================


def config_result_to_dict(result: ConfigResult) -> dict:
    """Convert ConfigResult to JSON-serializable dict."""
    return {
        "success": result.success,
        "action": result.action.value,
        "resource_type": result.resource_type,
        "resource_id": result.resource_id,
        "message": result.message,
        "backup_path": str(result.backup_path) if result.backup_path else None,
        "changes": result.changes,
        "error": result.error
    }


# ==================== Endpoints ====================


@router.post("/ssid")
async def config_ssid(request: SSIDConfigRequest):
    """
    Configure a wireless SSID.

    Automatically creates backup before applying changes.

    Args:
        request: SSID configuration parameters

    Returns:
        Configuration result with backup path

    Raises:
        502: Meraki API error
    """
    try:
        # Get client
        client = await asyncio.to_thread(get_client)

        # Apply configuration
        result = await asyncio.to_thread(
            configure_ssid,
            network_id=request.network_id,
            ssid_number=request.ssid_number,
            name=request.name,
            enabled=request.enabled,
            auth_mode=request.auth_mode,
            psk=request.psk,
            vlan_id=request.vlan_id,
            ip_assignment_mode=request.ip_assignment_mode,
            backup=True,
            client_name=request.client_name,
            client=client
        )

        logger.info(f"SSID config result: {result}")
        return config_result_to_dict(result)

    except Exception as e:
        logger.exception(f"SSID configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/firewall")
async def config_firewall(request: FirewallRuleRequest):
    """
    Add a firewall L3 rule.

    Automatically creates backup before applying changes.

    Args:
        request: Firewall rule parameters

    Returns:
        Configuration result with backup path

    Raises:
        502: Meraki API error
    """
    try:
        # Get client
        client = await asyncio.to_thread(get_client)

        # Apply configuration
        result = await asyncio.to_thread(
            add_firewall_rule,
            network_id=request.network_id,
            policy=request.policy,
            protocol=request.protocol,
            src_cidr=request.src_cidr,
            dest_cidr=request.dest_cidr,
            dest_port=request.dest_port,
            comment=request.comment,
            position=request.position,
            backup=True,
            client_name=request.client_name,
            client=client
        )

        logger.info(f"Firewall config result: {result}")
        return config_result_to_dict(result)

    except Exception as e:
        logger.exception(f"Firewall configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/acl")
async def config_acl(request: ACLRequest):
    """
    Add a switch ACL rule.

    Automatically creates backup before applying changes.

    Args:
        request: ACL rule parameters

    Returns:
        Configuration result with backup path

    Raises:
        502: Meraki API error
    """
    try:
        # Get client
        client = await asyncio.to_thread(get_client)

        # Apply configuration
        result = await asyncio.to_thread(
            add_switch_acl,
            network_id=request.network_id,
            policy=request.policy,
            protocol=request.protocol,
            src_cidr=request.src_cidr,
            src_port=request.src_port,
            dest_cidr=request.dest_cidr,
            dest_port=request.dest_port,
            vlan=request.vlan,
            comment=request.comment,
            backup=True,
            client_name=request.client_name,
            client=client
        )

        logger.info(f"ACL config result: {result}")
        return config_result_to_dict(result)

    except Exception as e:
        logger.exception(f"ACL configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vlan")
async def config_vlan(request: VLANRequest):
    """
    Create a VLAN.

    Automatically creates backup before applying changes.

    Args:
        request: VLAN parameters

    Returns:
        Configuration result with backup path

    Raises:
        502: Meraki API error
    """
    try:
        # Get client
        client = await asyncio.to_thread(get_client)

        # Apply configuration
        result = await asyncio.to_thread(
            create_vlan,
            network_id=request.network_id,
            vlan_id=request.vlan_id,
            name=request.name,
            subnet=request.subnet,
            appliance_ip=request.appliance_ip,
            backup=True,
            client_name=request.client_name,
            client=client
        )

        logger.info(f"VLAN config result: {result}")
        return config_result_to_dict(result)

    except Exception as e:
        logger.exception(f"VLAN configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def config_rollback(request: RollbackRequest):
    """
    Rollback configuration from backup.

    Args:
        request: Backup path and client name

    Returns:
        Rollback result

    Raises:
        404: Backup not found
        502: Meraki API error
    """
    try:
        backup_path = Path(request.backup_path)

        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup not found: {request.backup_path}"
            )

        # Get client
        client = await asyncio.to_thread(get_client)

        # Rollback
        result = await asyncio.to_thread(
            rollback_config,
            backup_path=backup_path,
            client=client
        )

        logger.info(f"Rollback result: {result}")
        return config_result_to_dict(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
