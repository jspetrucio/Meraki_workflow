---
name: executar-especifico
agent: meraki-specialist
trigger_keywords: []
risk_level: high
hooks:
  pre: pre-task
  post: post-task
steps:
  - name: parse_intent
    type: agent
    description: "Classify operation as read-only, write-single, write-batch, or multi-task"
  - name: resolve_targets
    type: tool
    tool: discover_networks
    description: "Identify target network, devices, and resources"
  - name: safety_check
    type: gate
    message_template: "This operation will modify network configuration. Proceed?"
    condition: "parse_intent.result.type != 'read-only'"
  - name: execute
    type: agent
    description: "Execute the identified operation using appropriate API endpoints"
  - name: verify
    type: agent
    description: "Verify execution result by re-reading current state"
---

# Meraki Specialist - Executar Especifico

Fallback task for configuration requests that don't match other specialist tasks.

## When Activated

- Requests that don't match T1-T5 triggers
- One-off queries: "What is the serial of the core switch?"
- Rare operations: "Configure Bluetooth on the AP in room 5"
- Multi-task combos: "Create VLAN and configure firewall and SSID"
- API queries: "List all networks in the org"

## Operation Types

- **read-only**: Only GET needed, no preview/confirmation required
- **write-single**: One write operation, full safety flow
- **write-batch**: Multiple writes, full safety flow + batch warning
- **multi-task**: Decompose into sequential tasks with individual confirmation

## Rules

1. Read-only is always safe -- execute without confirmation
2. Write follows universal safety flow
3. Multi-task executes sequentially, never in parallel
4. If endpoint not found: inform API limitation, suggest Dashboard
5. If operation looks like diagnosis: suggest handoff to Network Analyst
