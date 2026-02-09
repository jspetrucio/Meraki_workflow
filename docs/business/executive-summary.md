# CNL (Cisco Neural Language) -- Executive Summary

> **Author:** jspetrucio
> **Date:** February 2026
> **Classification:** Cisco Internal
> **Status:** For Executive Review
> **Demo:** Available on request

---

> **TL;DR**
>
> - **What:** Natural language interface for the entire Cisco Meraki platform -- discovery, configuration, monitoring, and automation via conversation.
> - **Why now:** Juniper Marvis is winning competitive deals on AI narrative. Gartner predicts network automation triples by 2026. The first-mover window is closing.
> - **Differentiator:** Only product combining NL configuration + BYOK (Bring Your Own Key) + intelligence layer + native Meraki integration. No competitor offers all four.
> - **Impact:** $212M--$451M total annual business impact for Cisco. Customer ROI of 350--600% with 2--3 month payback.
> - **Ask:** 3 engineers, 6 months, ~$500K. Working prototype with 646 tests already exists. Internal beta in 90 days.

---

## 1. Executive Summary

Cisco Neural Language (CNL) is a conversational AI interface that lets network engineers manage the entire Meraki platform using natural language -- replacing hundreds of manual Dashboard clicks with simple commands like *"block telnet on all switches"* (executed in 10 seconds vs. 30 minutes manually). With Juniper Marvis actively winning deals on AI narrative and network engineers losing **40--51% of their workweek** to manual tasks (Skybox Security, 2024), Cisco faces an urgent competitive gap in AI-powered network management. CNL closes that gap with three specialized AI agents, a built-in safety layer, and a BYOK model that gives enterprises full control over their AI provider and data -- a capability **no competitor offers**. The prototype is working today with 646 passing tests, and a $500K Phase 1 investment can deliver an internal beta within 90 days, targeting **$87M--$216M in direct annual revenue** and **$212M--$451M in total business impact**.

---

## 2. The Problem

**Cisco Meraki has no natural language interface for network management.** This gap is costing us deals, customers, and market credibility.

- **Juniper Marvis is the #1 sales argument against Meraki** in competitive deals, positioning Juniper ahead of Cisco on AI narrative in peer reviews.
- Network professionals spend **40--51% of their workweek** on manual, repetitive tasks (Skybox Security, 2024). That is over 20 hours per engineer per week lost to clicking through dashboards.
- **90% of network managers fear compliance audit failures** due to misconfigurations, and 69% have identified 2+ compliance issues during external audits.
- Cisco's ThousandEyes AI Assistant (GA July 2025) covers monitoring and troubleshooting but **does NOT configure anything** -- leaving the configuration gap wide open.
- **Gartner predicts network automation will triple by 2026.** The market is moving. We are not.

---

## 3. The Solution: Cisco Neural Language (CNL)

CNL is a natural language interface for the **complete Meraki platform** -- not just monitoring, but discovery, configuration, automation, and reporting, all via conversation.

**What works today:**

| Command | What Happens | Time Saved |
|---------|-------------|------------|
| *"Block telnet on all switches"* | ACL applied across 12 switches with backup | 30 min to 10 sec |
| *"Which device consumes the most bandwidth?"* | Real-time traffic analysis with NL answer | 1--2 hours to seconds |
| *"Run a security audit on NYC office"* | Comprehensive report with actionable insights | 4--8 hours to 2 min |
| *"Create a workflow for device-offline alerts"* | Production-ready automation JSON generated | 2--3 hours to 1 min |

**Architecture highlights:**

- **3 specialized AI agents:** network-analyst, meraki-specialist, workflow-creator
- **Built-in safety layer:** confirmation prompts, dry-run mode, automatic backup/rollback for every write operation
- **BYOK (Bring Your Own Key):** customer uses their own AI provider -- OpenAI, Claude, Azure, AWS Bedrock, or Google Gemini
- **Multi-platform:** Web UI (React 19), CLI, Desktop (Tauri 2.0), Docker

---

## 4. Key Differentiators

| Capability | CNL | Juniper Marvis | ThousandEyes AI | HPE Aruba | rConfig |
|-----------|-----|----------------|-----------------|-----------|---------|
| NL Troubleshooting | Yes | Yes | Yes | Limited | No |
| **NL Configuration** | **Yes** | No | No | No | Yes (generic) |
| **NL Discovery** | **Yes** | Partial | No | No | No |
| **NL Workflow Creation** | **Yes** | No | No | No | No |
| **BYOK Multi-Provider AI** | **Yes** | No | No | No | No |
| Security Audit via NL | Yes | No | No | No | No |
| Compliance Check via NL | Yes | No | No | No | Partial |
| Auto-Remediation | Yes | Limited | No | No | No |
| **Native Meraki Integration** | **Yes** | N/A | Monitoring only | N/A | Generic NCM |

**CNL is the only product in the industry that combines:** natural language configuration + BYOK multi-provider AI + domain-specific intelligence layer + native Meraki integration. No competitor offers all four.

---

## 5. BYOK: The Strategic Advantage

**Bring Your Own Key** means the customer supplies their own AI provider API key. CNL never processes, stores, or routes AI traffic through Cisco infrastructure.

| Benefit | Impact |
|---------|--------|
| **Data sovereignty** | Customer data never leaves their infrastructure |
| **Compliance** | Simplifies GDPR, HIPAA, PCI-DSS, FedRAMP adherence |
| **Zero vendor lock-in** | Switch providers (OpenAI/Claude/Azure/Bedrock/Gemini) in one config line |
| **Cost control** | 40--90% savings vs. vendor-locked AI solutions |
| **Enterprise adoption** | Removes the #1 blocker for AI adoption in regulated industries |

**No competitor offers BYOK for network management AI.** Juniper Marvis is locked to their proprietary backend. ThousandEyes AI is locked to Cisco's model. For regulated industries -- government, financial services, healthcare -- BYOK is not a feature, it is a **requirement**. CNL is the only tool that satisfies this.

---

## 6. Current Status

**This is not a concept. It is a working system.**

| Metric | Status |
|--------|--------|
| **Test suite** | 646 tests passing |
| **API coverage** | 30+ Meraki SDK methods wrapped and tested |
| **Tool schemas** | 35 tools across 3 specialized agents |
| **Safety layer** | Full: confirmation, dry-run, backup/rollback, rate limiting |
| **Frontend** | React 19 + TypeScript + shadcn/ui + Zustand |
| **Backend** | Python 3.10+ FastAPI + WebSocket |
| **Desktop** | Tauri 2.0 native app (optional) |
| **Distribution** | pip, npm, Docker, Homebrew -- all ready |
| **Live demo** | Available on request |

---

## 7. Market Opportunity

| Metric | Value | Source |
|--------|-------|--------|
| Network automation market (2025) | **$5.7--$7.9B** | MarketsandMarkets, Straits, Precedence |
| Market growth rate | **18--22% CAGR** | Multiple analysts |
| Gartner automation forecast | **Triples by 2026** | Gartner, Sep 2024 |
| Cisco networking revenue (Q3 FY25) | **$7.0B** (+8% YoY) | Cisco IR |
| Cisco ARR | **$30.6B** (+5%) | Cisco IR |
| Meraki installed base (est.) | **300K--500K customers** | CRN / estimate |

---

## 8. Business Impact

### Customer ROI (per 5-engineer team managing 50 sites)

| Item | Annual Value |
|------|-------------|
| Time savings (5 eng x $45K avg) | $225,000 |
| Error reduction (~30 incidents avoided) | $150,000--$500,000 |
| Headcount optimization (2--3 fewer positions) | $200,000--$300,000 |
| Downtime reduction | $100,000--$200,000 |
| Compliance cost avoidance | $50,000--$100,000 |
| **Total annual savings** | **$725,000--$1,325,000** |
| **Customer ROI** | **350--600%** |
| **Payback period** | **2--3 months** |

### Cisco Revenue Opportunity

| Category | Conservative | Aggressive |
|----------|-------------|-----------|
| Direct CNL revenue | **$87M/year** | **$216M/year** |
| Indirect impact (churn, upsell, acquisition) | $125M/year | $235M/year |
| **Total annual impact** | **$212M/year** | **$451M/year** |
| Development investment (Year 1) | $1.0M | $1.6M |
| **ROI for Cisco** | **3,400%** | **7,500%** |

---

## 9. Roadmap

| Phase | Scope | Story Points | API Coverage | Timeline |
|-------|-------|-------------|-------------|----------|
| **Phase 1** (P0) | Core Operations -- VPN, IPS, AMP, content filtering, firmware, live tools, alerts | 90 SP | **~15%** | 3 months |
| **Phase 2** (P1) | Platform Depth -- SD-WAN, templates, HA, camera, sensors, advanced switching | 75 SP | **~35%** | 2 months |
| **Phase 3** (P2) | Specialized Features -- Systems Manager, Insight, cellular gateway, licensing | 50 SP | **~50%** | 2 months |
| **Phase 4** | Intelligence Layer -- 12 AI-powered smart tools | 155 SP | Beyond API | 3 months |

**Phase 4 smart tools** represent CNL's highest-value differentiator: health scores, security audits, compliance checks, anomaly detection, auto-remediation, and predictive maintenance. These combine data from multiple API sources to deliver intelligence that **does not exist in the Meraki Dashboard or any competitor product**.

---

## 10. The Ask

| Resource | Detail |
|----------|--------|
| **Engineering** | 3 engineers for 6 months (backend, frontend, DevOps/test) |
| **Executive sponsor** | VP/SVP from Meraki Product organization |
| **Pilot program** | 5--10 MSP partners for early validation |
| **Phase 1 investment** | **~$500K** (3 engineers x 6 months) |
| **Target milestone** | Internal beta in **90 days** |

### Execution plan:

1. **Immediate:** Demo to Meraki Product leadership
2. **30 days:** Align with ThousandEyes team on complementary positioning
3. **60 days:** Pilot with 5--10 selected MSP partners
4. **90 days:** Internal beta (Cisco IT dogfooding)
5. **6 months:** Public beta with free tier
6. **9 months:** GA launch with Pro + Enterprise tiers

---

## 11. Why Now

**Competitive urgency is real.** Juniper Marvis is winning deals today. rConfig, a startup, is already shipping NL-based network configuration. The first-mover window for Cisco to own this category is closing.

**The market is ready.** Gartner predicts network automation triples by 2026. Enterprises are allocating AI budgets now. Customer demand for conversational network management is growing.

**Cisco strategy alignment.** CNL aligns directly with Cisco's AI-first infrastructure vision and the push toward software/subscription revenue growth (+25% YoY in Q3 FY25).

**We are not starting from zero.** A working prototype exists with 646 passing tests, multi-platform distribution, and a live demo. This is an acceleration opportunity, not a greenfield bet.

**The question is not whether conversational network management will happen. It is whether Cisco leads it or follows.**

---

> **Contact:** Jose Petrucio da Silva (jspetrucio)
> **Project:** CNL -- Cisco Neural Language
> **Classification:** Cisco Internal
> **Demo:** Available on request
