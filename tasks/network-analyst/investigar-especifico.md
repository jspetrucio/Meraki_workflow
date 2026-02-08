---
name: investigar-especifico
agent: network-analyst
trigger_keywords: []
risk_level: low
steps:
  - name: parse_intent
    type: agent
    description: "Parse the user's investigation request to identify targets and scope"
  - name: resolve_targets
    type: tool
    tool: discover_networks
  - name: investigate
    type: agent
    description: "Investigate the specific issue or question raised by the user"
  - name: summarize
    type: agent
    description: "Summarize investigation findings with actionable conclusions"
---

# Network Analyst - Investigar Especifico

This is a fallback task for freeform investigation requests.

When the user asks a specific question about their network that doesn't match other task patterns:

1. Parse the user's intent — what are they trying to find out?
2. Identify the relevant network resources (devices, VLANs, rules, etc.)
3. Gather the necessary data via API calls
4. Analyze and interpret the findings
5. Provide a clear, concise answer to the user's question
6. Suggest follow-up actions if relevant

Adapt your investigation approach based on the user's specific question.
