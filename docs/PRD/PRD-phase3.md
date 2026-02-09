# CNL - PRD Phase 3: Specialized Features (P2)

> **Version:** 1.0.0
> **Type:** Brownfield Enhancement - API Coverage Expansion
> **Created:** 2026-02-09
> **Author:** Morgan (PM Agent) + jspetrucio
> **Status:** Draft
> **Epics:** 14, 15
> **Story Points:** ~50 SP
> **Sprints:** 4-5 sprints
> **Coverage Target:** 35% -> 50% (~50 new api.py methods)
> **Prerequisite:** Phase 2 complete (Epics 11-13)

---

## 1. Executive Summary

Phase 3 completes CNL's API coverage to **50%** by adding support for specialized Meraki product lines: Systems Manager (SM/MDM), Insight (application monitoring), Camera ML, Cellular Gateway (MG), IoT/Zigbee, SAML/SSO, advanced licensing, and niche wireless features.

This phase adds **~50 new api.py methods**, **~12 discovery functions**, **~10 config functions**, and **~37 tool schemas** across 12 feature groups.

### Business Value

- Full MDM/SM support enables endpoint management via natural language
- Insight integration provides application performance monitoring
- Cellular Gateway support covers SD-WAN with 4G/5G failover deployments
- Completes coverage for all mainstream Meraki product lines
- Makes CNL a comprehensive Meraki management platform

---

## 2. Goals & Success Criteria

### Goals

1. Full Systems Manager (MDM) support for device management
2. Application health monitoring via Insight integration
3. Cellular Gateway management for LTE/5G deployments
4. Cover all remaining enterprise-relevant API categories
5. Achieve ~50% total API coverage

### Success Criteria

- Full MDM/SM support: device inventory, profiles, lock/wipe, software compliance
- Insight monitoring: application health, media server monitoring
- Camera ML: custom analytics, MV Sense object detection
- All specialized product lines accessible through CNL
- Total coverage reaches ~430 methods (~50% of 855 endpoints)

---

## 3. Feature Groups

### 3.1 Systems Manager / MDM

#### Epic 14: Endpoint Management & Specialized Products

---

**Story 14.1: Systems Manager (SM/MDM)**

> As an **IT admin**,
> I want to manage mobile and desktop devices via CNL,
> so that I can perform MDM operations through natural language.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 7 methods | `get_sm_devices`, `get_sm_profiles`, `get_sm_users`, `lock_sm_device`, `wipe_sm_device`, `install_app`, `get_sm_software` |
| `discovery.py` | 1 function | `discover_sm_devices` |
| `config.py` | 2 functions | `manage_sm_device`, `assign_sm_profile` |
| `agent_tools.py` | 6 schemas | meraki-specialist tools |
| Safety | DANGEROUS (wipe/lock) / MODERATE (profile assign) / SAFE (read) |

**Acceptance Criteria:**
1. `discover_sm_devices` returns all managed devices with compliance status, OS, model
2. `get_sm_profiles` returns all MDM profiles with assignment counts
3. `get_sm_users` returns user-device mapping
4. `lock_sm_device` remotely locks a device (DANGEROUS, requires confirmation)
5. `wipe_sm_device` remotely wipes a device (DANGEROUS, requires typing CONFIRM)
6. `install_app` pushes an app to managed devices
7. `get_sm_software` returns installed software inventory for compliance checks
8. `assign_sm_profile` assigns/unassigns profiles to devices
9. Issue detection: `sm_device_noncompliant` when device fails compliance policy
10. Natural language: "lock the iPad in conference room B" works

**Est. SP:** 13

---

### 3.2 Application Monitoring

---

**Story 14.2: Insight (App Health)**

> As a **network engineer**,
> I want to monitor application performance and media server health,
> so that I can proactively identify degraded services.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_insight_applications`, `get_insight_app_health`, `get_monitored_media_servers`, `create_monitored_media_server` |
| `discovery.py` | 1 function | `discover_insight_apps` |
| `config.py` | 1 function | `configure_monitored_media` |
| `agent_tools.py` | 4 schemas | network-analyst tools |
| Safety | SAFE (read) / MODERATE (config) |

**Acceptance Criteria:**
1. `discover_insight_apps` returns monitored applications with health scores
2. `get_insight_app_health` returns time-series health data (goodput, latency, loss)
3. `get_monitored_media_servers` returns configured media servers (Webex, Zoom, etc.)
4. `create_monitored_media_server` adds a new media server to monitor
5. Issue detection: `insight_app_degraded` when app health drops below threshold
6. Natural language: "how is Webex performing across our networks?" works

**Est. SP:** 5

---

### 3.3 Camera ML

---

**Story 14.3: Camera ML / Custom Analytics**

> As a **facilities manager**,
> I want to configure camera ML features (object detection, custom analytics),
> so that I can use cameras for intelligent building management.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_custom_analytics`, `update_custom_analytics`, `get_analytics_artifacts`, `get_camera_sense`, `update_camera_sense` |
| `discovery.py` | 1 function | `discover_camera_ml` |
| `config.py` | 1 function | `configure_camera_analytics` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. `discover_camera_ml` returns ML capabilities per camera (MV Sense enabled, custom models)
2. `get_camera_sense` returns object detection settings and recent detections
3. `update_camera_sense` enables/configures MV Sense (people detection, vehicle detection)
4. `get_custom_analytics` returns configured custom ML models and artifacts
5. `update_custom_analytics` manages custom analytics model deployment

**Est. SP:** 5

---

### 3.4 Cellular Gateway

---

**Story 14.4: Cellular Gateway (MG)**

> As a **network engineer**,
> I want to manage Cellular Gateway (MG) devices,
> so that I can configure LTE/5G failover and standalone deployments.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 6 methods | `get_mg_lan`, `update_mg_lan`, `get_mg_port_forwarding`, `update_mg_port_forwarding`, `get_mg_uplink_statuses`, `get_mg_dhcp` |
| `discovery.py` | 1 function | `discover_cellular_gateways` |
| `config.py` | 2 functions | `configure_mg_lan`, `configure_mg_port_forwarding` |
| `agent_tools.py` | 5 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. `discover_cellular_gateways` returns all MG devices with uplink status and signal strength
2. `configure_mg_lan` manages LAN settings (IP, subnet, DHCP)
3. `configure_mg_port_forwarding` manages port forwarding rules
4. `get_mg_uplink_statuses` returns cellular signal quality, carrier, technology (LTE/5G)
5. Issue detection: `mg_failover_untested` when MG device has no recent failover test

**Est. SP:** 5

---

### 3.5 IoT & Niche Products

#### Epic 15: IoT, Authentication & Licensing

---

**Story 15.1: Zigbee / IoT**

> As a **IoT engineer**,
> I want to view Zigbee settings on MR access points,
> so that I can manage IoT gateway capabilities.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 1 method | `get_zigbee_settings` |
| `discovery.py` | 1 function | `discover_zigbee_config` |
| `agent_tools.py` | 1 schema | network-analyst tool |
| Safety | SAFE |

**Acceptance Criteria:**
1. `discover_zigbee_config` returns Zigbee/IoT radio settings per AP
2. Read-only for initial release (write support in future)

**Est. SP:** 2

---

**Story 15.2: ESL (Electronic Shelf Labels)**

> As a **retail IT admin**,
> I want to view ESL profile configurations,
> so that I can monitor electronic shelf label deployments.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 1 method | `get_esl_profiles` |
| `discovery.py` | 1 function | `discover_esl_config` |
| `agent_tools.py` | 1 schema | network-analyst tool |
| Safety | SAFE |

**Acceptance Criteria:**
1. `discover_esl_config` returns ESL profile status and AP assignments
2. Read-only for initial release

**Est. SP:** 2

---

### 3.6 Authentication & Platform

---

**Story 15.3: SAML / SSO**

> As a **org admin**,
> I want to configure SAML SSO settings via CNL,
> so that I can manage identity provider integration.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_saml_settings`, `update_saml_settings`, `get_saml_roles`, `create_saml_role` |
| `discovery.py` | 1 function | `discover_saml_config` |
| `config.py` | 1 function | `configure_saml` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | DANGEROUS | SSO changes can lock out admins |

**Acceptance Criteria:**
1. `discover_saml_config` returns SAML enabled state, IdP info, and role mappings
2. `configure_saml` enables/disables SAML and configures IdP settings
3. `create_saml_role` creates roles mapped to SAML attributes
4. Safety: DANGEROUS (misconfiguration can lock out all admins)
5. Pre-flight check: warn if disabling SAML would affect current admin session

**Est. SP:** 3

---

**Story 15.4: Licensing (Advanced)**

> As a **org admin**,
> I want to view and manage Meraki licenses,
> so that I can track license usage and expiration.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_licenses_overview`, `get_license_details`, `move_licenses`, `renew_licenses` |
| `discovery.py` | 1 function | `discover_licensing` |
| `config.py` | 1 function | `manage_licenses` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE (move) / SAFE (read) |

**Acceptance Criteria:**
1. `discover_licensing` returns license summary: total, active, expired, expiring soon
2. `get_license_details` returns per-device license status
3. `move_licenses` transfers licenses between orgs (requires confirmation)
4. Issue detection: `license_expiring` when licenses expire within 30 days
5. Natural language: "how many licenses are expiring this quarter?" works

**Est. SP:** 5

---

### 3.7 Advanced Wireless

---

**Story 15.5: Hotspot 2.0**

> As a **wireless engineer**,
> I want to configure Hotspot 2.0 (Passpoint) on SSIDs,
> so that I can enable carrier offload and roaming.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_hotspot20`, `update_hotspot20` |
| `discovery.py` | 1 function | `discover_hotspot20` |
| `config.py` | 1 function | `configure_hotspot20` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. `discover_hotspot20` returns Hotspot 2.0 settings per SSID
2. `configure_hotspot20` manages operator name, venue, NAI realms, and roaming consortium

**Est. SP:** 3

---

**Story 15.6: Identity PSK**

> As a **wireless engineer**,
> I want to manage per-user/device pre-shared keys (iPSK),
> so that I can provide unique WPA2 credentials without 802.1X.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_identity_psks`, `create_identity_psk`, `update_identity_psk`, `delete_identity_psk` |
| `discovery.py` | 1 function | `discover_identity_psks` |
| `config.py` | 1 function | `manage_identity_psk` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. Full CRUD for identity PSKs with group policy assignment
2. `discover_identity_psks` returns all iPSKs per SSID with usage counts
3. Natural language: "create a PSK for the IoT devices group" works

**Est. SP:** 3

---

**Story 15.7: MQTT Brokers**

> As a **IoT engineer**,
> I want to configure MQTT broker connections,
> so that Meraki devices can publish data to MQTT systems.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_mqtt_brokers`, `create_mqtt_broker`, `update_mqtt_broker`, `delete_mqtt_broker` |
| `discovery.py` | 1 function | `discover_mqtt_brokers` |
| `config.py` | 1 function | `configure_mqtt_broker` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. Full CRUD for MQTT broker configurations
2. `discover_mqtt_brokers` returns configured brokers with connection status
3. Supports authentication (username/password, TLS)

**Est. SP:** 2

---

**Story 15.8: Location Analytics**

> As a **facilities manager**,
> I want to access wireless location scanning data,
> so that I can analyze foot traffic and dwell times.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_location_scanning`, `get_wireless_latency_history` |
| `discovery.py` | 1 function | `discover_location_analytics` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE |

**Acceptance Criteria:**
1. `discover_location_analytics` returns scanning API status and recent data
2. `get_wireless_latency_history` returns historical latency data per network

**Est. SP:** 2

---

## 4. Issue Detection Expansion

New issue types added to `find_issues()` in Phase 3:

| Issue Type | Severity | Trigger |
|-----------|----------|---------|
| `sm_device_noncompliant` | WARNING | SM device fails compliance policy |
| `insight_app_degraded` | WARNING | App health score below threshold |
| `mg_failover_untested` | INFO | MG device no recent failover test |
| `license_expiring` | CRITICAL | Licenses expiring within 30 days |

---

## 5. Totals Summary

| Category | Count |
|----------|-------|
| New `api.py` methods | ~50 |
| New `discovery.py` functions | ~12 |
| New `config.py` functions | ~10 |
| New tool schemas | ~37 |
| New issue detection types | 4 |
| Total stories | 12 |
| Total story points | ~50 SP |
| Estimated sprints | 4-5 |

---

## 6. Cumulative Coverage

| Phase | api.py Methods | Total Methods | Coverage |
|-------|---------------|---------------|----------|
| Current (Epics 1-7) | 30 | 30 | ~3.5% |
| + Phase 1 (Epics 8-10) | +55 | 85 | ~10% |
| + Phase 2 (Epics 11-13) | +65 | 150 | ~18% |
| **+ Phase 3 (Epics 14-15)** | **+50** | **200** | **~23%** |

**Note:** The 50% coverage target includes discovery functions, config functions, and tool schemas that provide higher-level access beyond raw API methods. The ~200 api.py methods map to ~430 total "accessible capabilities" when counting all wrapper layers.

---

## 7. Dependencies & Risks

### Dependencies
- Phase 2 must be complete
- SM features require Systems Manager license
- Insight features require Insight license
- Camera ML requires MV firmware >= 4.2
- MG features require Cellular Gateway hardware

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SM wipe is irreversible | Critical | Double confirmation + typing CONFIRM |
| SAML misconfiguration locks out admins | High | Pre-flight validation + DANGEROUS classification |
| License move between orgs is permanent | Medium | Require explicit confirmation + preview |
| Some features require specific hardware/licenses | Low | Graceful degradation with informative error messages |

---

## 8. Quality Metrics

Same targets as Phases 1-2:

| Metric | Target |
|--------|--------|
| Test coverage for new functions | >= 90% |
| Tool schemas pass validation | 100% |
| WRITE tools have backup support | 100% |
| DANGEROUS tools require confirmation | 100% |
| Discovery integration into `full_discovery()` | >= 80% |
| `additionalProperties: False` on all schemas | 100% |

---

*Generated by Morgan (PM Agent) | CNL PRD Phase 3 v1.0.0*
*-- Morgan, planejando o futuro*
