---
name: drift-detection
agent: network-analyst
trigger_keywords: [drift, changed, difference, compare, baseline, what changed, config drift]
risk_level: low
steps:
  - name: load_baseline
    type: agent
    description: "Load the most recent baseline snapshot for comparison"
  - name: discover_current
    type: tool
    tool: full_discovery
  - name: compare_snapshots
    type: agent
    description: "Compare baseline snapshot with current state to identify configuration drift"
  - name: generate_drift_report
    type: agent
    description: "Generate a drift report highlighting all changes since baseline"
---

# Network Analyst - Drift Detection

Compare the current network state against a saved baseline snapshot:

1. Load the most recent baseline snapshot for this client
2. Run a fresh discovery to get current state
3. Compare key areas:
   - Device inventory changes (added/removed/changed)
   - VLAN configuration changes
   - Firewall rule modifications
   - SSID setting changes
   - Switch port configuration drift
4. Categorize changes: Intentional vs Unexpected
5. Flag any changes that may indicate security concerns
6. Recommend actions for unexpected drift
