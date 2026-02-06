"""
Tests for N8N template engine and template endpoints.

Tests cover:
- Template loading and listing
- Variable substitution
- Template validation
- Error handling for missing variables
- API endpoints for template deployment
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from scripts.n8n_template_engine import N8NTemplateEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory with test templates."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create a simple test template
    simple_template = {
        "name": "CNL - Test Template",
        "nodes": [
            {
                "parameters": {
                    "url": "{{CNL_BASE_URL}}/api/test",
                    "method": "POST"
                },
                "name": "Test Node",
                "type": "n8n-nodes-base.httpRequest"
            }
        ],
        "connections": {},
        "settings": {"executionOrder": "v1"}
    }

    test_file = template_dir / "test-template.json"
    test_file.write_text(json.dumps(simple_template))

    return template_dir


@pytest.fixture
def engine(temp_template_dir):
    """Create template engine with test templates."""
    # Override metadata for test template
    original_metadata = N8NTemplateEngine.TEMPLATE_METADATA.copy()
    N8NTemplateEngine.TEMPLATE_METADATA = {
        "test-template": {
            "name": "Test Template",
            "description": "A test template",
            "category": "testing",
            "required_vars": ["CNL_BASE_URL"],
            "optional_vars": ["NOTIFICATION_EMAIL"]
        }
    }

    engine = N8NTemplateEngine(template_dir=temp_template_dir)

    yield engine

    # Restore original metadata
    N8NTemplateEngine.TEMPLATE_METADATA = original_metadata


@pytest.fixture
def real_template_dir():
    """Get path to real template directory."""
    return Path(__file__).parent.parent / "templates" / "n8n"


@pytest.fixture
def real_engine(real_template_dir):
    """Create engine with real templates."""
    return N8NTemplateEngine(template_dir=real_template_dir)


# ---------------------------------------------------------------------------
# Template Engine Tests
# ---------------------------------------------------------------------------


def test_list_templates(engine):
    """Test listing available templates."""
    templates = engine.list_templates()

    assert len(templates) == 1
    assert templates[0]["id"] == "test-template"
    assert templates[0]["name"] == "Test Template"
    assert templates[0]["description"] == "A test template"
    assert "required_vars" in templates[0]
    assert "optional_vars" in templates[0]


def test_get_template_metadata(engine):
    """Test getting metadata for specific template."""
    meta = engine.get_template_metadata("test-template")

    assert meta["id"] == "test-template"
    assert meta["name"] == "Test Template"
    assert meta["required_vars"] == ["CNL_BASE_URL"]
    assert meta["optional_vars"] == ["NOTIFICATION_EMAIL"]


def test_get_nonexistent_template_metadata(engine):
    """Test error when getting metadata for nonexistent template."""
    with pytest.raises(ValueError, match="not found"):
        engine.get_template_metadata("nonexistent")


def test_render_with_all_variables(engine):
    """Test rendering template with all variables provided."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "test@example.com"
    }

    result = engine.render("test-template", variables)

    assert isinstance(result, dict)
    assert result["name"] == "CNL - Test Template"
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["parameters"]["url"] == "http://localhost:3141/api/test"


def test_render_substitutes_all_occurrences(temp_template_dir, engine):
    """Test that variable substitution replaces all occurrences."""
    # Create template with multiple occurrences of same variable
    template = {
        "name": "{{CNL_BASE_URL}}",
        "nodes": [
            {"url": "{{CNL_BASE_URL}}/path1"},
            {"url": "{{CNL_BASE_URL}}/path2"}
        ]
    }

    test_file = temp_template_dir / "multi-var.json"
    test_file.write_text(json.dumps(template))

    # Add metadata
    N8NTemplateEngine.TEMPLATE_METADATA["multi-var"] = {
        "name": "Multi Var",
        "description": "Test",
        "category": "test",
        "required_vars": ["CNL_BASE_URL"],
        "optional_vars": []
    }

    result = engine.render("multi-var", {"CNL_BASE_URL": "http://test.com"})

    assert result["name"] == "http://test.com"
    assert result["nodes"][0]["url"] == "http://test.com/path1"
    assert result["nodes"][1]["url"] == "http://test.com/path2"


def test_render_missing_required_variable(engine):
    """Test error when required variable is missing."""
    with pytest.raises(ValueError, match="Missing required variables"):
        engine.render("test-template", {})


def test_render_with_only_required_variables(engine):
    """Test rendering with only required variables (optional omitted)."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141"
    }

    # Should succeed even though optional NOTIFICATION_EMAIL not provided
    result = engine.render("test-template", variables)
    assert isinstance(result, dict)


def test_sanitize_special_characters(temp_template_dir, engine):
    """Test that special characters in values are properly escaped."""
    template = {
        "name": "{{VALUE}}",
        "nodes": []
    }

    test_file = temp_template_dir / "escape-test.json"
    test_file.write_text(json.dumps(template))

    N8NTemplateEngine.TEMPLATE_METADATA["escape-test"] = {
        "name": "Escape Test",
        "description": "Test",
        "category": "test",
        "required_vars": ["VALUE"],
        "optional_vars": []
    }

    # Test various special characters - after JSON parsing, these are unescaped
    # The important thing is the JSON is valid (no parse errors)
    test_cases = [
        'Value with "quotes"',
        'Value with \nNewline',
        'Value with \tTab',
        'Value with \\Backslash',
    ]

    for input_val in test_cases:
        # Should not raise ValueError or JSONDecodeError
        result = engine.render("escape-test", {"VALUE": input_val})
        assert isinstance(result, dict)
        assert "name" in result


def test_render_invalid_json_after_substitution(temp_template_dir, engine):
    """Test error when substitution produces invalid JSON."""
    # Create intentionally broken template
    broken_file = temp_template_dir / "broken.json"
    broken_file.write_text('{"name": "{{VALUE}}", "nodes": [}')  # Invalid JSON

    N8NTemplateEngine.TEMPLATE_METADATA["broken"] = {
        "name": "Broken",
        "description": "Test",
        "category": "test",
        "required_vars": ["VALUE"],
        "optional_vars": []
    }

    with pytest.raises(ValueError, match="not valid JSON"):
        engine.render("broken", {"VALUE": "test"})


def test_deploy_calls_client_create_workflow(engine):
    """Test that deploy() renders template and calls N8N client."""
    mock_client = Mock()
    mock_client.create_workflow.return_value = {
        "id": "workflow-123",
        "name": "CNL - Test Template",
        "active": False
    }

    variables = {"CNL_BASE_URL": "http://localhost:3141"}

    result = engine.deploy(mock_client, "test-template", variables)

    assert mock_client.create_workflow.called
    assert result["id"] == "workflow-123"
    assert result["name"] == "CNL - Test Template"


# ---------------------------------------------------------------------------
# Real Template Tests
# ---------------------------------------------------------------------------


def test_all_real_templates_exist(real_template_dir):
    """Test that all templates defined in metadata exist as files."""
    for template_id in N8NTemplateEngine.TEMPLATE_METADATA.keys():
        template_file = real_template_dir / f"{template_id}.json"
        assert template_file.exists(), f"Template file missing: {template_file}"


def test_all_real_templates_are_valid_json(real_template_dir):
    """Test that all real templates are valid JSON."""
    for template_id in N8NTemplateEngine.TEMPLATE_METADATA.keys():
        template_file = real_template_dir / f"{template_id}.json"
        if template_file.exists():
            content = template_file.read_text()
            try:
                data = json.loads(content)
                assert isinstance(data, dict)
                assert "name" in data
                assert "nodes" in data
                assert "connections" in data
            except json.JSONDecodeError as exc:
                pytest.fail(f"Template {template_id} is not valid JSON: {exc}")


def test_daily_discovery_template_rendering(real_engine):
    """Test rendering the daily-discovery template."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com"
    }

    result = real_engine.render("daily-discovery", variables)

    assert result["name"] == "CNL - Daily Discovery"
    assert len(result["nodes"]) > 0
    assert "Schedule Trigger" in [n["name"] for n in result["nodes"]]

    # Check URL substitution
    discovery_node = next(n for n in result["nodes"] if "Run Discovery" in n["name"])
    assert "localhost:3141" in discovery_node["parameters"]["url"]


def test_device_offline_alert_template_rendering(real_engine):
    """Test rendering the device-offline-alert template."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com",
        "SLACK_WEBHOOK": "https://hooks.slack.com/test"
    }

    result = real_engine.render("device-offline-alert", variables)

    assert result["name"] == "CNL - Device Offline Alert"
    assert any("Webhook" in n["name"] for n in result["nodes"])

    # Check Slack webhook substitution
    slack_node = next(n for n in result["nodes"] if "Slack" in n["name"])
    assert "hooks.slack.com" in slack_node["parameters"]["webhookUri"]


def test_firmware_compliance_template_rendering(real_engine):
    """Test rendering the firmware-compliance template."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com"
    }

    result = real_engine.render("firmware-compliance", variables)

    assert result["name"] == "CNL - Firmware Compliance Check"
    assert any("Weekly" in n["name"] for n in result["nodes"])


def test_security_audit_template_rendering(real_engine):
    """Test rendering the security-audit template."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com"
    }

    result = real_engine.render("security-audit", variables)

    assert result["name"] == "CNL - Security Audit"
    assert any("Security" in n["name"] for n in result["nodes"])


def test_config_drift_template_rendering(real_engine):
    """Test rendering the config-drift template."""
    variables = {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com"
    }

    result = real_engine.render("config-drift", variables)

    assert result["name"] == "CNL - Config Drift Detection"
    assert any("Drift" in n["name"] for n in result["nodes"])


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """Mock settings with N8N enabled."""
    with patch("scripts.n8n_routes.SettingsManager") as mock:
        settings = Mock()
        settings.n8n_enabled = True
        settings.n8n_url = "http://localhost:5678"
        settings.n8n_api_key = "test-key"
        mock.return_value.load.return_value = settings
        yield mock


@pytest.fixture
def api_client(mock_settings):
    """Create test client for API."""
    from scripts.server import app
    return TestClient(app)


def test_list_templates_endpoint(api_client, mock_settings):
    """Test GET /api/v1/n8n/templates endpoint."""
    response = api_client.get("/api/v1/n8n/templates")

    assert response.status_code == 200
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) == 5  # All 5 templates

    # Check structure
    for template in templates:
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "category" in template
        assert "required_vars" in template
        assert "optional_vars" in template


@patch("scripts.n8n_routes.get_n8n_client")
def test_deploy_template_endpoint_success(mock_get_client, api_client, mock_settings):
    """Test POST /api/v1/n8n/templates/{name}/deploy endpoint (success case)."""
    # Mock N8N client
    mock_client = Mock()
    mock_client.create_workflow.return_value = {
        "id": "wf-123",
        "name": "CNL - Daily Discovery",
        "active": False
    }
    mock_get_client.return_value = mock_client

    payload = {
        "variables": {
            "CNL_BASE_URL": "http://localhost:3141",
            "NOTIFICATION_EMAIL": "admin@example.com"
        }
    }

    response = api_client.post("/api/v1/n8n/templates/daily-discovery/deploy", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["workflow_id"] == "wf-123"
    assert "Daily Discovery" in result["workflow_name"]
    assert mock_client.create_workflow.called


@patch("scripts.n8n_routes.get_n8n_client")
def test_deploy_template_missing_required_variables(mock_get_client, api_client, mock_settings):
    """Test deploy endpoint with missing required variables."""
    mock_get_client.return_value = Mock()

    # Empty variables (missing required CNL_BASE_URL)
    payload = {"variables": {}}

    response = api_client.post("/api/v1/n8n/templates/daily-discovery/deploy", json=payload)

    assert response.status_code == 400
    assert "Missing required variables" in response.json()["detail"]


@patch("scripts.n8n_routes.get_n8n_client")
def test_deploy_template_n8n_unavailable(mock_get_client, api_client, mock_settings):
    """Test deploy endpoint when N8N client is unavailable."""
    mock_get_client.return_value = None

    payload = {
        "variables": {
            "CNL_BASE_URL": "http://localhost:3141",
            "NOTIFICATION_EMAIL": "admin@example.com"
        }
    }

    response = api_client.post("/api/v1/n8n/templates/daily-discovery/deploy", json=payload)

    assert response.status_code == 503
    assert "not available" in response.json()["detail"]


def test_deploy_template_n8n_disabled(api_client):
    """Test deploy endpoint when N8N is disabled in settings."""
    with patch("scripts.n8n_routes.SettingsManager") as mock:
        settings = Mock()
        settings.n8n_enabled = False
        mock.return_value.load.return_value = settings

        payload = {
            "variables": {
                "CNL_BASE_URL": "http://localhost:3141",
                "NOTIFICATION_EMAIL": "admin@example.com"
            }
        }

        response = api_client.post("/api/v1/n8n/templates/daily-discovery/deploy", json=payload)

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]
