# CNL - PRD Phase 2: Platform Depth (P1)

> **Version:** 1.0.0
> **Type:** Brownfield Enhancement - API Coverage Expansion
> **Created:** 2026-02-09
> **Author:** Morgan (PM Agent) + jspetrucio
> **Status:** Draft
> **Epics:** 11, 12, 13
> **Story Points:** ~75 SP
> **Sprints:** 5-7 sprints
> **Coverage Target:** 15% -> 35% (~65 new api.py methods)
> **Prerequisite:** Phase 1 complete (Epics 8-10)

---

## 1. Executive Summary

Phase 2 broadens CNL's coverage to **advanced networking features** used in enterprise deployments. After Phase 1 covers the essentials, Phase 2 adds the depth needed by network architects: SD-WAN, adaptive policy, config templates, advanced switching (stacks, 802.1X, HA), camera analytics, sensors, and more.

This phase adds **~65 new api.py methods**, **~20 discovery functions**, **~18 config functions**, and **~62 tool schemas** across 20 feature groups.

### Business Value

- Enables network architects to manage complex enterprise deployments entirely from CNL
- Covers 80% of enterprise use cases (SD-WAN, templates, HA, camera, sensors)
- Adds visibility into MV camera analytics and MT sensor data
- Supports advanced switching features required by campus/branch deployments

---

## 2. Goals & Success Criteria

### Goals

1. Cover advanced platform operations for enterprise use cases
2. Add camera analytics and sensor monitoring capabilities
3. Enable config template management for multi-site deployments
4. Maintain standardized implementation pattern and quality metrics

### Success Criteria

- A network architect can use CNL for SD-WAN, config templates, HA, camera analytics, sensors, and advanced switching -- covering 80% of enterprise use cases
- All new features follow the 7-step implementation pattern
- All quality metrics from Phase 1 maintained

---

## 3. Feature Groups

### 3.1 Advanced Appliance / SD-WAN

#### Epic 11: SD-WAN, Policy & Templates

---

**Story 11.1: SD-WAN / Uplink Selection**

> As a **network architect**,
> I want to configure SD-WAN uplink policies and preferences,
> so that I can optimize WAN path selection across the organization.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_uplink_selection`, `update_uplink_selection`, `get_uplink_statuses`, `get_vpn_exclusions` |
| `discovery.py` | 1 function | `discover_sdwan_config` |
| `config.py` | 2 functions | `configure_sdwan_policy`, `set_uplink_preference` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | DANGEROUS | SD-WAN changes affect all traffic paths |

**Acceptance Criteria:**
1. `discover_sdwan_config` returns current uplink selection policies and preferences
2. `configure_sdwan_policy` supports performance-based and custom uplink policies
3. `set_uplink_preference` configures WAN1/WAN2 preference per traffic type
4. `get_vpn_exclusions` returns traffic excluded from VPN tunnels
5. Issue detection: `sdwan_no_policy` when no SD-WAN policy is configured

**Est. SP:** 8

---

**Story 11.2: Client VPN**

> As a **network admin**,
> I want to configure Client VPN (AnyConnect) settings,
> so that remote users can connect securely.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_client_vpn`, `update_client_vpn` |
| `discovery.py` | 1 function | `discover_client_vpn` |
| `config.py` | 1 function | `configure_client_vpn` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE | Affects remote access |

**Acceptance Criteria:**
1. `discover_client_vpn` returns VPN enabled state, auth mode, and subnet
2. `configure_client_vpn` supports enabling/disabling and setting auth type (Meraki/AD/RADIUS)
3. Backup + rollback supported

**Est. SP:** 3

---

**Story 11.3: Adaptive Policy / SGT**

> As a **security architect**,
> I want to manage Adaptive Policy (SGT-based) via CNL,
> so that I can define micro-segmentation policies.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_adaptive_policies`, `create_adaptive_policy`, `get_adaptive_policy_acls`, `get_policy_objects`, `create_policy_object` |
| `discovery.py` | 1 function | `discover_adaptive_policies` |
| `config.py` | 2 functions | `configure_adaptive_policy`, `create_policy_object` |
| `agent_tools.py` | 5 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Policy changes affect segmentation |

**Acceptance Criteria:**
1. `discover_adaptive_policies` returns all SGT assignments, ACLs, and policies
2. `configure_adaptive_policy` creates/updates policy with source/destination SGTs
3. `create_policy_object` manages reusable policy objects (IPs, FQDNs, ports)
4. Integration with existing SGT preflight check in config.py

**Est. SP:** 8

---

**Story 11.4: Config Templates**

> As a **network architect**,
> I want to manage configuration templates and bind/unbind networks,
> so that I can standardize configurations across multiple sites.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_config_templates`, `create_config_template`, `update_config_template`, `bind_network`, `unbind_network` |
| `discovery.py` | 1 function | `discover_templates` |
| `config.py` | 1 function | `manage_template` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Binding/unbinding affects entire network configs |

**Acceptance Criteria:**
1. `discover_templates` returns all templates with bound network counts
2. `bind_network` associates a network with a template (with auto-bind options)
3. `unbind_network` disassociates a network (preserving or removing config)
4. Template CRUD fully supported

**Est. SP:** 5

---

**Story 11.5: Policy Objects**

> As a **security admin**,
> I want to manage reusable policy objects and groups,
> so that firewall rules reference named objects instead of raw IPs.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_policy_objects`, `create_policy_object`, `update_policy_object`, `delete_policy_object`, `get_policy_object_groups` |
| `discovery.py` | 1 function | `discover_policy_objects` |
| `config.py` | 1 function | `manage_policy_object` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | MODERATE | Objects referenced by rules |

**Acceptance Criteria:**
1. `discover_policy_objects` returns all objects and groups with usage counts
2. Full CRUD for policy objects (CIDR, FQDN, port ranges)
3. Group management for organizing objects
4. Dependency check before delete (warn if object is in use)

**Est. SP:** 5

---

### 3.2 Advanced Switching

#### Epic 12: Switching, Wireless & Monitoring

---

**Story 12.1: Switch Stacks**

> As a **network engineer**,
> I want to manage switch stacks via CNL,
> so that I can configure stack members and routing.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_switch_stacks`, `create_switch_stack`, `add_to_stack`, `remove_from_stack`, `get_stack_routing` |
| `discovery.py` | 1 function | `discover_switch_stacks` |
| `config.py` | 1 function | `manage_switch_stack` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Stack changes can cause outages |

**Acceptance Criteria:**
1. `discover_switch_stacks` returns all stacks with member serials and roles
2. Stack CRUD operations supported
3. `get_stack_routing` returns routing interfaces for stack
4. Safety: DANGEROUS for add/remove operations

**Est. SP:** 5

---

**Story 12.2: 802.1X / Access Policies**

> As a **security engineer**,
> I want to configure 802.1X access policies on switch ports,
> so that I can enforce NAC on wired connections.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_access_policies`, `create_access_policy`, `update_access_policy`, `delete_access_policy` |
| `discovery.py` | 1 function | `discover_access_policies` |
| `config.py` | 1 function | `configure_access_policy` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE | Affects port authentication |

**Acceptance Criteria:**
1. `discover_access_policies` returns all policies with RADIUS server configs
2. `configure_access_policy` supports MAB, 802.1X, and hybrid modes
3. RADIUS server configuration included
4. Issue detection: `access_policy_missing` when no NAC on trunk ports

**Est. SP:** 5

---

**Story 12.3: Port Schedules**

> As a **network admin**,
> I want to configure switch port schedules,
> so that ports are enabled/disabled at specific times.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_port_schedules`, `create_port_schedule`, `update_port_schedule`, `delete_port_schedule` |
| `discovery.py` | 1 function | `discover_port_schedules` |
| `config.py` | 1 function | `configure_port_schedule` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. Full CRUD for port schedules with time windows
2. Assignable to specific ports via switch port configuration
3. Natural language: "disable lab ports after 6pm" works

**Est. SP:** 3

---

**Story 12.4: HA / Warm Spare**

> As a **network architect**,
> I want to configure High Availability (warm spare) on MX appliances,
> so that I can ensure failover capability.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_warm_spare`, `update_warm_spare`, `swap_warm_spare` |
| `discovery.py` | 1 function | `discover_ha_config` |
| `config.py` | 2 functions | `configure_warm_spare`, `trigger_failover` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Failover causes brief outage |

**Acceptance Criteria:**
1. `discover_ha_config` returns HA status, primary/spare IPs, and last failover time
2. `configure_warm_spare` enables/disables HA with spare uplink IPs
3. `trigger_failover` initiates manual failover (DANGEROUS, requires typing CONFIRM)
4. Issue detection: `no_ha_configured` on critical networks

**Est. SP:** 5

---

### 3.3 Wireless & Camera

---

**Story 12.5: Air Marshal (Rogue AP Detection)**

> As a **security engineer**,
> I want to monitor rogue APs detected by Air Marshal,
> so that I can identify unauthorized wireless devices.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_air_marshal`, `get_air_marshal_rules` |
| `discovery.py` | 1 function | `discover_rogue_aps` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE | Read-only |

**Acceptance Criteria:**
1. `discover_rogue_aps` returns detected rogue APs with classification
2. Data includes BSSID, SSID, channel, signal strength, and containment status
3. Issue detection: `rogue_aps_detected` when uncontained rogues exist
4. Natural language: "are there any rogue APs?" works

**Est. SP:** 3

---

**Story 12.6: SSID Firewall Rules**

> As a **wireless engineer**,
> I want to manage per-SSID firewall rules (L3/L7),
> so that I can apply traffic filtering at the wireless level.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_ssid_l3_firewall`, `update_ssid_l3_firewall`, `get_ssid_l7_firewall`, `update_ssid_l7_firewall` |
| `discovery.py` | 1 function | `discover_ssid_firewall` |
| `config.py` | 1 function | `configure_ssid_firewall` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. `discover_ssid_firewall` returns L3 and L7 rules per SSID
2. `configure_ssid_firewall` supports both L3 (IP/port) and L7 (application) rules
3. Backup + rollback per SSID

**Est. SP:** 3

---

**Story 12.7: Splash Pages**

> As a **network admin**,
> I want to configure captive portal splash pages for SSIDs,
> so that I can customize the guest WiFi experience.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_splash_settings`, `update_splash_settings` |
| `discovery.py` | 1 function | `discover_splash_config` |
| `config.py` | 1 function | `configure_splash_page` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Acceptance Criteria:**
1. `discover_splash_config` returns splash page type and settings per SSID
2. `configure_splash_page` supports click-through, sign-on, and sponsored guest

**Est. SP:** 3

---

### 3.4 Camera & Sensor

#### Epic 13: Camera Analytics, Sensors & Observability

---

**Story 13.1: Camera Analytics & Snapshots**

> As a **facilities manager**,
> I want to access camera analytics and generate snapshots,
> so that I can monitor occupancy and generate visual evidence.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_camera_analytics_overview`, `get_camera_analytics_zones`, `get_camera_analytics_history`, `generate_snapshot`, `get_video_link` |
| `discovery.py` | 1 function | `discover_camera_analytics` |
| `agent_tools.py` | 5 schemas | network-analyst tools |
| Safety | SAFE | Read-only |

**Acceptance Criteria:**
1. `discover_camera_analytics` returns analytics summary with people counts
2. `get_camera_analytics_zones` returns defined analytics zones
3. `generate_snapshot` captures a snapshot image from a camera
4. `get_video_link` returns a shareable video link with timestamp

**Est. SP:** 5

---

**Story 13.2: Sensor Readings & Alerts**

> As a **facilities engineer**,
> I want to view sensor readings and configure alerts,
> so that I can monitor environmental conditions (temperature, humidity, etc.).

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_sensor_readings_latest`, `get_sensor_readings_history`, `get_sensor_alert_profiles`, `create_sensor_alert` |
| `discovery.py` | 1 function | `discover_sensors` |
| `config.py` | 1 function | `configure_sensor_alert` |
| `agent_tools.py` | 4 schemas | network-analyst + meraki-specialist tools |
| Safety | SAFE (read) / MODERATE (alert config) |

**Acceptance Criteria:**
1. `discover_sensors` returns all MT sensors with latest readings
2. `get_sensor_readings_history` returns time-series data for a sensor
3. `create_sensor_alert` configures threshold-based alerts
4. Issue detection: `sensor_alert_missing` when no alerts on critical sensors

**Est. SP:** 5

---

### 3.5 Platform & Observability

---

**Story 13.3: Floor Plans**

> As a **network admin**,
> I want to manage floor plans and device placement,
> so that I can maintain accurate location maps.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_floor_plans`, `create_floor_plan`, `update_floor_plan`, `delete_floor_plan` |
| `discovery.py` | 1 function | `discover_floor_plans` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE (read) / MODERATE (write) |

**Est. SP:** 3

---

**Story 13.4: Group Policies**

> As a **network admin**,
> I want to manage group policies for client devices,
> so that I can apply bandwidth limits and access rules to groups.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_group_policies`, `create_group_policy`, `update_group_policy`, `delete_group_policy` |
| `discovery.py` | 1 function | `discover_group_policies` |
| `config.py` | 1 function | `configure_group_policy` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Est. SP:** 3

---

**Story 13.5: LLDP/CDP Discovery**

> As a **network engineer**,
> I want to view LLDP/CDP neighbor data from devices,
> so that I can map physical topology.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 1 method | `get_lldp_cdp` |
| `discovery.py` | 1 function | `discover_lldp_cdp` |
| `agent_tools.py` | 1 schema | network-analyst tool |
| Safety | SAFE |

**Est. SP:** 2

---

**Story 13.6: Packet Capture**

> As a **network engineer**,
> I want to initiate packet captures from Meraki devices,
> so that I can debug traffic issues.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `create_packet_capture`, `get_packet_capture_status` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE | Read-only diagnostic |

**Est. SP:** 3

---

**Story 13.7: NetFlow Configuration**

> As a **network admin**,
> I want to configure NetFlow export settings,
> so that I can send flow data to a collector.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_netflow_settings`, `update_netflow_settings` |
| `discovery.py` | 1 function | `discover_netflow_config` |
| `config.py` | 1 function | `configure_netflow` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Est. SP:** 2

---

**Story 13.8: PoE Status Monitoring**

> As a **network engineer**,
> I want to monitor PoE power consumption and budget per switch,
> so that I can prevent power overloads.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `discovery.py` | 1 function | `discover_poe_status` |
| `agent_tools.py` | 1 schema | network-analyst tool |
| Safety | SAFE |

**Acceptance Criteria:**
1. `discover_poe_status` returns per-port PoE draw and total budget utilization
2. Issue detection: `poe_budget_exceeded` when >90% budget used

**Est. SP:** 2

---

**Story 13.9: Static Routes (Appliance)**

> As a **network engineer**,
> I want to manage static routes on MX appliances,
> so that I can configure routing without OSPF/BGP.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_static_routes`, `create_static_route`, `update_static_route`, `delete_static_route` |
| `discovery.py` | 1 function | `discover_static_routes` |
| `config.py` | 1 function | `manage_static_route` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE |

**Est. SP:** 3

---

## 4. Issue Detection Expansion

New issue types added to `find_issues()` in Phase 2:

| Issue Type | Severity | Trigger |
|-----------|----------|---------|
| `stp_inconsistent` | WARNING | STP configuration mismatch across stack |
| `no_ha_configured` | WARNING | No warm spare on critical MX |
| `rogue_aps_detected` | CRITICAL | Uncontained rogue APs found |
| `sdwan_no_policy` | INFO | No SD-WAN uplink policy configured |
| `sensor_alert_missing` | WARNING | No alerts on environmental sensors |
| `poe_budget_exceeded` | CRITICAL | PoE budget >90% on a switch |
| `access_policy_missing` | WARNING | No 802.1X on critical trunk ports |

---

## 5. Totals Summary

| Category | Count |
|----------|-------|
| New `api.py` methods | ~65 |
| New `discovery.py` functions | ~20 |
| New `config.py` functions | ~18 |
| New tool schemas | ~62 |
| New issue detection types | 7 |
| Total stories | 20 |
| Total story points | ~75 SP |
| Estimated sprints | 5-7 |

---

## 6. Dependencies & Risks

### Dependencies
- Phase 1 must be complete (all ~55 new methods working + tested)
- Camera analytics requires MV firmware >= 4.x
- Sensor features require MT device licenses
- Adaptive Policy requires org-level enablement

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SD-WAN config complexity (many interrelated settings) | High | Start with read-only, add write incrementally |
| Config template bind/unbind can override network settings | High | DANGEROUS classification + detailed preview |
| Adaptive Policy is org-wide (affects all networks) | High | Require org-admin role + explicit confirmation |
| Camera analytics may be resource-intensive | Medium | Pagination and time-range limits |

---

## 7. Quality Metrics

Same targets as Phase 1:

| Metric | Target |
|--------|--------|
| Test coverage for new functions | >= 90% |
| Tool schemas pass validation | 100% |
| WRITE tools have backup support | 100% |
| DANGEROUS tools require confirmation | 100% |
| Discovery integration into `full_discovery()` | >= 80% |
| `additionalProperties: False` on all schemas | 100% |

---

*Generated by Morgan (PM Agent) | CNL PRD Phase 2 v1.0.0*
*-- Morgan, planejando o futuro*
