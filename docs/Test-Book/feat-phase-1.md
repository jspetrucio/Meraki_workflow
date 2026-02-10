# Test Book - Brownfield Phase 1

> **Scope:** Epics 8, 9, 10 (22 stories, 118 automated tests)
> **How to use:** Send the NL command via chat (localhost:5173) or WebSocket. Verify the response matches the expected result. Mark PASS/FAIL.
> **Target Network:** JOSE_HQ (`L_3705899543372511235`) in org Jose_Org (`1437319`)

---

## Network Reference - JOSE_HQ

| Property | Value |
|----------|-------|
| **Network ID** | `L_3705899543372511235` |
| **Org ID** | `1437319` |
| **Org Name** | Jose_Org |
| **Product Types** | `camera`, `switch`, `wireless` |
| **MX Appliance** | **NOT AVAILABLE** |
| **Switch** | Q4AC-XTVK-VJSJ (MS120-8FP) - online |
| **AP** | Q3AJ-BCQ2-K2T2 (MR36) - online |
| **AP** | Q5AA-Y4CT-9ZMV (CW9162I) - online |
| **Camera** | Q2UW-MVS2-WF2C (MV63X "Patio") - online |
| **Camera** | Q2UV-QPG3-XFYN (MV63 "External") - online |
| **SSIDs** | #2 JCiardelli (enabled, psk), #0 MERAKI_NETWORK (disabled), #1 MERAKI_GUEST (disabled) |

> **IMPORTANT:** JOSE_HQ has NO MX appliance. All appliance-dependent features (VPN, Content Filter, IPS, AMP, Traffic Shaping, Firewall L3, VLANs, NAT, Port Forwarding, Bandwidth Limits) will return **"Network has no MX appliance"** or empty results via the hardware product-type guard.

---

## Epic 8 - Network Security

### Story 8.1 - Site-to-Site VPN (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 8.1.1 | Discover VPN topology | "Show me the VPN topology" | Returns empty/no VPN data. JOSE_HQ has no MX appliance; VPN topology requires appliance hardware | |
| 8.1.2 | Discover VPN - no MX | "Show VPN topology for network L_3705899543372511235" | Returns empty result with no errors. Guard detects no appliance, returns gracefully | |
| 8.1.3 | Configure S2S VPN hub | "Configure network L_3705899543372511235 as VPN hub with subnet 10.0.0.0/24" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. S2S VPN requires MX appliance." | |
| 8.1.4 | Configure S2S VPN dry-run | "Configure VPN hub on L_3705899543372511235 - dry run" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`. Guard fires BEFORE dry-run check | |
| 8.1.5 | Add VPN peer | "Add VPN peer 203.0.113.1 with secret MyPSK to network L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message about no MX | |
| 8.1.6 | Backup VPN config | "Backup VPN configuration" | May create empty/partial backup. No MX VPN configs to back up | |
| 8.1.7 | Detect VPN peer down | Run full discovery on Jose_Org | No `vpn_peer_down` issue expected - no MX, no VPN peers to be down | |

### Story 8.2 - Content Filtering (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 8.2.1 | Discover content filter | "Show content filtering config for network L_3705899543372511235" | Returns empty dict `{}`. Guard detects no appliance, skips API call | |
| 8.2.2 | Configure content filter | "Block adult content category on network L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. Content filtering requires MX appliance." | |
| 8.2.3 | Add blocked URL | "Block facebook.com on network L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance` | |
| 8.2.4 | Detect permissive filter | Full discovery on JOSE_HQ | No `content_filter_permissive` issue - content filtering discovery returns empty (no MX) | |

### Story 8.3 - IPS / Intrusion Detection (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 8.3.1 | Discover IPS settings | "Show IPS settings for network L_3705899543372511235" | Returns empty dict `{}`. Guard detects no appliance, skips API call | |
| 8.3.2 | Configure IPS mode | "Enable IPS in prevention mode on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. IPS/IDS requires MX appliance." | |
| 8.3.3 | Set IPS mode shortcut | "Set IPS to detection on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance` (delegates to configure_ips which has the guard) | |
| 8.3.4 | Detect IPS disabled | Full discovery on JOSE_HQ | No `ips_disabled` issue - IPS discovery returns empty (no MX) | |

### Story 8.4 - AMP / Malware Protection (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 8.4.1 | Discover AMP settings | "Show malware protection settings for L_3705899543372511235" | Returns empty dict `{}`. Guard detects no appliance, skips API call | |
| 8.4.2 | Configure AMP | "Enable malware protection on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. AMP/Malware Protection requires MX appliance." | |
| 8.4.3 | Detect AMP disabled | Full discovery on JOSE_HQ | No `amp_disabled` issue - AMP discovery returns empty (no MX) | |

### Story 8.5 - Traffic Shaping (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 8.5.1 | Discover traffic shaping | "Show traffic shaping rules for L_3705899543372511235" | Returns empty dict `{}`. Guard detects no appliance, skips API call | |
| 8.5.2 | Configure traffic shaping | "Add traffic shaping rule for YouTube with 5Mbps limit on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. Traffic shaping requires MX appliance." | |
| 8.5.3 | Set bandwidth limit | "Set WAN1 bandwidth to 100Mbps down 50Mbps up on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. Bandwidth limits requires MX appliance." | |

---

## Epic 9 - Alerts, Firmware & Observability

### Story 9.1 - Alerts & Webhooks (generic - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.1.1 | Discover alerts | "Show alert settings for network L_3705899543372511235" | Returns configured alert types and their enabled/disabled status for JOSE_HQ | |
| 9.1.2 | Discover webhooks | "List webhooks for network L_3705899543372511235" | Returns list of webhook endpoints (may be empty if none configured) | |
| 9.1.3 | Configure alerts | "Enable device goes down alert on L_3705899543372511235" | Safety prompt (MODERATE), updates alert config, returns ConfigResult | |
| 9.1.4 | Create webhook | "Create webhook endpoint https://hooks.example.com/meraki on L_3705899543372511235" | Safety prompt (MODERATE), creates HTTP server endpoint, returns URL + shared secret | |
| 9.1.5 | Detect no alerts | Full discovery on JOSE_HQ | If no alerts are configured, issue list includes `no_alerts_configured` with severity MEDIUM | |

### Story 9.2 - Firmware Upgrades (generic - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.2.1 | Discover firmware | "Show firmware status for network L_3705899543372511235" | Returns current firmware version for switch (MS120-8FP), wireless (MR36, CW9162I), camera (MV63X, MV63) + next upgrade info | |
| 9.2.2 | Schedule upgrade | "Schedule firmware upgrade for L_3705899543372511235 next Saturday at 2am" | Safety prompt (DANGEROUS), schedules upgrade window, returns confirmation | |
| 9.2.3 | Cancel upgrade | "Cancel firmware upgrade for L_3705899543372511235" | Safety prompt (DANGEROUS), cancels pending upgrade | |
| 9.2.4 | Detect outdated firmware | Full discovery on JOSE_HQ | If any device has outdated firmware, issue list includes `firmware_outdated` with severity LOW | |

### Story 9.3 - Live Tools: Ping (device-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.3.1 | Ping from switch | "Ping 8.8.8.8 from device Q4AC-XTVK-VJSJ" | Initiates ping from MS120-8FP switch, polls for result, returns latency/loss/replies | |
| 9.3.2 | Ping from AP | "Ping 1.1.1.1 from Q3AJ-BCQ2-K2T2 with 10 packets" | Initiates ping from MR36 AP, returns results with 10 packet count | |

### Story 9.4 - Live Tools: Traceroute (device-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.4.1 | Traceroute from switch | "Traceroute to 8.8.8.8 from device Q4AC-XTVK-VJSJ" | Initiates traceroute from MS120-8FP, polls for result, returns hop-by-hop path | |

### Story 9.5 - Live Tools: Cable Test (switch - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.5.1 | Cable test on port | "Run cable test on port 1 of switch Q4AC-XTVK-VJSJ" | Initiates cable test on MS120-8FP port 1, polls for result, returns cable status per pair | |

### Story 9.6 - SNMP Configuration (generic - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.6.1 | Discover SNMP | "Show SNMP settings for network L_3705899543372511235" | Returns SNMP access mode (none/community/users), community string if set | |
| 9.6.2 | Configure SNMP | "Enable SNMP v2c with community 'public' on L_3705899543372511235" | Safety prompt (MODERATE), sets SNMP config, returns ConfigResult | |
| 9.6.3 | Detect no SNMP | Full discovery on JOSE_HQ | If SNMP access=none, issue list includes `no_snmp_configured` with severity LOW | |

### Story 9.7 - Syslog Configuration (generic - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.7.1 | Discover syslog | "Show syslog servers for network L_3705899543372511235" | Returns list of syslog server IPs, ports, and roles (may be empty) | |
| 9.7.2 | Configure syslog | "Add syslog server 10.0.0.5 port 514 on L_3705899543372511235" | Safety prompt (MODERATE), adds syslog server, returns ConfigResult | |
| 9.7.3 | Detect no syslog | Full discovery on JOSE_HQ | If 0 syslog servers configured, issue list includes `no_syslog_configured` with severity LOW | |

### Story 9.8 - Change Log (org-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 9.8.1 | View recent changes | "Show recent changes in the organization" | Returns list of admin actions in Jose_Org with timestamp, admin email, action description | |
| 9.8.2 | View changes filtered | "Show changes from the last hour" | Returns filtered change log entries within timespan for Jose_Org | |

---

## Epic 10 - Switching, Wireless & Platform

### Story 10.1 - Switch L3 Routing (switch Q4AC-XTVK-VJSJ - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.1.1 | Discover switch routing | "Show L3 routing interfaces on switch Q4AC-XTVK-VJSJ" | Returns L3 interfaces (VLAN, IP, subnet) and static routes for MS120-8FP | |
| 10.1.2 | Configure L3 interface | "Create L3 interface on VLAN 100 with IP 10.1.1.1/24 on switch Q4AC-XTVK-VJSJ" | Safety prompt (DANGEROUS), creates backup, applies config, returns ConfigResult | |
| 10.1.3 | Configure L3 dry-run | "Add L3 interface VLAN 200 on Q4AC-XTVK-VJSJ - dry run" | Returns planned changes without applying | |
| 10.1.4 | Add static route | "Add static route 192.168.0.0/16 via 10.1.1.254 on switch Q4AC-XTVK-VJSJ" | Safety prompt (DANGEROUS), adds static route, returns success | |

### Story 10.2 - STP Configuration (switch - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.2.1 | Discover STP config | "Show STP settings for network L_3705899543372511235" | Returns STP bridge priority and RSTP enabled/disabled status for JOSE_HQ | |
| 10.2.2 | Configure STP | "Set STP bridge priority to 4096 and enable RSTP on L_3705899543372511235" | Safety prompt (DANGEROUS), creates backup, applies STP config | |
| 10.2.3 | Configure STP dry-run | "Set STP priority to 8192 on L_3705899543372511235 - dry run" | Returns what WOULD change without applying | |
| 10.2.4 | Detect STP inconsistency | Full discovery on JOSE_HQ | If STP enabled but RSTP disabled, issue list includes `stp_inconsistency` with severity MEDIUM | |

### Story 10.3 - Device Reboot & LED Blink (device-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.3.1 | Reboot switch | "Reboot device Q4AC-XTVK-VJSJ" | Safety prompt (DANGEROUS), confirms reboot of MS120-8FP, sends reboot command, returns success | |
| 10.3.2 | Blink LEDs on AP | "Blink LEDs on device Q3AJ-BCQ2-K2T2 for 30 seconds" | No safety prompt (SAFE), triggers LED blink on MR36 AP, returns confirmation with duration | |
| 10.3.3 | Reboot without confirmation | "Reboot device Q4AC-XTVK-VJSJ" and deny confirmation | Operation is cancelled, no reboot sent to MS120-8FP | |

### Story 10.4 - NAT & Port Forwarding (requires MX - NOT AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.4.1 | Discover NAT rules | "Show NAT rules for network L_3705899543372511235" | Returns `{"1to1_nat": {"rules": []}, "1tomany_nat": {"rules": []}}`. Guard detects no appliance, returns empty structure | |
| 10.4.2 | Discover port forwarding | "Show port forwarding rules for L_3705899543372511235" | Returns `{"rules": []}`. Guard detects no appliance, returns empty structure | |
| 10.4.3 | Configure 1:1 NAT | "Add 1:1 NAT mapping 203.0.113.5 to 10.0.0.5 on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. 1:1 NAT requires MX appliance." | |
| 10.4.4 | Configure port forwarding | "Forward port 8080 TCP to 10.0.0.10:80 on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance`, message "Network has no MX appliance. Port forwarding requires MX appliance." | |

### Story 10.5 - RF Profiles (wireless - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.5.1 | Discover RF profiles | "Show RF profiles for network L_3705899543372511235" | Returns list of RF profiles for JOSE_HQ wireless (MR36, CW9162I) with band settings, channel width, power | |
| 10.5.2 | Configure RF profile | "Create RF profile 'HighDensity' with 20MHz channel width on L_3705899543372511235" | Safety prompt (MODERATE), creates profile for wireless network, returns ConfigResult | |
| 10.5.3 | Assign RF profile | "Assign RF profile 'HighDensity' to AP Q3AJ-BCQ2-K2T2 on L_3705899543372511235" | Assigns profile to MR36 AP, returns confirmation | |

### Story 10.6 - Wireless Health (wireless - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.6.1 | Discover wireless health | "Show wireless health for network L_3705899543372511235" | Returns connection stats, failed connections, latency, signal quality for JOSE_HQ wireless (SSID JCiardelli) | |
| 10.6.2 | Get connection stats | "Show wireless connection stats for L_3705899543372511235" | Returns connection success/failure counts for SSID JCiardelli | |
| 10.6.3 | Get latency stats | "Show wireless latency for L_3705899543372511235" | Returns latency distribution data for active SSIDs | |
| 10.6.4 | Get signal quality | "Show wireless signal quality for L_3705899543372511235" | Returns SNR and RSSI distribution from MR36 and CW9162I | |
| 10.6.5 | Get channel utilization | "Show channel utilization for L_3705899543372511235" | Returns per-band channel utilization percentages from APs | |
| 10.6.6 | Get failed connections | "Show failed wireless connections for L_3705899543372511235" | Returns list of failed connections with reason codes (may be empty if no failures) | |

### Story 10.7 - Switch QoS (switch - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.7.1 | Discover QoS config | "Show QoS rules for network L_3705899543372511235" | Returns list of QoS rules on MS120-8FP with DSCP, protocol, ports (may be empty if no rules configured) | |
| 10.7.2 | Configure QoS | "Add QoS rule for voice traffic (DSCP 46) on ports 5060-5061 UDP on L_3705899543372511235" | Safety prompt (MODERATE), adds QoS rule on switch, returns ConfigResult | |

### Story 10.8 - Org Admins Management (org-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.8.1 | Discover org admins | "List organization administrators" | Returns list of Jose_Org admins with name, email, access level (full/read-only/per-network) | |
| 10.8.2 | Create admin | "Add admin user@example.com as read-only admin" | Safety prompt (DANGEROUS), creates admin in Jose_Org, returns admin details | |
| 10.8.3 | Delete admin | "Remove admin user@example.com" | Safety prompt (DANGEROUS), confirms deletion, removes admin from Jose_Org | |
| 10.8.4 | Guard-rail: last admin | "Delete the only remaining admin" | Operation BLOCKED with error: cannot delete last admin | |
| 10.8.5 | Guard-rail: self-delete | "Delete the admin associated with the current API key" | Operation BLOCKED or warned: cannot delete self-associated admin | |

### Story 10.9 - Inventory Management (org-level - AVAILABLE)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| 10.9.1 | Discover inventory | "Show device inventory" | Returns 12 devices: MS120-8FP, MR36, CW9162I x2, MV63X, MV63 x3, MV12WE x2, MV22, CW9162I across JOSE_HQ and FingerSarasota | |
| 10.9.2 | Claim device | "Claim device with serial XXXX-XXXX-XXXX" | Safety prompt (MODERATE), claims device to Jose_Org, returns confirmation | |
| 10.9.3 | Release device | "Release device Q2UV-QPG3-XFYN from inventory" | Safety prompt (DANGEROUS), confirms release of MV63 "External" camera, removes from org | |

---

## Cross-Cutting Tests

### Safety Layer

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| X.1 | SAFE op no prompt | "Show wireless health for L_3705899543372511235" (SAFE) | Executes immediately, no confirmation prompt. Returns wireless health data | |
| X.2 | MODERATE op prompts | "Configure SNMP on L_3705899543372511235" (MODERATE) | Shows confirmation prompt with operation details before executing | |
| X.3 | DANGEROUS op prompts | "Reboot device Q4AC-XTVK-VJSJ" (DANGEROUS) | Shows confirmation prompt with WARNING, requires explicit "yes" | |
| X.4 | Deny dangerous op | "Configure STP on L_3705899543372511235" then deny confirmation | Operation cancelled, no changes made, message confirms cancellation | |
| X.5 | Dry-run bypass safety | "Configure VPN on L_3705899543372511235 dry-run" | Guard fires BEFORE dry-run (no MX). Returns `missing_hardware:appliance` error, not dry-run result | |

### Hardware Product-Type Guards

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| X.6 | Appliance guard - discovery | "Show firewall rules for L_3705899543372511235" | Returns `{"l3_rules": [], "l7_rules": []}` - empty result, no API call made (no MX) | |
| X.7 | Appliance guard - config | "Add firewall rule deny tcp port 23 on L_3705899543372511235" | Returns ConfigResult `success=False`, error=`missing_hardware:appliance` | |
| X.8 | Switch guard - available | "Show STP settings for L_3705899543372511235" | Returns STP config successfully (MS120-8FP switch is present) | |
| X.9 | Wireless guard - available | "Show wireless health for L_3705899543372511235" | Returns wireless health successfully (MR36 + CW9162I APs are present) | |

### Agent Router Classification

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| X.10 | Route to analyst | "Analyze wireless health for L_3705899543372511235" | Classified as network-analyst, uses discover_wireless_health | |
| X.11 | Route to specialist | "Configure QoS rules on L_3705899543372511235" | Classified as meraki-specialist, uses configure_qos | |
| X.12 | Route discovery verb | "Discover STP settings for L_3705899543372511235" | Classified correctly, calls discover_stp_config | |
| X.13 | Route config verb | "Set up port forwarding on L_3705899543372511235" | Classified as meraki-specialist, calls configure_port_forwarding (will fail with missing_hardware:appliance) | |
| X.14 | Route ambiguous | "Show me the admins" | Classified as network-analyst (read-only), calls discover_org_admins | |

### Issue Detection (Full Discovery)

| # | Test Name | NL Command | Expected Result | Status |
|---|-----------|------------|-----------------|--------|
| X.15 | Full discovery JOSE_HQ | "Run full discovery on Jose_Org" | Returns issue list. Expected issues: `insecure_ssids` (FingerDesign-Guest on FingerSarasota is open). Appliance-dependent issues (vpn_peer_down, content_filter_permissive, ips_disabled, amp_disabled) should NOT appear since there is no MX | |
| X.16 | Verify no false appliance issues | Check issue list from full discovery | No appliance-related issues reported. No "IPS disabled" / "AMP disabled" / "content filter permissive" for JOSE_HQ since hardware guard returns empty before issue detection runs | |

---

## Hardware Availability Matrix - JOSE_HQ

| Feature | Required Hardware | Available? | Discovery Behavior | Config Behavior |
|---------|------------------|------------|-------------------|-----------------|
| VPN (S2S, Peer) | appliance (MX) | NO | Empty result | `missing_hardware:appliance` |
| Content Filtering | appliance (MX) | NO | Empty `{}` | `missing_hardware:appliance` |
| IPS/IDS | appliance (MX) | NO | Empty `{}` | `missing_hardware:appliance` |
| AMP/Malware | appliance (MX) | NO | Empty `{}` | `missing_hardware:appliance` |
| Traffic Shaping | appliance (MX) | NO | Empty `{}` | `missing_hardware:appliance` |
| Firewall L3/L7 | appliance (MX) | NO | Empty rules | `missing_hardware:appliance` |
| VLANs | appliance (MX) | NO | Empty `[]` | `missing_hardware:appliance` |
| NAT (1:1, 1:Many) | appliance (MX) | NO | Empty rules | `missing_hardware:appliance` |
| Port Forwarding | appliance (MX) | NO | Empty `{"rules":[]}` | `missing_hardware:appliance` |
| Bandwidth Limits | appliance (MX) | NO | N/A | `missing_hardware:appliance` |
| STP | switch (MS) | YES | Returns STP config | Normal operation |
| Switch ACLs | switch (MS) | YES | Returns ACL rules | Normal operation |
| Switch QoS | switch (MS) | YES | Returns QoS rules | Normal operation |
| Switch L3 Routing | switch (MS) | YES | Returns interfaces | Normal operation |
| SSIDs | wireless (MR) | YES | Returns 15 SSIDs | Normal operation |
| RF Profiles | wireless (MR) | YES | Returns profiles | Normal operation |
| Wireless Health | wireless (MR) | YES | Returns health data | N/A (read-only) |
| Alerts/Webhooks | generic | YES | Returns config | Normal operation |
| Firmware | generic | YES | Returns versions | Normal operation |
| SNMP/Syslog | generic | YES | Returns config | Normal operation |
| Org Admins | org-level | YES | Returns admin list | Normal operation |
| Inventory | org-level | YES | Returns 12 devices | Normal operation |
| Ping/Traceroute | device-level | YES | Returns results | N/A (live tool) |
| Cable Test | switch port | YES | Returns status | N/A (live tool) |

---

## Summary

| Epic | Stories | Tests | Range | Notes |
|------|---------|-------|-------|-------|
| 8 - Network Security | 5 | 20 | 8.1.1 - 8.5.3 | All tests expect `missing_hardware:appliance` (no MX in JOSE_HQ) |
| 9 - Alerts & Observability | 8 | 19 | 9.1.1 - 9.8.2 | All tests should pass normally (generic/device-level features) |
| 10 - Switching, Wireless & Platform | 9 | 26 | 10.1.1 - 10.9.3 | Switch/Wireless tests pass; NAT/Port Forwarding expect `missing_hardware` |
| Cross-Cutting | - | 16 | X.1 - X.16 | Includes 4 new hardware guard tests |
| **Total** | **22** | **81** | | |
