# Project Brief: Cisco Neural Language (CNL)

> **Type:** Brownfield (evolving existing codebase into product)
> **Project Context:** Internal Cisco tool (requires Cisco branding approval)
> **Working Name:** Cisco Neural Language (CNL)
> **Created:** 2026-02-05
> **Author:** Atlas (Analyst Agent) + jspetrucio
> **Status:** Draft - Pending Review

---

## Executive Summary

**Cisco Neural Language (CNL)** is a local-first automation platform that allows Cisco network engineers to manage Meraki networks using natural language. Currently an internal CLI tool with 10 fully implemented Python modules (codenamed "Meraki Workflow"), the project will be transformed into a distributable product available as a desktop app (Tauri), CLI, Docker container, and npm/Homebrew package. Users interact with specialized AI agents (network-analyst, meraki-specialist, workflow-creator) through a chat-style interface to discover, configure, and automate Meraki networks.

**Primary problem:** Meraki administrators spend hours on repetitive Dashboard tasks (discovery, configuration, compliance auditing) that could be automated through natural language commands. No internal tool exists that bridges natural language to Meraki API operations with multi-client support.

**Value proposition:** Install locally, connect your Meraki API key, and manage your entire network infrastructure through conversation - discovery to deployment in minutes, not hours.

---

## Problem Statement

### Current Pain Points

1. **Manual configuration overhead:** Meraki Dashboard requires clicking through dozens of screens for routine operations (SSID setup, firewall rules, ACL policies). At scale (100+ networks), this becomes unsustainable.

2. **No programmatic workflow creation:** Cisco Workflows cannot be created via API - administrators must manually build each workflow in the Dashboard GUI. This blocks automation at the most critical layer.

3. **Multi-client management gap:** MSPs and Cisco engineers managing multiple client organizations must switch contexts constantly. No tool provides unified multi-tenant management with automation.

4. **Expensive AI alternatives:** Cisco AI Assistant (the only commercial NL-to-Meraki tool) is enterprise-tier, Dashboard-locked, and single-organization. Selector AI costs $50K-$500K+/year.

5. **Discovery and auditing friction:** Understanding a client's full network state (devices, SSIDs, VLANs, firewall rules, offline devices) requires navigating multiple Dashboard sections and mentally aggregating information.

### Impact

- Engineers spend **2-4 hours per client** on routine discovery and configuration
- Security misconfigurations go undetected until audit (no automated compliance checking)
- Workflow creation bottleneck limits automation adoption
- Knowledge siloed in senior engineers who know the Dashboard intimately

### Why Now

- LLM APIs are mature and cost-effective for natural language understanding
- Meraki API v1 has comprehensive coverage (829+ endpoints)
- Cisco's own AI Assistant validates the market demand
- Multi-provider AI (Claude, GPT, Gemini, Ollama) makes BYOK viable
- The tool already exists and works - it just needs productization

---

## Proposed Solution

### Core Concept

Transform the existing Meraki Workflow CLI into a **local-first application** with a chat interface where users interact with specialized AI agents through natural language. The app runs entirely on the user's machine - no cloud infrastructure, no subscription, no data leaving the laptop.

### Architecture

```
User (Natural Language)
        |
   ┌────▼────────────────┐
   │   Interface Layer    │
   │  CLI | Web UI | App  │
   └────┬────────────────┘
        |
   ┌────▼────────────────┐
   │   Agent Router       │
   │  Routes NL → Agent   │
   └────┬───┬───┬────────┘
        |   |   |
   ┌────▼┐ ┌▼──┐ ┌▼──────────┐
   │Netw.│ │Mer│ │Workflow   │
   │Anal.│ │Spc│ │Creator    │
   └──┬──┘ └─┬─┘ └────┬─────┘
      |      |        |
   ┌──▼──────▼────────▼─────┐
   │   Python Core Modules    │
   │  auth|api|discovery|     │
   │  config|report|workflow  │
   └──────────┬──────────────┘
              |
   ┌──────────▼──────────────┐
   │  AI Engine (BYOK)       │
   │  Claude|GPT|Gemini|     │
   │  Ollama (local)         │
   └──────────┬──────────────┘
              |
   ┌──────────▼──────────────┐
   │  Meraki Dashboard API    │
   └─────────────────────────┘
```

### Key Differentiators

1. **Local-first:** Zero cloud dependency. Data stays on the user's machine.
2. **Multi-provider AI:** User brings their own API key (Claude, GPT, Gemini) or runs Ollama locally for zero cost.
3. **Agent-based:** Three specialized agents with deep Meraki domain knowledge, not a generic chatbot.
4. **Multi-client:** Built from day one for managing multiple Meraki organizations.
5. **Open source:** Only open-source NL-to-Meraki tool in the market.
6. **Workflow generation:** Programmatic creation of SecureX/Cisco Workflow JSONs (unique capability).

---

## Target Users

### Primary Segment: Cisco Network Engineers

- **Profile:** Cisco employees who deploy and manage Meraki networks for enterprise clients
- **Current workflow:** SSH into Dashboard, manually click through configuration screens, copy-paste between spreadsheets and Dashboard
- **Pain points:** Repetitive configuration, slow discovery, context-switching between clients
- **Goal:** Reduce client visit time from hours to minutes
- **Technical level:** High (comfortable with CLI and APIs)

### Secondary Segment: MSPs and Meraki Partners/Integrators

- **Profile:** Managed Service Providers and Cisco Partners managing 10-100+ Meraki client organizations
- **Current workflow:** Dashboard per client, manual auditing, no standardized workflows
- **Pain points:** Multi-client management overhead, inconsistent configurations, slow onboarding
- **Goal:** Scale operations without scaling headcount
- **Technical level:** Medium-High

### Tertiary Segment: Any Meraki Administrator

- **Profile:** IT administrators at organizations using Meraki (schools, hospitals, retail chains)
- **Current workflow:** Dashboard GUI for everything
- **Pain points:** Limited automation, security misconfigurations, lack of reporting
- **Goal:** Automate routine tasks, get visibility into network health
- **Technical level:** Medium (prefers GUI over CLI)

---

## Goals & Success Metrics

### Business Objectives

- Achieve **500 GitHub stars** within 6 months of public release
- Reach **100 active monthly users** (pip install + active usage) within 6 months
- Establish as the **#1 open-source Meraki automation tool** (by GitHub stars and community activity)
- Build community of **20+ contributors** within first year

### User Success Metrics

- **Time to first discovery:** < 5 minutes from install to seeing network overview
- **Configuration speed:** 10x faster than manual Dashboard operations
- **Onboarding completion rate:** > 80% of users who install complete onboarding (API key + first discovery)
- **Agent interaction success rate:** > 90% of natural language commands correctly understood and executed

### Key Performance Indicators (KPIs)

- **Install-to-discovery time:** Target < 5 minutes
- **Weekly active users (WAU):** Track growth trajectory
- **Commands per session:** Average NL commands executed per user session
- **Agent routing accuracy:** % of commands correctly routed to right agent
- **Error rate:** % of commands that fail at API level

---

## MVP Scope

### Core Features (Must Have)

- **Multi-channel install:**
  - `pip install cnl` (Python users)
  - `npx cnl` (Node.js users)
  - `brew install cnl` (Mac users)
  - `docker run cnl` (Enterprise/CI)
  - **Tauri desktop app** - `CNL.app` / `CNL.exe` (primary experience)
- **Guided onboarding:** First-run wizard collecting Meraki API Key, Org ID, and AI provider API key
- **Desktop app (Tauri):** Native app with chat interface, system tray, menubar status
- **Local web UI (chat):** Browser-based fallback at `localhost:3141` with agent sidebar
- **Three AI agents:**
  - **Network Analyst:** Full discovery, health analysis, issue detection, recommendations
  - **Meraki Specialist:** Configure SSID, firewall, ACL, VLAN, switch ports via NL
  - **Workflow Creator:** Generate SecureX/Cisco Workflow JSONs from NL descriptions
- **Multi-provider AI (BYOK):** Support for Anthropic (Claude), OpenAI (GPT), and Google (Gemini) APIs
- **Multi-client profiles:** Manage multiple Meraki organizations with profile switching
- **Discovery with reporting:** Automated network scan with HTML report generation
- **Configuration with safety:** Automatic backup before changes, rollback capability
- **CLI mode:** Full CLI access for power users (`cnl discover`, `cnl config`, etc.)
- **N8N integration:** Optional plugin for advanced workflow automation (scheduled audits, alerts, triggers)

### Out of Scope for MVP

- Ollama/local LLM support (Phase 2)
- Real-time monitoring/alerting (Phase 2)
- Multi-user/team features (Phase 2)
- Cloud-hosted version / SaaS (Phase 3+)
- Mobile app (not planned)
- Non-Meraki vendor support (future consideration)
- Community agent marketplace (Phase 3)

### MVP Success Criteria

The MVP is successful when:
1. A user can install via any channel (pip, npx, brew, docker, .app) within 2 minutes
2. The Tauri desktop app opens with a functional chat interface
3. The onboarding collects credentials and validates API connectivity
4. User can say "analyze my network" and get a complete discovery report
5. User can say "block telnet on all networks" and the agent configures firewall rules
6. User can say "create a device offline alert workflow" and get exportable JSON
7. All operations work with Claude, GPT, or Gemini as the AI backend
8. N8N integration allows scheduling automated discovery/compliance workflows

---

## Post-MVP Vision

### Phase 2 Features (1-3 months after MVP)

- **Ollama support:** Run completely offline with local LLMs (Llama, Mistral)
- **Compliance templates:** Pre-built security compliance checks (PCI, HIPAA, SOC2)
- **Scheduled discovery:** Automatic periodic network scans with change detection (via N8N)
- **Diff reports:** Compare network state between snapshots, highlight changes
- **Real-time monitoring:** Dashboard with live device status and alerts
- **Multi-user/team features:** Shared configurations, role-based access

### Long-term Vision (6-12 months)

- **Community agent marketplace:** Users create and share custom agents
- **Multi-vendor support:** Extend beyond Meraki (Aruba, UniFi, Fortinet)
- **Team collaboration:** Shared configurations, approval workflows, audit logs
- **Integration hub:** Slack, Teams, PagerDuty, ServiceNow connectors
- **AI-powered remediation:** Automatic fix suggestions with one-click apply

### Expansion Opportunities

- **Cisco partner program integration:** Official Cisco DevNet listing
- **Enterprise tier:** RBAC, SSO, audit trail, compliance reporting
- **Training mode:** Interactive learning environment for new Meraki admins
- **API-as-a-service:** Expose agent capabilities as REST API for third-party integrations

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** macOS (primary), Windows, Linux
- **Python:** 3.10+ required
- **Browser:** Any modern browser (Chrome, Safari, Firefox) for web UI
- **Performance:** Discovery of 100-network org should complete in < 60 seconds
- **Memory:** < 200MB RAM for the local server

### Technology Stack (Current + Planned)

- **Backend:** Python 3.10+ (existing - FastAPI to be added for web server)
- **Frontend:** React + TypeScript (new - chat UI component)
- **AI Integration:** LiteLLM or equivalent for multi-provider abstraction
- **CLI:** Click (existing)
- **Templates:** Jinja2 (existing)
- **API Client:** Official Meraki Python SDK (existing)
- **Reports:** HTML via Jinja2 (existing), WeasyPrint for PDF (existing)
- **Desktop App:** Tauri (MVP - primary distribution)
- **Workflow Automation:** N8N (optional, user-hosted or cloud)
- **Package Manager:** pip + npm + Homebrew + Docker (all MVP)

### Architecture Considerations

- **Repository Structure:** Monorepo - Python backend + React frontend in same repo
- **Service Architecture:** Single local process (FastAPI serves both API and static frontend)
- **WebSocket:** For real-time chat streaming between UI and agents
- **Agent Framework:** Custom routing layer mapping NL intent to agent + tool calls
- **Integration Requirements:** Meraki API v1 (existing), LLM provider APIs (new), N8N API (optional)
- **Security:** API keys stored locally in `~/.meraki/credentials` (existing pattern). Never transmitted to any cloud service except the chosen AI provider for inference.

### Existing Codebase (Brownfield Inventory)

| Module | Lines | Status | Reuse Plan |
|--------|-------|--------|------------|
| `scripts/auth.py` | ~200 | Production | Keep as-is |
| `scripts/api.py` | ~500 | Production | Keep as-is |
| `scripts/discovery.py` | ~600 | Production | Keep, add WebSocket streaming |
| `scripts/config.py` | ~400 | Production | Keep, add NL parsing layer |
| `scripts/workflow.py` | ~350 | Production | Keep as-is |
| `scripts/report.py` | ~300 | Production | Keep, add web-served reports |
| `scripts/changelog.py` | ~150 | Production | Keep as-is |
| `scripts/cli.py` | ~400 | Production | Keep for CLI mode |
| `scripts/report_server.py` | ~100 | Production | Evolve into main web server |
| Agent definitions (3) | ~600 | Production | Adapt for programmatic routing |

**Estimated reuse:** ~85% of existing code carries forward unchanged.

---

## Constraints & Assumptions

### Constraints

- **Budget:** Internal Cisco project. Development time is the primary cost.
- **Timeline:** MVP target within 6-8 weeks of focused development (expanded scope with Tauri + multi-channel).
- **Resources:** Single developer (jspetrucio) + AI agents for acceleration.
- **Technical:**
  - Meraki API rate limit: 10 requests/second per organization (SDK handles)
  - Workflows cannot be created via API (generate JSON for manual import)
  - Some Meraki features require specific licenses (Camera API needs MV license)
  - LLM API costs passed to user (BYOK model)

### Key Assumptions

- Users have Python 3.10+ installed (or are willing to install it)
- Users have a valid Meraki Dashboard API key with appropriate permissions
- Users are willing to provide their own AI provider API key
- The Meraki Python SDK will continue to be maintained by Cisco
- LLM providers will maintain backwards-compatible APIs
- Local-first approach is preferred over cloud-hosted for this user base
- English is the primary language (Portuguese as secondary)
- Users have basic familiarity with network concepts (VLANs, SSIDs, firewalls)

---

## Risks & Open Questions

### Key Risks

- **Cisco API changes:** Meraki API v1 is stable but Cisco could deprecate endpoints or change rate limits. *Mitigation:* Pin SDK versions, maintain compatibility layer.
- **AI provider dependency:** Multi-provider mitigates single-provider risk, but all providers could change pricing or terms. *Mitigation:* Ollama support (Phase 2) provides offline fallback.
- **Agent accuracy:** NL-to-config errors could cause network outages. *Mitigation:* Mandatory backup before changes, confirmation prompts for destructive operations, dry-run mode.
- **Cisco branding approval:** Product name "Cisco Neural Language" needs internal branding team approval. *Mitigation:* Use working name, submit branding request early.
- **Market timing:** Cisco AI Assistant could expand rapidly, reducing the gap. *Mitigation:* Move fast, position as complementary internal tool.
- **Scope creep:** Multi-channel distribution (5 channels) + desktop app + N8N is ambitious for MVP. *Mitigation:* Prioritize Tauri app + pip first, add other channels incrementally.

### Open Questions

- Cisco branding team approval process and timeline for "Cisco Neural Language" name?
- Internal distribution channels available (Cisco internal app store, DevNet, etc.)?
- How to handle AI agent errors gracefully in production (hallucinated API calls, wrong network targeted)?
- What level of confirmation/approval should be required before applying configurations?
- Should the web UI support multiple simultaneous chat sessions (one per client)?
- How to handle Meraki organizations with 1000+ networks (pagination, performance)?
- What telemetry/analytics (if any) should be collected for product improvement?

### Areas Needing Further Research

- Meraki API terms of service for third-party distribution
- LiteLLM vs custom multi-provider abstraction layer
- Tauri vs Electron build size and performance comparison
- Ollama model quality for network configuration tasks
- FastAPI WebSocket performance for real-time chat streaming
- React chat UI component libraries (best fit for agent-style interface)

---

## Appendices

### A. Research Summary

#### Competitive Landscape (Feb 2026)

| Product | Type | NL Support | Multi-Client | Open Source | Price |
|---------|------|-----------|-------------|-------------|-------|
| Cisco AI Assistant | Native Dashboard | Full NL | Single org | No | Enterprise $$$|
| Cisco Workflows | Native Dashboard | No (GUI) | Single org | No | Included |
| Selector AI | SaaS AIOps | Queries only | Enterprise | No | $50K-500K+/yr |
| Meraki Python SDK | Library | No | Manual | Yes | Free |
| **Cisco Neural Language** | **Local app** | **Full NL** | **Yes** | **Internal** | **Free** |

**Key finding:** No direct competitor exists for open-source, NL-powered, multi-client Meraki automation.

#### Market Validation

- Cisco invested in AI Assistant (validates demand for NL network management)
- Selector AI raised $66M (validates AIOps market)
- 829+ Meraki System Atomics (validates automation demand)
- Active Meraki developer community on DevNet (distribution channel)

### B. Existing Codebase Capabilities

**Fully operational modules:**
- Multi-profile credential management
- Complete Meraki API wrapper with retry/rate-limit handling
- Network discovery with issue detection and recommendations
- SSID, VLAN, Firewall, ACL configuration with backup/rollback
- SecureX/Cisco Workflow JSON generation with 10 templates
- HTML/PDF report generation
- Click-based CLI with all operations
- Change tracking with Git integration

### C. References

- [Meraki Dashboard API v1](https://developer.cisco.com/meraki/api-v1/)
- [Meraki Python SDK](https://github.com/meraki/dashboard-api-python)
- [Cisco Workflows Documentation](https://documentation.meraki.com/Platform_Management/Workflows)
- [Tauri Framework](https://tauri.app/)
- [LiteLLM - Multi-provider LLM gateway](https://github.com/BerriAI/litellm)
- [Vercel AI SDK](https://sdk.vercel.ai/)

---

## Next Steps

### Immediate Actions

1. **Review this Project Brief** - Validate assumptions, fill gaps, approve direction
2. **Handoff to @pm** - Create PRD with detailed user stories and technical requirements
3. **Handoff to @architect** - Define technical architecture (FastAPI + React + Agent Router)
4. **Prototype agent router** - Build the NL → agent routing layer as proof of concept
5. **Design web UI** - Wireframe the chat interface with agent sidebar

### PM Handoff

This Project Brief provides the full context for **Cisco Neural Language (CNL)**. Please start in 'PRD Generation Mode', review the brief thoroughly to work with the user to create the PRD section by section as the template indicates, asking for any necessary clarification or suggesting improvements.

---

*Generated by Atlas (Analyst Agent) | Cisco Neural Language (CNL) Project Brief v1.0*
*— Atlas, investigando a verdade*
