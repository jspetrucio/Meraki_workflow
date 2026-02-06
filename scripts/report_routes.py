"""
REST API routes for report generation.

Endpoints:
- GET /api/v1/reports/{client} - List reports
- GET /api/v1/reports/{client}/{filename} - Serve report HTML
- POST /api/v1/reports/{client}/generate - Generate discovery report
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from scripts.api import get_client
from scripts.discovery import full_discovery, load_snapshot
from scripts.report import generate_discovery_report, save_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# ==================== Request Models ====================


class ReportGenerateRequest(BaseModel):
    """Request to generate report."""
    profile: Optional[str] = None
    snapshot_path: Optional[str] = None  # If provided, use snapshot instead of new discovery


# ==================== Helper Functions ====================


def get_report_dir(client_name: str) -> Path:
    """Get reports directory for a client."""
    report_dir = Path("clients") / client_name / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def list_report_files(client_name: str) -> list[dict]:
    """List all HTML reports for a client."""
    report_dir = get_report_dir(client_name)

    if not report_dir.exists():
        return []

    reports = []
    for html_file in sorted(report_dir.glob("*.html"), reverse=True):
        # Get file info
        stat = html_file.stat()
        reports.append({
            "filename": html_file.name,
            "path": str(html_file),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime
        })

    return reports


# ==================== Endpoints ====================


@router.get("/{client}")
async def get_reports(client: str):
    """
    List all reports for a client.

    Args:
        client: Client name

    Returns:
        List of report files with metadata
    """
    try:
        reports = await asyncio.to_thread(list_report_files, client)
        return {"reports": reports}

    except Exception as e:
        logger.exception(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client}/{filename}")
async def get_report_file(client: str, filename: str):
    """
    Serve a report HTML file.

    Args:
        client: Client name
        filename: Report filename

    Returns:
        HTML file response

    Raises:
        404: Report not found
    """
    try:
        report_path = Path("clients") / client / "reports" / filename

        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {filename}"
            )

        # Serve HTML file
        return FileResponse(
            path=str(report_path),
            media_type="text/html",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to serve report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{client}/generate")
async def generate_report(client: str, request: ReportGenerateRequest):
    """
    Generate a discovery report for a client.

    Can either run new discovery or use existing snapshot.

    Args:
        client: Client name
        request: Generation options (profile, snapshot path)

    Returns:
        Report path and summary

    Raises:
        404: Snapshot not found (if snapshot_path provided)
        502: Meraki API error (if running new discovery)
    """
    try:
        # Load or create discovery result
        if request.snapshot_path:
            # Use existing snapshot
            snapshot_path = Path(request.snapshot_path)

            if not snapshot_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Snapshot not found: {request.snapshot_path}"
                )

            logger.info(f"Generating report from snapshot: {snapshot_path}")
            discovery = await asyncio.to_thread(load_snapshot, snapshot_path)

        else:
            # Run new discovery
            logger.info(f"Running discovery for report: {client}")
            meraki_client = await asyncio.to_thread(
                get_client,
                request.profile or "default",
                False
            )

            discovery = await asyncio.to_thread(
                full_discovery,
                meraki_client.org_id,
                meraki_client
            )

        # Generate report
        logger.info(f"Generating HTML report for {client}")
        report = await asyncio.to_thread(
            generate_discovery_report,
            discovery,
            client
        )

        # Save HTML
        report_path = await asyncio.to_thread(save_html, report)

        logger.info(f"Report generated: {report_path}")

        return {
            "report_path": str(report_path),
            "filename": report_path.name,
            "summary": discovery.summary()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
