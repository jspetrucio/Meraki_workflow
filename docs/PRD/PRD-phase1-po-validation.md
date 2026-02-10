# PRD Phase 1 -- Product Owner Validation Report

> **PRD:** CNL Phase 1: Core Operations (P0)
> **Validator:** Pax (PO Agent)
> **Date:** 2026-02-09
> **PRD Version:** 1.0.0
> **Validation Mode:** Comprehensive (Brownfield Checklist)
> **Overall Readiness:** 87%
> **Decision:** CONDITIONAL APPROVAL

---

## 1. Executive Summary

**Project Type:** Brownfield Enhancement -- API Coverage Expansion
**Scope:** Epics 8-10, adding ~55-67 new api.py methods, ~17-20 discovery functions, ~20-23 config functions, and ~55-61 tool schemas across 22 stories.
**Baseline:** Epics 1-7 complete, 643 tests passing, 7-step implementation pattern established.

### Overall Assessment

The PRD is well-structured and demonstrates strong alignment with the existing codebase architecture. It correctly leverages the established 7-step implementation pattern, existing safety layer, backup/rollback infrastructure, and FUNCTION_REGISTRY model. However, there are **numeric inconsistencies** in the totals summary, a **story count discrepancy** (22 actual vs. 20 stated), and several areas where specification depth is insufficient for DANGEROUS operations. After addressing the must-fix items below, this PRD is ready for sharding into individual story files and development.

**Go/No-Go:** CONDITIONAL GO -- pending resolution of 3 must-fix deficiencies.

---

## 2. Category-by-Category Validation

### 2.1 Project Setup (Brownfield) -- PASS

| Check | Status | Notes |
|-------|--------|-------|
| Existing system integration points identified | PASS | PRD references api.py, discovery.py, config.py, agent_router.py, agent_tools.py, safety.py -- all verified to exist |
| 7-step implementation pattern documented | PASS | Section 4 describes the exact pattern matching current codebase |
| Rollback procedures defined | PASS | Backup + rollback support specified for WRITE operations |
| Development environment preserves existing functionality | PASS | PRD states "100% backward compatibility" as a goal; existing 643 tests serve as regression suite |
| Prerequisites correctly stated | PASS | Epics 1-7 complete, Task Executor (Epic 7), Safety Layer (Story 3.3) |

**Notes:** The brownfield integration is well thought out. The PRD correctly identifies that new functions must be registered in `FUNCTION_REGISTRY` (agent_router.py line 251), new safety classifications added to both `SAFETY_CLASSIFICATION` (safety.py) and `TOOL_SAFETY` (agent_tools.py), and new tool schemas added to the appropriate `NETWORK_ANALYST_TOOLS` or `MERAKI_SPECIALIST_TOOLS` lists.

---

### 2.2 Infrastructure -- PASS

| Check | Status | Notes |
|-------|--------|-------|
| Database (skip -- file-based) | N/A | Correctly file-based; backups written to `clients/{name}/backups/` |
| API framework (FastAPI) | PASS | Already set up at `scripts/server.py`; no new routes needed (tools exposed via agent chat) |
| Testing infrastructure (pytest) | PASS | 25 test files exist; pytest configured in CI |
| CI/CD (GitHub Actions) | PASS | `ci.yml` runs pytest on Python 3.10/3.11/3.12 with `--maxfail=3` |
| Meraki SDK integration | PASS | `MerakiClient` class with `wait_on_rate_limit=True`, `retry_4xx_error=True`, `maximum_retries=3` |

**Notes:** The existing `MerakiClient.safe_call()` method (api.py line 350) correctly handles 400/404 errors gracefully, which is critical for discovery functions that may hit endpoints unsupported by certain network types.

---

### 2.3 External Dependencies -- PASS with WARN

| Check | Status | Notes |
|-------|--------|-------|
| Meraki API key required | PASS | Handled by existing `scripts/auth.py` profile system |
| Rate limiting addressed | WARN | PRD mentions leveraging `safe_call()` but does not specify rate budget allocation for 67 new methods |
| API version/limits acknowledged | PASS | Risk table mentions firmware version requirements |
| SDK version compatibility | PASS | Uses `meraki` Python SDK with built-in rate limiting |

**WARN Detail (Rate Limiting):** The Meraki API enforces 10 requests/second per organization. With ~67 new methods (many of which will be called during `full_discovery()`), the expanded discovery could hit rate limits. The PRD should specify:
1. Whether discovery functions use batched calls or sequential calls
2. Expected API call count for a full discovery run post-Phase 1
3. Whether any new endpoints use action batches (organization-wide operations)

---

### 2.4 UI/UX -- PASS

| Check | Status | Notes |
|-------|--------|-------|
| Frontend exists (React 19) | PASS | `frontend/` directory with React 19 + shadcn/ui |
| Minimal UI impact | PASS | All new features are backend tool schemas exposed via existing chat interface |
| Confirmation dialogs for DANGEROUS ops | PASS | Existing safety layer handles typed CONFIRM via WebSocket |
| No new UI components needed | PASS | Correct -- all interaction through existing NL chat |

---

### 2.5 Feature Sequencing -- PASS with WARN

#### Epic 8 (Security Services) -- 5 Stories

| Story | Depends On | Can Parallelize? |
|-------|-----------|-----------------|
| 8.1 VPN | None (new endpoint group) | Yes (independent) |
| 8.2 Content Filtering | None | Yes |
| 8.3 IPS | None | Yes |
| 8.4 AMP | None | Yes |
| 8.5 Traffic Shaping | None | Yes |

**Verdict:** All 5 stories in Epic 8 are independent and can be parallelized.

#### Epic 9 (Alerts, Firmware & Observability) -- 8 Stories

| Story | Depends On | Can Parallelize? |
|-------|-----------|-----------------|
| 9.1 Alerts & Webhooks | None | Yes |
| 9.2 Firmware | None | Yes |
| 9.3 Ping | None | Yes |
| 9.4 Traceroute | None | Yes |
| 9.5 Cable Test | None | Yes |
| 9.6 SNMP | None | Yes |
| 9.7 Syslog | None | Yes |
| 9.8 Change Log | None | Yes |

**Verdict:** All 8 stories in Epic 9 are independent and can be parallelized.

#### Epic 10 (Switching, Wireless & Platform) -- 9 Stories

| Story | Depends On | Can Parallelize? |
|-------|-----------|-----------------|
| 10.1 L3 Routing | None | Yes |
| 10.2 STP | None | Yes |
| 10.3 Reboot/Blink | None | Yes |
| 10.4 NAT | None | Yes |
| 10.5 RF Profiles | None | Yes |
| 10.6 Wireless Health | None | Yes |
| 10.7 QoS | None | Yes |
| 10.8 Org Admins | None | Yes |
| 10.9 Inventory | None | Yes |

**Verdict:** All 9 stories in Epic 10 are independent and can be parallelized.

**Cross-Epic Dependencies:** None identified. All 22 stories are independent of each other, which is excellent for parallel development. Each story follows the same 7-step pattern and touches the same set of files, but at different function/schema insertion points.

**WARN:** The `full_discovery()` integration (adding new discovery functions into the main discovery loop at discovery.py line 536) needs careful ordering to avoid merge conflicts when multiple stories are developed in parallel. Recommend assigning `full_discovery()` integration as a final integration step per epic, not per story.

---

### 2.6 Risk Management (CRITICAL for Brownfield) -- WARN

| Risk Area | Status | Details |
|-----------|--------|---------|
| VPN config changes (DANGEROUS) | PASS | Story 8.1 correctly classified as DANGEROUS with backup + confirmation |
| STP changes (DANGEROUS) | PASS | Story 10.2 correctly classified as DANGEROUS |
| L3 routing changes (DANGEROUS) | PASS | Story 10.1 correctly classified as DANGEROUS with backup + rollback |
| Device reboot (DANGEROUS) | PASS | Story 10.3 correctly classified as DANGEROUS for reboot, SAFE for blink |
| Admin management (DANGEROUS) | PASS | Story 10.8 correctly classified as DANGEROUS |
| Firmware upgrades (DANGEROUS) | PASS | Story 9.2 correctly classified as DANGEROUS |
| Device release (DANGEROUS) | PASS | Story 10.9 correctly classifies release as DANGEROUS |
| Rate limiting with new methods | WARN | See section 2.3 |
| All WRITE tools have backup | WARN | See deficiency D-2 below |
| All DANGEROUS tools need confirmation | PASS | Existing safety layer defaults unclassified operations to DANGEROUS |
| Dry-run support for DANGEROUS ops | WARN | PRD does not mention dry-run mode for VPN, STP, or L3 routing |

**DANGEROUS Operations Inventory:**

| Operation | Story | Risk Description |
|-----------|-------|-----------------|
| `configure_s2s_vpn` | 8.1 | Can break all branch connectivity |
| `add_vpn_peer` | 8.1 | Can create routing conflicts |
| `update_intrusion_settings` | 8.3 | Can disable security protection |
| `schedule_firmware_upgrade` | 9.2 | Can cause device reboots at scheduled time |
| `configure_switch_l3_interface` | 10.1 | Can break inter-VLAN routing |
| `add_switch_static_route` | 10.1 | Can create routing black holes |
| `configure_stp` | 10.2 | Can cause broadcast storms/loops |
| `reboot_device` | 10.3 | Causes service interruption |
| `manage_admin` / `create_admin` / `delete_admin` | 10.8 | Security-sensitive access control |
| `release_device` | 10.9 | Permanently removes device from org |

**WARN Detail:** The PRD specifies backup + confirmation for DANGEROUS operations but does not describe:
1. Whether `dry-run` mode (already supported in safety.py) will be available for VPN, STP, and L3 routing changes
2. What the backup scope is for VPN config (org-level, not network-level -- current `backup_config()` is network-scoped)
3. Rollback procedure for firmware upgrades (cannot easily roll back firmware)

---

### 2.7 MVP Scope -- PASS

| Check | Status | Notes |
|-------|--------|-------|
| All stories support day-1/day-2 operations | PASS | VPN, security, firmware, monitoring, switching, wireless -- all core ops |
| No feature creep | PASS | No UI stories, no new infrastructure, no new agents |
| Business value clearly stated | PASS | "Covers 80% of support ticket categories" |
| Aligned with coverage expansion goal | PASS | 3.5% -> 15% API coverage |

**Notes:** The scope is tightly focused on API method coverage. No unnecessary features detected.

---

### 2.8 Documentation -- PASS

| Check | Status | Notes |
|-------|--------|-------|
| Architecture docs exist | PASS | `docs/Architecture/` with 4 documents |
| Implementation pattern documented | PASS | Section 4 of PRD + existing codebase pattern |
| Stories have acceptance criteria | PASS | All 22 stories have numbered AC |
| Scope tables per story | PASS | Layer/New Items/Details tables in every story |
| Safety classifications specified | PASS | SAFE/MODERATE/DANGEROUS per story |
| Story point estimates | PASS | All stories have SP estimates |

---

### 2.9 Quality Metrics -- PASS

| Metric | Target | Verifiable? | Notes |
|--------|--------|-------------|-------|
| Test coverage >= 90% | PASS | Yes -- pytest + CI enforcement | Consistent with existing 643 tests |
| Tool schemas pass validation | PASS | Yes -- `validate_tool_schema()` exists | Existing function at agent_tools.py line 1014 |
| `additionalProperties: False` | PASS | Yes -- validation checks this | Existing check at agent_tools.py line 1056 |
| WRITE tools have backup | PASS | Yes -- verifiable in code review | backup_config() pattern exists |
| DANGEROUS tools require confirmation | PASS | Yes -- safety.py defaults unknown to DANGEROUS | safety.py line 104 |
| Discovery integration >= 80% | PASS | Yes -- check `full_discovery()` | Currently covers all existing features |

---

## 3. Critical Deficiencies

### D-1: Story Count Discrepancy (MUST FIX)

**Location:** Section 6 (Totals Summary) and Section 1 (Executive Summary)
**Issue:** The PRD states "20 stories" and "20 most common daily operations." The actual count is:
- Epic 8: 5 stories
- Epic 9: 8 stories
- Epic 10: 9 stories
- **Total: 22 stories**

**Impact:** Sprint planning, capacity allocation, and progress tracking will be incorrect if based on 20 stories.
**Fix:** Update the following references from 20 to 22:
- Section 1: "20 most common daily operations" -> "22 most common daily operations"
- Section 6 table: "Total stories | 20" -> "Total stories | 22"

### D-2: Numeric Totals Mismatch (MUST FIX)

**Location:** Section 6 (Totals Summary)
**Issue:** The itemized counts per story do not match the stated totals:

| Category | PRD States | Actual Sum | Delta |
|----------|-----------|------------|-------|
| api.py methods | ~55 | 67 | +12 |
| discovery.py functions | ~17 | 20 | +3 |
| config.py functions | ~20 | 23 | +3 |
| tool schemas | ~55 | 61 | +6 |
| Story points | ~90 | 93 | +3 |

**Impact:** Underestimating scope leads to underestimated timelines. Sprint velocity calculations will drift.
**Fix:** Update Section 6 totals to match the actual per-story sums, or reconcile by adjusting individual story scopes. The `~` prefix helps but the deltas are significant (up to 22%).

### D-3: VPN Backup Scope Gap (MUST FIX)

**Location:** Story 8.1 (Site-to-Site VPN)
**Issue:** VPN configuration is org-level (`getOrganizationApplianceVpn`), but the existing `backup_config()` function (config.py line 76) operates at network-level scope. There is no org-level backup mechanism. Story 8.1 AC #4 states "Backup created before any VPN config change" but does not specify how org-level backup will work.

**Impact:** If VPN backup uses the existing network-scoped backup, it will not capture the full org-level VPN topology. A failed rollback could leave partial VPN configuration.
**Fix:** Story 8.1 must either:
- (a) Extend `backup_config()` to support org-level resources, or
- (b) Create a new `backup_vpn_config()` function specifically for org-level VPN topology

---

## 4. Risk Assessment (Top 5)

### Risk 1: Cascading VPN Outage (HIGH)
- **Probability:** Medium
- **Impact:** Critical -- affects all branch connectivity
- **Trigger:** Incorrect VPN topology change (hub-spoke to full-mesh or vice versa)
- **Mitigation:** DANGEROUS classification + typed CONFIRM + org-level backup
- **Residual Gap:** Dry-run mode not specified for VPN changes

### Risk 2: STP Loop Storm (HIGH)
- **Probability:** Low
- **Impact:** Critical -- can take down entire L2 domain
- **Trigger:** Bridge priority change to incorrect value, or mode change during production hours
- **Mitigation:** DANGEROUS classification + backup + confirmation
- **Residual Gap:** No time-of-day restriction or maintenance window awareness

### Risk 3: Rate Limit Exhaustion During Discovery (MEDIUM)
- **Probability:** Medium (especially for large orgs with 50+ networks)
- **Impact:** Medium -- discovery fails mid-run, partial data
- **Trigger:** `full_discovery()` with ~20 new discovery functions hitting endpoints per network
- **Mitigation:** Existing `safe_call()` and SDK `wait_on_rate_limit=True`
- **Residual Gap:** No discovery call budget estimation; no progress indicator

### Risk 4: Firmware Rollback Impossibility (MEDIUM)
- **Probability:** Low
- **Impact:** High -- firmware downgrades often not supported
- **Trigger:** `schedule_firmware_upgrade` pushes broken firmware
- **Mitigation:** `cancel_firmware_upgrade` for pending upgrades
- **Residual Gap:** PRD does not address what happens after firmware is applied (no downgrade API)

### Risk 5: Admin Account Lockout (MEDIUM)
- **Probability:** Low
- **Impact:** High -- could lock out the API key owner
- **Trigger:** `delete_admin` removes the only org admin, or changes own role
- **Mitigation:** DANGEROUS classification + confirmation
- **Residual Gap:** No guard-rail preventing self-deletion or last-admin-standing protection

---

## 5. Recommendations

### Must-Fix (Required before development starts)

| ID | Item | Priority | Effort |
|----|------|----------|--------|
| MF-1 | Fix story count: 20 -> 22 in Sections 1 and 6 | Critical | 5 min |
| MF-2 | Reconcile numeric totals in Section 6 with per-story sums | Critical | 15 min |
| MF-3 | Specify org-level backup mechanism for VPN (Story 8.1) | Critical | Add 1 paragraph to 8.1 AC |

### Should-Fix (Recommended before sprint planning)

| ID | Item | Priority | Effort |
|----|------|----------|--------|
| SF-1 | Add dry-run mode requirement for VPN (8.1), STP (10.2), and L3 routing (10.1) DANGEROUS operations | High | Add AC line per story |
| SF-2 | Add guard-rail AC to Story 10.8: "Cannot delete the last org admin" and "Cannot delete own admin account via API key" | High | Add 2 AC lines |
| SF-3 | Add note to Story 9.2: "Firmware downgrades are not supported by Meraki API; cancel is only available for pending upgrades" | Medium | Add 1 AC line |
| SF-4 | Specify expected `full_discovery()` API call budget post-Phase 1 (estimate total calls for a 50-network org) | Medium | Add subsection to Section 7 |
| SF-5 | Add `full_discovery()` integration strategy: recommend per-epic integration pass to avoid merge conflicts | Medium | Add note to Section 4 |

### Consider (Nice-to-have)

| ID | Item | Priority | Effort |
|----|------|----------|--------|
| C-1 | Add minimum firmware version requirements per story (some API endpoints require specific firmware) | Low | Research + table |
| C-2 | Consider maintenance window awareness for DANGEROUS ops (time-of-day check before STP/VPN changes) | Low | Future enhancement |
| C-3 | Add progress/status callback for Live Tools (ping/traceroute/cable test) async operations | Low | UX improvement |
| C-4 | Consider batch API calls for discovery functions to reduce rate limit impact | Low | Performance optimization |
| C-5 | Add per-story test count estimates (e.g., 8-15 tests per story) to improve sprint predictability | Low | Planning aid |

---

## 6. Story-Level Validation Matrix

| Story | AC Complete? | Safety Correct? | Scope Table? | Backup Specified? | Discovery Integration? | SP Reasonable? |
|-------|-------------|-----------------|-------------|-------------------|----------------------|----------------|
| 8.1 VPN | PASS | PASS (DANGEROUS) | PASS | WARN (org-level gap) | PASS | PASS (8 SP) |
| 8.2 Content Filtering | PASS | PASS (MODERATE) | PASS | PASS | PASS | PASS (5 SP) |
| 8.3 IPS | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (5 SP) |
| 8.4 AMP | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (3 SP) |
| 8.5 Traffic Shaping | PASS | PASS (MODERATE) | PASS | PASS | PASS | PASS (5 SP) |
| 9.1 Alerts | PASS | PASS (MODERATE) | PASS | PASS | PASS | PASS (8 SP) |
| 9.2 Firmware | PASS | PASS (DANGEROUS) | PASS | N/A (firmware, not config) | PASS | PASS (8 SP) |
| 9.3 Ping | PASS | PASS (SAFE) | PASS | N/A (read-only) | N/A (no discovery) | PASS (3 SP) |
| 9.4 Traceroute | PASS | PASS (SAFE) | PASS | N/A (read-only) | N/A (no discovery) | PASS (3 SP) |
| 9.5 Cable Test | PASS | PASS (SAFE) | PASS | N/A (read-only) | N/A (no discovery) | PASS (3 SP) |
| 9.6 SNMP | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (3 SP) |
| 9.7 Syslog | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (3 SP) |
| 9.8 Change Log | PASS | PASS (SAFE) | PASS | N/A (read-only) | PASS | PASS (2 SP) |
| 10.1 L3 Routing | PASS | PASS (DANGEROUS) | PASS | PASS | PASS | PASS (5 SP) |
| 10.2 STP | PASS | PASS (DANGEROUS) | PASS | WARN (no backup mentioned) | PASS | PASS (3 SP) |
| 10.3 Reboot/Blink | PASS | PASS (split DANGEROUS/SAFE) | PASS | N/A (no config change) | N/A (no discovery) | PASS (2 SP) |
| 10.4 NAT | PASS | PASS (MODERATE) | PASS | PASS | PASS | PASS (5 SP) |
| 10.5 RF Profiles | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (5 SP) |
| 10.6 Wireless Health | PASS | PASS (SAFE) | PASS | N/A (read-only) | PASS | PASS (5 SP) |
| 10.7 QoS | PASS | PASS (MODERATE) | PASS | WARN (no backup mentioned) | PASS | PASS (3 SP) |
| 10.8 Org Admins | PASS | PASS (DANGEROUS) | PASS | WARN (no backup for admin changes) | PASS | PASS (3 SP) |
| 10.9 Inventory | PASS | PASS (split MODERATE/DANGEROUS) | PASS | N/A (no config to backup) | PASS | PASS (3 SP) |

**Backup WARNs:** Stories 8.3, 8.4, 9.6, 9.7, 10.2, 10.5, 10.7, and 10.8 specify MODERATE or DANGEROUS safety but do not explicitly mention backup support in their acceptance criteria. The existing safety layer does mandate backup for MODERATE and DANGEROUS operations (safety.py line 118-122), so this will be enforced at runtime. However, the PRD quality metric states "All WRITE tools have backup support = 100%". Recommend adding explicit backup AC to each WRITE story for clarity and traceability.

---

## 7. Codebase Integration Verification

### Verified Integration Points

| Component | File | Integration Method | Status |
|-----------|------|-------------------|--------|
| API wrapper | `scripts/api.py` | Add methods with `@log_api_call` | VERIFIED -- decorator exists (line 53) |
| Discovery | `scripts/discovery.py` | Add functions using `client.safe_call()` | VERIFIED -- pattern exists (line 350) |
| Config | `scripts/config.py` | Add functions returning `ConfigResult` | VERIFIED -- dataclass exists (line 55) |
| Agent Router | `scripts/agent_router.py` | Register in `FUNCTION_REGISTRY` via `_build_function_registry()` | VERIFIED -- builder pattern exists (line 203-251) |
| Tool Schemas | `scripts/agent_tools.py` | Add to `NETWORK_ANALYST_TOOLS` or `MERAKI_SPECIALIST_TOOLS` | VERIFIED -- lists exist (line 106, 379) |
| Safety Layer | `scripts/safety.py` | Add to `SAFETY_CLASSIFICATION` dict | VERIFIED -- dict exists (line 50) |
| Tool Safety | `scripts/agent_tools.py` | Add to `TOOL_SAFETY` dict | VERIFIED -- dict exists (line 31) |
| Issue Detection | `scripts/discovery.py` | Extend `find_issues()` function | VERIFIED -- function exists (line 621) |
| Full Discovery | `scripts/discovery.py` | Add calls in `full_discovery()` loop | VERIFIED -- network loop exists (line 536) |

### Dual Safety Registration Note

The codebase has **two separate safety classification dictionaries** that must stay synchronized:
1. `SAFETY_CLASSIFICATION` in `scripts/safety.py` (line 50) -- used by `classify_operation()`
2. `TOOL_SAFETY` in `scripts/agent_tools.py` (line 31) -- used by `get_tool_safety()` and `requires_confirmation()`

Each new tool must be registered in **both** dictionaries. This is not mentioned in the PRD and should be documented in the implementation pattern (Section 4) or addressed by refactoring into a single source of truth.

---

## 8. Final Decision

### CONDITIONAL APPROVAL

The PRD is approved for sharding into individual story files and development, **conditional upon resolving the 3 must-fix deficiencies:**

1. **MF-1:** Fix story count from 20 to 22
2. **MF-2:** Reconcile numeric totals with per-story sums
3. **MF-3:** Specify org-level backup mechanism for VPN (Story 8.1)

The should-fix items (SF-1 through SF-5) are strongly recommended before sprint planning but do not block story file creation.

### Confidence Level

| Dimension | Score |
|-----------|-------|
| Completeness | 85% -- story content is thorough; totals need correction |
| Feasibility | 95% -- all integration points verified in codebase |
| Safety | 80% -- DANGEROUS ops identified; backup gaps and dry-run gaps remain |
| Sequencing | 95% -- all stories independent; excellent parallelization |
| Clarity | 90% -- consistent format; acceptance criteria are actionable |
| **Overall** | **87%** |

---

*Validated by Pax (PO Agent) | 2026-02-09*
*PRD: CNL Phase 1 v1.0.0*
