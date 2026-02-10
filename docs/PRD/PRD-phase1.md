# CNL - PRD Phase 1: Core Operations (P0)

> **Version:** 1.0.0
> **Type:** Brownfield Enhancement - API Coverage Expansion
> **Created:** 2026-02-09
> **Author:** Morgan (PM Agent) + jspetrucio
> **Status:** Draft
> **Epics:** 8, 9, 10
> **Story Points:** ~93 SP
> **Sprints:** 6-8 sprints
> **Coverage Target:** 3.5% -> 15% (~67 new api.py methods)
> **Prerequisite:** Epics 1-7 complete (643 tests passing)

---

## 1. Executive Summary

Phase 1 addresses the **most critical gap** in CNL's Meraki API coverage: day-1 and day-2 operations. Today, CNL covers ~30 unique SDK methods (~3.5% of 855 endpoints). After Phase 1, engineers will be able to perform the **22 most common daily operations** without touching the Dashboard UI.

This phase adds **~67 new api.py methods**, **~20 discovery functions**, **~23 config functions**, and **~61 tool schemas** across 22 feature groups.

### Business Value

- Enables network engineers to manage VPN, security, firmware, and monitoring via natural language
- Eliminates the need to switch between CNL and Dashboard for common operations
- Covers 80% of support ticket categories (VPN issues, firmware updates, security config, alerting)

---

## 2. Goals & Success Criteria

### Goals

1. Cover the 20 most-requested day-1/day-2 operations in CNL
2. Maintain 100% backward compatibility with existing functionality
3. Follow the standardized 7-step implementation pattern for every feature
4. Achieve >= 90% test coverage on all new functions

### Success Criteria

- A network engineer can configure Site-to-Site VPN, IPS, content filtering, firmware upgrades, alerts, SNMP/syslog, and use live tools (ping/traceroute/cable test) entirely from CNL
- All WRITE tools have backup support
- All DANGEROUS tools require confirmation
- All tool schemas pass `validate_tool_schema()` with `additionalProperties: False`
- Discovery functions integrated into `full_discovery()` for >= 80% of new features

---

## 3. Feature Groups

### 3.1 Security Services

#### Epic 8: Network Security & Monitoring

---

**Story 8.1: Site-to-Site VPN**

> As a **network engineer**,
> I want to configure and monitor Site-to-Site VPN through CNL,
> so that I can manage VPN tunnels without navigating the Dashboard.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_vpn_config`, `update_vpn_config`, `get_vpn_statuses` |
| `discovery.py` | 1 function | `discover_vpn_topology` |
| `config.py` | 2 functions | `configure_s2s_vpn`, `add_vpn_peer` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Requires confirmation + backup |

**Acceptance Criteria:**
1. `discover_vpn_topology` returns all VPN peers, status, and subnets for an org
2. `configure_s2s_vpn` supports hub-and-spoke and full-mesh topologies
3. `add_vpn_peer` adds a third-party VPN peer with IKE/IPSec settings
4. Backup created before any VPN config change (org-level backup via new `backup_vpn_config()` since VPN is org-scoped, not network-scoped)
5. Dry-run mode supported: preview VPN topology changes before applying
6. VPN status integrated into `full_discovery()` output
6. Issue detection: `vpn_peer_down` added to `find_issues()`

**Est. SP:** 8

---

**Story 8.2: Content Filtering**

> As a **network admin**,
> I want to manage content filtering rules via natural language,
> so that I can quickly block/allow URL categories and specific sites.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_content_filtering`, `update_content_filtering`, `get_content_categories` |
| `discovery.py` | 1 function | `discover_content_filtering` |
| `config.py` | 2 functions | `configure_content_filter`, `add_blocked_url` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_content_filtering` returns blocked URLs, allowed URLs, and blocked categories
2. `configure_content_filter` accepts URL lists and category IDs
3. `get_content_categories` returns all available Meraki content categories
4. `add_blocked_url` appends to existing blocked list (does not replace)
5. Issue detection: `content_filter_permissive` when no filtering configured
6. Backup + rollback supported

**Est. SP:** 5

---

**Story 8.3: IPS / Intrusion Detection**

> As a **security admin**,
> I want to configure Intrusion Prevention System settings,
> so that I can enable/adjust IPS protection levels across networks.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_intrusion_settings`, `update_intrusion_settings` |
| `discovery.py` | 1 function | `discover_ips_settings` |
| `config.py` | 2 functions | `configure_ips`, `set_ips_mode` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_ips_settings` returns IPS mode (prevention/detection/disabled) and rule set
2. `configure_ips` supports mode switching and whitelisted rules
3. `set_ips_mode` is a convenience wrapper for common mode changes
4. Issue detection: `ips_disabled` when IPS is off on any network
5. Supports both network-level and org-level IPS settings

**Est. SP:** 5

---

**Story 8.4: AMP / Malware Protection**

> As a **security admin**,
> I want to manage Advanced Malware Protection settings,
> so that I can enable AMP and manage allowed file hashes.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_malware_settings`, `update_malware_settings` |
| `discovery.py` | 1 function | `discover_amp_settings` |
| `config.py` | 1 function | `configure_amp` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_amp_settings` returns AMP mode and allowed file list
2. `configure_amp` enables/disables AMP and manages file hash whitelist
3. Issue detection: `amp_disabled` when AMP is off
4. Integrated into security section of `full_discovery()`

**Est. SP:** 3

---

**Story 8.5: Traffic Shaping (Appliance)**

> As a **network engineer**,
> I want to configure traffic shaping and bandwidth limits,
> so that I can manage QoS on MX appliances.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_traffic_shaping`, `update_traffic_shaping`, `get_uplink_bandwidth` |
| `discovery.py` | 1 function | `discover_traffic_shaping` |
| `config.py` | 2 functions | `configure_traffic_shaping`, `set_bandwidth_limit` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_traffic_shaping` returns current shaping rules and bandwidth settings
2. `configure_traffic_shaping` supports per-application and per-rule shaping
3. `set_bandwidth_limit` configures global uplink bandwidth limits
4. Backup + rollback supported

**Est. SP:** 5

---

### 3.2 Monitoring & Alerting

#### Epic 9: Alerts, Firmware & Observability

---

**Story 9.1: Alerts & Webhooks**

> As a **network admin**,
> I want to configure alert profiles and webhook endpoints,
> so that I receive notifications when network events occur.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_alert_settings`, `update_alert_settings`, `get_webhook_servers`, `create_webhook_server`, `test_webhook` |
| `discovery.py` | 2 functions | `discover_alerts`, `discover_webhooks` |
| `config.py` | 2 functions | `configure_alerts`, `create_webhook_endpoint` |
| `agent_tools.py` | 5 schemas | meraki-specialist + workflow-creator tools |
| Safety | MODERATE | Requires confirmation for alert changes |

**Acceptance Criteria:**
1. `discover_alerts` returns all alert profiles and their destinations
2. `discover_webhooks` returns configured HTTP servers and payload templates
3. `configure_alerts` supports enabling/disabling specific alert types
4. `create_webhook_endpoint` registers a new HTTP server + tests connectivity
5. `test_webhook` sends a test payload to verify endpoint
6. Issue detection: `no_alerts_configured` when no alerts are set up
7. Integration with workflow-creator for automated alert workflows

**Est. SP:** 8

---

**Story 9.2: Firmware Upgrades**

> As a **network admin**,
> I want to view firmware status and schedule upgrades,
> so that I can keep all devices on supported firmware versions.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_firmware_upgrades`, `update_firmware_upgrades`, `get_firmware_by_device` |
| `discovery.py` | 1 function | `discover_firmware_status` |
| `config.py` | 2 functions | `schedule_firmware_upgrade`, `cancel_firmware_upgrade` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Firmware changes require explicit confirmation |

**Acceptance Criteria:**
1. `discover_firmware_status` returns current vs. latest firmware for all device types
2. `get_firmware_by_device` returns per-device firmware version and compliance status
3. `schedule_firmware_upgrade` supports scheduling upgrades for a specific time window
4. `cancel_firmware_upgrade` cancels a pending scheduled upgrade
5. Issue detection: `firmware_outdated` when devices are behind latest stable
6. Supports network-level and org-level firmware management
7. Note: Firmware downgrades are not supported by Meraki API; `cancel_firmware_upgrade` only works for pending (not yet applied) upgrades

**Est. SP:** 8

---

**Story 9.3: Live Tools -- Ping**

> As a **network engineer**,
> I want to run ping tests from Meraki devices,
> so that I can diagnose connectivity issues without SSH access.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `create_ping`, `get_ping_result` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE | Read-only diagnostic |

**Acceptance Criteria:**
1. `create_ping` initiates a ping from a device to a target IP/hostname
2. `get_ping_result` polls for results (async operation with retry)
3. Results include loss%, min/avg/max latency
4. Supports specifying source interface and count
5. Natural language: "ping 8.8.8.8 from switch SW01" works

**Est. SP:** 3

---

**Story 9.4: Live Tools -- Traceroute**

> As a **network engineer**,
> I want to run traceroute from Meraki devices,
> so that I can diagnose routing and path issues.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `create_traceroute`, `get_traceroute_result` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE | Read-only diagnostic |

**Acceptance Criteria:**
1. `create_traceroute` initiates a traceroute from a device
2. `get_traceroute_result` polls for results with hop-by-hop data
3. Results include hop IP, hostname (if resolvable), and latency
4. Natural language: "traceroute to 10.0.0.1 from AP-lobby" works

**Est. SP:** 3

---

**Story 9.5: Live Tools -- Cable Test**

> As a **network engineer**,
> I want to run cable tests on switch ports,
> so that I can diagnose physical layer issues remotely.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `create_cable_test`, `get_cable_test_result` |
| `agent_tools.py` | 2 schemas | network-analyst tools |
| Safety | SAFE | Read-only diagnostic |

**Acceptance Criteria:**
1. `create_cable_test` runs TDR on a specific switch port
2. `get_cable_test_result` returns cable status, length, and pair status
3. Results clearly indicate pass/fail per pair
4. Natural language: "test cable on port 5 of switch SW-Core" works

**Est. SP:** 3

---

**Story 9.6: SNMP Configuration**

> As a **network admin**,
> I want to configure SNMP settings via CNL,
> so that I can integrate Meraki with NMS tools.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_snmp_settings`, `update_snmp_settings` (org + network) |
| `discovery.py` | 1 function | `discover_snmp_config` |
| `config.py` | 1 function | `configure_snmp` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_snmp_config` returns SNMP version, community strings, and user configs
2. `configure_snmp` supports SNMPv2c and SNMPv3 configuration
3. Supports both org-level and network-level SNMP settings
4. Issue detection: `no_snmp_configured` when SNMP is disabled

**Est. SP:** 3

---

**Story 9.7: Syslog Configuration**

> As a **network admin**,
> I want to configure syslog servers via CNL,
> so that I can centralize log collection.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_syslog_servers`, `update_syslog_servers` |
| `discovery.py` | 1 function | `discover_syslog_config` |
| `config.py` | 1 function | `configure_syslog` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_syslog_config` returns configured syslog servers and roles
2. `configure_syslog` adds/removes syslog server entries with roles
3. Issue detection: `no_syslog_configured` when no syslog servers exist

**Est. SP:** 3

---

**Story 9.8: Change Log Access**

> As a **network admin**,
> I want to view recent configuration changes from the Dashboard,
> so that I can audit who changed what and when.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 1 method | `get_config_changes` |
| `discovery.py` | 1 function | `discover_recent_changes` |
| `agent_tools.py` | 1 schema | network-analyst tool |
| Safety | SAFE | Read-only |

**Acceptance Criteria:**
1. `get_config_changes` returns org-wide change log with admin, timestamp, and description
2. `discover_recent_changes` filters for last 24h/7d/30d changes
3. Natural language: "show me who changed the firewall rules this week" works

**Est. SP:** 2

---

### 3.3 Switching & Wireless

#### Epic 10: Advanced Switching, Wireless & Platform

---

**Story 10.1: Switch Routing L3**

> As a **network engineer**,
> I want to configure Layer 3 routing interfaces on switches,
> so that I can manage inter-VLAN routing without the Dashboard.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_switch_routing_interfaces`, `create_routing_interface`, `update_routing_interface`, `delete_routing_interface`, `get_switch_static_routes` |
| `discovery.py` | 1 function | `discover_switch_routing` |
| `config.py` | 2 functions | `configure_switch_l3_interface`, `add_switch_static_route` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | DANGEROUS | L3 routing changes can cause outages |

**Acceptance Criteria:**
1. `discover_switch_routing` returns all L3 interfaces and static routes per switch
2. `configure_switch_l3_interface` creates/updates SVIs with IP, VLAN, OSPF settings
3. `add_switch_static_route` adds static routes to switch routing table
4. Backup + rollback supported for all L3 changes
5. Safety classification: DANGEROUS (requires confirmation)
6. Dry-run mode supported: preview L3 routing changes before applying

**Est. SP:** 5

---

**Story 10.2: STP Configuration**

> As a **network engineer**,
> I want to configure Spanning Tree Protocol settings,
> so that I can prevent loops and optimize L2 topology.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `get_stp_settings`, `update_stp_settings` |
| `discovery.py` | 1 function | `discover_stp_config` |
| `config.py` | 1 function | `configure_stp` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | DANGEROUS | STP changes can cause network loops |

**Acceptance Criteria:**
1. `discover_stp_config` returns STP mode (RSTP/MSTP) and bridge priority per switch
2. `configure_stp` supports mode selection and per-VLAN bridge priority
3. Issue detection: STP inconsistency warnings
4. Safety: DANGEROUS classification
5. Dry-run mode supported: preview STP changes before applying
6. Backup + rollback supported

**Est. SP:** 3

---

**Story 10.3: Device Reboot & LED Blink**

> As a **network admin**,
> I want to remotely reboot devices and blink LEDs,
> so that I can troubleshoot and identify physical devices.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 2 methods | `reboot_device`, `blink_leds` |
| `agent_tools.py` | 2 schemas | meraki-specialist tools |
| Safety | DANGEROUS (reboot) / SAFE (blink) |

**Acceptance Criteria:**
1. `reboot_device` reboots a device by serial with confirmation
2. `blink_leds` blinks LEDs for identification (configurable duration)
3. Natural language: "reboot AP-lobby" and "blink the LEDs on SW-Core for 30 seconds" work
4. Reboot requires explicit confirmation dialog

**Est. SP:** 2

---

**Story 10.4: NAT & Port Forwarding**

> As a **network engineer**,
> I want to configure NAT rules and port forwarding on MX appliances,
> so that I can manage inbound services via CNL.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 6 methods | `get_1to1_nat`, `update_1to1_nat`, `get_1tomany_nat`, `update_1tomany_nat`, `get_port_forwarding`, `update_port_forwarding` |
| `discovery.py` | 2 functions | `discover_nat_rules`, `discover_port_forwarding` |
| `config.py` | 2 functions | `configure_1to1_nat`, `configure_port_forwarding` |
| `agent_tools.py` | 4 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_nat_rules` returns all 1:1 and 1:Many NAT rules
2. `discover_port_forwarding` returns all port forwarding rules
3. `configure_1to1_nat` creates/updates 1:1 NAT mappings
4. `configure_port_forwarding` adds/removes port forwarding rules
5. Backup + rollback for all NAT changes

**Est. SP:** 5

---

**Story 10.5: RF Profiles (Wireless)**

> As a **wireless engineer**,
> I want to manage RF profiles for access points,
> so that I can optimize radio settings across the deployment.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_rf_profiles`, `create_rf_profile`, `update_rf_profile`, `delete_rf_profile` |
| `discovery.py` | 1 function | `discover_rf_profiles` |
| `config.py` | 1 function | `configure_rf_profile` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE | RF changes affect wireless coverage |

**Acceptance Criteria:**
1. `discover_rf_profiles` returns all RF profiles with band settings
2. `configure_rf_profile` supports 2.4GHz and 5GHz settings (channel width, min power, etc.)
3. CRUD operations supported (create, read, update, delete)
4. Profiles assignable to specific APs

**Est. SP:** 5

---

**Story 10.6: Wireless Health Monitoring**

> As a **network analyst**,
> I want comprehensive wireless health metrics,
> so that I can diagnose Wi-Fi issues proactively.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 5 methods | `get_wireless_connection_stats`, `get_wireless_latency_stats`, `get_wireless_signal_quality`, `get_channel_utilization`, `get_failed_connections` |
| `discovery.py` | 1 function | `discover_wireless_health` |
| `agent_tools.py` | 5 schemas | network-analyst tools |
| Safety | SAFE | Read-only |

**Acceptance Criteria:**
1. `discover_wireless_health` returns aggregated health metrics per network
2. Metrics include: connection success rate, avg latency, signal quality scores
3. `get_channel_utilization` returns per-AP channel utilization data
4. `get_failed_connections` returns failed auth/assoc/DHCP breakdown
5. Integrated into discovery reports with health summary

**Est. SP:** 5

---

**Story 10.7: Switch QoS**

> As a **network engineer**,
> I want to configure QoS rules on switches,
> so that I can prioritize critical traffic.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_qos_rules`, `create_qos_rule`, `update_qos_rule`, `delete_qos_rule` |
| `discovery.py` | 1 function | `discover_qos_config` |
| `config.py` | 1 function | `configure_qos` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | MODERATE | Requires confirmation |

**Acceptance Criteria:**
1. `discover_qos_config` returns all QoS rules and their order
2. `configure_qos` supports DSCP marking and CoS mapping
3. CRUD operations for QoS rules with order management

**Est. SP:** 3

---

**Story 10.8: Org Admins Management**

> As a **org admin**,
> I want to manage Dashboard admin accounts via CNL,
> so that I can provision and audit admin access.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 4 methods | `get_admins`, `create_admin`, `update_admin`, `delete_admin` |
| `discovery.py` | 1 function | `discover_org_admins` |
| `config.py` | 1 function | `manage_admin` |
| `agent_tools.py` | 3 schemas | meraki-specialist tools |
| Safety | DANGEROUS | Admin management is security-sensitive |

**Acceptance Criteria:**
1. `discover_org_admins` returns all admins with roles and 2FA status
2. `create_admin` provisions a new admin with specified role
3. `delete_admin` removes an admin (requires explicit confirmation)
4. `manage_admin` updates role/permissions
5. Guard-rail: Cannot delete the last remaining org admin
6. Guard-rail: Cannot delete the admin account associated with the current API key

**Est. SP:** 3

---

**Story 10.9: Inventory Management**

> As a **network admin**,
> I want to manage device inventory (claim/release),
> so that I can onboard and offboard devices via CNL.

**Scope:**
| Layer | New Items | Details |
|-------|-----------|---------|
| `api.py` | 3 methods | `get_inventory`, `claim_device`, `release_device` |
| `discovery.py` | 1 function | `discover_inventory` |
| `agent_tools.py` | 3 schemas | network-analyst tools |
| Safety | MODERATE (claim) / DANGEROUS (release) |

**Acceptance Criteria:**
1. `discover_inventory` returns full org inventory with claim status
2. `claim_device` claims a device by serial/order number
3. `release_device` releases a device from the org (requires confirmation)
4. Natural language: "claim device Q2XX-XXXX-XXXX" works

**Est. SP:** 3

---

## 4. Implementation Pattern

Every feature follows the standardized 7-step pattern defined in the roadmap:

1. **api.py** -- Add SDK wrapper method with `@log_api_call`
2. **discovery.py** -- Add discovery function with `client.safe_call()`
3. **config.py** -- Add config function with backup + `ConfigResult`
4. **agent_router.py** -- Register in `FUNCTION_REGISTRY`
5. **agent_tools.py** -- Add tool schema + safety classification
6. **safety.py** -- Register in safety layer
7. **tests/** -- Add comprehensive tests (happy path, errors, backup, safety)

**Integration Note:** Both `SAFETY_CLASSIFICATION` in `safety.py` and `TOOL_SAFETY` in `agent_tools.py` must be updated for each new tool (dual safety registration). Discovery functions should be integrated into `full_discovery()` per-epic (not per-story) to avoid merge conflicts when stories are developed in parallel.

---

## 5. Issue Detection Expansion

New issue types added to `find_issues()` in Phase 1:

| Issue Type | Severity | Trigger |
|-----------|----------|---------|
| `firmware_outdated` | WARNING | Device firmware behind latest stable |
| `ips_disabled` | CRITICAL | IPS disabled on any MX network |
| `amp_disabled` | WARNING | AMP disabled on any MX network |
| `no_syslog_configured` | INFO | No syslog servers configured |
| `no_snmp_configured` | INFO | No SNMP configured |
| `vpn_peer_down` | CRITICAL | VPN peer status is down |
| `content_filter_permissive` | WARNING | No content filtering rules |
| `no_alerts_configured` | WARNING | No alert profiles configured |

---

## 6. Totals Summary

| Category | Count |
|----------|-------|
| New `api.py` methods | ~67 |
| New `discovery.py` functions | ~20 |
| New `config.py` functions | ~23 |
| New tool schemas | ~61 |
| New issue detection types | 8 |
| Total stories | 22 |
| Total story points | ~93 SP |
| Estimated sprints | 6-8 |

---

## 7. Dependencies & Risks

### Dependencies
- Epics 1-7 must be complete and stable (643 tests passing)
- Task Executor (Epic 7) must support new FUNCTION_REGISTRY entries
- Safety layer (Story 3.3) must support new safety classifications

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Some endpoints require specific MX/MS firmware versions | Medium | Document minimum firmware requirements per feature |
| VPN config changes can cause network outages | High | Mandatory backup + dry-run support + DANGEROUS classification |
| Live Tools are async (polling required) | Low | Implement polling with timeout in api.py methods |
| Rate limiting with ~67 new methods | Medium | Leverage existing `safe_call()` and rate limiter |

---

## 8. Quality Metrics

| Metric | Target |
|--------|--------|
| Test coverage for new functions | >= 90% |
| Tool schemas pass validation | 100% |
| WRITE tools have backup support | 100% |
| DANGEROUS tools require confirmation | 100% |
| Discovery integration into `full_discovery()` | >= 80% |
| `additionalProperties: False` on all schemas | 100% |

---

*Generated by Morgan (PM Agent) | CNL PRD Phase 1 v1.0.0*
*-- Morgan, planejando o futuro*
