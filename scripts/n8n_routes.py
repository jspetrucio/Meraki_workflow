"""
REST API routes for N8N integration.

Provides endpoints for:
- Test connection to N8N instance
- List/create workflows
- Get execution history

All routes require N8N to be enabled in settings, otherwise return 503.
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.n8n_client import get_n8n_client
from scripts.n8n_template_engine import N8NTemplateEngine
from scripts.settings import SettingsManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/n8n", tags=["n8n"])


# ---------------------------------------------------------------------------
# Response / Request models
# ---------------------------------------------------------------------------


class N8NConnectionResult(BaseModel):
    """Result of N8N connection test."""
    connected: bool
    message: str
    version: Optional[str] = None


class N8NWorkflowCreate(BaseModel):
    """Request to create a new N8N workflow."""
    name: str
    nodes: list[dict]
    connections: dict


class N8NWorkflowResponse(BaseModel):
    """N8N workflow object."""
    id: str
    name: str
    active: bool
    nodes: list[dict]
    connections: dict
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class N8NExecutionResponse(BaseModel):
    """N8N execution object."""
    id: str
    workflowId: str
    mode: str
    startedAt: str
    stoppedAt: Optional[str] = None
    status: str


class TemplateDeployRequest(BaseModel):
    """Request to deploy a template."""
    variables: dict = {}


class WorkflowPushRequest(BaseModel):
    """Request to push a rendered workflow to N8N."""
    workflow: dict


class WorkflowActivateRequest(BaseModel):
    """Request to activate/deactivate a workflow."""
    active: bool


# ---------------------------------------------------------------------------
# Helper to check if N8N is enabled
# ---------------------------------------------------------------------------


def _check_n8n_enabled():
    """Raise 503 if N8N is not enabled."""
    manager = SettingsManager()
    settings = manager.load()
    if not settings.n8n_enabled:
        raise HTTPException(
            status_code=503,
            detail="N8N not configured"
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/test-connection", response_model=N8NConnectionResult)
async def test_connection():
    """
    Test connectivity to N8N instance.

    Returns:
        N8NConnectionResult with connection status and version info
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        return N8NConnectionResult(
            connected=False,
            message="N8N client could not be initialized"
        )

    try:
        # Run in thread pool to avoid blocking
        result = await asyncio.to_thread(client.test_connection)
        client.close()

        return N8NConnectionResult(
            connected=True,
            message="Connected to N8N",
            version=result.get("version")
        )
    except Exception as exc:
        if client:
            client.close()
        return N8NConnectionResult(
            connected=False,
            message=f"Connection failed: {type(exc).__name__}"
        )


@router.get("/workflows")
async def list_workflows():
    """
    List all N8N workflows.

    Returns:
        list[dict]: Array of workflow objects
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        workflows = await asyncio.to_thread(client.list_workflows)
        return workflows
    except Exception as exc:
        logger.error(f"Failed to list N8N workflows: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.post("/workflows")
async def create_workflow(req: N8NWorkflowCreate):
    """
    Create a new N8N workflow.

    Args:
        req: Workflow creation request

    Returns:
        dict: Created workflow object
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        workflow_data = {
            "name": req.name,
            "nodes": req.nodes,
            "connections": req.connections
        }
        result = await asyncio.to_thread(client.create_workflow, workflow_data)
        return result
    except Exception as exc:
        logger.error(f"Failed to create N8N workflow: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.get("/executions")
async def get_executions(
    workflow_id: Optional[str] = None,
    limit: int = 20
):
    """
    Get N8N execution history.

    Args:
        workflow_id: Optional workflow ID to filter by
        limit: Maximum number of executions to return (default: 20)

    Returns:
        list[dict]: Array of execution objects
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        executions = await asyncio.to_thread(
            client.get_executions,
            workflow_id=workflow_id,
            limit=limit
        )
        return executions
    except Exception as exc:
        logger.error(f"Failed to get N8N executions: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Template Endpoints
# ---------------------------------------------------------------------------


@router.get("/templates")
async def list_templates():
    """
    List all available N8N workflow templates.

    Returns:
        list[dict]: Array of template objects with metadata
    """
    engine = N8NTemplateEngine()
    templates = engine.list_templates()
    return templates


@router.post("/templates/{template_name}/deploy")
async def deploy_template(template_name: str, req: TemplateDeployRequest):
    """
    Deploy a workflow template to N8N.

    Renders the template with provided variables and creates the workflow.

    Args:
        template_name: Template ID (e.g., "daily-discovery")
        req: Deployment request with variable values

    Returns:
        dict: Created workflow object with deployment info
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    engine = N8NTemplateEngine()

    try:
        # Deploy template
        result = await asyncio.to_thread(
            engine.deploy,
            client,
            template_name,
            req.variables
        )

        return {
            "success": True,
            "workflow_id": result.get("id"),
            "workflow_name": result.get("name"),
            "active": result.get("active", False),
            "message": f"Template '{template_name}' deployed successfully"
        }
    except ValueError as exc:
        # Template rendering errors (missing variables, invalid template)
        logger.error(f"Template rendering error: {exc}")
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    except Exception as exc:
        # N8N API errors
        logger.error(f"Failed to deploy template '{template_name}': {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Workflow Management Endpoints
# ---------------------------------------------------------------------------


@router.post("/workflows/push")
async def push_workflow(req: WorkflowPushRequest):
    """
    Push a rendered workflow directly to N8N instance.

    This endpoint accepts a complete N8N workflow JSON and creates it.
    Use this when you have a pre-rendered workflow (e.g., from template engine).

    Args:
        req: Workflow push request with complete workflow JSON

    Returns:
        dict: Created workflow object from N8N
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        result = await asyncio.to_thread(client.create_workflow, req.workflow)
        return {
            "success": True,
            "workflow_id": result.get("id"),
            "workflow_name": result.get("name"),
            "active": result.get("active", False),
            "message": "Workflow pushed successfully"
        }
    except Exception as exc:
        logger.error(f"Failed to push workflow: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.get("/workflows/sync")
async def sync_workflows():
    """
    Sync workflow status from N8N instance.

    Fetches all workflows from N8N with their current activation status
    and recent execution information.

    Returns:
        dict: Sync result with workflows array and metadata
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        # Get all workflows
        workflows = await asyncio.to_thread(client.list_workflows)

        # Enrich with execution data
        for workflow in workflows:
            wf_id = workflow.get("id")
            if wf_id:
                try:
                    # Get last execution for this workflow
                    executions = await asyncio.to_thread(
                        client.get_workflow_executions,
                        wf_id,
                        limit=1
                    )
                    if executions:
                        last_exec = executions[0]
                        workflow["lastExecution"] = {
                            "startedAt": last_exec.get("startedAt"),
                            "stoppedAt": last_exec.get("stoppedAt"),
                            "status": last_exec.get("status", "unknown")
                        }
                except Exception as exc:
                    logger.warning(f"Failed to get executions for workflow {wf_id}: {exc}")
                    workflow["lastExecution"] = None

        return {
            "success": True,
            "workflows": workflows,
            "count": len(workflows),
            "synced_at": "now"  # Could use datetime.now().isoformat()
        }
    except Exception as exc:
        logger.error(f"Failed to sync workflows: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.put("/workflows/{workflow_id}/activate")
async def activate_workflow(workflow_id: str):
    """
    Activate a workflow on N8N instance.

    Args:
        workflow_id: N8N workflow ID

    Returns:
        dict: Updated workflow object
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        result = await asyncio.to_thread(client.activate_workflow, workflow_id)
        return {
            "success": True,
            "workflow_id": result.get("id"),
            "active": result.get("active", False),
            "message": f"Workflow '{result.get('name')}' activated"
        }
    except Exception as exc:
        logger.error(f"Failed to activate workflow {workflow_id}: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.put("/workflows/{workflow_id}/deactivate")
async def deactivate_workflow(workflow_id: str):
    """
    Deactivate a workflow on N8N instance.

    Args:
        workflow_id: N8N workflow ID

    Returns:
        dict: Updated workflow object
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        result = await asyncio.to_thread(client.deactivate_workflow, workflow_id)
        return {
            "success": True,
            "workflow_id": result.get("id"),
            "active": result.get("active", False),
            "message": f"Workflow '{result.get('name')}' deactivated"
        }
    except Exception as exc:
        logger.error(f"Failed to deactivate workflow {workflow_id}: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    Delete a workflow from N8N instance.

    Args:
        workflow_id: N8N workflow ID

    Returns:
        dict: Deletion confirmation
    """
    _check_n8n_enabled()

    client = get_n8n_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="N8N client not available"
        )

    try:
        await asyncio.to_thread(client.delete_workflow, workflow_id)
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow deleted successfully"
        }
    except Exception as exc:
        logger.error(f"Failed to delete workflow {workflow_id}: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"N8N API error: {type(exc).__name__}"
        )
    finally:
        client.close()
