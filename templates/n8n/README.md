# N8N Workflow Templates for CNL

This directory contains pre-built N8N workflow templates that can be deployed to automate Meraki network operations.

## Available Templates

### 1. Daily Discovery (`daily-discovery.json`)
**Schedule:** Daily at 7:00 AM
**Purpose:** Runs network discovery and alerts on changes

**Required Variables:**
- `CNL_BASE_URL` - Base URL of CNL API (e.g., `http://localhost:3141`)
- `NOTIFICATION_EMAIL` - Email address for notifications

**Optional Variables:**
- `CRON_SCHEDULE` - Override default schedule

### 2. Device Offline Alert (`device-offline-alert.json`)
**Trigger:** Webhook/Polling
**Purpose:** Alerts when devices go offline

**Required Variables:**
- `CNL_BASE_URL` - Base URL of CNL API
- `NOTIFICATION_EMAIL` - Email address for alerts

**Optional Variables:**
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

### 3. Firmware Compliance (`firmware-compliance.json`)
**Schedule:** Weekly (Sunday midnight)
**Purpose:** Checks firmware versions against known-good list

**Required Variables:**
- `CNL_BASE_URL` - Base URL of CNL API
- `NOTIFICATION_EMAIL` - Email address for reports

### 4. Security Audit (`security-audit.json`)
**Schedule:** Daily at 6:00 AM
**Purpose:** Scans for security issues (open SSIDs, weak encryption, etc.)

**Required Variables:**
- `CNL_BASE_URL` - Base URL of CNL API
- `NOTIFICATION_EMAIL` - Email address for security reports

### 5. Configuration Drift Detection (`config-drift.json`)
**Schedule:** Daily at midnight
**Purpose:** Detects configuration changes from baseline

**Required Variables:**
- `CNL_BASE_URL` - Base URL of CNL API
- `NOTIFICATION_EMAIL` - Email address for drift alerts

**Optional Variables:**
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

## Usage

### Via REST API

**List Available Templates:**
```bash
curl http://localhost:3141/api/v1/n8n/templates
```

**Deploy a Template:**
```bash
curl -X POST http://localhost:3141/api/v1/n8n/templates/daily-discovery/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "CNL_BASE_URL": "http://localhost:3141",
      "NOTIFICATION_EMAIL": "admin@example.com"
    }
  }'
```

### Via Python

```python
from scripts.n8n_template_engine import N8NTemplateEngine
from scripts.n8n_client import N8NClient

# Initialize
engine = N8NTemplateEngine()
client = N8NClient(base_url="http://localhost:5678", api_key="your-key")

# Deploy template
result = engine.deploy(
    client,
    "daily-discovery",
    {
        "CNL_BASE_URL": "http://localhost:3141",
        "NOTIFICATION_EMAIL": "admin@example.com"
    }
)

print(f"Deployed workflow: {result['id']}")
```

## Template Structure

Each template is a valid N8N workflow JSON file with:

- **name** - Workflow name (prefixed with "CNL - ")
- **nodes** - Array of N8N nodes (triggers, HTTP requests, code, notifications)
- **connections** - Node connection graph
- **settings** - N8N workflow settings

Variables are specified using `{{VARIABLE_NAME}}` syntax and are replaced during deployment.

## Adding New Templates

1. Create a new JSON file in this directory
2. Add metadata to `N8NTemplateEngine.TEMPLATE_METADATA` in `scripts/n8n_template_engine.py`
3. Write tests in `tests/test_n8n_templates.py`

## Notes

- Templates require N8N to be configured and enabled in CNL settings
- All workflows use CNL API endpoints to retrieve network data
- Email notifications require N8N email node to be configured
- Slack notifications require webhook URL
