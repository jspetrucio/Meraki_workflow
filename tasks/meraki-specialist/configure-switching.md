---
name: configure-switching
agent: meraki-specialist
trigger_keywords: [vlan, acl, switch port, qos, trunk, stp, port config, access port, sgt]
risk_level: high
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Parse user request to identify switching configuration changes needed"
  - name: resolve_targets
    type: tool
    tool: discover_networks
    description: "Identify switches, ports, and VLANs involved"
  - name: catalyst_detection
    type: tool
    tool: detect_catalyst_mode
    args_from:
      serial: resolve_targets.result.serial
    description: "Detect if switch is Catalyst in monitored mode (blocks writes)"
  - name: sgt_preflight_check
    type: tool
    tool: sgt_preflight_check
    args_from:
      serial: resolve_targets.result.serial
    description: "Check for TrustSec/SGT port restrictions before any changes"
  - name: backup_current_state
    type: tool
    tool: backup_config
    args_from:
      network_id: resolve_targets.result.id
    description: "Backup current switching configuration before changes"
  - name: generate_preview
    type: agent
    description: "Generate before/after preview including catalyst mode and SGT warnings"
  - name: confirm
    type: gate
    message_template: "Review the switching configuration changes above. Apply these changes?"
  - name: apply_changes
    type: agent
    description: "Apply switching configuration changes via appropriate API endpoints"
  - name: verify
    type: agent
    description: "Verify applied switching configuration by re-reading current state"
---

# Meraki Specialist - Configure Switching

Configure MS (Switch) and Catalyst managed-mode switching settings.

## Scope

- VLANs (create, update, delete)
- ACLs (Access Control Lists)
- Switch port configuration (type, VLAN, name)
- QoS / CoS rules
- STP settings
- DHCP server
- Storm control
- Port schedules

## Catalyst Detection Flow
1. `detect_catalyst_mode(serial)` for each switch
2. If `monitored` -> ABORT: "Device is read-only, not configurable via API"
3. If `managed` -> activate SGT preflight check
4. If `native_meraki` -> proceed normally

## SGT Preflight
- Test writeability of each target port
- If port is read-only (SGT locked): warn user, suggest alternatives
- NEVER attempt write on SGT-locked port

## Safety Rules
1. ACL without allow-all final rule: NEVER create (unless user explicitly confirms implicit deny)
2. VLAN 1: Alert user about default VLAN risk
3. Trunk port on uplink: Alert and confirm
4. Batch > 10 devices: Alert impact, suggest gradual rollout
5. Port shutdown: Double confirmation required
6. SGT locked port: NEVER attempt write
