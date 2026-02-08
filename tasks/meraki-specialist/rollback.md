---
name: rollback
agent: meraki-specialist
trigger_keywords: [rollback, undo, revert, restore, go back, undo change]
risk_level: high
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Identify which change to rollback from changelog or user description"
  - name: list_backups
    type: agent
    description: "List available backups from the change log"
  - name: select_backup
    type: gate
    message_template: "Select which change to rollback from the list above."
  - name: generate_preview
    type: agent
    description: "Generate rollback preview showing current state vs backup state"
  - name: confirm_rollback
    type: gate
    message_template: "Review the rollback preview above. Proceed with rollback?"
  - name: rollback_config
    type: tool
    tool: rollback_config
    description: "Restore the backup state for the selected change"
  - name: verify
    type: agent
    description: "Verify rollback was applied correctly by comparing with backup state"
---

# Meraki Specialist - Rollback

Revert a previous configuration change using saved backup state.

## Flow
1. Identify the change to rollback (from changelog or user description)
2. Load the backup state saved by pre-task hook
3. Show rollback preview (current state vs backup state)
4. Confirm with user via gate
5. Apply backup state (PUT original config)
6. Verify restoration

## Limitations
1. Changes made outside this agent may conflict with backup
2. Cannot delete VLAN if devices are assigned
3. VPN rollback only affects local side, not remote peer
4. Firmware rollback is NOT available via API (manual process)
5. If pre-task hook failed to save backup, rollback requires manual recreation
