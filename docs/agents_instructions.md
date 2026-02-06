# Meraki Agents Instructions

> **Complete Guide to Using Meraki Workflow Agents**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Meraki Agents](#2-meraki-agents)
3. [How to Invoke Agents](#3-how-to-invoke-agents)
4. [Agent Workflows](#4-agent-workflows)
5. [Appendix](#5-appendix)

---

## 1. Overview

### What are Meraki Agents?

Meraki Agents are specialized AI assistants designed to perform specific tasks on Meraki networks. Each agent has deep knowledge in its domain and follows established workflows to ensure consistent, safe, and documented operations.

### Quick Reference Table

| Agent | Purpose | Invoke With | Color |
|-------|---------|-------------|-------|
| **maestro** | Orchestrate complex multi-agent tasks | `/maestro` | 🟡 Gold |
| **meraki-specialist** | Configure ACL, Firewall, SSID, Switch, Camera, QoS | `/meraki-specialist` | 🔵 Cyan |
| **network-analyst** | Discovery, diagnostics, health analysis | `/network-analyst` | 🟢 Green |
| **workflow-creator** | Create automation workflows (SecureX JSON) | `/workflow-creator` | 🟠 Orange |
| **report-designer** | Generate visual HTML reports | `/report-designer` | 🔷 Blue |
| **security** | Security audit and compliance checks | `/security` | 🟣 Magenta |

### When to Use Each Agent

```
┌─────────────────────────────────────────────────────────────┐
│  What do you need to do?                                     │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Analyze   │       │ Configure │       │ Automate  │
    │ Network   │       │ Devices   │       │ Tasks     │
    └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ network-  │       │ meraki-   │       │ workflow- │
    │ analyst   │       │ specialist│       │ creator   │
    └───────────┘       └───────────┘       └───────────┘

    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Generate  │       │ Security  │       │ Multiple  │
    │ Report    │       │ Audit     │       │ Tasks     │
    └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ report-   │       │ security  │       │ maestro   │
    │ designer  │       │           │       │           │
    └───────────┘       └───────────┘       └───────────┘
```

---

## 2. Meraki Agents

### 2.1 Maestro (Orchestrator)

**Color:** 🟡 Gold
**Model:** Claude Opus (most capable)
**File:** `.claude/agents/maestro.md`

#### Purpose

The Maestro is the central orchestrator that coordinates multiple specialized agents to complete complex tasks. It plans, delegates, validates, and reports.

#### When to Use

- Tasks that span multiple domains (config + workflow + security)
- Complex client onboarding
- Multi-step operations requiring coordination
- When you're not sure which agent to use

#### Capabilities

- Analyzes task complexity
- Decomposes into subtasks
- Maps subtasks to appropriate agents
- Creates execution plans
- Validates outputs at each step (quality gates)
- Provides consolidated reports

#### Operation Mode

```
1. Receive task
2. Read project context
3. Analyze complexity
4. Decompose into subtasks
5. Map to agents
6. Create execution plan
7. >>> PRESENT PLAN & WAIT FOR CONFIRMATION <<<
8. Execute sequentially
9. Validate each output
10. Report final result
```

#### Example Commands

```
"Configure this client's network with ACL, firewall, and SSIDs"
→ Maestro coordinates: meraki-specialist (3 tasks)

"Analyze the network, fix security issues, and create monitoring workflows"
→ Maestro coordinates: network-analyst → security → workflow-creator

"Complete client onboarding for ACME Corp"
→ Maestro coordinates: network-analyst → meraki-specialist → workflow-creator → report-designer
```

#### Invocation

```
/maestro Configure complete network setup for client XYZ
```

---

### 2.2 Meraki Specialist (Configuration)

**Color:** 🔵 Cyan
**Model:** Claude Sonnet
**File:** `.claude/agents/meraki-specialist.md`

#### Purpose

The configuration expert for all Meraki devices. Translates natural language requests into API calls with safety checks and documentation.

#### When to Use

- Configure ACLs on switches
- Set up firewall rules (L3/L7)
- Create or modify SSIDs
- Configure switch ports
- Set up VLANs
- Configure camera settings
- Apply QoS policies
- Any device configuration via Meraki API

#### Capabilities

**MX (Security Appliance):**
- Firewall L3/L7 rules
- NAT (1:1, 1:Many, Port Forwarding)
- Site-to-Site VPN
- Client VPN
- Traffic Shaping
- Content Filtering
- Threat Protection

**MS (Switch):**
- VLANs
- ACLs (Access Control Lists)
- Port Configuration
- QoS / CoS
- STP Settings
- DHCP Server
- Port Schedules
- Storm Control

**MR (Wireless):**
- SSIDs
- Splash Pages
- RF Profiles
- Air Marshal
- Bluetooth Settings
- Location Analytics

**MV (Camera):**
- Quality & Resolution
- Retention Settings
- Motion Zones
- Schedules
- Analytics (MV Sense)

**General:**
- Alerts & Notifications
- SNMP
- Syslog
- Tags
- Firmware Management

#### Workflow

```
1. Understand requirement
2. Validate context (network exists, device exists)
3. Show preview of changes
4. >>> WAIT FOR CONFIRMATION <<<
5. Backup current config
6. Apply configuration
7. Validate result
8. Document in changelog
```

#### Example Commands

```
"Create an ACL to block port 23 on the core switch"
"Configure a new guest SSID with captive portal"
"Set up QoS policy limiting YouTube to 5Mbps"
"Add VLAN 100 for IoT devices"
"Configure firewall rule to block Tor traffic"
```

#### Invocation

```
/meraki-specialist Create ACL to block telnet on all switches
```

---

### 2.3 Network Analyst (Discovery & Diagnostics)

**Color:** 🟢 Green
**Model:** Claude Sonnet
**File:** `.claude/agents/network-analyst.md`

#### Purpose

Specialized in network discovery and diagnostics. Analyzes existing Meraki environments, identifies problems, and suggests improvements.

#### When to Use

- First visit to a client (discovery)
- Network health assessment
- Troubleshooting issues
- Identifying configuration problems
- Generating network inventory
- Checking firmware compliance

#### Capabilities

**Discovery:**
- List all organizations/networks
- Map device topology
- Identify existing configurations
- Collect performance metrics
- Detect problems and gaps

**Health Analysis:**
- Device status (online/offline)
- Firmware versions
- Resource utilization
- Active alerts
- Usage trends

**Intelligent Suggestions:**
- Recommended workflows
- Security improvements
- Performance optimizations
- Best practices violations

#### Workflow

```
1. Connect & validate credentials
2. Collect data (full discovery)
3. Analyze findings
4. Save to clients/{client}/discovery/
5. Generate report
6. Present summary with issues
```

#### Output

- **Discovery JSON:** `clients/{client}/discovery/{date}.json`
- **HTML Report:** `clients/{client}/reports/{date}.html`
- **Changelog entry:** `clients/{client}/CHANGELOG.md`

#### Example Commands

```
"Analyze this client's network"
"What problems exist in this network?"
"Run full discovery for jose-org"
"Check network health status"
"Which devices have outdated firmware?"
```

#### Invocation

```
/network-analyst Analyze the network for client ACME
```

#### Integration

Automatically calls **report-designer** after discovery to generate visual reports.

---

### 2.4 Workflow Creator (Automation)

**Color:** 🟠 Orange
**Model:** Claude Sonnet
**File:** `.claude/agents/workflow-creator.md`

#### Purpose

Creates Meraki automation workflows in Cisco SecureX JSON format. These workflows can be imported into the Meraki Dashboard for automated remediation, monitoring, and compliance.

#### When to Use

- Create device offline alerts
- Set up firmware compliance checks
- Automate security responses
- Create scheduled reports
- Build remediation workflows
- Any automation for Meraki events

#### Capabilities

- Generates SecureX-compatible JSON
- Access to 829 pre-built Meraki Atomics
- Supports triggers: Webhook, Schedule, API Call, Email
- Actions: Meraki ops, Slack, Teams, Email, PagerDuty, ServiceNow
- Variables, conditions, loops, parallel execution

#### Available Templates

**Provisioning:**
- site-onboarding
- device-claim
- network-clone

**Remediation:**
- device-offline-handler
- port-flap-fix
- wan-failover-alert

**Compliance:**
- firmware-audit
- config-baseline-check
- acl-audit

**Monitoring:**
- capacity-report
- health-dashboard
- license-expiry-check

#### Workflow

```
1. Understand requirement
2. Select or create template
3. Generate SecureX JSON
4. Validate against schema
5. Save to clients/{client}/workflows/
6. Provide import instructions
```

#### Output

- **Workflow JSON:** `clients/{client}/workflows/{name}.json`
- **Import instructions:** How to import into Dashboard

#### Example Commands

```
"Create a workflow to notify when a device goes offline"
"Build firmware compliance check workflow"
"Create security alert handler for Slack"
"Set up daily health report workflow"
```

#### Invocation

```
/workflow-creator Create device offline alert workflow
```

#### Important Note

Workflows **cannot** be created via API - they must be imported manually into the Dashboard. The agent generates the JSON file and provides step-by-step import instructions.

---

### 2.5 Report Designer (Visual Reports)

**Color:** 🔷 Blue
**Model:** Claude Sonnet
**File:** `.claude/agents/report-designer.md`

#### Purpose

Transforms discovery JSON data into professional, interactive HTML reports. Creates visual dashboards that can be presented to clients.

#### When to Use

- After running network discovery
- Client presentation preparation
- Executive summary reports
- Network documentation

#### Capabilities

- Professional HTML reports with Tailwind CSS
- Interactive charts (Chart.js)
- Executive summary cards
- Device inventory tables (sortable/filterable)
- Issues & alerts by severity
- Configuration overview
- Metrics dashboard
- Recommendations section
- Responsive design (desktop/tablet/mobile)
- Print-optimized mode

#### Report Sections

1. **Executive Summary** - Networks, devices, issues, health score
2. **Topology View** - Hierarchical network diagram
3. **Device Inventory** - All devices with status
4. **Issues & Alerts** - Problems by severity
5. **Configurations** - VLANs, SSIDs, Firewall, VPN
6. **Metrics Dashboard** - Interactive charts
7. **Recommendations** - Suggested improvements
8. **Workflows** - Recommended automations

#### Workflow

```
1. Receive discovery JSON
2. Validate data structure
3. Generate HTML with Tailwind/Chart.js
4. Start local server (localhost:8080)
5. Open in Safari browser
6. Wait for user (Ctrl+C to stop)
```

#### Output

- **HTML Report:** `clients/{client}/reports/{date}_visual.html`
- **Local Server:** http://localhost:8080

#### Example Commands

```
"Generate visual report for the analysis"
"Create client presentation from discovery"
"Show the pretty report for jose-org"
```

#### Invocation

```
/report-designer Generate visual report for client jose-org
```

#### Integration

Automatically called by **network-analyst** after discovery completion.

---

### 2.6 Security (Audit & Compliance)

**Color:** 🟣 Magenta
**Model:** Claude Sonnet
**File:** `.claude/agents/security.md`

#### Purpose

Security analyst that audits Meraki configurations for vulnerabilities and compliance issues. Identifies security gaps and provides remediation recommendations.

#### When to Use

- Security audit of client network
- Compliance verification
- Vulnerability assessment
- Before/after configuration review
- Periodic security checks

#### Capabilities

**Configuration Audit:**
- ACL analysis (overly permissive rules)
- Firewall rule review
- Wireless security (open SSIDs, weak auth)
- VPN configuration
- Firmware version compliance
- Default credentials check

**Security Checks:**
- Open management ports
- Insecure protocols (Telnet, HTTP)
- Missing encryption
- Weak authentication methods
- Exposed services

**Compliance:**
- Best practices verification
- Policy compliance
- Regulatory requirements (PCI, HIPAA basics)

#### Severity Levels

| Level | Response Time | Examples |
|-------|--------------|----------|
| **CRITICAL** | 72 hours | Open admin access, default passwords |
| **HIGH** | 7 days | Weak encryption, missing firewall rules |
| **MEDIUM** | 30 days | Outdated firmware, suboptimal configs |
| **LOW** | 90 days | Missing documentation, minor issues |

#### Workflow

```
1. Collect current configurations
2. Run security checks
3. Identify vulnerabilities
4. Classify by severity
5. Generate recommendations
6. Create remediation plan
7. Output security report
```

#### Output

- **Security Report:** Findings by severity
- **Remediation Plan:** Step-by-step fixes
- **Compliance Status:** Pass/fail summary

#### Example Commands

```
"Audit security for this client's network"
"Check for vulnerabilities in the configuration"
"Verify compliance with security best practices"
"Review firewall rules for security issues"
```

#### Invocation

```
/security Audit security configuration for client ACME
```

---

## 3. How to Invoke Agents

### 3.1 Slash Command

The most direct way to invoke an agent:

```
/agent-name <task description>
```

**Examples:**

```
/maestro Configure complete network for new client
/meraki-specialist Create VLAN 100 for IoT devices
/network-analyst Run full discovery
/workflow-creator Create device offline handler
/report-designer Generate visual report
/security Audit network configuration
```

### 3.2 Natural Language

Agents are automatically selected based on your request:

| You Say | Agent Used |
|---------|------------|
| "Analyze this network" | network-analyst |
| "Configure an ACL" | meraki-specialist |
| "Create a workflow for..." | workflow-creator |
| "Generate a report" | report-designer |
| "Check security" | security |
| "Set up everything for this client" | maestro |

### 3.3 Examples by Task Type

#### Discovery & Analysis

```
"Analyze the network for client jose-org"
"What's the current state of this network?"
"Run discovery and show me what you find"
"Check network health"
```
→ **network-analyst**

#### Configuration

```
"Create an ACL to block port 23"
"Configure a new SSID called Guest-WiFi"
"Set up QoS for video streaming"
"Add firewall rule to block social media"
```
→ **meraki-specialist**

#### Automation

```
"Create a workflow to alert when device goes offline"
"Build automation for firmware compliance"
"Set up scheduled health reports"
```
→ **workflow-creator**

#### Reports

```
"Generate visual report from the discovery"
"Create client presentation"
"Show the dashboard report"
```
→ **report-designer**

#### Security

```
"Audit security configuration"
"Check for vulnerabilities"
"Verify compliance"
```
→ **security**

#### Complex Multi-Step

```
"Configure complete network: ACL + Firewall + SSID"
"Onboard new client with full setup"
"Analyze, fix issues, and create monitoring"
```
→ **maestro**

---

## 4. Agent Workflows

### 4.1 Discovery → Report Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User: "Analyze the network for client jose-org"            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  network-analyst                                             │
│  1. Validate credentials                                     │
│  2. Run full discovery                                       │
│  3. Analyze findings                                         │
│  4. Save: clients/jose-org/discovery/{date}.json            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (automatic)
┌─────────────────────────────────────────────────────────────┐
│  report-designer                                             │
│  1. Load discovery JSON                                      │
│  2. Generate HTML report                                     │
│  3. Start local server                                       │
│  4. Open in browser                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Output:                                                     │
│  - Discovery JSON                                            │
│  - Visual HTML report                                        │
│  - Summary with issues                                       │
│  - Recommendations                                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Configuration Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User: "Create SSID Guest-WiFi with captive portal"         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  meraki-specialist                                           │
│  1. Parse requirement                                        │
│  2. Validate network exists                                  │
│  3. Check available SSID slots                               │
│  4. Show configuration preview                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  >>> WAIT FOR USER CONFIRMATION <<<                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (user confirms)
┌─────────────────────────────────────────────────────────────┐
│  meraki-specialist                                           │
│  1. Backup current config                                    │
│  2. Apply SSID configuration                                 │
│  3. Apply splash page settings                               │
│  4. Validate result                                          │
│  5. Update changelog                                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Complex Tasks (Maestro)

```
┌─────────────────────────────────────────────────────────────┐
│  User: "Configure network with ACL, firewall, and SSIDs"    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  maestro                                                     │
│  1. Analyze task                                             │
│  2. Decompose into subtasks:                                 │
│     - Task 1: Configure ACLs                                 │
│     - Task 2: Set up firewall rules                          │
│     - Task 3: Create SSIDs                                   │
│  3. Create execution plan                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  >>> PRESENT PLAN & WAIT FOR APPROVAL <<<                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (user approves)
┌─────────────────────────────────────────────────────────────┐
│  maestro → meraki-specialist (Task 1: ACLs)                 │
│  Validate output ✓                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  maestro → meraki-specialist (Task 2: Firewall)             │
│  Validate output ✓                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  maestro → meraki-specialist (Task 3: SSIDs)                │
│  Validate output ✓                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  maestro: Final Report                                       │
│  - All tasks completed                                       │
│  - Summary of changes                                        │
│  - Changelog updated                                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Decision Tree: Which Agent to Use?

```
START
  │
  ├─► "I need to configure something"
  │     └─► Single config? ──► meraki-specialist
  │         Multiple configs? ──► maestro
  │
  ├─► "I need to analyze/understand the network"
  │     └─► network-analyst
  │
  ├─► "I need automation/alerts"
  │     └─► workflow-creator
  │
  ├─► "I need a visual report"
  │     └─► report-designer
  │
  ├─► "I need a security check"
  │     └─► security
  │
  └─► "I need multiple things done"
        └─► maestro
```

---

## 5. Appendix

### Agent File Locations

| Agent | File Path |
|-------|-----------|
| maestro | `.claude/agents/maestro.md` |
| meraki-specialist | `.claude/agents/meraki-specialist.md` |
| network-analyst | `.claude/agents/network-analyst.md` |
| workflow-creator | `.claude/agents/workflow-creator.md` |
| report-designer | `.claude/agents/report-designer.md` |
| security | `.claude/agents/security.md` |

### Output Locations

| Output Type | Path |
|-------------|------|
| Discovery Data | `clients/{client}/discovery/{date}.json` |
| Visual Reports | `clients/{client}/reports/{date}_visual.html` |
| Workflows | `clients/{client}/workflows/{name}.json` |
| Config Backups | `clients/{client}/discovery/{config}_backup.json` |
| Changelog | `clients/{client}/CHANGELOG.md` |

### Related Documentation

- [Workflow Design](/docs/Workflow_Design.md) - Detailed workflow documentation
- [Cisco Workflows Schema](/.claude/knowledge/cisco-workflows-schema.md) - SecureX JSON format
- [Meraki API Reference](https://developer.cisco.com/meraki/api-v1/)

---

*Document Version: 1.0*
*Last Updated: 2026-02-04*
*Generated with Claude Code (Opus 4.5)*
