# CNL - Meraki API Coverage Roadmap

> **Document Type:** Product Planning & Gap Analysis
> **Version:** 1.0
> **Date:** 2026-02-08
> **Author:** CNL Product Team
> **Status:** Draft for Review

---

## Executive Summary

The Cisco Neural Language (CNL) project currently wraps **~30 unique Meraki SDK methods** across `api.py`, `discovery.py`, `config.py`, and `automation.py`. The Meraki Dashboard API v1 exposes approximately **855 documented endpoints** spanning 12 product categories. This puts current coverage at roughly **3.5%**.

### What We Cover Well (Day-0 Provisioning & Visibility)

| Capability | Status |
|---|---|
| Organization & network enumeration | Solid |
| Device inventory & status monitoring | Solid |
| SSID read/write (create, enable, disable, configure auth) | Solid |
| VLAN CRUD (create, read, update, delete) | Solid |
| L3 & L7 firewall rule read/write | Solid |
| Switch port read/write with SGT preflight | Solid |
| Switch ACL read/write | Solid |
| Network clients & bandwidth usage | Solid |
| Traffic analysis by application | Solid |
| Camera quality read/write | Basic |
| Action Batches (bulk operations) | Solid |
| Configuration backup & rollback | Solid |
| Discovery snapshot & diff comparison | Solid |
| Issue detection & suggestion engine | Solid |

### What Is Missing (Day-1 / Day-2 Operations)

- **Security services:** IPS/IDS, AMP, content filtering, Air Marshal
- **VPN:** Site-to-Site VPN, Client VPN, SD-WAN policies
- **Network services:** SNMP, syslog, NetFlow, MQTT, DHCP server
- **Device lifecycle:** Firmware upgrades, live tools (ping, traceroute, cable test), reboot, LED blink, packet capture
- **Advanced switching:** Stacks, L3 routing, STP, QoS, port schedules, port mirroring, storm control, PoE, 802.1X, DAI, DHCP snooping
- **Advanced wireless:** RF profiles, wireless health, Bluetooth, splash pages, Hotspot 2.0, identity PSK, SSID firewall, traffic shaping
- **Appliance:** NAT (1:1, 1:many), port forwarding, static routes, warm spare/HA, uplinks, inbound firewall, connectivity monitoring
- **Platform:** Org admins, SAML/SSO, licensing, inventory management, config templates, policy objects, adaptive policy, webhooks, change log, API usage log
- **Camera:** Video analytics, MV Sense, snapshots, RTSP, analytics zones, boundaries
- **Sensor:** Readings, history, alerts, commands
- **Cellular Gateway:** LAN, firewall, uplink, DHCP
- **Insight:** Monitored media servers, app health, web apps
- **Systems Manager:** Device management, profiles, commands, software, trusted access
- **Alerting:** Alert profiles, webhook HTTP servers, payload templates

---

## Current Implementation Inventory

### api.py -- MerakiClient Methods (28 methods)

| # | Method | Type | Meraki SDK Method Called | Agent |
|---|--------|------|------------------------|-------|
| 1 | `get_organizations()` | READ | `organizations.getOrganizations` | network-analyst |
| 2 | `get_organization(org_id)` | READ | `organizations.getOrganization` | network-analyst |
| 3 | `get_networks(org_id)` | READ | `organizations.getOrganizationNetworks` | network-analyst |
| 4 | `get_network(network_id)` | READ | `networks.getNetwork` | network-analyst |
| 5 | `get_network_devices(network_id)` | READ | `networks.getNetworkDevices` | network-analyst |
| 6 | `get_device(serial)` | READ | `devices.getDevice` | network-analyst |
| 7 | `get_device_status(org_id)` | READ | `organizations.getOrganizationDevicesStatuses` | network-analyst |
| 8 | `get_switch_ports(serial)` | READ | `switch.getDeviceSwitchPorts` | network-analyst, meraki-specialist |
| 9 | `update_switch_port(serial, port_id)` | WRITE | `switch.updateDeviceSwitchPort` | meraki-specialist |
| 10 | `get_switch_acls(network_id)` | READ | `switch.getNetworkSwitchAccessControlLists` | network-analyst |
| 11 | `update_switch_acls(network_id, rules)` | WRITE | `switch.updateNetworkSwitchAccessControlLists` | meraki-specialist |
| 12 | `get_ssids(network_id)` | READ | `wireless.getNetworkWirelessSsids` | network-analyst |
| 13 | `get_ssid(network_id, number)` | READ | `wireless.getNetworkWirelessSsid` | network-analyst |
| 14 | `update_ssid(network_id, number)` | WRITE | `wireless.updateNetworkWirelessSsid` | meraki-specialist |
| 15 | `enable_ssid(network_id, number, name)` | WRITE | `wireless.updateNetworkWirelessSsid` | meraki-specialist |
| 16 | `disable_ssid(network_id, number)` | WRITE | `wireless.updateNetworkWirelessSsid` | meraki-specialist |
| 17 | `get_l3_firewall_rules(network_id)` | READ | `appliance.getNetworkApplianceFirewallL3FirewallRules` | network-analyst |
| 18 | `update_l3_firewall_rules(network_id, rules)` | WRITE | `appliance.updateNetworkApplianceFirewallL3FirewallRules` | meraki-specialist |
| 19 | `get_l7_firewall_rules(network_id)` | READ | `appliance.getNetworkApplianceFirewallL7FirewallRules` | network-analyst |
| 20 | `update_l7_firewall_rules(network_id, rules)` | WRITE | `appliance.updateNetworkApplianceFirewallL7FirewallRules` | meraki-specialist |
| 21 | `get_vlans(network_id)` | READ | `appliance.getNetworkApplianceVlans` | network-analyst |
| 22 | `get_vlan(network_id, vlan_id)` | READ | `appliance.getNetworkApplianceVlan` | network-analyst |
| 23 | `create_vlan(network_id, ...)` | WRITE | `appliance.createNetworkApplianceVlan` | meraki-specialist |
| 24 | `update_vlan(network_id, vlan_id)` | WRITE | `appliance.updateNetworkApplianceVlan` | meraki-specialist |
| 25 | `delete_vlan(network_id, vlan_id)` | WRITE | `appliance.deleteNetworkApplianceVlan` | meraki-specialist |
| 26 | `get_camera_quality(serial)` | READ | `camera.getDeviceCameraQualityAndRetention` | network-analyst |
| 27 | `update_camera_quality(serial)` | WRITE | `camera.updateDeviceCameraQualityAndRetention` | meraki-specialist |
| 28 | `get_network_clients(network_id)` | READ | `networks.getNetworkClients` | network-analyst |
| 29 | `get_network_clients_bandwidth_usage(network_id)` | READ | `networks.getNetworkClientsBandwidthUsageHistory` | network-analyst |
| 30 | `get_network_clients_overview(network_id)` | READ | `networks.getNetworkClientsOverview` | network-analyst |
| 31 | `get_network_traffic(network_id)` | READ | `networks.getNetworkTraffic` | network-analyst |

**Utility methods** (not direct API calls): `get_network_by_name`, `get_device_by_name`, `safe_call`, `get_client`, `log_api_call`.

### discovery.py -- Discovery Functions (10 functions)

| # | Function | Type | api.py Methods Used | Agent |
|---|----------|------|---------------------|-------|
| 1 | `discover_networks(org_id, client)` | READ | `get_networks` | network-analyst |
| 2 | `discover_devices(network_id, client)` | READ | `get_network_devices` | network-analyst |
| 3 | `discover_ssids(network_id, client)` | READ | `get_ssids` | network-analyst |
| 4 | `discover_vlans(network_id, client)` | READ | `get_vlans` | network-analyst |
| 5 | `discover_firewall_rules(network_id, client)` | READ | `get_l3_firewall_rules`, `get_l7_firewall_rules` | network-analyst |
| 6 | `discover_switch_ports(serial, client)` | READ | `get_switch_ports` | network-analyst |
| 7 | `discover_switch_acls(network_id, client)` | READ | `get_switch_acls` | network-analyst |
| 8 | `discover_clients(network_id, client)` | READ | `get_network_clients` | network-analyst |
| 9 | `discover_traffic(network_id, client)` | READ | `get_network_traffic` | network-analyst |
| 10 | `full_discovery(org_id, client)` | READ | All of the above + `get_organization`, `get_device_status` | network-analyst |

**Analysis functions:** `find_issues`, `generate_suggestions` (5 issue types detected).
**Snapshot functions:** `save_snapshot`, `load_snapshot`, `list_snapshots`, `compare_snapshots`.

### config.py -- Configuration Functions (14 functions)

| # | Function | Type | api.py Methods Used | Agent |
|---|----------|------|---------------------|-------|
| 1 | `backup_config(network_id, ...)` | UTIL | `get_ssids`, `get_vlans`, `get_l3/l7_firewall_rules`, `get_switch_acls` | meraki-specialist |
| 2 | `rollback_config(backup_path)` | WRITE | `update_ssid`, `update_vlan`, `update_l3/l7_firewall_rules`, `update_switch_acls` | meraki-specialist |
| 3 | `configure_ssid(network_id, ...)` | WRITE | `update_ssid` | meraki-specialist |
| 4 | `enable_ssid(network_id, ...)` | WRITE | `configure_ssid` | meraki-specialist |
| 5 | `disable_ssid(network_id, ...)` | WRITE | `configure_ssid` | meraki-specialist |
| 6 | `create_vlan(network_id, ...)` | WRITE | `create_vlan` | meraki-specialist |
| 7 | `update_vlan(network_id, ...)` | WRITE | `update_vlan` | meraki-specialist |
| 8 | `delete_vlan(network_id, ...)` | WRITE | `delete_vlan` | meraki-specialist |
| 9 | `get_firewall_rules(network_id)` | READ | `get_l3_firewall_rules` | meraki-specialist |
| 10 | `add_firewall_rule(network_id, ...)` | WRITE | `get_l3_firewall_rules`, `update_l3_firewall_rules` | meraki-specialist |
| 11 | `remove_firewall_rule(network_id, ...)` | WRITE | `get_l3_firewall_rules`, `update_l3_firewall_rules` | meraki-specialist |
| 12 | `add_switch_acl(network_id, ...)` | WRITE | `get_switch_acls`, `update_switch_acls` | meraki-specialist |
| 13 | `check_switch_port_writeability(serial)` | READ | Direct REST API (switch ports) | meraki-specialist |
| 14 | `update_switch_port(serial, port_id)` | WRITE | Direct REST API (switch ports) | meraki-specialist |

**Task Executor support (Epic 7):** `detect_catalyst_mode`, `sgt_preflight_check`, `check_license`, `backup_current_state`.

### automation.py -- ActionBatchManager (9 methods)

| # | Method | Type | Meraki SDK Method Called | Agent |
|---|--------|------|------------------------|-------|
| 1 | `preview_batch(actions)` | WRITE | `organizations.createOrganizationActionBatch` (confirmed=False) | meraki-specialist |
| 2 | `execute_batch(actions)` | WRITE | `organizations.createOrganizationActionBatch` (confirmed=True) | meraki-specialist |
| 3 | `get_batch_status(batch_id)` | READ | `organizations.getOrganizationActionBatch` | meraki-specialist |
| 4 | `list_batches(status)` | READ | `organizations.getOrganizationActionBatches` | meraki-specialist |
| 5 | `delete_batch(batch_id)` | WRITE | `organizations.deleteOrganizationActionBatch` | meraki-specialist |
| 6 | `bulk_update_switch_ports(devices, config)` | WRITE | `execute_batch` | meraki-specialist |
| 7 | `bulk_create_vlans(networks, config)` | WRITE | `execute_batch` | meraki-specialist |
| 8 | `bulk_update_ssids(networks, number, config)` | WRITE | `execute_batch` | meraki-specialist |
| 9 | `bulk_update_firewall_rules(networks, rules)` | WRITE | `execute_batch` | meraki-specialist |

**Bonus helpers:** `bulk_reboot_devices(serials)`, `bulk_blink_leds(serials, duration)`.

### agent_tools.py -- Tool Schema & Safety Registry

| Agent | Tool Count | Safety Breakdown |
|-------|-----------|------------------|
| network-analyst | 14 tools | 14 SAFE |
| meraki-specialist | 15 tools | 4 SAFE, 5 MODERATE, 6 DANGEROUS |
| workflow-creator | 6 tools | 6 SAFE |
| **Total** | **35 tools** | **24 SAFE, 5 MODERATE, 6 DANGEROUS** |

---

## Gap Analysis by Product Category

### 1. Organizations (~65 endpoints)

**What we HAVE:**
- [x] `getOrganizations` -- List all organizations
- [x] `getOrganization` -- Get organization details
- [x] `getOrganizationNetworks` -- List networks
- [x] `getOrganizationDevicesStatuses` -- Device statuses
- [x] `createOrganizationActionBatch` -- Action batches (create, get, list, delete)
- [x] `getOrganizationLicensing` -- License check (basic)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Admins** | `getOrganizationAdmins`, `createOrganizationAdmin`, `updateOrganizationAdmin`, `deleteOrganizationAdmin` | ~4 |
| **SAML** | `getOrganizationSaml`, `updateOrganizationSaml`, SAML roles CRUD | ~6 |
| **Licensing** | `getOrganizationLicenses`, `moveOrganizationLicenses`, `renewOrganizationLicensesSeats`, licensing overview | ~8 |
| **Inventory** | `getOrganizationInventoryDevices`, `claimIntoOrganizationInventory`, `releaseFromOrganizationInventory` | ~5 |
| **Config Templates** | `getOrganizationConfigTemplates`, CRUD, bind/unbind networks | ~6 |
| **Policy Objects** | `getOrganizationPolicyObjects`, CRUD, policy object groups | ~8 |
| **Adaptive Policy** | SGT, ACLs, policies, settings | ~12 |
| **Firmware Upgrades** | `getOrganizationFirmwareUpgrades`, `getOrganizationFirmwareUpgradesByDevice`, stage/schedule | ~8 |
| **API Usage** | `getOrganizationApiRequests`, `getOrganizationApiRequestsOverview` | ~3 |
| **Branding** | `getOrganizationBrandingPolicies`, CRUD | ~4 |
| **Alerts** | `getOrganizationAlertsProfiles`, CRUD | ~4 |
| **Webhooks** | `getOrganizationWebhooksAlertTypes`, `getOrganizationWebhooksCallbacksStatuses` | ~3 |
| **SNMP** | `getOrganizationSnmp`, `updateOrganizationSnmp` | ~2 |
| **Change Log** | `getOrganizationConfigurationChanges` | ~1 |
| **Login Security** | `getOrganizationLoginSecurity`, `updateOrganizationLoginSecurity` | ~2 |

### 2. Networks (~55 endpoints)

**What we HAVE:**
- [x] `getNetwork` -- Get network details
- [x] `getNetworkDevices` -- List devices in network
- [x] `getNetworkClients` -- List connected clients
- [x] `getNetworkClientsBandwidthUsageHistory` -- Bandwidth history
- [x] `getNetworkClientsOverview` -- Clients summary
- [x] `getNetworkTraffic` -- Traffic by application

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Settings** | `getNetworkSettings`, `updateNetworkSettings` | ~2 |
| **Group Policies** | `getNetworkGroupPolicies`, CRUD | ~4 |
| **Floor Plans** | `getNetworkFloorPlans`, CRUD | ~4 |
| **Firmware Upgrades** | `getNetworkFirmwareUpgrades`, `updateNetworkFirmwareUpgrades`, staged upgrades | ~6 |
| **Alerts** | `getNetworkAlertsSettings`, `updateNetworkAlertsSettings`, alert history | ~3 |
| **Syslog** | `getNetworkSyslogServers`, `updateNetworkSyslogServers` | ~2 |
| **SNMP** | `getNetworkSnmp`, `updateNetworkSnmp` | ~2 |
| **NetFlow** | `getNetworkNetflow`, `updateNetworkNetflow` | ~2 |
| **Traffic Analysis** | `getNetworkTrafficAnalysis`, `updateNetworkTrafficAnalysis` | ~2 |
| **Traffic Shaping** | `getNetworkTrafficShapingApplicationCategories`, `getNetworkTrafficShapingDscpTaggingOptions` | ~2 |
| **MQTT Brokers** | `getNetworkMqttBrokers`, CRUD | ~4 |
| **Webhooks** | `getNetworkWebhooksHttpServers`, `createNetworkWebhooksHttpServer`, payload templates, tests | ~8 |
| **Client Policies** | `getNetworkClientPolicy`, `updateNetworkClientPolicy` | ~2 |
| **Meraki Auth Users** | `getNetworkMerakiAuthUsers`, CRUD | ~4 |
| **Splash Auth** | `getNetworkClientSplashAuthorizationStatus`, `updateNetworkClientSplashAuthorizationStatus` | ~2 |
| **Topology** | `getNetworkTopologyLinkLayer` | ~1 |
| **Network CRUD** | `createOrganizationNetwork`, `updateNetwork`, `deleteNetwork`, `combineOrganizationNetworks` | ~4 |
| **Bind/Unbind** | `bindNetwork`, `unbindNetwork` (templates) | ~2 |

### 3. Devices (~40 endpoints)

**What we HAVE:**
- [x] `getDevice` -- Get device details
- [x] `getOrganizationDevicesStatuses` -- All device statuses

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Live Tools - Ping** | `createDeviceLiveToolsPing`, `getDeviceLiveToolsPing` | ~2 |
| **Live Tools - Ping Device** | `createDeviceLiveToolsPingDevice`, `getDeviceLiveToolsPingDevice` | ~2 |
| **Live Tools - Traceroute** | `createDeviceLiveToolsTraceroute`, `getDeviceLiveToolsTraceroute` (cable test too) | ~2 |
| **Live Tools - Cable Test** | `createDeviceLiveToolsCableTest`, `getDeviceLiveToolsCableTest` | ~2 |
| **Live Tools - ARP Table** | `createDeviceLiveToolsArpTable`, `getDeviceLiveToolsArpTable` | ~2 |
| **Live Tools - MAC Table** | `createDeviceLiveToolsMacTable`, `getDeviceLiveToolsMacTable` (routing table too) | ~2 |
| **Live Tools - ACL Hits** | (recent API additions for Catalyst) | ~2 |
| **Live Tools - DHCP Leases** | Lease table for MX/appliance | ~2 |
| **Live Tools - Wake on LAN** | `createDeviceLiveToolsWakeOnLan` | ~1 |
| **Reboot** | `rebootDevice` | ~1 |
| **Blink LEDs** | `blinkDeviceLeds` | ~1 |
| **Management Interface** | `getDeviceManagementInterface`, `updateDeviceManagementInterface` | ~2 |
| **LLDP/CDP** | `getDeviceLldpCdp` | ~1 |
| **Cellular SIMs** | `getDeviceCellularSims`, `updateDeviceCellularSims` | ~2 |
| **Update Device** | `updateDevice` (name, tags, address, notes, etc.) | ~1 |
| **Claim/Remove** | `claimNetworkDevices`, `removeNetworkDevices` | ~2 |
| **Packet Capture** | (available via Live Tools API) | ~2 |

### 4. Wireless / MR (~75 endpoints)

**What we HAVE:**
- [x] `getNetworkWirelessSsids` -- List SSIDs
- [x] `getNetworkWirelessSsid` -- Get single SSID
- [x] `updateNetworkWirelessSsid` -- Update SSID (name, auth, PSK, enabled, VLAN, IP assignment)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **RF Profiles** | `getNetworkWirelessRfProfiles`, CRUD, assign to APs | ~5 |
| **Wireless Health** | `getNetworkWirelessConnectionStats`, `getNetworkWirelessLatencyStats`, `getNetworkWirelessSignalQualityScores`, channel utilization, failed connections | ~10 |
| **Air Marshal** | `getNetworkWirelessAirMarshal`, rogue AP detection | ~3 |
| **Bluetooth** | `getNetworkWirelessBluetoothSettings`, `updateNetworkWirelessBluetoothSettings`, BLE scanning | ~3 |
| **Splash Pages** | `getNetworkWirelessSsidSplashSettings`, `updateNetworkWirelessSsidSplashSettings` | ~2 |
| **Billing** | `getNetworkWirelessBilling`, `updateNetworkWirelessBilling` | ~2 |
| **SSID Firewall** | `getNetworkWirelessSsidFirewallL3FirewallRules`, `updateNetworkWirelessSsidFirewallL3FirewallRules`, L7 rules | ~4 |
| **Traffic Shaping** | `getNetworkWirelessSsidTrafficShapingRules`, `updateNetworkWirelessSsidTrafficShapingRules` | ~3 |
| **Identity PSK** | `getNetworkWirelessSsidIdentityPsks`, CRUD | ~4 |
| **Hotspot 2.0** | `getNetworkWirelessSsidHotspot20`, `updateNetworkWirelessSsidHotspot20` | ~2 |
| **Bonjour Forwarding** | `getNetworkWirelessSsidBonjourForwarding`, `updateNetworkWirelessSsidBonjourForwarding` | ~2 |
| **Schedules** | `getNetworkWirelessSsidSchedules`, `updateNetworkWirelessSsidSchedules` | ~2 |
| **Zigbee** | `getNetworkWirelessEthernetPortsProfiles` (IoT) | ~3 |
| **Location Analytics** | `getNetworkWirelessLatencyHistory`, scanning API | ~5 |
| **ESL (Electronic Shelf Labels)** | ESL profile management | ~3 |
| **Wireless Settings** | `getNetworkWirelessSettings`, `updateNetworkWirelessSettings` | ~2 |
| **Alternate Mgmt Interface** | `getNetworkWirelessAlternateManagementInterface` | ~2 |

### 5. Switching / MS (~80 endpoints)

**What we HAVE:**
- [x] `getDeviceSwitchPorts` -- List switch ports
- [x] `updateDeviceSwitchPort` -- Update port config
- [x] `getNetworkSwitchAccessControlLists` -- Get ACLs
- [x] `updateNetworkSwitchAccessControlLists` -- Update ACLs
- [x] SGT preflight check (custom implementation)
- [x] Catalyst mode detection

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Stacks** | `getNetworkSwitchStacks`, `createNetworkSwitchStack`, CRUD, stack routing interfaces | ~8 |
| **Routing / L3** | `getDeviceSwitchRoutingInterfaces`, CRUD, static routes, OSPF | ~8 |
| **DHCP** | `getDeviceSwitchRoutingInterfaceDhcp`, `updateDeviceSwitchRoutingInterfaceDhcp`, network DHCP | ~4 |
| **STP** | `getNetworkSwitchStp`, `updateNetworkSwitchStp` | ~2 |
| **QoS** | `getNetworkSwitchQosRules`, CRUD, QoS order | ~5 |
| **Port Schedules** | `getNetworkSwitchPortSchedules`, CRUD | ~4 |
| **Port Mirroring** | (via port config, clone port) | ~2 |
| **Storm Control** | `getNetworkSwitchStormControl`, `updateNetworkSwitchStormControl` | ~2 |
| **Link Aggregation** | `getNetworkSwitchLinkAggregations`, CRUD | ~4 |
| **MTU** | `getNetworkSwitchMtu`, `updateNetworkSwitchMtu` | ~2 |
| **VLAN Profiles** | (config templates) | ~3 |
| **Warm Spare** | `getDeviceSwitchWarmSpare` (HA for stacks) | ~2 |
| **PoE** | Per-port PoE config (via updateSwitchPort) | ~2 |
| **Access Policies (802.1X)** | `getNetworkSwitchAccessPolicies`, CRUD | ~4 |
| **DAI** | `getNetworkSwitchDhcpV4ServersSeen`, Dynamic ARP Inspection | ~2 |
| **DHCP Snooping** | `getNetworkSwitchDhcpServerPolicy`, `updateNetworkSwitchDhcpServerPolicy` | ~2 |
| **Switch Settings** | `getNetworkSwitchSettings`, `updateNetworkSwitchSettings` | ~2 |
| **Port Statuses** | `getDeviceSwitchPortsStatuses`, `getOrganizationSwitchPortsBySwitch` | ~3 |

### 6. Appliance / MX (~90 endpoints)

**What we HAVE:**
- [x] `getNetworkApplianceFirewallL3FirewallRules` -- L3 rules
- [x] `updateNetworkApplianceFirewallL3FirewallRules` -- Update L3 rules
- [x] `getNetworkApplianceFirewallL7FirewallRules` -- L7 rules
- [x] `updateNetworkApplianceFirewallL7FirewallRules` -- Update L7 rules
- [x] `getNetworkApplianceVlans` -- List VLANs
- [x] `getNetworkApplianceVlan` -- Get VLAN
- [x] `createNetworkApplianceVlan` -- Create VLAN
- [x] `updateNetworkApplianceVlan` -- Update VLAN
- [x] `deleteNetworkApplianceVlan` -- Delete VLAN

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Site-to-Site VPN** | `getNetworkApplianceVpnSiteToSiteVpn`, `updateNetworkApplianceVpnSiteToSiteVpn`, `getOrganizationApplianceVpnStats`, VPN statuses, third-party peers | ~6 |
| **Client VPN** | `getNetworkApplianceClientSecurityEvents` (AnyConnect integration) | ~3 |
| **Content Filtering** | `getNetworkApplianceContentFiltering`, `updateNetworkApplianceContentFiltering`, content filtering categories | ~3 |
| **IPS / Intrusion Detection** | `getNetworkApplianceSecurityIntrusion`, `updateNetworkApplianceSecurityIntrusion`, org-wide settings | ~4 |
| **AMP / Malware** | `getNetworkApplianceSecurityMalware`, `updateNetworkApplianceSecurityMalware` | ~2 |
| **Traffic Shaping** | `getNetworkApplianceTrafficShaping`, `updateNetworkApplianceTrafficShaping`, uplink bandwidth, custom perf classes | ~6 |
| **SD-WAN** | `getNetworkApplianceTrafficShapingUplinkSelection`, `updateNetworkApplianceTrafficShapingUplinkSelection`, uplink bandwidth, VPN exclusions | ~5 |
| **1:1 NAT** | `getNetworkApplianceFirewallOneToOneNatRules`, `updateNetworkApplianceFirewallOneToOneNatRules` | ~2 |
| **1:Many NAT** | `getNetworkApplianceFirewallOneToManyNatRules`, `updateNetworkApplianceFirewallOneToManyNatRules` | ~2 |
| **Port Forwarding** | `getNetworkApplianceFirewallPortForwardingRules`, `updateNetworkApplianceFirewallPortForwardingRules` | ~2 |
| **Static Routes** | `getNetworkApplianceStaticRoutes`, CRUD | ~4 |
| **Warm Spare / HA** | `getNetworkApplianceWarmSpare`, `updateNetworkApplianceWarmSpare`, swap | ~3 |
| **Uplinks** | `getOrganizationApplianceUplinkStatuses`, `getNetworkApplianceUplinksUsageHistory`, uplink settings | ~4 |
| **Inbound Firewall** | `getNetworkApplianceFirewallInboundFirewallRules`, `updateNetworkApplianceFirewallInboundFirewallRules` | ~2 |
| **Inbound Cellular Firewall** | `getNetworkApplianceFirewallInboundCellularFirewallRules` | ~2 |
| **Firewalled Services** | `getNetworkApplianceFirewallFirewalledServices`, `updateNetworkApplianceFirewallFirewalledService` | ~2 |
| **Single LAN** | `getNetworkApplianceSingleLan`, `updateNetworkApplianceSingleLan` | ~2 |
| **VLAN Ports** | `getNetworkAppliancePorts`, `getNetworkAppliancePort`, `updateNetworkAppliancePort` | ~3 |
| **Connectivity Monitoring** | `getNetworkApplianceConnectivityMonitoringDestinations` | ~2 |
| **Security Events** | `getNetworkApplianceSecurityEvents`, `getOrganizationApplianceSecurityEvents` | ~2 |
| **DHCP** | `getNetworkApplianceDhcpSubnets` (appliance DHCP) | ~1 |
| **Appliance Settings** | `getNetworkApplianceSettings` | ~1 |
| **Prefixes** | `getNetworkAppliancePrefixesDelegatedStatics` (IPv6) | ~3 |

### 7. Camera / MV (~30 endpoints)

**What we HAVE:**
- [x] `getDeviceCameraQualityAndRetention` -- Quality settings
- [x] `updateDeviceCameraQualityAndRetention` -- Update quality

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Video Analytics** | `getDeviceCameraAnalyticsOverview`, `getDeviceCameraAnalyticsRecent`, `getDeviceCameraAnalyticsZoneHistory` | ~5 |
| **Analytics Zones** | `getDeviceCameraAnalyticsZones` | ~1 |
| **MV Sense** | `getDeviceCameraSense`, `updateDeviceCameraSense`, object detection | ~3 |
| **Video Link** | `getDeviceCameraVideoLink` | ~1 |
| **Snapshots** | `generateDeviceCameraSnapshot` | ~1 |
| **Wireless Profiles** | `getNetworkCameraWirelessProfiles`, CRUD | ~4 |
| **Custom Analytics** | `getDeviceCameraCustomAnalytics`, `updateDeviceCameraCustomAnalytics`, artifacts | ~4 |
| **RTSP** | `getDeviceCameraVideoSettings`, `updateDeviceCameraVideoSettings` (external RTSP) | ~2 |
| **Boundaries** | `getNetworkCameraSchedules` (motion alerts, boundaries) | ~3 |

### 8. Sensor / MT (~15 endpoints)

**What we HAVE:**
- (none)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Readings** | `getOrganizationSensorReadingsHistory`, `getOrganizationSensorReadingsLatest` | ~2 |
| **Alerts** | `getNetworkSensorAlertsProfiles`, CRUD, alert conditions | ~4 |
| **Commands** | `createDeviceSensorCommand` (LED, buzzer) | ~2 |
| **Relationships** | `getNetworkSensorRelationships`, assign sensors to devices | ~3 |
| **Overview** | `getOrganizationSensorReadingsHistory` (aggregated) | ~2 |

### 9. Cellular Gateway / MG (~15 endpoints)

**What we HAVE:**
- (none)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **LAN** | `getDeviceCellularGatewayLan`, `updateDeviceCellularGatewayLan` | ~2 |
| **Port Forwarding** | `getDeviceCellularGatewayPortForwardingRules`, `updateDeviceCellularGatewayPortForwardingRules` | ~2 |
| **Firewall** | `getNetworkCellularGatewaySubnetPool`, `updateNetworkCellularGatewaySubnetPool` | ~2 |
| **Uplink** | `getOrganizationCellularGatewayUplinkStatuses` | ~1 |
| **DHCP** | `getNetworkCellularGatewayDhcp`, `updateNetworkCellularGatewayDhcp` | ~2 |
| **Subnet Pool** | `getNetworkCellularGatewaySubnetPool` | ~1 |
| **Settings** | `getNetworkCellularGatewayConnectivityMonitoringDestinations` | ~2 |

### 10. Insight (~15 endpoints)

**What we HAVE:**
- (none)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Monitored Media** | `getOrganizationInsightMonitoredMediaServers`, CRUD | ~4 |
| **App Health** | `getOrganizationInsightApplications`, `getOrganizationInsightApplicationsHealthByTime` | ~3 |
| **App Categories** | Application category lookup | ~2 |
| **Web Apps** | Web application performance monitoring | ~3 |

### 11. Systems Manager / SM (~45 endpoints)

**What we HAVE:**
- (none)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **Devices** | `getNetworkSmDevices`, `getNetworkSmDevicePerformanceHistory`, lock, wipe, unenroll | ~10 |
| **Profiles** | `getNetworkSmProfiles`, assign, unassign | ~4 |
| **Users** | `getNetworkSmUsers`, user device mapping | ~3 |
| **Commands** | `getNetworkSmDeviceSoftwares`, install/uninstall apps, restart | ~5 |
| **Desktop Logs** | `getNetworkSmDeviceDesktopLogs` | ~1 |
| **Software** | `getNetworkSmDeviceSoftwares`, compliance checks | ~3 |
| **Trusted Access** | `getOrganizationSmSentryPoliciesAssignmentsByNetwork` | ~4 |
| **Target Groups** | `getNetworkSmTargetGroups`, CRUD | ~4 |
| **MDM Config** | `getNetworkSmDeviceCerts`, bypass activation lock | ~3 |
| **Apple VPP** | `getOrganizationSmVppAccounts` | ~2 |

### 12. Webhooks & Alerting (~20 endpoints)

**What we HAVE:**
- (none -- workflow-creator generates JSON files, not live webhooks)

**What we are MISSING:**

| Endpoint Group | Key Endpoints | Count |
|---|---|---|
| **HTTP Servers** | `getNetworkWebhooksHttpServers`, CRUD | ~4 |
| **Payload Templates** | `getNetworkWebhooksPayloadTemplates`, CRUD | ~4 |
| **Webhook Tests** | `createNetworkWebhooksWebhookTest`, `getNetworkWebhooksWebhookTest` | ~2 |
| **Alert Profiles** | `getOrganizationAlertsProfiles`, CRUD | ~4 |
| **Alert Types** | `getOrganizationWebhooksAlertTypes` | ~1 |
| **Webhook Logs** | `getOrganizationWebhooksLogs` | ~1 |

---

## Priority Roadmap

### Phase 1 -- P0: Core Operations (Epics 8-10, ~90 story points)

These are the features most frequently requested in day-1/day-2 operations. Completing this phase takes coverage from **~3.5% to ~15%**.

| Feature Group | New `api.py` Methods | New `discovery.py` Functions | New `config.py` Functions | New Tool Schemas | Est. SP | Agent |
|---|---|---|---|---|---|---|
| **Site-to-Site VPN** | `get_vpn_config`, `update_vpn_config`, `get_vpn_statuses` | `discover_vpn_topology` | `configure_s2s_vpn`, `add_vpn_peer` | 3 | 8 | meraki-specialist |
| **Content Filtering** | `get_content_filtering`, `update_content_filtering`, `get_content_categories` | `discover_content_filtering` | `configure_content_filter`, `add_blocked_url` | 3 | 5 | meraki-specialist |
| **IPS / Intrusion Detection** | `get_intrusion_settings`, `update_intrusion_settings` | `discover_ips_settings` | `configure_ips`, `set_ips_mode` | 2 | 5 | meraki-specialist |
| **AMP / Malware Protection** | `get_malware_settings`, `update_malware_settings` | `discover_amp_settings` | `configure_amp` | 2 | 3 | meraki-specialist |
| **Traffic Shaping (Appliance)** | `get_traffic_shaping`, `update_traffic_shaping`, `get_uplink_bandwidth` | `discover_traffic_shaping` | `configure_traffic_shaping`, `set_bandwidth_limit` | 3 | 5 | meraki-specialist |
| **Alerts & Webhooks** | `get_alert_settings`, `update_alert_settings`, `get_webhook_servers`, `create_webhook_server`, `test_webhook` | `discover_alerts`, `discover_webhooks` | `configure_alerts`, `create_webhook_endpoint` | 5 | 8 | meraki-specialist, workflow-creator |
| **Firmware Upgrades** | `get_firmware_upgrades`, `update_firmware_upgrades`, `get_firmware_by_device` | `discover_firmware_status` | `schedule_firmware_upgrade`, `cancel_firmware_upgrade` | 3 | 8 | meraki-specialist |
| **Live Tools (Ping)** | `create_ping`, `get_ping_result` | -- | -- | 2 | 3 | network-analyst |
| **Live Tools (Traceroute)** | `create_traceroute`, `get_traceroute_result` | -- | -- | 2 | 3 | network-analyst |
| **Live Tools (Cable Test)** | `create_cable_test`, `get_cable_test_result` | -- | -- | 2 | 3 | network-analyst |
| **SNMP** | `get_snmp_settings`, `update_snmp_settings` (org + network) | `discover_snmp_config` | `configure_snmp` | 2 | 3 | meraki-specialist |
| **Syslog** | `get_syslog_servers`, `update_syslog_servers` | `discover_syslog_config` | `configure_syslog` | 2 | 3 | meraki-specialist |
| **Switch Routing L3** | `get_switch_routing_interfaces`, `create_routing_interface`, `update_routing_interface`, `delete_routing_interface`, `get_switch_static_routes` | `discover_switch_routing` | `configure_switch_l3_interface`, `add_switch_static_route` | 4 | 5 | meraki-specialist |
| **STP** | `get_stp_settings`, `update_stp_settings` | `discover_stp_config` | `configure_stp` | 2 | 3 | meraki-specialist |
| **Change Log** | `get_config_changes` | `discover_recent_changes` | -- | 1 | 2 | network-analyst |
| **Device Reboot** | `reboot_device`, `blink_leds` | -- | -- | 2 | 2 | meraki-specialist |
| **NAT / Port Forwarding** | `get_1to1_nat`, `update_1to1_nat`, `get_1tomany_nat`, `update_1tomany_nat`, `get_port_forwarding`, `update_port_forwarding` | `discover_nat_rules`, `discover_port_forwarding` | `configure_1to1_nat`, `configure_port_forwarding` | 4 | 5 | meraki-specialist |
| **RF Profiles** | `get_rf_profiles`, `create_rf_profile`, `update_rf_profile`, `delete_rf_profile` | `discover_rf_profiles` | `configure_rf_profile` | 3 | 5 | meraki-specialist |
| **Wireless Health** | `get_wireless_connection_stats`, `get_wireless_latency_stats`, `get_wireless_signal_quality`, `get_channel_utilization`, `get_failed_connections` | `discover_wireless_health` | -- | 5 | 5 | network-analyst |
| **Switch QoS** | `get_qos_rules`, `create_qos_rule`, `update_qos_rule`, `delete_qos_rule` | `discover_qos_config` | `configure_qos` | 3 | 3 | meraki-specialist |
| **Org Admins** | `get_admins`, `create_admin`, `update_admin`, `delete_admin` | `discover_org_admins` | `manage_admin` | 3 | 3 | meraki-specialist |
| **Inventory Management** | `get_inventory`, `claim_device`, `release_device` | `discover_inventory` | -- | 3 | 3 | network-analyst |
| **TOTALS** | **~55 new methods** | **~17 new functions** | **~20 new functions** | **~55 new schemas** | **~90 SP** | -- |

### Phase 2 -- P1: Platform Depth (Epics 11-13, ~75 story points)

Broadens coverage to advanced networking features. Takes coverage from **~15% to ~35%**.

| Feature Group | New `api.py` Methods | New `discovery.py` Functions | New `config.py` Functions | New Tool Schemas | Est. SP | Agent |
|---|---|---|---|---|---|---|
| **SD-WAN / Uplink Selection** | `get_uplink_selection`, `update_uplink_selection`, `get_uplink_statuses`, `get_vpn_exclusions` | `discover_sdwan_config` | `configure_sdwan_policy`, `set_uplink_preference` | 4 | 8 | meraki-specialist |
| **Client VPN** | `get_client_vpn`, `update_client_vpn` | `discover_client_vpn` | `configure_client_vpn` | 2 | 3 | meraki-specialist |
| **Adaptive Policy / SGT** | `get_adaptive_policies`, `create_adaptive_policy`, `get_adaptive_policy_acls`, `get_policy_objects`, `create_policy_object` | `discover_adaptive_policies` | `configure_adaptive_policy`, `create_policy_object` | 5 | 8 | meraki-specialist |
| **Config Templates** | `get_config_templates`, `create_config_template`, `update_config_template`, `bind_network`, `unbind_network` | `discover_templates` | `manage_template` | 4 | 5 | meraki-specialist |
| **Policy Objects** | `get_policy_objects`, `create_policy_object`, `update_policy_object`, `delete_policy_object`, `get_policy_object_groups` | `discover_policy_objects` | `manage_policy_object` | 4 | 5 | meraki-specialist |
| **Camera Analytics & Snapshots** | `get_camera_analytics_overview`, `get_camera_analytics_zones`, `get_camera_analytics_history`, `generate_snapshot`, `get_video_link` | `discover_camera_analytics` | -- | 5 | 5 | network-analyst |
| **Sensor Readings & Alerts** | `get_sensor_readings_latest`, `get_sensor_readings_history`, `get_sensor_alert_profiles`, `create_sensor_alert` | `discover_sensors` | `configure_sensor_alert` | 4 | 5 | network-analyst, meraki-specialist |
| **Switch Stacks** | `get_switch_stacks`, `create_switch_stack`, `add_to_stack`, `remove_from_stack`, `get_stack_routing` | `discover_switch_stacks` | `manage_switch_stack` | 4 | 5 | meraki-specialist |
| **802.1X / Access Policies** | `get_access_policies`, `create_access_policy`, `update_access_policy`, `delete_access_policy` | `discover_access_policies` | `configure_access_policy` | 3 | 5 | meraki-specialist |
| **Port Schedules** | `get_port_schedules`, `create_port_schedule`, `update_port_schedule`, `delete_port_schedule` | `discover_port_schedules` | `configure_port_schedule` | 3 | 3 | meraki-specialist |
| **HA / Warm Spare** | `get_warm_spare`, `update_warm_spare`, `swap_warm_spare` | `discover_ha_config` | `configure_warm_spare`, `trigger_failover` | 3 | 5 | meraki-specialist |
| **Air Marshal** | `get_air_marshal`, `get_air_marshal_rules` | `discover_rogue_aps` | -- | 2 | 3 | network-analyst |
| **SSID Firewall** | `get_ssid_l3_firewall`, `update_ssid_l3_firewall`, `get_ssid_l7_firewall`, `update_ssid_l7_firewall` | `discover_ssid_firewall` | `configure_ssid_firewall` | 4 | 3 | meraki-specialist |
| **Splash Pages** | `get_splash_settings`, `update_splash_settings` | `discover_splash_config` | `configure_splash_page` | 2 | 3 | meraki-specialist |
| **Floor Plans** | `get_floor_plans`, `create_floor_plan`, `update_floor_plan`, `delete_floor_plan` | `discover_floor_plans` | -- | 2 | 3 | network-analyst |
| **Group Policies** | `get_group_policies`, `create_group_policy`, `update_group_policy`, `delete_group_policy` | `discover_group_policies` | `configure_group_policy` | 3 | 3 | meraki-specialist |
| **LLDP/CDP** | `get_lldp_cdp` | `discover_lldp_cdp` | -- | 1 | 2 | network-analyst |
| **Packet Capture** | `create_packet_capture`, `get_packet_capture_status` | -- | -- | 2 | 3 | network-analyst |
| **NetFlow** | `get_netflow_settings`, `update_netflow_settings` | `discover_netflow_config` | `configure_netflow` | 2 | 2 | meraki-specialist |
| **PoE** | (port-level via `updateDeviceSwitchPort` poeEnabled) | `discover_poe_status` | -- | 1 | 2 | network-analyst |
| **Static Routes (Appliance)** | `get_static_routes`, `create_static_route`, `update_static_route`, `delete_static_route` | `discover_static_routes` | `manage_static_route` | 3 | 3 | meraki-specialist |
| **TOTALS** | **~65 new methods** | **~20 new functions** | **~18 new functions** | **~62 new schemas** | **~75 SP** | -- |

### Phase 3 -- P2: Specialized Features (Epics 14-15, ~50 story points)

Covers niche and specialized product lines. Takes coverage from **~35% to ~50%**.

| Feature Group | New `api.py` Methods | New `discovery.py` Functions | New `config.py` Functions | New Tool Schemas | Est. SP | Agent |
|---|---|---|---|---|---|---|
| **Systems Manager (SM/MDM)** | `get_sm_devices`, `get_sm_profiles`, `get_sm_users`, `lock_sm_device`, `wipe_sm_device`, `install_app`, `get_sm_software` | `discover_sm_devices` | `manage_sm_device`, `assign_sm_profile` | 6 | 13 | meraki-specialist |
| **Insight (App Health)** | `get_insight_applications`, `get_insight_app_health`, `get_monitored_media_servers`, `create_monitored_media_server` | `discover_insight_apps` | `configure_monitored_media` | 4 | 5 | network-analyst |
| **Camera ML / Custom Analytics** | `get_custom_analytics`, `update_custom_analytics`, `get_analytics_artifacts`, `get_camera_sense`, `update_camera_sense` | `discover_camera_ml` | `configure_camera_analytics` | 4 | 5 | meraki-specialist |
| **Cellular Gateway (MG)** | `get_mg_lan`, `update_mg_lan`, `get_mg_port_forwarding`, `update_mg_port_forwarding`, `get_mg_uplink_statuses`, `get_mg_dhcp` | `discover_cellular_gateways` | `configure_mg_lan`, `configure_mg_port_forwarding` | 5 | 5 | meraki-specialist |
| **Zigbee / IoT** | `get_zigbee_settings` | `discover_zigbee_config` | -- | 1 | 2 | network-analyst |
| **ESL (Electronic Shelf Labels)** | `get_esl_profiles` | `discover_esl_config` | -- | 1 | 2 | network-analyst |
| **SAML / SSO** | `get_saml_settings`, `update_saml_settings`, `get_saml_roles`, `create_saml_role` | `discover_saml_config` | `configure_saml` | 3 | 3 | meraki-specialist |
| **Licensing (Advanced)** | `get_licenses_overview`, `get_license_details`, `move_licenses`, `renew_licenses` | `discover_licensing` | `manage_licenses` | 3 | 5 | meraki-specialist |
| **Hotspot 2.0** | `get_hotspot20`, `update_hotspot20` | `discover_hotspot20` | `configure_hotspot20` | 2 | 3 | meraki-specialist |
| **Identity PSK** | `get_identity_psks`, `create_identity_psk`, `update_identity_psk`, `delete_identity_psk` | `discover_identity_psks` | `manage_identity_psk` | 3 | 3 | meraki-specialist |
| **MQTT Brokers** | `get_mqtt_brokers`, `create_mqtt_broker`, `update_mqtt_broker`, `delete_mqtt_broker` | `discover_mqtt_brokers` | `configure_mqtt_broker` | 3 | 2 | meraki-specialist |
| **Location Analytics** | `get_location_scanning`, `get_wireless_latency_history` | `discover_location_analytics` | -- | 2 | 2 | network-analyst |
| **TOTALS** | **~50 new methods** | **~12 new functions** | **~10 new functions** | **~37 new schemas** | **~50 SP** | -- |

---

## Implementation Pattern

Every new Meraki API capability follows a standardized 7-step pattern. This ensures consistency across the codebase and makes each new feature testable and immediately available to the agent pipeline.

### Step 1: `api.py` -- Add SDK Wrapper Method

Add a new method to `MerakiClient` that wraps the Meraki Python SDK call with logging, error handling, and retry logic.

```python
# api.py
@log_api_call
def get_content_filtering(self, network_id: str) -> dict:
    """Retorna configuracao de content filtering."""
    return self.dashboard.appliance.getNetworkApplianceContentFiltering(network_id)

@log_api_call
def update_content_filtering(self, network_id: str, **kwargs) -> dict:
    """Atualiza configuracao de content filtering."""
    return self.dashboard.appliance.updateNetworkApplianceContentFiltering(
        network_id, **kwargs
    )
```

**Conventions:**
- Always use `@log_api_call` decorator
- Always type-hint return values
- Use `Optional[str]` for `org_id` parameters that default to `self.org_id`
- Keep methods thin: no business logic, just SDK calls

### Step 2: `discovery.py` -- Add Discovery Function (READ operations)

For every new READ capability, add a discovery function that wraps the api.py method with safe error handling and structured output.

```python
# discovery.py
def discover_content_filtering(network_id: str, client: MerakiClient) -> dict:
    """Descobre configuracao de content filtering de uma network."""
    logger.debug(f"Descobrindo content filtering da network {network_id}")
    result = client.safe_call(client.get_content_filtering, network_id, default={})
    return result
```

**Conventions:**
- Always accept `(target_id, client)` parameters
- Use `client.safe_call()` to handle 400/404 gracefully
- Add to `full_discovery()` if the feature should appear in automatic scans
- Add corresponding issue detection in `find_issues()` if applicable

### Step 3: `config.py` -- Add Configuration Function (WRITE operations)

For every new WRITE capability, add a configuration function with automatic backup and rollback support.

```python
# config.py
def configure_content_filter(
    network_id: str,
    blocked_urls: Optional[list[str]] = None,
    allowed_urls: Optional[list[str]] = None,
    blocked_categories: Optional[list[dict]] = None,
    backup: bool = True,
    client_name: Optional[str] = None,
    client: Optional[MerakiClient] = None,
) -> ConfigResult:
    """Configura content filtering na network."""
    client = client or get_client()
    backup_path = None

    try:
        if backup and client_name:
            backup_path = backup_config(network_id, client_name, "content_filter", client)

        update_data = {}
        if blocked_urls is not None:
            update_data["blockedUrlPatterns"] = blocked_urls
        # ... (build payload)

        result = client.update_content_filtering(network_id, **update_data)

        return ConfigResult(
            success=True,
            action=ConfigAction.UPDATE,
            resource_type="content_filter",
            resource_id=network_id,
            message="Content filtering configurado",
            backup_path=backup_path,
            changes=update_data,
        )
    except APIError as e:
        return ConfigResult(success=False, ...)
```

**Conventions:**
- Always accept `backup=True` and `client_name` parameters
- Always create backup before WRITE operations
- Return `ConfigResult` with structured success/failure info
- Accept `Optional[MerakiClient]` for testability

### Step 4: `agent_router.py` -- Register in FUNCTION_REGISTRY

Add the new function to the `FUNCTION_REGISTRY` dict and to the agent's functions list so the router can dispatch calls.

```python
# agent_router.py
FUNCTION_REGISTRY = {
    # ... existing entries ...
    "discover_content_filtering": discovery.discover_content_filtering,
    "configure_content_filter": config.configure_content_filter,
}

# Add to appropriate agent functions list
NETWORK_ANALYST_FUNCTIONS.append("discover_content_filtering")
MERAKI_SPECIALIST_FUNCTIONS.append("configure_content_filter")
```

### Step 5: `agent_tools.py` -- Add Tool Schema + Safety Classification

Define the OpenAI function-calling schema and classify the tool's safety level.

```python
# agent_tools.py

# In TOOL_SAFETY dict:
TOOL_SAFETY["discover_content_filtering"] = SafetyLevel.SAFE
TOOL_SAFETY["configure_content_filter"] = SafetyLevel.MODERATE

# In MERAKI_SPECIALIST_TOOLS list:
{
    "type": "function",
    "function": {
        "name": "configure_content_filter",
        "description": "Configure content filtering (URL blocking, category blocking)",
        "parameters": {
            "type": "object",
            "properties": {
                "network_id": {"type": "string", "description": "Network ID"},
                "blocked_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URLs to block",
                },
                # ...
            },
            "required": ["network_id"],
            "additionalProperties": False,
        },
    },
}
```

### Step 6: `safety.py` -- Add Safety Classification

Register the tool in the safety layer for dry-run support and confirmation prompts.

```python
# safety.py
# In SAFETY_REGISTRY or equivalent:
WRITE_OPERATIONS["configure_content_filter"] = {
    "level": "moderate",
    "requires_confirmation": True,
    "supports_dry_run": True,
    "supports_undo": True,
}
```

### Step 7: `tests/` -- Add Tests

Create comprehensive tests covering:
- Happy path (successful API call)
- Error handling (APIError, 400, 404, 429)
- Backup creation
- Safety classification
- Tool schema validation

```python
# tests/test_content_filtering.py
class TestDiscoverContentFiltering:
    def test_returns_config(self, mock_client):
        result = discover_content_filtering("N_123", mock_client)
        assert "blockedUrlPatterns" in result

    def test_handles_unsupported_network(self, mock_client):
        mock_client.safe_call.return_value = {}
        result = discover_content_filtering("N_123", mock_client)
        assert result == {}

class TestConfigureContentFilter:
    def test_creates_backup(self, mock_client, tmp_path):
        result = configure_content_filter("N_123", blocked_urls=["example.com"], ...)
        assert result.backup_path is not None

    def test_safety_classification(self):
        assert get_tool_safety("configure_content_filter") == SafetyLevel.MODERATE
```

---

## Metrics & Goals

### Coverage Targets

| Phase | Target Coverage | New Methods | Estimated Effort | Timeline |
|---|---|---|---|---|
| Current (Epics 1-7) | ~3.5% (~30 methods) | -- | Done | Complete |
| Phase 1 (Epics 8-10) | ~15% (~130 methods) | ~55 api.py + ~37 other | ~90 SP | 6-8 sprints |
| Phase 2 (Epics 11-13) | ~35% (~300 methods) | ~65 api.py + ~38 other | ~75 SP | 5-7 sprints |
| Phase 3 (Epics 14-15) | ~50% (~430 methods) | ~50 api.py + ~22 other | ~50 SP | 4-5 sprints |

### Remaining 50%

The remaining ~425 endpoints are in categories that are either:
- **Deprecated / Legacy** -- Older API versions, superseded endpoints
- **Niche / Rarely Used** -- ESL specialized, Zigbee advanced, SM Apple DEP/VPP
- **Read-only analytics variants** -- Granular time-series breakdowns, per-device stats
- **Administrative** -- Org creation, org deletion, early access features

These will be added on-demand as customer requirements dictate, but are not prioritized for proactive implementation.

### Quality Metrics per Phase

| Metric | Target |
|---|---|
| Test coverage for new functions | >= 90% |
| All tool schemas pass `validate_tool_schema()` | 100% |
| All WRITE tools have backup support | 100% |
| All DANGEROUS tools require confirmation | 100% |
| Discovery functions integrated into `full_discovery()` | >= 80% |
| Tool schemas have `additionalProperties: False` | 100% |

### Success Criteria

- **Phase 1 complete:** A network engineer can use CNL to perform the 20 most common day-1 operations (VPN, IPS, content filtering, firmware, alerts, live tools, SNMP/syslog) without touching the Dashboard UI.
- **Phase 2 complete:** A network architect can use CNL for advanced platform operations (SD-WAN, templates, HA, camera analytics, sensors, advanced switching) covering 80% of enterprise use cases.
- **Phase 3 complete:** Full MDM/SM support, Insight monitoring, and all specialized product lines are accessible, making CNL a comprehensive Meraki management platform.

---

## Appendix A: Meraki SDK Module Mapping

For reference, the Meraki Python SDK organizes endpoints into these modules:

| SDK Module | CNL Category | Phase |
|---|---|---|
| `dashboard.organizations` | Organizations | 1-2 |
| `dashboard.networks` | Networks | 1-2 |
| `dashboard.devices` | Devices | 1 |
| `dashboard.appliance` | Appliance / MX | 1-2 |
| `dashboard.switch` | Switching / MS | 1-2 |
| `dashboard.wireless` | Wireless / MR | 1-2 |
| `dashboard.camera` | Camera / MV | 2-3 |
| `dashboard.cellularGateway` | Cellular Gateway / MG | 3 |
| `dashboard.sensor` | Sensor / MT | 2-3 |
| `dashboard.insight` | Insight | 3 |
| `dashboard.sm` | Systems Manager | 3 |

## Appendix B: Issue Detection Expansion

As new discovery functions are added, the `find_issues()` function in `discovery.py` should be expanded to detect additional issue types:

| Phase | New Issue Types |
|---|---|
| Phase 1 | `firmware_outdated`, `ips_disabled`, `amp_disabled`, `no_syslog_configured`, `no_snmp_configured`, `vpn_peer_down`, `content_filter_permissive`, `no_alerts_configured` |
| Phase 2 | `stp_inconsistent`, `no_ha_configured`, `rogue_aps_detected`, `sdwan_no_policy`, `sensor_alert_missing`, `poe_budget_exceeded`, `access_policy_missing` |
| Phase 3 | `sm_device_noncompliant`, `insight_app_degraded`, `mg_failover_untested`, `license_expiring` |

---

*Document generated 2026-02-08. Next review scheduled for Phase 1 kick-off.*
