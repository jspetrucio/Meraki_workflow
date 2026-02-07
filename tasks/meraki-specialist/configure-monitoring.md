---
name: configure-monitoring
agent: meraki-specialist
trigger_keywords: [alert, snmp, syslog, camera, motion alert, notification]
risk_level: medium
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Parse user request to identify monitoring configuration changes"
  - name: resolve_targets
    type: tool
    tool: get_network_details
    description: "Identify network, devices, and current monitoring settings"
  - name: apply_changes
    type: tool
    tool: apply_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Apply monitoring configuration changes"
  - name: verify
    type: tool
    tool: verify_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Verify applied monitoring configuration"
---

# Meraki Specialist - Configure Monitoring

Configure monitoring, alerting, and observability settings across all device types.

## Scope
- Alerts and notifications (email, webhook, SMS)
- SNMP (v2c, v3)
- Syslog servers
- Camera (MV) quality, retention, motion zones
- Device tags
- Firmware scheduling
- Webhooks

## Notes
- No gate step required: monitoring changes are low-disruption
- Firmware updates are the exception: suggest maintenance window

## Safety Rules
1. SNMP community string: Never use "public" or "private"
2. SNMP v2 vs v3: Alert that v2 has no encryption, recommend v3
3. Syslog without TLS: Inform logs travel in plaintext
4. Firmware during business hours: Alert impact, suggest maintenance window
5. Camera retention < 7 days: Alert compliance concern
6. Webhook to external URL: Alert about endpoint security
