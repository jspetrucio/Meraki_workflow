# Checklist: N8N Workflow Review

## Metadata

```yaml
checklist_id: n8n-workflow-review
squad: n8n-automation
version: 1.0.0
```

## Purpose

Validate N8N workflow before deployment.

---

## 1. Structure Validation

- [ ] **Workflow has name** - Descriptive name following pattern: `{vendor}-{action}-{trigger}`
- [ ] **Has description** - Clear description of what workflow does
- [ ] **Trigger configured** - Exactly one trigger node (Webhook, Schedule, or Manual)
- [ ] **All nodes connected** - No orphan nodes without connections
- [ ] **End nodes defined** - Clear termination points

## 2. Node Configuration

- [ ] **HTTP Request nodes have timeout** - Default 30s, max 300s
- [ ] **Credentials not hardcoded** - Use N8N credentials, not inline secrets
- [ ] **URLs use variables** - `{{ $vars.API_URL }}` not hardcoded URLs
- [ ] **Proper node naming** - Descriptive names, not "HTTP Request 1"

## 3. Error Handling

- [ ] **Error workflow configured** - What happens on failure?
- [ ] **Try/Catch blocks** - For critical operations
- [ ] **Retry logic** - For API calls that may fail
- [ ] **Notification on failure** - Alert team when workflow fails

## 4. Security

- [ ] **No secrets in workflow JSON** - All secrets in N8N credentials
- [ ] **Webhook has authentication** - Header auth or IP whitelist
- [ ] **Input validation** - Validate webhook payloads
- [ ] **Rate limiting considered** - Don't overwhelm external APIs

## 5. Performance

- [ ] **Batch processing** - Use Split In Batches for large datasets
- [ ] **Wait nodes for rate limits** - Respect API limits (Meraki: 10 req/s)
- [ ] **No infinite loops** - Check loop conditions
- [ ] **Reasonable timeouts** - Don't hang forever

## 6. Documentation

- [ ] **Sticky notes present** - Explain workflow purpose and setup
- [ ] **Variables documented** - List all variables with descriptions
- [ ] **Credentials listed** - Which credentials are needed
- [ ] **Setup instructions** - How to configure after import

## 7. Testing

- [ ] **Tested with sample data** - At least one successful run
- [ ] **Edge cases tested** - Empty data, errors, etc
- [ ] **Manual trigger works** - Can run manually for debugging

---

## Review Summary

| Category | Pass | Fail | N/A |
|----------|------|------|-----|
| Structure | | | |
| Node Config | | | |
| Error Handling | | | |
| Security | | | |
| Performance | | | |
| Documentation | | | |
| Testing | | | |

## Reviewer Notes

```
Date:
Reviewer:
Workflow:
Result: [ ] APPROVED [ ] NEEDS CHANGES

Notes:
```

---

## Common Issues

### Issue: Hardcoded API keys

**Problem:** API keys in workflow JSON instead of credentials
**Fix:** Use N8N Credentials and reference via `{{ $credentials.xxx }}`

### Issue: No error handling

**Problem:** Workflow fails silently
**Fix:** Add Error Workflow or Catch block

### Issue: Rate limiting not respected

**Problem:** API returns 429 errors
**Fix:** Add Wait node between requests or use Split In Batches with delay

### Issue: Webhook without auth

**Problem:** Anyone can trigger the workflow
**Fix:** Add Header Authentication or IP whitelist
