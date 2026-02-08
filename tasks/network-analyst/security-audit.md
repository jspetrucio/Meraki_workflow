---
name: security-audit
agent: network-analyst
trigger_keywords: [security, audit, vulnerability, firewall audit, compliance, security posture]
risk_level: low
steps:
  - name: resolve_targets
    type: tool
    tool: discover_networks
  - name: discover_firewall_rules
    type: tool
    tool: discover_firewall_rules
    args_from:
      network_id: resolve_targets.result.id
  - name: discover_ssids
    type: tool
    tool: discover_ssids
    args_from:
      network_id: resolve_targets.result.id
  - name: analyze_security
    type: agent
    description: "Analyze firewall rules and SSIDs for security vulnerabilities"
  - name: generate_findings
    type: agent
    description: "Generate a prioritized security findings report"
---

# Network Analyst - Security Audit

Perform a security audit of the specified network:

1. Review all firewall rules for overly permissive entries (allow-any, wide CIDR ranges)
2. Check SSID configurations for open/weak authentication
3. Verify encryption standards (WPA2 minimum, prefer WPA3)
4. Look for unused or shadow rules
5. Generate prioritized findings: Critical > High > Medium > Low
6. Suggest remediation steps for each finding

If critical findings require immediate config changes, prepare handoff to Meraki Specialist.
