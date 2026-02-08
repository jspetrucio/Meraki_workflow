---
name: discovery-completo
agent: network-analyst
trigger_keywords: [discovery, discover, scan, network scan, full analysis, analyze network, map network]
risk_level: low
hooks:
  pre: pre-analysis
  post: post-analysis
steps:
  - name: full_discovery
    type: tool
    tool: full_discovery
  - name: find_issues
    type: tool
    tool: find_issues
    args_from:
      discovery_data: full_discovery.result
  - name: generate_suggestions
    type: tool
    tool: generate_suggestions
    args_from:
      issues: find_issues.result
  - name: interpret_results
    type: agent
    description: "Interpret discovery results into a user-friendly narrative"
  - name: save_snapshot
    type: tool
    tool: save_snapshot
    args_from:
      discovery_data: full_discovery.result
  - name: offer_report
    type: gate
    message_template: "Discovery complete. Want to see the visual report?"
  - name: generate_report
    type: tool
    tool: generate_discovery_report
    condition: "offer_report.approved == true"
    args_from:
      discovery_data: full_discovery.result
---

# Network Analyst - Discovery Completo

You receive three data objects. Your job:

1. **Count everything**: X networks, Y devices, Z SSIDs, W VLANs, N firewall rules
2. **Highlight critical issues first**: offline devices, open SSIDs, allow-any rules
3. **Then warnings**: outdated firmware, unused VLANs, weak encryption
4. **Briefly mention what's healthy**
5. **End with top 3 actionable recommendations** from suggestions
6. **If issue requires config change**: prepare handoff context for Meraki Specialist

Do NOT list raw data. Synthesize. The user already has the visual report for details.
