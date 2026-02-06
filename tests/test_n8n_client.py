"""
Tests for N8N API client and routes.

Tests:
- N8NClient authentication headers (self-hosted vs cloud)
- N8NClient API methods with mocked httpx responses
- get_n8n_client helper function
- N8N routes with mocked client
- Graceful degradation when N8N not configured
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from scripts.n8n_client import N8NClient, get_n8n_client
from scripts.settings import Settings, SettingsManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def self_hosted_client():
    """N8N client for self-hosted instance."""
    return N8NClient(base_url="http://localhost:5678", api_key="test-key-123")


@pytest.fixture
def cloud_client():
    """N8N client for n8n.cloud instance."""
    return N8NClient(base_url="https://my-instance.app.n8n.cloud", api_key="cloud-token-456")


@pytest.fixture
def no_auth_client():
    """N8N client without authentication."""
    return N8NClient(base_url="http://localhost:5678")


@pytest.fixture
def mock_settings_manager(tmp_path):
    """Mock settings manager with temporary directory."""
    manager = SettingsManager(config_dir=tmp_path)
    return manager


# ---------------------------------------------------------------------------
# TestN8NClientAuth - Authentication header tests
# ---------------------------------------------------------------------------


class TestN8NClientAuth:
    """Test authentication header generation."""

    def test_self_hosted_auth_header(self, self_hosted_client):
        """Self-hosted N8N should use X-N8N-API-KEY header."""
        headers = self_hosted_client._auth_headers()
        assert headers == {"X-N8N-API-KEY": "test-key-123"}

    def test_cloud_auth_header(self, cloud_client):
        """N8N cloud should use Bearer token."""
        headers = cloud_client._auth_headers()
        assert headers == {"Authorization": "Bearer cloud-token-456"}

    def test_no_auth_header(self, no_auth_client):
        """No auth key should return empty headers."""
        headers = no_auth_client._auth_headers()
        assert headers == {}

    def test_invalid_url_scheme(self):
        """Invalid URL scheme should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            N8NClient(base_url="ftp://invalid.com", api_key="key")

    def test_url_trailing_slash_stripped(self):
        """Trailing slash should be stripped from URL."""
        client = N8NClient(base_url="http://localhost:5678/", api_key="key")
        assert client.base_url == "http://localhost:5678"


# ---------------------------------------------------------------------------
# TestN8NClientMethods - API method tests with mocked responses
# ---------------------------------------------------------------------------


class TestN8NClientMethods:
    """Test N8N API client methods."""

    @patch("httpx.Client.get")
    def test_test_connection_success(self, mock_get, self_hosted_client):
        """test_connection should return version info on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "version": "1.0.0"}
        mock_get.return_value = mock_response

        result = self_hosted_client.test_connection()

        assert result["status"] == "ok"
        assert result["version"] == "1.0.0"
        mock_get.assert_called_once_with("/api/v1")

    @patch("httpx.Client.get")
    def test_test_connection_failure(self, mock_get, self_hosted_client):
        """test_connection should raise HTTPError on failure."""
        mock_get.side_effect = httpx.HTTPError("Connection refused")

        with pytest.raises(httpx.HTTPError):
            self_hosted_client.test_connection()

    @patch("httpx.Client.get")
    def test_list_workflows_success(self, mock_get, self_hosted_client):
        """list_workflows should return array of workflows."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "name": "Workflow 1"},
                {"id": "2", "name": "Workflow 2"}
            ]
        }
        mock_get.return_value = mock_response

        workflows = self_hosted_client.list_workflows()

        assert len(workflows) == 2
        assert workflows[0]["name"] == "Workflow 1"
        mock_get.assert_called_once_with("/api/v1/workflows")

    @patch("httpx.Client.get")
    def test_list_workflows_empty(self, mock_get, self_hosted_client):
        """list_workflows should handle empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        workflows = self_hosted_client.list_workflows()

        assert workflows == []

    @patch("httpx.Client.get")
    def test_get_workflow_success(self, mock_get, self_hosted_client):
        """get_workflow should return workflow by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "My Workflow",
            "active": True
        }
        mock_get.return_value = mock_response

        workflow = self_hosted_client.get_workflow("123")

        assert workflow["id"] == "123"
        assert workflow["name"] == "My Workflow"
        mock_get.assert_called_once_with("/api/v1/workflows/123")

    @patch("httpx.Client.post")
    def test_create_workflow_success(self, mock_post, self_hosted_client):
        """create_workflow should POST workflow data."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "456",
            "name": "New Workflow",
            "active": False
        }
        mock_post.return_value = mock_response

        workflow_data = {
            "name": "New Workflow",
            "nodes": [],
            "connections": {}
        }
        result = self_hosted_client.create_workflow(workflow_data)

        assert result["id"] == "456"
        mock_post.assert_called_once_with("/api/v1/workflows", json=workflow_data)

    @patch("httpx.Client.patch")
    def test_activate_workflow_success(self, mock_patch, self_hosted_client):
        """activate_workflow should PATCH with active=true."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "active": True
        }
        mock_patch.return_value = mock_response

        result = self_hosted_client.activate_workflow("123")

        assert result["active"] is True
        mock_patch.assert_called_once_with(
            "/api/v1/workflows/123",
            json={"active": True}
        )

    @patch("httpx.Client.patch")
    def test_deactivate_workflow_success(self, mock_patch, self_hosted_client):
        """deactivate_workflow should PATCH with active=false."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "active": False
        }
        mock_patch.return_value = mock_response

        result = self_hosted_client.deactivate_workflow("123")

        assert result["active"] is False
        mock_patch.assert_called_once_with(
            "/api/v1/workflows/123",
            json={"active": False}
        )

    @patch("httpx.Client.get")
    def test_get_executions_success(self, mock_get, self_hosted_client):
        """get_executions should return execution history."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "exec1", "workflowId": "123", "status": "success"},
                {"id": "exec2", "workflowId": "123", "status": "failed"}
            ]
        }
        mock_get.return_value = mock_response

        executions = self_hosted_client.get_executions(workflow_id="123", limit=10)

        assert len(executions) == 2
        assert executions[0]["status"] == "success"
        mock_get.assert_called_once_with(
            "/api/v1/executions",
            params={"limit": 10, "workflowId": "123"}
        )

    @patch("httpx.Client.get")
    def test_get_executions_no_workflow_filter(self, mock_get, self_hosted_client):
        """get_executions without workflow_id should not include workflowId param."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        self_hosted_client.get_executions(limit=20)

        mock_get.assert_called_once_with(
            "/api/v1/executions",
            params={"limit": 20}
        )

    def test_close_client(self, self_hosted_client):
        """close should call httpx client close."""
        with patch.object(self_hosted_client._client, 'close') as mock_close:
            self_hosted_client.close()
            mock_close.assert_called_once()


# ---------------------------------------------------------------------------
# TestGetN8NClient - Helper function tests
# ---------------------------------------------------------------------------


class TestGetN8NClient:
    """Test get_n8n_client helper function."""

    def test_returns_none_when_not_enabled(self, mock_settings_manager):
        """Should return None when n8n_enabled is False."""
        settings = Settings(
            n8n_enabled=False,
            n8n_url="http://localhost:5678"
        )
        mock_settings_manager.save(settings)

        with patch("scripts.n8n_client.SettingsManager", return_value=mock_settings_manager):
            client = get_n8n_client()
            assert client is None

    def test_returns_none_when_no_url(self, mock_settings_manager):
        """Should return None when n8n_url is not set."""
        settings = Settings(
            n8n_enabled=True,
            n8n_url=None
        )
        mock_settings_manager.save(settings)

        with patch("scripts.n8n_client.SettingsManager", return_value=mock_settings_manager):
            client = get_n8n_client()
            assert client is None

    def test_returns_client_when_configured(self, mock_settings_manager):
        """Should return N8NClient when properly configured."""
        settings = Settings(
            n8n_enabled=True,
            n8n_url="http://localhost:5678",
            n8n_api_key="test-key"
        )
        mock_settings_manager.save(settings)

        with patch("scripts.n8n_client.SettingsManager", return_value=mock_settings_manager):
            client = get_n8n_client()
            assert client is not None
            assert isinstance(client, N8NClient)
            assert client.base_url == "http://localhost:5678"
            assert client.api_key == "test-key"

    def test_returns_none_on_exception(self, mock_settings_manager):
        """Should return None if exception occurs during client creation."""
        settings = Settings(
            n8n_enabled=True,
            n8n_url="invalid://url",  # Invalid scheme
            n8n_api_key="test-key"
        )
        mock_settings_manager.save(settings)

        with patch("scripts.n8n_client.SettingsManager", return_value=mock_settings_manager):
            client = get_n8n_client()
            assert client is None


# ---------------------------------------------------------------------------
# TestN8NRoutes - API route tests
# ---------------------------------------------------------------------------


class TestN8NRoutes:
    """Test N8N FastAPI routes."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with N8N routes."""
        from fastapi import FastAPI
        from scripts.n8n_routes import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """FastAPI test client."""
        return TestClient(app)

    @patch("scripts.n8n_routes.get_n8n_client")
    @patch("scripts.n8n_routes.SettingsManager")
    def test_test_connection_success(self, mock_settings_mgr, mock_get_client, client):
        """POST /test-connection should return success when N8N is reachable."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.n8n_enabled = True
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # Mock N8N client
        mock_n8n = Mock()
        mock_n8n.test_connection.return_value = {"status": "ok", "version": "1.0.0"}
        mock_get_client.return_value = mock_n8n

        response = client.post("/api/v1/n8n/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["version"] == "1.0.0"
        mock_n8n.close.assert_called_once()

    @patch("scripts.n8n_routes.get_n8n_client")
    @patch("scripts.n8n_routes.SettingsManager")
    def test_test_connection_failure(self, mock_settings_mgr, mock_get_client, client):
        """POST /test-connection should return failure when N8N is unreachable."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.n8n_enabled = True
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # Mock N8N client that raises exception
        mock_n8n = Mock()
        mock_n8n.test_connection.side_effect = httpx.ConnectError("Connection refused")
        mock_get_client.return_value = mock_n8n

        response = client.post("/api/v1/n8n/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert "ConnectError" in data["message"]

    @patch("scripts.n8n_routes.SettingsManager")
    def test_test_connection_not_enabled(self, mock_settings_mgr, client):
        """POST /test-connection should return 503 when N8N not enabled."""
        mock_settings = Mock()
        mock_settings.n8n_enabled = False
        mock_settings_mgr.return_value.load.return_value = mock_settings

        response = client.post("/api/v1/n8n/test-connection")

        assert response.status_code == 503
        assert response.json()["detail"] == "N8N not configured"

    @patch("scripts.n8n_routes.get_n8n_client")
    @patch("scripts.n8n_routes.SettingsManager")
    def test_list_workflows_success(self, mock_settings_mgr, mock_get_client, client):
        """GET /workflows should return workflow list."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.n8n_enabled = True
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # Mock N8N client
        mock_n8n = Mock()
        mock_n8n.list_workflows.return_value = [
            {"id": "1", "name": "Workflow 1"},
            {"id": "2", "name": "Workflow 2"}
        ]
        mock_get_client.return_value = mock_n8n

        response = client.get("/api/v1/n8n/workflows")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Workflow 1"
        mock_n8n.close.assert_called_once()

    @patch("scripts.n8n_routes.SettingsManager")
    def test_list_workflows_not_enabled(self, mock_settings_mgr, client):
        """GET /workflows should return 503 when N8N not enabled."""
        mock_settings = Mock()
        mock_settings.n8n_enabled = False
        mock_settings_mgr.return_value.load.return_value = mock_settings

        response = client.get("/api/v1/n8n/workflows")

        assert response.status_code == 503

    @patch("scripts.n8n_routes.get_n8n_client")
    @patch("scripts.n8n_routes.SettingsManager")
    def test_create_workflow_success(self, mock_settings_mgr, mock_get_client, client):
        """POST /workflows should create workflow."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.n8n_enabled = True
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # Mock N8N client
        mock_n8n = Mock()
        mock_n8n.create_workflow.return_value = {
            "id": "new-wf",
            "name": "Test Workflow",
            "active": False
        }
        mock_get_client.return_value = mock_n8n

        workflow_data = {
            "name": "Test Workflow",
            "nodes": [],
            "connections": {}
        }
        response = client.post("/api/v1/n8n/workflows", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "new-wf"
        mock_n8n.close.assert_called_once()

    @patch("scripts.n8n_routes.get_n8n_client")
    @patch("scripts.n8n_routes.SettingsManager")
    def test_get_executions_success(self, mock_settings_mgr, mock_get_client, client):
        """GET /executions should return execution history."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.n8n_enabled = True
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # Mock N8N client
        mock_n8n = Mock()
        mock_n8n.get_executions.return_value = [
            {"id": "exec1", "status": "success"}
        ]
        mock_get_client.return_value = mock_n8n

        response = client.get("/api/v1/n8n/executions?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_n8n.close.assert_called_once()


# ---------------------------------------------------------------------------
# TestGracefulDegradation - No errors when N8N not configured
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """Test that application handles missing N8N configuration gracefully."""

    def test_get_n8n_client_no_config_no_error(self, mock_settings_manager):
        """get_n8n_client should return None without errors when not configured."""
        settings = Settings(n8n_enabled=False)
        mock_settings_manager.save(settings)

        with patch("scripts.n8n_client.SettingsManager", return_value=mock_settings_manager):
            # Should not raise any exceptions
            client = get_n8n_client()
            assert client is None

    def test_settings_load_with_n8n_defaults(self, mock_settings_manager):
        """Settings should load with N8N defaults without errors."""
        # Don't save anything - use defaults
        settings = mock_settings_manager.load()

        assert settings.n8n_enabled is False
        assert settings.n8n_url is None
        assert settings.n8n_api_key is None

    @patch("scripts.n8n_routes.SettingsManager")
    def test_routes_return_503_not_crash(self, mock_settings_mgr):
        """Routes should return 503, not crash, when N8N disabled."""
        from fastapi import FastAPI
        from scripts.n8n_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        mock_settings = Mock()
        mock_settings.n8n_enabled = False
        mock_settings_mgr.return_value.load.return_value = mock_settings

        # All routes should return 503
        endpoints = [
            ("POST", "/api/v1/n8n/test-connection"),
            ("GET", "/api/v1/n8n/workflows"),
            ("GET", "/api/v1/n8n/executions")
        ]

        for method, path in endpoints:
            if method == "POST":
                response = client.post(path)
            else:
                response = client.get(path)

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()
