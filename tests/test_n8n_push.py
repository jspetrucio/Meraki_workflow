"""
Tests for N8N workflow push and management endpoints.

Covers:
- POST /api/v1/n8n/workflows/push
- GET /api/v1/n8n/workflows/sync
- PUT /api/v1/n8n/workflows/{id}/activate
- PUT /api/v1/n8n/workflows/{id}/deactivate
- DELETE /api/v1/n8n/workflows/{id}
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scripts.n8n_client import N8NClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def n8n_client():
    """Mock N8N client."""
    return N8NClient(base_url="http://localhost:5678", api_key="test-key")


@pytest.fixture
def sample_workflow():
    """Sample N8N workflow JSON."""
    return {
        "name": "Test Workflow",
        "nodes": [
            {
                "id": "node1",
                "type": "n8n-nodes-base.scheduleTrigger",
                "parameters": {"rule": {"interval": [{"triggerAtHour": 7}]}}
            },
            {
                "id": "node2",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": "http://localhost:3141/api/v1/discovery/full",
                    "method": "POST"
                }
            }
        ],
        "connections": {
            "node1": {"main": [[{"node": "node2", "type": "main", "index": 0}]]}
        },
        "active": False
    }


@pytest.fixture
def sample_workflow_response():
    """Sample N8N API response for created workflow."""
    return {
        "id": "workflow123",
        "name": "Test Workflow",
        "active": False,
        "createdAt": "2026-02-05T10:00:00.000Z",
        "updatedAt": "2026-02-05T10:00:00.000Z",
        "nodes": [],
        "connections": {}
    }


@pytest.fixture
def sample_execution():
    """Sample N8N execution object."""
    return {
        "id": "exec123",
        "workflowId": "workflow123",
        "mode": "trigger",
        "startedAt": "2026-02-05T09:00:00.000Z",
        "stoppedAt": "2026-02-05T09:00:30.000Z",
        "status": "success",
        "data": {}
    }


# ---------------------------------------------------------------------------
# N8NClient Tests - New Methods
# ---------------------------------------------------------------------------


def test_delete_workflow_success(n8n_client):
    """Test successful workflow deletion."""
    with patch.object(n8n_client._client, 'delete') as mock_delete:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        n8n_client.delete_workflow("workflow123")

        mock_delete.assert_called_once_with("/api/v1/workflows/workflow123")


def test_delete_workflow_not_found(n8n_client):
    """Test deletion of non-existent workflow."""
    with patch.object(n8n_client._client, 'delete') as mock_delete:
        mock_delete.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        with pytest.raises(httpx.HTTPStatusError):
            n8n_client.delete_workflow("nonexistent")


def test_get_workflow_executions(n8n_client):
    """Test getting executions for a specific workflow."""
    with patch.object(n8n_client._client, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "exec1", "status": "success"},
                {"id": "exec2", "status": "error"}
            ]
        }
        mock_get.return_value = mock_response

        result = n8n_client.get_workflow_executions("workflow123", limit=5)

        assert len(result) == 2
        assert result[0]["id"] == "exec1"
        mock_get.assert_called_once()


def test_activate_workflow(n8n_client):
    """Test activating a workflow."""
    with patch.object(n8n_client._client, 'patch') as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "workflow123",
            "name": "Test",
            "active": True
        }
        mock_patch.return_value = mock_response

        result = n8n_client.activate_workflow("workflow123")

        assert result["active"] is True
        mock_patch.assert_called_once_with(
            "/api/v1/workflows/workflow123",
            json={"active": True}
        )


def test_deactivate_workflow(n8n_client):
    """Test deactivating a workflow."""
    with patch.object(n8n_client._client, 'patch') as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "workflow123",
            "name": "Test",
            "active": False
        }
        mock_patch.return_value = mock_response

        result = n8n_client.deactivate_workflow("workflow123")

        assert result["active"] is False
        mock_patch.assert_called_once_with(
            "/api/v1/workflows/workflow123",
            json={"active": False}
        )


# ---------------------------------------------------------------------------
# API Route Tests - Mock N8N responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_push_workflow_success(sample_workflow, sample_workflow_response):
    """Test pushing a workflow to N8N."""
    from scripts.n8n_routes import push_workflow, WorkflowPushRequest

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.create_workflow.return_value = sample_workflow_response
        mock_client.return_value = mock_instance

        req = WorkflowPushRequest(workflow=sample_workflow)
        result = await push_workflow(req)

        assert result["success"] is True
        assert result["workflow_id"] == "workflow123"
        assert result["workflow_name"] == "Test Workflow"
        mock_instance.create_workflow.assert_called_once_with(sample_workflow)


@pytest.mark.asyncio
async def test_push_workflow_n8n_unavailable():
    """Test push when N8N is not available."""
    from scripts.n8n_routes import push_workflow, WorkflowPushRequest
    from fastapi import HTTPException

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_client.return_value = None

        req = WorkflowPushRequest(workflow={"name": "Test"})

        with pytest.raises(HTTPException) as exc_info:
            await push_workflow(req)

        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_sync_workflows_success(sample_workflow_response, sample_execution):
    """Test syncing workflows from N8N."""
    from scripts.n8n_routes import sync_workflows

    workflows = [
        {**sample_workflow_response, "id": "wf1"},
        {**sample_workflow_response, "id": "wf2", "name": "Another Workflow"}
    ]

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.list_workflows.return_value = workflows
        mock_instance.get_workflow_executions.return_value = [sample_execution]
        mock_client.return_value = mock_instance

        result = await sync_workflows()

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["workflows"]) == 2
        # Check that execution data was enriched
        assert "lastExecution" in result["workflows"][0]


@pytest.mark.asyncio
async def test_sync_workflows_handles_execution_errors():
    """Test sync continues when execution fetch fails for a workflow."""
    from scripts.n8n_routes import sync_workflows

    workflows = [{"id": "wf1", "name": "Test"}]

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.list_workflows.return_value = workflows
        mock_instance.get_workflow_executions.side_effect = httpx.HTTPError("Error")
        mock_client.return_value = mock_instance

        result = await sync_workflows()

        # Sync should still succeed, but lastExecution will be None
        assert result["success"] is True
        assert result["workflows"][0]["lastExecution"] is None


@pytest.mark.asyncio
async def test_activate_workflow_endpoint():
    """Test activate workflow endpoint."""
    from scripts.n8n_routes import activate_workflow

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.activate_workflow.return_value = {
            "id": "workflow123",
            "name": "Test Workflow",
            "active": True
        }
        mock_client.return_value = mock_instance

        result = await activate_workflow("workflow123")

        assert result["success"] is True
        assert result["workflow_id"] == "workflow123"
        assert result["active"] is True
        assert "activated" in result["message"]


@pytest.mark.asyncio
async def test_deactivate_workflow_endpoint():
    """Test deactivate workflow endpoint."""
    from scripts.n8n_routes import deactivate_workflow

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.deactivate_workflow.return_value = {
            "id": "workflow123",
            "name": "Test Workflow",
            "active": False
        }
        mock_client.return_value = mock_instance

        result = await deactivate_workflow("workflow123")

        assert result["success"] is True
        assert result["workflow_id"] == "workflow123"
        assert result["active"] is False
        assert "deactivated" in result["message"]


@pytest.mark.asyncio
async def test_delete_workflow_endpoint():
    """Test delete workflow endpoint."""
    from scripts.n8n_routes import delete_workflow

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.delete_workflow.return_value = None
        mock_client.return_value = mock_instance

        result = await delete_workflow("workflow123")

        assert result["success"] is True
        assert result["workflow_id"] == "workflow123"
        assert "deleted" in result["message"]
        mock_instance.delete_workflow.assert_called_once_with("workflow123")


@pytest.mark.asyncio
async def test_delete_workflow_n8n_error():
    """Test delete when N8N returns error."""
    from scripts.n8n_routes import delete_workflow
    from fastapi import HTTPException

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.delete_workflow.side_effect = httpx.HTTPError("Not found")
        mock_client.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            await delete_workflow("workflow123")

        assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# Integration Tests - Multiple operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_workflow_lifecycle(sample_workflow, sample_workflow_response):
    """Test complete workflow lifecycle: push -> activate -> deactivate -> delete."""
    from scripts.n8n_routes import (
        push_workflow, WorkflowPushRequest,
        activate_workflow,
        deactivate_workflow,
        delete_workflow
    )

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # 1. Push workflow
        mock_instance.create_workflow.return_value = sample_workflow_response
        push_result = await push_workflow(WorkflowPushRequest(workflow=sample_workflow))
        workflow_id = push_result["workflow_id"]

        # 2. Activate workflow
        mock_instance.activate_workflow.return_value = {
            **sample_workflow_response,
            "active": True
        }
        activate_result = await activate_workflow(workflow_id)
        assert activate_result["active"] is True

        # 3. Deactivate workflow
        mock_instance.deactivate_workflow.return_value = {
            **sample_workflow_response,
            "active": False
        }
        deactivate_result = await deactivate_workflow(workflow_id)
        assert deactivate_result["active"] is False

        # 4. Delete workflow
        mock_instance.delete_workflow.return_value = None
        delete_result = await delete_workflow(workflow_id)
        assert delete_result["success"] is True


@pytest.mark.asyncio
async def test_sync_after_push(sample_workflow, sample_workflow_response):
    """Test that sync reflects newly pushed workflow."""
    from scripts.n8n_routes import (
        push_workflow, WorkflowPushRequest,
        sync_workflows
    )

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Push workflow
        mock_instance.create_workflow.return_value = sample_workflow_response
        await push_workflow(WorkflowPushRequest(workflow=sample_workflow))

        # Sync workflows
        mock_instance.list_workflows.return_value = [sample_workflow_response]
        mock_instance.get_workflow_executions.return_value = []

        sync_result = await sync_workflows()

        assert sync_result["count"] == 1
        assert sync_result["workflows"][0]["id"] == "workflow123"


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_push_invalid_workflow_json():
    """Test pushing malformed workflow JSON."""
    from scripts.n8n_routes import push_workflow, WorkflowPushRequest
    from fastapi import HTTPException

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.create_workflow.side_effect = httpx.HTTPError("Invalid JSON")
        mock_client.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            await push_workflow(WorkflowPushRequest(workflow={"name": "Test"}))

        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_activate_nonexistent_workflow():
    """Test activating a workflow that doesn't exist."""
    from scripts.n8n_routes import activate_workflow
    from fastapi import HTTPException

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.activate_workflow.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )
        mock_client.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            await activate_workflow("nonexistent")

        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_sync_workflows_n8n_down():
    """Test sync when N8N server is down."""
    from scripts.n8n_routes import sync_workflows
    from fastapi import HTTPException

    with patch('scripts.n8n_routes._check_n8n_enabled'), \
         patch('scripts.n8n_routes.get_n8n_client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.list_workflows.side_effect = httpx.ConnectError("Connection refused")
        mock_client.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            await sync_workflows()

        assert exc_info.value.status_code == 502
