# Test Book - Brownfield Phase 1

> **Scope:** Epics 8, 9, 10 (22 stories, 118 automated tests)
> **How to use:** Send the NL command via chat (localhost:5173) or WebSocket. Verify the response matches the expected result. Mark PASS/FAIL.
> **Pre-requisites:** API Key + Org ID configured, at least 1 network with MX appliance, 1 switch, 1 AP.

---

## Epic 8 - Network Security

### Story 8.1 - Site-to-Site VPN

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 8.1.1 | Discover VPN topology | "Show me the VPN topology" | Returns list of VPN peers with mode (hub/spoke), subnets, and connectivity status |
| 8.1.2 | Discover VPN - no MX | "Show VPN topology" on org with no MX appliances | Returns empty result with no errors, message indicating no VPN data found |
| 8.1.3 | Configure S2S VPN hub | "Configure network N_xxx as VPN hub with subnet 10.0.0.0/24" | Safety prompt (DANGEROUS), asks confirmation, creates backup, applies VPN config, returns ConfigResult with success |
| 8.1.4 | Configure S2S VPN dry-run | "Configure VPN hub on N_xxx - dry run" | Returns what WOULD change without applying, no API call made |
| 8.1.5 | Add VPN peer | "Add VPN peer 203.0.113.1 with secret MyPSK to network N_xxx" | Safety prompt (DANGEROUS), asks confirmation, adds third-party peer with IKE/IPSec settings |
| 8.1.6 | Backup VPN config | "Backup VPN configuration" | Creates backup file in clients/{name}/discovery/ with all MX VPN configs |
| 8.1.7 | Detect VPN peer down | Run full discovery on org with offline VPN peer | Issue list includes `vpn_peer_down` with severity HIGH and peer details |

### Story 8.2 - Content Filtering

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 8.2.1 | Discover content filter | "Show content filtering config for network N_xxx" | Returns blocked URL patterns, blocked categories, allowed URL patterns |
| 8.2.2 | Configure content filter | "Block adult content category on network N_xxx" | Safety prompt (MODERATE), applies category block, returns ConfigResult |
| 8.2.3 | Add blocked URL | "Block facebook.com on network N_xxx" | Appends URL to blocked list (does NOT replace existing), returns updated list |
| 8.2.4 | Detect permissive filter | Full discovery on network with topSites and 0 blocked categories | Issue list includes `content_filter_permissive` with severity MEDIUM |

### Story 8.3 - IPS / Intrusion Detection

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 8.3.1 | Discover IPS settings | "Show IPS settings for network N_xxx" | Returns IPS mode (prevention/detection/disabled), whitelisted rules |
| 8.3.2 | Configure IPS mode | "Enable IPS in prevention mode on N_xxx" | Safety prompt (MODERATE), sets IPS mode, returns ConfigResult |
| 8.3.3 | Set IPS mode shortcut | "Set IPS to detection on N_xxx" | Convenience call, sets mode only, returns success |
| 8.3.4 | Detect IPS disabled | Full discovery on network with IPS disabled | Issue list includes `ips_disabled` with severity MEDIUM |

### Story 8.4 - AMP / Malware Protection

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 8.4.1 | Discover AMP settings | "Show malware protection settings for N_xxx" | Returns AMP mode (enabled/disabled), allowed file hashes |
| 8.4.2 | Configure AMP | "Enable malware protection on N_xxx" | Safety prompt (MODERATE), enables AMP, returns ConfigResult |
| 8.4.3 | Detect AMP disabled | Full discovery on network with AMP disabled | Issue list includes `amp_disabled` with severity MEDIUM |

### Story 8.5 - Traffic Shaping

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 8.5.1 | Discover traffic shaping | "Show traffic shaping rules for N_xxx" | Returns per-app and per-rule shaping rules list |
| 8.5.2 | Configure traffic shaping | "Add traffic shaping rule for YouTube with 5Mbps limit on N_xxx" | Safety prompt (MODERATE), adds shaping rule, returns ConfigResult |
| 8.5.3 | Set bandwidth limit | "Set WAN1 bandwidth to 100Mbps down 50Mbps up on N_xxx" | Sets uplink bandwidth limits, returns success |

---

## Epic 9 - Alerts, Firmware & Observability

### Story 9.1 - Alerts & Webhooks

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.1.1 | Discover alerts | "Show alert settings for network N_xxx" | Returns configured alert types and their enabled/disabled status |
| 9.1.2 | Discover webhooks | "List webhooks for network N_xxx" | Returns list of webhook endpoints with URLs and status |
| 9.1.3 | Configure alerts | "Enable device goes down alert on N_xxx" | Safety prompt (MODERATE), updates alert config, returns ConfigResult |
| 9.1.4 | Create webhook | "Create webhook endpoint https://hooks.example.com/meraki on N_xxx" | Safety prompt (MODERATE), creates HTTP server endpoint, returns URL + shared secret |
| 9.1.5 | Detect no alerts | Full discovery on network with 0 alerts configured | Issue list includes `no_alerts_configured` with severity MEDIUM |

### Story 9.2 - Firmware Upgrades

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.2.1 | Discover firmware | "Show firmware status for network N_xxx" | Returns current firmware version per product type + next upgrade info |
| 9.2.2 | Schedule upgrade | "Schedule firmware upgrade for N_xxx next Saturday at 2am" | Safety prompt (DANGEROUS), schedules upgrade window, returns confirmation |
| 9.2.3 | Cancel upgrade | "Cancel firmware upgrade for N_xxx" | Safety prompt (DANGEROUS), cancels pending upgrade |
| 9.2.4 | Detect outdated firmware | Full discovery on network with outdated firmware | Issue list includes `firmware_outdated` with severity LOW |

### Story 9.3 - Live Tools: Ping

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.3.1 | Ping from device | "Ping 8.8.8.8 from device Q2XX-XXXX-XXXX" | Initiates ping, polls for result, returns latency/loss/replies |
| 9.3.2 | Ping with count | "Ping 1.1.1.1 from Q2XX with 10 packets" | Returns results with specified packet count |

### Story 9.4 - Live Tools: Traceroute

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.4.1 | Traceroute from device | "Traceroute to 8.8.8.8 from device Q2XX-XXXX-XXXX" | Initiates traceroute, polls for result, returns hop-by-hop path |

### Story 9.5 - Live Tools: Cable Test

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.5.1 | Cable test on port | "Run cable test on port 1 of switch Q2XX-XXXX-XXXX" | Initiates cable test, polls for result, returns cable status per pair |

### Story 9.6 - SNMP Configuration

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.6.1 | Discover SNMP | "Show SNMP settings for network N_xxx" | Returns SNMP access mode (none/community/users), community string if set |
| 9.6.2 | Configure SNMP | "Enable SNMP v2c with community 'public' on N_xxx" | Safety prompt (MODERATE), sets SNMP config, returns ConfigResult |
| 9.6.3 | Detect no SNMP | Full discovery on network with SNMP access=none | Issue list includes `no_snmp_configured` with severity LOW |

### Story 9.7 - Syslog Configuration

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.7.1 | Discover syslog | "Show syslog servers for network N_xxx" | Returns list of syslog server IPs, ports, and roles |
| 9.7.2 | Configure syslog | "Add syslog server 10.0.0.5 port 514 on N_xxx" | Safety prompt (MODERATE), adds syslog server, returns ConfigResult |
| 9.7.3 | Detect no syslog | Full discovery on network with 0 syslog servers | Issue list includes `no_syslog_configured` with severity LOW |

### Story 9.8 - Change Log

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 9.8.1 | View recent changes | "Show recent changes in the organization" | Returns list of admin actions with timestamp, admin email, action description |
| 9.8.2 | View changes filtered | "Show changes from the last hour" | Returns filtered change log entries within timespan |

---

## Epic 10 - Switching, Wireless & Platform

### Story 10.1 - Switch L3 Routing

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.1.1 | Discover switch routing | "Show L3 routing interfaces on switch Q2XX-XXXX-XXXX" | Returns L3 interfaces (VLAN, IP, subnet) and static routes |
| 10.1.2 | Configure L3 interface | "Create L3 interface on VLAN 100 with IP 10.1.1.1/24 on switch Q2XX" | Safety prompt (DANGEROUS), creates backup, applies config, returns ConfigResult |
| 10.1.3 | Configure L3 dry-run | "Add L3 interface VLAN 200 on Q2XX - dry run" | Returns planned changes without applying |
| 10.1.4 | Add static route | "Add static route 192.168.0.0/16 via 10.1.1.254 on switch Q2XX" | Safety prompt (DANGEROUS), adds static route, returns success |

### Story 10.2 - STP Configuration

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.2.1 | Discover STP config | "Show STP settings for network N_xxx" | Returns STP bridge priority and RSTP enabled/disabled status |
| 10.2.2 | Configure STP | "Set STP bridge priority to 4096 and enable RSTP on N_xxx" | Safety prompt (DANGEROUS), creates backup, applies STP config |
| 10.2.3 | Configure STP dry-run | "Set STP priority to 8192 on N_xxx - dry run" | Returns what WOULD change without applying |
| 10.2.4 | Detect STP inconsistency | Full discovery on network with STP enabled but RSTP disabled | Issue list includes `stp_inconsistency` with severity MEDIUM |

### Story 10.3 - Device Reboot & LED Blink

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.3.1 | Reboot device | "Reboot device Q2XX-XXXX-XXXX" | Safety prompt (DANGEROUS), confirms reboot, sends reboot command, returns success |
| 10.3.2 | Blink LEDs | "Blink LEDs on device Q2XX-XXXX-XXXX for 30 seconds" | No safety prompt (SAFE), triggers LED blink, returns confirmation with duration |
| 10.3.3 | Reboot without confirmation | "Reboot device Q2XX" and deny confirmation | Operation is cancelled, no reboot sent |

### Story 10.4 - NAT & Port Forwarding

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.4.1 | Discover NAT rules | "Show NAT rules for network N_xxx" | Returns 1:1 NAT and 1:Many NAT rules with public/private IPs |
| 10.4.2 | Discover port forwarding | "Show port forwarding rules for N_xxx" | Returns port forwarding rules with ports, protocol, local IP |
| 10.4.3 | Configure 1:1 NAT | "Add 1:1 NAT mapping 203.0.113.5 to 10.0.0.5 on N_xxx" | Safety prompt (MODERATE), applies NAT rule, returns ConfigResult |
| 10.4.4 | Configure port forwarding | "Forward port 8080 TCP to 10.0.0.10:80 on N_xxx" | Safety prompt (MODERATE), adds forwarding rule, returns ConfigResult |

### Story 10.5 - RF Profiles

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.5.1 | Discover RF profiles | "Show RF profiles for network N_xxx" | Returns list of RF profiles with band settings, channel width, power |
| 10.5.2 | Configure RF profile | "Create RF profile 'HighDensity' with 20MHz channel width on N_xxx" | Safety prompt (MODERATE), creates/updates profile, returns ConfigResult |
| 10.5.3 | Assign RF profile | "Assign RF profile 'HighDensity' to AP Q2XX on N_xxx" | Assigns profile to specific AP, returns confirmation |

### Story 10.6 - Wireless Health

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.6.1 | Discover wireless health | "Show wireless health for network N_xxx" | Returns connection stats, failed connections, latency, signal quality |
| 10.6.2 | Get connection stats | "Show wireless connection stats for N_xxx" | Returns connection success/failure counts per SSID |
| 10.6.3 | Get latency stats | "Show wireless latency for N_xxx" | Returns latency distribution data per SSID |
| 10.6.4 | Get signal quality | "Show wireless signal quality for N_xxx" | Returns SNR and RSSI distribution |
| 10.6.5 | Get channel utilization | "Show channel utilization for N_xxx" | Returns per-band channel utilization percentages |
| 10.6.6 | Get failed connections | "Show failed wireless connections for N_xxx" | Returns list of failed connections with reason codes |

### Story 10.7 - Switch QoS

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.7.1 | Discover QoS config | "Show QoS rules for network N_xxx" | Returns list of QoS rules with DSCP, protocol, ports |
| 10.7.2 | Configure QoS | "Add QoS rule for voice traffic (DSCP 46) on ports 5060-5061 UDP on N_xxx" | Safety prompt (MODERATE), adds QoS rule, returns ConfigResult |

### Story 10.8 - Org Admins Management

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.8.1 | Discover org admins | "List organization administrators" | Returns list of admins with name, email, access level (full/read-only/per-network) |
| 10.8.2 | Create admin | "Add admin user@example.com as read-only admin" | Safety prompt (DANGEROUS), creates admin, returns admin details |
| 10.8.3 | Delete admin | "Remove admin user@example.com" | Safety prompt (DANGEROUS), confirms deletion, removes admin |
| 10.8.4 | Guard-rail: last admin | "Delete the only remaining admin" | Operation BLOCKED with error: cannot delete last admin |
| 10.8.5 | Guard-rail: self-delete | "Delete the admin associated with the current API key" | Operation BLOCKED or warned: cannot delete self-associated admin |

### Story 10.9 - Inventory Management

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| 10.9.1 | Discover inventory | "Show device inventory" | Returns list of all org devices with serial, model, network assignment, claimed date |
| 10.9.2 | Claim device | "Claim device with serial Q2XX-XXXX-XXXX" | Safety prompt (MODERATE), claims device to org, returns confirmation |
| 10.9.3 | Release device | "Release device Q2XX-XXXX-XXXX from inventory" | Safety prompt (DANGEROUS), confirms release, removes from org |

---

## Cross-Cutting Tests

### Safety Layer

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| X.1 | SAFE op no prompt | "Show wireless health for N_xxx" (SAFE) | Executes immediately, no confirmation prompt |
| X.2 | MODERATE op prompts | "Configure SNMP on N_xxx" (MODERATE) | Shows confirmation prompt with operation details before executing |
| X.3 | DANGEROUS op prompts | "Reboot device Q2XX" (DANGEROUS) | Shows confirmation prompt with WARNING, requires explicit "yes" |
| X.4 | Deny dangerous op | "Configure STP on N_xxx" then deny confirmation | Operation cancelled, no changes made, message confirms cancellation |
| X.5 | Dry-run bypass | "Configure VPN dry-run" | No safety prompt since dry-run makes no changes, shows planned diff |

### Agent Router Classification

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| X.6 | Route to analyst | "Analyze wireless health" | Classified as network-analyst, uses discover_wireless_health |
| X.7 | Route to specialist | "Configure QoS rules" | Classified as meraki-specialist, uses configure_qos |
| X.8 | Route discovery verb | "Discover STP settings" | Classified correctly, calls discover_stp_config |
| X.9 | Route config verb | "Set up port forwarding" | Classified as meraki-specialist, calls configure_port_forwarding |
| X.10 | Route ambiguous | "Show me the admins" | Classified as network-analyst (read-only), calls discover_org_admins |

### Issue Detection (Full Discovery)

| # | Test Name | Description | Expected Result |
|---|-----------|-------------|-----------------|
| X.11 | Full discovery all issues | Run full discovery on org with known issues | Returns combined issue list covering: devices_offline, insecure_ssids, vpn_peer_down, content_filter_permissive, ips_disabled, amp_disabled, no_alerts_configured, firmware_outdated, no_snmp_configured, no_syslog_configured, stp_inconsistency |
| X.12 | Full discovery clean org | Run full discovery on well-configured org | Returns empty or minimal issue list, all sections populated |

---

## Summary

| Epic | Stories | Tests | Range |
|------|---------|-------|-------|
| 8 - Network Security | 5 | 20 | 8.1.1 - 8.5.3 |
| 9 - Alerts & Observability | 8 | 19 | 9.1.1 - 9.8.2 |
| 10 - Switching, Wireless & Platform | 9 | 26 | 10.1.1 - 10.9.3 |
| Cross-Cutting | - | 12 | X.1 - X.12 |
| **Total** | **22** | **77** | |
