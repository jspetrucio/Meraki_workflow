"""
N8N REST API client.

Supports both self-hosted (X-N8N-API-KEY) and n8n.cloud (Bearer token) auth.
Gracefully handles missing N8N configuration.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

import httpx

from scripts.settings import SettingsManager

logger = logging.getLogger(__name__)


class N8NClient:
    """Client for N8N REST API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize N8N client.

        Args:
            base_url: N8N instance URL
            api_key: Optional API key for authentication

        Raises:
            ValueError: If base_url is invalid
        """
        # Validate URL
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Must be http or https")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=5.0,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> dict:
        """
        Get authentication headers based on instance type.

        Returns:
            dict: Authentication headers (X-N8N-API-KEY for self-hosted, Bearer for cloud)
        """
        if not self.api_key:
            return {}

        # n8n.cloud uses Bearer token, self-hosted uses X-N8N-API-KEY
        if "n8n.cloud" in self.base_url:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {"X-N8N-API-KEY": self.api_key}

    def test_connection(self) -> dict:
        """
        Test connectivity to N8N instance.

        Returns:
            dict: Response from N8N API (typically contains version info)

        Raises:
            httpx.HTTPError: If connection fails
        """
        try:
            resp = self._client.get("/api/v1")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(f"N8N connection test failed: {exc}")
            raise

    def list_workflows(self) -> list[dict]:
        """
        List all workflows.

        Returns:
            list[dict]: Array of workflow objects

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.get("/api/v1/workflows")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) if isinstance(data, dict) else data
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to list N8N workflows: {exc}")
            raise

    def get_workflow(self, workflow_id: str) -> dict:
        """
        Get a specific workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            dict: Workflow object

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.get(f"/api/v1/workflows/{workflow_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to get N8N workflow {workflow_id}: {exc}")
            raise

    def create_workflow(self, data: dict) -> dict:
        """
        Create a new workflow.

        Args:
            data: Workflow data (name, nodes, connections, etc.)

        Returns:
            dict: Created workflow object

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.post("/api/v1/workflows", json=data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to create N8N workflow: {exc}")
            raise

    def activate_workflow(self, workflow_id: str) -> dict:
        """
        Activate a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            dict: Updated workflow object

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.patch(
                f"/api/v1/workflows/{workflow_id}",
                json={"active": True}
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to activate N8N workflow {workflow_id}: {exc}")
            raise

    def deactivate_workflow(self, workflow_id: str) -> dict:
        """
        Deactivate a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            dict: Updated workflow object

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.patch(
                f"/api/v1/workflows/{workflow_id}",
                json={"active": False}
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to deactivate N8N workflow {workflow_id}: {exc}")
            raise

    def get_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        Get workflow execution history.

        Args:
            workflow_id: Optional workflow ID to filter by
            limit: Maximum number of executions to return

        Returns:
            list[dict]: Array of execution objects

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id

            resp = self._client.get("/api/v1/executions", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) if isinstance(data, dict) else data
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to get N8N executions: {exc}")
            raise

    def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            resp = self._client.delete(f"/api/v1/workflows/{workflow_id}")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning(f"Failed to delete N8N workflow {workflow_id}: {exc}")
            raise

    def get_workflow_executions(self, workflow_id: str, limit: int = 5) -> list[dict]:
        """
        Get recent executions for a specific workflow.

        This is a convenience method that wraps get_executions with workflow_id filter.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of executions to return (default: 5)

        Returns:
            list[dict]: Array of execution objects

        Raises:
            httpx.HTTPError: If request fails
        """
        return self.get_executions(workflow_id=workflow_id, limit=limit)

    def close(self):
        """Close the HTTP client."""
        self._client.close()


def get_n8n_client() -> Optional[N8NClient]:
    """
    Get N8N client from settings.

    Returns:
        N8NClient if N8N is configured and enabled, None otherwise
    """
    try:
        manager = SettingsManager()
        settings = manager.load()

        if not settings.n8n_enabled:
            logger.debug("N8N not enabled in settings")
            return None

        if not settings.n8n_url:
            logger.warning("N8N enabled but URL not configured")
            return None

        return N8NClient(
            base_url=settings.n8n_url,
            api_key=settings.n8n_api_key
        )
    except Exception as exc:
        logger.warning(f"Failed to create N8N client: {exc}")
        return None
