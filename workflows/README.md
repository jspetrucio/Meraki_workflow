# Meraki Workflows

This directory contains Cisco Meraki Workflows in JSON format for import via Dashboard.

## Structure

```
workflows/
├── README.md
└── {client-name}/
    └── {workflow-name}.json
```

## Available Workflows

### jose-org

| Workflow | Description |
|----------|-------------|
| `data-usage-daily-alert.json` | Alerts to Slack when daily data usage exceeds 3GB, then every 1GB after |

## Import Instructions

### Option 1: Import from File

1. Go to **Meraki Dashboard > Organization > Automation > Workspace**
2. Click **Actions > Import Workflow**
3. Select **Browse** tab
4. Choose the JSON file and click **Import**

### Option 2: Import from GitHub

1. Go to **Actions > Manage Git Repositories**
2. Click **New Git Repository**
3. Configure:
   - Display Name: `Meraki_Workflow`
   - Protocol: HTTPS
   - REST API Repository Type: GitHub
   - REST API Repository: `https://api.github.com/repos/jspetrucio/Meraki_workflow`
   - Branch: `main`
   - Code Path: `workflows`
4. Click **Submit**
5. Go to **Actions > Import Workflow > Git** tab
6. Select the repository and workflow to import

## Workflow Format

All workflows follow the Cisco SecureX Orchestration JSON schema with:
- `unique_name` fields exactly 37 alphanumeric characters after prefix
- Valid `definition_workflow_`, `variable_workflow_`, `definition_activity_` prefixes
