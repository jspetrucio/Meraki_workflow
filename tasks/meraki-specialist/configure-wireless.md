---
name: configure-wireless
agent: meraki-specialist
trigger_keywords: [ssid, wifi, wireless, splash page, bandwidth limit, rf profile, radio]
risk_level: high
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Parse user request to identify wireless configuration changes needed"
  - name: resolve_targets
    type: tool
    tool: get_network_details
    description: "Identify network, SSID slots, and affected APs"
  - name: backup_current_state
    type: tool
    tool: backup_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Backup current wireless configuration before changes"
  - name: generate_preview
    type: agent
    description: "Generate before/after preview of wireless changes for user review"
  - name: confirm
    type: gate
    message_template: "Review the wireless configuration changes above. Apply these changes?"
  - name: apply_changes
    type: tool
    tool: apply_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Apply wireless configuration changes"
  - name: verify
    type: tool
    tool: verify_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Verify applied wireless configuration matches expected state"
---

# Meraki Specialist - Configure Wireless

Configure MR (Access Point) wireless settings via Meraki Dashboard API.

## Scope
- SSIDs (create, update, enable/disable)
- Splash pages and captive portals
- RF profiles
- Bandwidth limits per client
- Air Marshal rules
- Bluetooth settings

## Safety Rules
1. PSK minimum 8 characters, suggest 12+ with complexity
2. Open SSID: ALWAYS alert user about security risk
3. WPA1: Alert deprecation, recommend WPA2 or WPA3
4. Splash without HTTPS: Alert interception risk
5. Unlimited bandwidth on guest SSID: Alert about link saturation

## Apply Sequence (order matters)
1. Configure SSID base (name, auth, encryption, PSK)
2. Configure splash page (if applicable)
3. Configure bandwidth limits (if applicable)
4. Configure IP assignment (bridge/NAT/layer3)
5. Enable SSID (enabled=true) -- ALWAYS last
