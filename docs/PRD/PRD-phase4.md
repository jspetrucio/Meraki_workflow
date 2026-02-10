# CNL - PRD Phase 4: Smart Tools -- CNL Intelligence Layer

> **Version:** 1.0.0
> **Type:** Brownfield Enhancement - Intelligence Layer
> **Created:** 2026-02-09
> **Author:** Morgan (PM Agent) + jspetrucio
> **Status:** Draft
> **Epics:** 16, 17, 18
> **Story Points:** ~155 SP
> **Sprints:** 8-10 sprints
> **Coverage Target:** Beyond API coverage -- 12 unique analytical capabilities
> **Prerequisite:** Phases 1-3 substantially complete

---

## 1. Executive Summary

Phase 4 is fundamentally different from Phases 1-3. While those phases add 1:1 API endpoint wrappers, Phase 4 builds **intelligent tools that combine multiple API data sources** with custom analysis logic to deliver insights and automation that **don't exist anywhere else** -- not in the Meraki Dashboard, not in the API, not in any competing tool.

This is the **"Neural Language" vision realized**: tools that understand network context, analyze patterns, predict problems, and automate remediation. These 12 smart tools are what differentiate CNL from a simple API wrapper.

### Business Value

- Transforms CNL from an API wrapper into an **intelligent network assistant**
- Delivers insights that require hours of manual analysis in seconds
- Enables proactive network management (predict failures, detect anomalies, auto-remediate)
- Provides compliance and security auditing at scale
- Generates complete network documentation automatically
- Creates the competitive moat: no other Meraki tool offers this level of intelligence

### What Makes This Different

| Phases 1-3 | Phase 4 |
|------------|---------|
| 1 API call = 1 function | Multiple API calls = 1 insight |
| Fetch data | Analyze data |
| "Show me VPN config" | "Is my VPN healthy? What should I fix?" |
| Manual operation | Automated analysis |
| Dashboard alternative | Dashboard enhancement |

---

## 2. Goals & Success Criteria

### Goals

1. Build 12 smart tools that provide unique analytical value
2. Each tool combines data from 3+ API sources with custom logic
3. Deliver actionable insights, not just raw data
4. Enable proactive (not just reactive) network management
5. Create the intelligence layer that embodies the "Neural Language" vision

### Success Criteria

- All 12 smart tools operational and tested
- Each tool produces actionable output (not just data dumps)
- Health Score Calculator provides accurate 0-100 scores validated against real networks
- Security Posture Audit covers PCI-DSS and CIS Meraki Benchmark baselines
- Auto-Remediation Engine successfully handles at least 5 common scenarios
- Network Documentation Generator produces a complete, professional-quality PDF
- All smart tools accessible via natural language commands

---

## 3. Smart Tools

### 3.1 Network Intelligence

#### Epic 16: Health, Security & Compliance

---

**Story 16.1: Health Score Calculator**

> As a **network manager**,
> I want a single 0-100 health score per site/network,
> so that I can quickly identify which locations need attention.

**Data Sources:**
- Device status (online/offline/alerting)
- Wireless health (connection success rate, latency, signal quality)
- Client error rates (auth failures, DHCP failures)
- Uplink status (primary/failover, utilization)
- Firmware compliance (up-to-date vs. outdated)

**Acceptance Criteria:**
1. Generates a 0-100 health score per network
2. Score breakdown by category: devices (25%), wireless (25%), clients (20%), uplinks (15%), firmware (15%)
3. Color-coded output: green (80-100), yellow (60-79), orange (40-59), red (0-39)
4. Per-network and org-wide aggregate scores
5. Trend comparison: "health improved 5 points since last week"
6. Natural language: "what's the health score for our HQ network?" works
7. Integrates into discovery reports as a summary metric

**Agent:** network-analyst
**Est. SP:** 8

---

**Story 16.2: Security Posture Audit**

> As a **security engineer**,
> I want a comprehensive security assessment of my Meraki deployment,
> so that I can identify vulnerabilities and compliance gaps.

**Data Sources:**
- IPS settings (enabled/disabled, mode)
- AMP settings (enabled/disabled)
- Content filtering rules
- Firewall rules (L3/L7 + inbound)
- Open/permissive ports
- Admin 2FA status
- SSID security settings (open vs. WPA2/3)
- Switch port security (802.1X, DAI)

**Acceptance Criteria:**
1. Generates a security report with findings categorized by severity (critical/high/medium/low)
2. Each finding includes: description, affected resource, remediation recommendation
3. Overall security score (A-F grade)
4. Comparison against CIS Meraki Benchmark (when available)
5. Executive summary suitable for management reports
6. Exportable as HTML/PDF
7. Natural language: "run a security audit on our production network" works

**Agent:** network-analyst
**Est. SP:** 13

---

**Story 16.3: Compliance Checker**

> As a **compliance officer**,
> I want to validate network configuration against industry baselines,
> so that I can ensure PCI-DSS, HIPAA, or CIS compliance.

**Data Sources:**
- All configuration endpoints (firewall, SSID, VPN, admin settings)
- Policy objects
- Admin settings (2FA, SAML)
- Logging configuration (syslog, SNMP)
- Encryption settings (WPA version, TLS)

**Acceptance Criteria:**
1. Supports compliance profiles: PCI-DSS, HIPAA, CIS Meraki Benchmark
2. Each profile defines a set of rules (e.g., "PCI-DSS 1.2.1: Restrict inbound traffic to required ports")
3. Check results: PASS / FAIL / NOT_APPLICABLE per rule
4. Remediation steps for each FAIL result
5. Compliance percentage score per profile
6. Historical tracking: "we were 78% compliant last month, now 85%"
7. Natural language: "check PCI-DSS compliance for our retail networks" works
8. Custom compliance profiles supported (YAML-based rule definitions)

**Agent:** network-analyst
**Est. SP:** 13

---

### 3.2 Predictive & Proactive

#### Epic 17: Prediction, Anomaly Detection & Automation

---

**Story 17.1: Capacity Planning**

> As a **network architect**,
> I want growth projections based on historical trends,
> so that I can plan infrastructure upgrades proactively.

**Data Sources:**
- Client count history (30/60/90 days)
- Bandwidth usage history
- Device count trends
- AP client density

**Acceptance Criteria:**
1. Projects client count and bandwidth growth for 30/60/90 day forecast
2. Identifies networks approaching capacity limits (AP client density, uplink saturation)
3. Recommends: "HQ wireless will exceed 80% capacity in ~45 days at current growth"
4. Generates visual trend charts (embedded in HTML report)
5. Natural language: "will we need more APs in the next quarter?" works

**Agent:** network-analyst
**Est. SP:** 8

---

**Story 17.2: Change Impact Analysis**

> As a **network engineer**,
> I want to simulate "what if" scenarios before applying changes,
> so that I can understand the blast radius of configuration changes.

**Data Sources:**
- Current client list with traffic patterns
- Traffic data by application
- Firewall rules / ACLs
- Active VPN tunnels
- VLAN assignments

**Acceptance Criteria:**
1. Accepts a proposed change (e.g., "block port 443") and simulates impact
2. Returns affected clients count and list
3. Shows affected applications and estimated traffic volume impacted
4. Provides risk assessment: low/medium/high/critical
5. Supports: firewall rule changes, ACL changes, VLAN changes, SSID changes
6. Natural language: "what happens if I block port 443 on the guest network?" works
7. Dry-run integration: can be triggered automatically before any config change

**Agent:** meraki-specialist
**Est. SP:** 13

---

**Story 17.3: Auto-Remediation Engine**

> As a **NOC engineer**,
> I want automated responses to common network events,
> so that routine issues are resolved without human intervention.

**Data Sources:**
- Device status (online/offline)
- Wireless health metrics
- Config backups
- All write endpoints (for remediation actions)
- Alert history

**Remediation Scenarios:**
| Trigger | Auto-Response | Safety |
|---------|--------------|--------|
| Device offline > 5 min | Reboot device | Requires pre-approval |
| SSID connection rate drops > 20% | Rollback last SSID change | Requires pre-approval |
| Uplink utilization > 90% for 15 min | Apply traffic shaping | Requires pre-approval |
| Rogue AP detected | Contain rogue | Requires confirmation |
| Firmware compliance < 80% | Schedule upgrade window | Requires confirmation |

**Acceptance Criteria:**
1. Configurable remediation rules (YAML-based)
2. Each rule has: trigger condition, action, safety level, cooldown period
3. Pre-approval mode: admin approves scenarios in advance, engine acts autonomously
4. Confirmation mode: engine proposes action, waits for human confirmation
5. Audit log: all automated actions logged with timestamp, trigger, action, result
6. Rollback: every automated action creates a backup, can be undone
7. Cooldown: prevents action loops (e.g., don't reboot the same device every 5 minutes)
8. Dashboard: shows active rules, recent actions, and success rate
9. Natural language: "set up auto-reboot for offline devices" works

**Agent:** meraki-specialist
**Est. SP:** 21

---

**Story 17.4: Bandwidth Anomaly Detection**

> As a **security/network engineer**,
> I want to detect unusual bandwidth patterns,
> so that I can identify potential intrusions, abuse, or failures.

**Data Sources:**
- Client bandwidth history (baseline)
- Traffic by application
- Historical usage patterns (time-of-day, day-of-week)

**Acceptance Criteria:**
1. Establishes per-network bandwidth baselines (7-day rolling average)
2. Detects anomalies: usage > 2 standard deviations from baseline
3. Classifies anomalies: spike (sudden increase), drop (sudden decrease), sustained high, unusual application
4. Alerts include: affected network, magnitude of deviation, top contributing clients/apps
5. Natural language: "are there any bandwidth anomalies this week?" works

**Agent:** network-analyst
**Est. SP:** 13

---

**Story 17.5: Predictive Maintenance**

> As a **network manager**,
> I want to predict device failures before they happen,
> so that I can replace failing equipment proactively.

**Data Sources:**
- Device uptime history
- Reboot frequency
- Firmware age
- Error rates (from device status)
- Model/hardware revision

**Acceptance Criteria:**
1. Scores each device on a 0-100 "reliability" scale
2. Flags devices with: frequent reboots, very old firmware, high error rates
3. Recommends replacement priority list
4. Tracks reliability trend over time
5. Natural language: "which devices are most likely to fail?" works

**Agent:** network-analyst
**Est. SP:** 13

---

### 3.3 Documentation & Operations

#### Epic 18: Documentation, Comparison & Workflow Generation

---

**Story 18.1: Multi-Site Config Comparison**

> As a **network architect**,
> I want to compare configurations across multiple sites,
> so that I can identify divergences from the standard.

**Data Sources:**
- All config endpoints across multiple networks
- Config templates (if bound)

**Acceptance Criteria:**
1. Accepts 2+ networks for comparison
2. Returns diff report: identical settings, divergent settings, unique settings
3. Highlights "significant" differences (security-impacting, performance-impacting)
4. Supports comparison categories: firewall, VLANs, SSIDs, switch ports, security
5. Natural language: "compare the config of HQ and branch-01" works
6. Exportable as HTML report

**Agent:** network-analyst
**Est. SP:** 8

---

**Story 18.2: Config Drift Detection**

> As a **network admin**,
> I want to be alerted when configuration changes unexpectedly,
> so that I can detect unauthorized or accidental changes.

**Data Sources:**
- Snapshot system (existing)
- Change log API
- All config endpoints

**Acceptance Criteria:**
1. Periodic snapshot comparison (configurable interval: hourly, daily, weekly)
2. Alert when config differs from baseline snapshot
3. Shows: what changed, when it changed, who changed it (from change log)
4. Suppresses known/approved changes (via integration with CNL change tracking)
5. Natural language: "has anything changed in our production network since last Monday?" works
6. Integrates with existing snapshot system in discovery.py

**Agent:** network-analyst
**Est. SP:** 8

---

**Story 18.3: Network Documentation Generator**

> As a **network engineer**,
> I want auto-generated complete network documentation,
> so that I can deliver professional documentation to clients without manual effort.

**Data Sources:**
- Full discovery output
- All config endpoints
- LLDP/CDP topology
- VLAN/subnet maps
- Security policy summary

**Acceptance Criteria:**
1. Generates a complete network documentation package including:
   - Network topology diagram (text-based or SVG)
   - IP addressing plan (VLANs, subnets, DHCP)
   - Device inventory with roles and locations
   - Security policy summary (firewall rules, ACLs, IPS, AMP)
   - Wireless configuration (SSIDs, RF, guest access)
   - VPN topology
   - Monitoring configuration (SNMP, syslog, alerts)
2. Output formats: HTML and PDF
3. Professional formatting with table of contents
4. Auto-updates: re-run to refresh documentation
5. Natural language: "generate complete documentation for the acme network" works
6. Customizable sections (include/exclude specific areas)

**Agent:** network-analyst
**Est. SP:** 13

---

**Story 18.4: Automated Workflow Generator**

> As a **network admin**,
> I want CNL to automatically generate remediation workflows based on detected issues,
> so that I can fix problems with one click instead of building workflows manually.

**Data Sources:**
- `find_issues()` output
- Workflow templates (existing)
- Remediation patterns

**Acceptance Criteria:**
1. Analyzes `find_issues()` output and generates targeted N8N/SecureX workflows
2. Each generated workflow addresses a specific detected issue
3. Workflow includes: detection trigger, validation step, remediation action, notification
4. User reviews generated workflow before deployment
5. Natural language: "create a workflow to fix the issues you found" works
6. Integrates with existing workflow templates in `workflow.py`

**Agent:** workflow-creator
**Est. SP:** 13

---

## 4. Architecture: Smart Tools Pattern

Smart tools follow a different pattern than Phases 1-3:

```python
# smart_tools/health_score.py

class HealthScoreCalculator:
    """Calculates network health scores from multiple data sources."""

    def __init__(self, client: MerakiClient):
        self.client = client

    async def calculate(self, network_id: str) -> HealthScoreResult:
        """Calculate health score for a network."""
        # 1. Gather data from multiple sources
        devices = await self._get_device_health(network_id)
        wireless = await self._get_wireless_health(network_id)
        clients = await self._get_client_health(network_id)
        uplinks = await self._get_uplink_health(network_id)
        firmware = await self._get_firmware_health(network_id)

        # 2. Calculate weighted scores
        score = (
            devices.score * 0.25 +
            wireless.score * 0.25 +
            clients.score * 0.20 +
            uplinks.score * 0.15 +
            firmware.score * 0.15
        )

        # 3. Generate findings and recommendations
        findings = self._analyze_findings(devices, wireless, clients, uplinks, firmware)

        return HealthScoreResult(
            network_id=network_id,
            score=round(score),
            grade=self._score_to_grade(score),
            breakdown={...},
            findings=findings,
            recommendations=self._generate_recommendations(findings),
        )
```

### Key Differences from API Wrappers

1. **Multiple API calls per tool** -- Each smart tool calls 3-10 API methods
2. **Custom analysis logic** -- Scoring, anomaly detection, compliance checking
3. **Actionable output** -- Recommendations, not just data
4. **Async execution** -- Uses `asyncio.gather()` for parallel data fetching
5. **Result caching** -- Expensive analyses cached for reasonable intervals

### File Structure

```
scripts/
  smart_tools/
    __init__.py
    health_score.py          # Story 16.1
    security_audit.py        # Story 16.2
    compliance_checker.py    # Story 16.3
    capacity_planning.py     # Story 17.1
    change_impact.py         # Story 17.2
    auto_remediation.py      # Story 17.3
    anomaly_detection.py     # Story 17.4
    predictive_maintenance.py # Story 17.5
    config_comparison.py     # Story 18.1
    drift_detection.py       # Story 18.2
    doc_generator.py         # Story 18.3
    workflow_generator.py    # Story 18.4
    compliance_profiles/
      pci_dss.yaml
      hipaa.yaml
      cis_meraki.yaml
    remediation_rules/
      default.yaml
```

---

## 5. Totals Summary

| Category | Count |
|----------|-------|
| Smart tools | 12 |
| API data sources per tool | 3-10 |
| Total stories | 12 |
| Total story points | ~155 SP |
| Estimated sprints | 8-10 |

### Story Point Breakdown by Epic

| Epic | Stories | SP |
|------|---------|-----|
| Epic 16: Health, Security & Compliance | 3 stories | 34 SP |
| Epic 17: Prediction, Anomaly & Automation | 5 stories | 68 SP |
| Epic 18: Documentation, Comparison & Workflows | 4 stories | 42 SP |
| **Total** | **12 stories** | **~155 SP** |

---

## 6. Dependencies & Risks

### Dependencies
- Phases 1-3 must be substantially complete (smart tools depend on underlying API coverage)
- `find_issues()` expansion from Phases 1-3 feeds into Compliance Checker and Workflow Generator
- Snapshot system (existing) feeds into Drift Detection
- N8N integration (Epic 5) feeds into Automated Workflow Generator

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auto-Remediation causes unintended changes | Critical | Pre-approval + cooldown + mandatory audit log |
| Health Score calibration (scores too high/low) | Medium | Validate against real networks, allow custom weights |
| Compliance profiles incomplete/inaccurate | Medium | Start with CIS Meraki Benchmark, iterate |
| Performance: smart tools make many API calls | Medium | Parallel fetching + result caching + rate limiting |
| Anomaly detection false positives | Medium | Tunable thresholds + learning period |

---

## 7. Why Phase 4 Matters

These 12 smart tools are what transform CNL from a **Meraki Dashboard replacement** into an **intelligent network management assistant**:

| Without Phase 4 | With Phase 4 |
|-----------------|--------------|
| "Show me the firewall rules" | "Are my firewall rules secure? Here's what to fix." |
| "List all devices" | "These 3 devices are at risk of failing soon." |
| "Show me bandwidth" | "There's an anomaly -- traffic is 300% above normal on VLAN 10." |
| "Run discovery" | "Your network health is 73/100. Here's what's dragging it down." |
| Manual documentation | "Here's your complete network documentation, auto-generated." |
| Reactive troubleshooting | "I auto-rebooted AP-lobby after it was offline for 5 min." |

This is the **competitive moat**. No other Meraki tool provides this level of automated intelligence.

---

## 8. Quality Metrics

| Metric | Target |
|--------|--------|
| Test coverage for smart tools | >= 85% |
| Health Score validated against 5+ real networks | Yes |
| Compliance profiles cover >= 80% of CIS Meraki Benchmark | Yes |
| Auto-Remediation has audit log for every action | 100% |
| All smart tools have < 30s execution time (100-network org) | Yes |
| False positive rate for anomaly detection | < 10% |

---

*Generated by Morgan (PM Agent) | CNL PRD Phase 4 v1.0.0*
*-- Morgan, planejando o futuro*
