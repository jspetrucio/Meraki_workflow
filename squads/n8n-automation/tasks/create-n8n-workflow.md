# Task: Create N8N Workflow

## Metadata

```yaml
task_id: create-n8n-workflow
squad: n8n-automation
agent: n8n-specialist
version: 1.0.0
```

## Purpose

Create a new N8N workflow from scratch or based on a template.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Name for the workflow |
| `template` | string | No | Template to use as base |
| `trigger` | string | No | Trigger type (webhook, schedule, manual) |
| `description` | string | No | Description of the workflow |

## Process

### Phase 1: Requirements Gathering

```
ELICIT from user:
1. What should trigger this workflow?
   - Webhook (Meraki alert, external system)
   - Schedule (cron expression)
   - Manual execution

2. What vendor(s) are involved?
   - Meraki only
   - Multi-vendor (which ones?)

3. What actions should happen?
   - Send notification (Slack, Email, PagerDuty)
   - Call API (which system?)
   - Store data (S3, database)
   - Create ticket (ServiceNow, Jira)

4. Any conditions/filters needed?
   - Device type
   - Severity level
   - Time of day
```

### Phase 2: Template Selection

```
IF template specified:
  Load template from: squads/n8n-automation/templates/n8n-workflows/{template}.json
  Customize based on requirements

ELSE:
  Start from scratch with selected trigger
```

### Phase 3: Workflow Design

```yaml
design_steps:
  1. Add trigger node
  2. Add processing nodes (Code, IF, etc)
  3. Add action nodes (Slack, HTTP, etc)
  4. Connect nodes
  5. Configure error handling
  6. Add sticky notes for documentation
```

### Phase 4: Variable Configuration

```
ELICIT variables needed:
- API keys (as N8N credentials)
- Channel names
- URLs
- Thresholds
```

### Phase 5: Validation

```
Run: validate-n8n-workflow
Check:
- [ ] All nodes connected
- [ ] No orphan nodes
- [ ] Credentials referenced exist
- [ ] Error handling present
```

### Phase 6: Export

```
Export workflow JSON to:
- clients/{client}/n8n-workflows/{name}.json (if client specified)
- squads/n8n-automation/templates/n8n-workflows/{name}.json (if saving as template)
```

## Output

```yaml
output:
  format: json
  location: "[specified path]"
  contents:
    - N8N workflow JSON
    - Variables documentation
    - Setup instructions
```

## Example Usage

```
User: Create a workflow to alert on Meraki device offline

Agent:
1. Trigger: Webhook (receive Meraki alert)
2. Vendor: Meraki
3. Action: Slack notification + PagerDuty if critical
4. Condition: Filter by device status "offline"

Template match: meraki-device-offline.json
Customizing...

Created: clients/acme/n8n-workflows/device-offline-alert.json

Next steps:
1. Import into N8N
2. Configure Slack credential
3. Set SLACK_CHANNEL variable
4. Point Meraki alerts to webhook URL
```

## Related

- Template: `meraki-device-offline.json`
- Task: `validate-n8n-workflow.md`
- Checklist: `n8n-workflow-review.md`
