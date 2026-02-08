---
name: configure-security
agent: meraki-specialist
trigger_keywords: [firewall, l3 rule, l7 rule, nat, vpn, traffic shaping, content filter]
risk_level: high
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Parse user request to identify security/firewall configuration changes"
  - name: resolve_targets
    type: tool
    tool: get_network_details
    description: "Identify network, MX appliance, and current firewall rules"
  - name: backup_current_state
    type: tool
    tool: backup_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Backup current security configuration before changes"
  - name: generate_preview
    type: agent
    description: "Generate rule preview showing new rule in context of existing rules"
  - name: confirm
    type: gate
    message_template: "Review the security configuration changes above. Apply these changes?"
  - name: apply_changes
    type: tool
    tool: apply_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Apply security configuration changes (PUT replaces entire rule set)"
  - name: verify
    type: tool
    tool: verify_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Verify applied security rules match expected state and position"
---

# Meraki Specialist - Configure Security

Configure MX (Security Appliance) firewall and security settings.

## Scope
- Firewall L3/L7 rules
- NAT (1:1, 1:Many, Port Forwarding)
- Site-to-Site VPN
- Client VPN
- Traffic Shaping
- Content Filtering
- Threat Protection (IPS/IDS)

## Critical Notes
- Firewall rules apply IMMEDIATELY -- no commit/rollback natively
- Firewall rules on Meraki are full replacement (PUT), not append
- Always GET all rules -> insert at correct position -> PUT all rules

## Safety Rules
1. Deny any any: NEVER without triple confirmation
2. Remove default allow: NEVER without explicit deny-all and confirmation
3. Firewall is PUT total: Alert that array errors overwrite ALL rules
4. VPN PSK: Minimum 20 characters, suggest auto-generation
5. NAT without firewall rule: Alert about service exposure
6. Always show new rule in context of existing rules
