---
name: health-check
agent: network-analyst
trigger_keywords: [health, health check, status, how is, performance, latency, uptime]
risk_level: low
steps:
  - name: resolve_network
    type: tool
    tool: get_network_details
  - name: get_health_metrics
    type: tool
    tool: get_device_statuses
    args_from:
      network_id: resolve_network.result.id
  - name: assess_thresholds
    type: agent
    description: "Assess device health metrics against acceptable thresholds"
  - name: generate_summary
    type: agent
    description: "Generate a concise health summary for the user"
---

# Network Analyst - Health Check

Analyze the health metrics of the specified network:

1. Check device statuses (online/offline/alerting)
2. Review latency and packet loss metrics
3. Compare against baseline thresholds
4. Highlight any devices or links in degraded state
5. Provide a clear health score and summary

Be concise. Focus on actionable findings.
