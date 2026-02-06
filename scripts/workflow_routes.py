"""
REST API routes for workflow management.

Endpoints:
- GET /api/v1/workflows - List workflows
- POST /api/v1/workflows - Create workflow
- GET /api/v1/workflows/templates - List templates
- POST /api/v1/workflows/from-template - Create from template
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.workflow import (
    list_workflows,
    save_workflow,
    create_device_offline_handler,
    create_firmware_compliance_check,
    create_scheduled_report,
    create_security_alert_handler,
    generate_import_instructions,
    WorkflowError,
    WorkflowValidationError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


# ==================== Request Models ====================


class WorkflowCreateRequest(BaseModel):
    """Request to create workflow."""
    client_name: str
    workflow_type: str  # device-offline, firmware-compliance, scheduled-report, security-alert
    params: Optional[dict] = None


class WorkflowTemplateRequest(BaseModel):
    """Request to create workflow from template."""
    client_name: str
    template_type: str
    params: Optional[dict] = None


# ==================== Template Definitions ====================


WORKFLOW_TEMPLATES = {
    "device-offline": {
        "name": "Device Offline Handler",
        "description": "Notifies when device goes offline",
        "params": {
            "slack_channel": {"type": "string", "default": "#network-alerts"},
            "wait_minutes": {"type": "integer", "default": 5}
        }
    },
    "firmware-compliance": {
        "name": "Firmware Compliance Check",
        "description": "Checks firmware versions across devices",
        "params": {
            "target_version": {"type": "string", "required": True},
            "email_recipients": {"type": "array", "required": True}
        }
    },
    "scheduled-report": {
        "name": "Scheduled Report",
        "description": "Generates periodic reports",
        "params": {
            "report_type": {"type": "string", "default": "discovery"},
            "schedule_cron": {"type": "string", "default": "0 8 * * 1"},
            "email_recipients": {"type": "array", "required": True}
        }
    },
    "security-alert": {
        "name": "Security Alert Handler",
        "description": "Processes security alerts",
        "params": {
            "slack_channel": {"type": "string", "default": "#security"},
            "pagerduty_enabled": {"type": "boolean", "default": False}
        }
    }
}


# ==================== Endpoints ====================


@router.get("")
async def get_workflows(client: str):
    """
    List workflows for a client.

    Args:
        client: Client name

    Returns:
        List of workflow names
    """
    try:
        workflows = await asyncio.to_thread(list_workflows, client)
        return {"workflows": workflows}

    except Exception as e:
        logger.exception(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")


@router.post("")
async def create_workflow(request: WorkflowCreateRequest):
    """
    Create a new workflow.

    Args:
        request: Workflow type and parameters

    Returns:
        Created workflow details and import instructions

    Raises:
        400: Invalid workflow type or parameters
        422: Workflow validation error
    """
    try:
        workflow_type = request.workflow_type
        params = request.params or {}

        # Create workflow based on type
        if workflow_type == "device-offline":
            workflow = create_device_offline_handler(
                slack_channel=params.get("slack_channel", "#network-alerts"),
                wait_minutes=params.get("wait_minutes", 5)
            )

        elif workflow_type == "firmware-compliance":
            if "target_version" not in params or "email_recipients" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="target_version and email_recipients are required"
                )
            workflow = create_firmware_compliance_check(
                target_version=params["target_version"],
                email_recipients=params["email_recipients"]
            )

        elif workflow_type == "scheduled-report":
            if "email_recipients" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="email_recipients is required"
                )
            workflow = create_scheduled_report(
                report_type=params.get("report_type", "discovery"),
                schedule_cron=params.get("schedule_cron", "0 8 * * 1"),
                email_recipients=params["email_recipients"]
            )

        elif workflow_type == "security-alert":
            workflow = create_security_alert_handler(
                slack_channel=params.get("slack_channel", "#security"),
                pagerduty_enabled=params.get("pagerduty_enabled", False)
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown workflow type: {workflow_type}"
            )

        # Save workflow
        filepath = await asyncio.to_thread(
            save_workflow,
            workflow,
            request.client_name
        )

        # Generate import instructions
        instructions = generate_import_instructions(workflow, request.client_name)

        logger.info(f"Workflow created: {filepath}")

        return {
            "workflow": workflow.to_simple_dict(),
            "filepath": str(filepath),
            "import_instructions": instructions
        }

    except WorkflowValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Workflow creation failed: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")


@router.get("/templates")
async def get_templates():
    """
    List available workflow templates.

    Returns:
        Dictionary of template definitions
    """
    return {"templates": WORKFLOW_TEMPLATES}


@router.post("/from-template")
async def create_from_template(request: WorkflowTemplateRequest):
    """
    Create workflow from template.

    Args:
        request: Template type and parameters

    Returns:
        Created workflow details and import instructions

    Raises:
        400: Invalid template type or missing required params
        422: Workflow validation error
    """
    try:
        template_type = request.template_type
        params = request.params or {}

        # Validate template exists
        if template_type not in WORKFLOW_TEMPLATES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown template: {template_type}. Available: {list(WORKFLOW_TEMPLATES.keys())}"
            )

        # Validate required params
        template_def = WORKFLOW_TEMPLATES[template_type]
        for param_name, param_def in template_def["params"].items():
            if param_def.get("required") and param_name not in params:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameter: {param_name}"
                )

        # Create workflow (same logic as create_workflow)
        if template_type == "device-offline":
            workflow = create_device_offline_handler(
                slack_channel=params.get("slack_channel", "#network-alerts"),
                wait_minutes=params.get("wait_minutes", 5)
            )

        elif template_type == "firmware-compliance":
            workflow = create_firmware_compliance_check(
                target_version=params["target_version"],
                email_recipients=params["email_recipients"]
            )

        elif template_type == "scheduled-report":
            workflow = create_scheduled_report(
                report_type=params.get("report_type", "discovery"),
                schedule_cron=params.get("schedule_cron", "0 8 * * 1"),
                email_recipients=params["email_recipients"]
            )

        elif template_type == "security-alert":
            workflow = create_security_alert_handler(
                slack_channel=params.get("slack_channel", "#security"),
                pagerduty_enabled=params.get("pagerduty_enabled", False)
            )

        # Save workflow
        filepath = await asyncio.to_thread(
            save_workflow,
            workflow,
            request.client_name
        )

        # Generate import instructions
        instructions = generate_import_instructions(workflow, request.client_name)

        logger.info(f"Workflow created from template {template_type}: {filepath}")

        return {
            "workflow": workflow.to_simple_dict(),
            "filepath": str(filepath),
            "import_instructions": instructions
        }

    except WorkflowValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Workflow creation from template failed: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Check server logs for details.")
