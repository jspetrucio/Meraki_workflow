"""
N8N Template Engine for CNL.

Loads, renders, and deploys N8N workflow templates with variable substitution.
Supports template validation and sanitization of variable values.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class N8NTemplateEngine:
    """Loads, renders, and deploys N8N workflow templates."""

    # Template directory (relative to project root)
    TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "n8n"

    # Metadata for all available templates
    TEMPLATE_METADATA = {
        "daily-discovery": {
            "name": "Scheduled Daily Discovery",
            "description": "Run discovery every morning at 7:00 AM, alert on changes",
            "category": "monitoring",
            "required_vars": ["CNL_BASE_URL", "NOTIFICATION_EMAIL"],
            "optional_vars": ["CRON_SCHEDULE"],
        },
        "device-offline-alert": {
            "name": "Device Offline Alert",
            "description": "Webhook/polling trigger, Slack/email notification on device down",
            "category": "alerting",
            "required_vars": ["CNL_BASE_URL", "NOTIFICATION_EMAIL"],
            "optional_vars": ["SLACK_WEBHOOK"],
        },
        "firmware-compliance": {
            "name": "Firmware Compliance Check",
            "description": "Weekly scan (Sunday midnight), report non-compliant devices",
            "category": "compliance",
            "required_vars": ["CNL_BASE_URL", "NOTIFICATION_EMAIL"],
            "optional_vars": [],
        },
        "security-audit": {
            "name": "Security Audit",
            "description": "Daily check (6:00 AM) for insecure SSIDs, open ports, weak encryption",
            "category": "security",
            "required_vars": ["CNL_BASE_URL", "NOTIFICATION_EMAIL"],
            "optional_vars": [],
        },
        "config-drift": {
            "name": "Configuration Drift Detection",
            "description": "Daily check (midnight) - compare current config to baseline, alert on drift",
            "category": "compliance",
            "required_vars": ["CNL_BASE_URL", "NOTIFICATION_EMAIL"],
            "optional_vars": ["SLACK_WEBHOOK"],
        },
    }

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template engine.

        Args:
            template_dir: Optional custom template directory (defaults to templates/n8n/)
        """
        self.template_dir = template_dir or self.TEMPLATE_DIR
        if not self.template_dir.exists():
            logger.warning(f"Template directory does not exist: {self.template_dir}")

    def list_templates(self) -> list[dict]:
        """
        List all available templates with metadata.

        Returns:
            list[dict]: Array of template objects with id, name, description, etc.
        """
        templates = []
        for template_id, meta in self.TEMPLATE_METADATA.items():
            template_path = self.template_dir / f"{template_id}.json"
            if template_path.exists():
                templates.append({
                    "id": template_id,
                    **meta
                })
            else:
                logger.warning(f"Template file not found: {template_path}")

        return templates

    def get_template_metadata(self, template_name: str) -> dict:
        """
        Get metadata for a specific template.

        Args:
            template_name: Template ID

        Returns:
            dict: Template metadata

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.TEMPLATE_METADATA:
            raise ValueError(f"Template '{template_name}' not found")

        return {
            "id": template_name,
            **self.TEMPLATE_METADATA[template_name]
        }

    def _sanitize_value(self, value: str) -> str:
        """
        Sanitize a variable value for safe injection into JSON.

        Escapes special characters that could break JSON structure.

        Args:
            value: Raw variable value

        Returns:
            str: Sanitized value safe for JSON injection
        """
        # Convert to string
        value = str(value)

        # Escape backslashes first (must be done before other escapes)
        value = value.replace("\\", "\\\\")

        # Escape quotes
        value = value.replace('"', '\\"')

        # Escape newlines and tabs
        value = value.replace("\n", "\\n")
        value = value.replace("\r", "\\r")
        value = value.replace("\t", "\\t")

        return value

    def render(self, template_name: str, variables: dict) -> dict:
        """
        Load template JSON and substitute variables.

        Replaces {{VARIABLE_NAME}} placeholders with provided values.
        Validates that all required variables are provided.

        Args:
            template_name: Template ID (e.g., "daily-discovery")
            variables: Dictionary of variable values to substitute

        Returns:
            dict: Rendered N8N workflow JSON ready for deployment

        Raises:
            ValueError: If template not found or required variables missing
        """
        # Load template file
        template_path = self.template_dir / f"{template_name}.json"
        if not template_path.exists():
            raise ValueError(f"Template file not found: {template_path}")

        # Read raw template content
        raw_content = template_path.read_text()

        # Get metadata
        metadata = self.get_template_metadata(template_name)

        # Sanitize all variable values
        sanitized_vars = {
            key: self._sanitize_value(value)
            for key, value in variables.items()
        }

        # Perform variable substitution
        rendered = raw_content
        for key, value in sanitized_vars.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, value)

        # Check for unresolved required variables
        remaining_vars = re.findall(r"\{\{(\w+)\}\}", rendered)
        if remaining_vars:
            required = set(metadata["required_vars"])
            unresolved_required = [v for v in remaining_vars if v in required]

            if unresolved_required:
                raise ValueError(
                    f"Missing required variables: {', '.join(unresolved_required)}"
                )

            # Optional variables remain as placeholders (user can fill manually in N8N)
            logger.info(
                f"Optional variables not provided: {', '.join(remaining_vars)}"
            )

        # Parse and validate JSON
        try:
            workflow = json.loads(rendered)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Generated workflow is not valid JSON: {exc}")

        return workflow

    def deploy(
        self,
        client: "N8NClient",
        template_name: str,
        variables: dict
    ) -> dict:
        """
        Render template and deploy to N8N instance.

        Args:
            client: N8NClient instance
            template_name: Template ID
            variables: Variable values for substitution

        Returns:
            dict: Created workflow object from N8N API

        Raises:
            ValueError: If template rendering fails
            httpx.HTTPError: If N8N API request fails
        """
        # Render template
        workflow_data = self.render(template_name, variables)

        # Create workflow via N8N API
        logger.info(f"Deploying template '{template_name}' to N8N")
        result = client.create_workflow(workflow_data)

        logger.info(f"Template deployed successfully: workflow ID {result.get('id')}")
        return result
