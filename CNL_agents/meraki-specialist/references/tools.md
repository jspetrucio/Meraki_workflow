# Reference: tools

## Propósito
Mapeamento completo de tool_name → endpoint Meraki Dashboard API.
Consultado pelo task_executor para resolver qual API call fazer.

---

## Convenção

- **tool_name:** snake_case, formato `{ação}_{recurso}`
- **endpoint:** Path relativo à base URL `https://api.meraki.com/api/v1`
- **scope:** org = organização, net = network, dev = device

---

## MX — Security Appliance

| Tool Name | Method | Endpoint | Scope |
|-----------|--------|----------|-------|
| get_l3_firewall_rules | GET | `/networks/{netId}/appliance/firewall/l3FirewallRules` | net |
| update_l3_firewall_rules | PUT | `/networks/{netId}/appliance/firewall/l3FirewallRules` | net |
| get_l7_firewall_rules | GET | `/networks/{netId}/appliance/firewall/l7FirewallRules` | net |
| update_l7_firewall_rules | PUT | `/networks/{netId}/appliance/firewall/l7FirewallRules` | net |
| get_1to1_nat_rules | GET | `/networks/{netId}/appliance/firewall/oneToOneNatRules` | net |
| update_1to1_nat_rules | PUT | `/networks/{netId}/appliance/firewall/oneToOneNatRules` | net |
| get_1tomany_nat_rules | GET | `/networks/{netId}/appliance/firewall/oneToManyNatRules` | net |
| update_1tomany_nat_rules | PUT | `/networks/{netId}/appliance/firewall/oneToManyNatRules` | net |
| get_port_forwarding_rules | GET | `/networks/{netId}/appliance/firewall/portForwardingRules` | net |
| update_port_forwarding_rules | PUT | `/networks/{netId}/appliance/firewall/portForwardingRules` | net |
| get_s2s_vpn_peers | GET | `/organizations/{orgId}/appliance/vpn/thirdPartyVPNPeers` | org |
| update_s2s_vpn_peers | PUT | `/organizations/{orgId}/appliance/vpn/thirdPartyVPNPeers` | org |
| get_client_vpn | GET | `/networks/{netId}/appliance/vpn/clientVpn` | net |
| update_client_vpn | PUT | `/networks/{netId}/appliance/vpn/clientVpn` | net |
| get_traffic_shaping_rules | GET | `/networks/{netId}/appliance/trafficShaping/rules` | net |
| update_traffic_shaping_rules | PUT | `/networks/{netId}/appliance/trafficShaping/rules` | net |
| get_content_filtering | GET | `/networks/{netId}/appliance/contentFiltering` | net |
| update_content_filtering | PUT | `/networks/{netId}/appliance/contentFiltering` | net |
| get_intrusion_settings | GET | `/networks/{netId}/appliance/security/intrusion` | net |
| update_intrusion_settings | PUT | `/networks/{netId}/appliance/security/intrusion` | net |
| get_malware_settings | GET | `/networks/{netId}/appliance/security/malware` | net |
| update_malware_settings | PUT | `/networks/{netId}/appliance/security/malware` | net |

## MS — Switch

| Tool Name | Method | Endpoint | Scope |
|-----------|--------|----------|-------|
| get_switch_ports | GET | `/devices/{serial}/switch/ports` | dev |
| get_switch_port | GET | `/devices/{serial}/switch/ports/{portId}` | dev |
| update_switch_port | PUT | `/devices/{serial}/switch/ports/{portId}` | dev |
| get_switch_acls | GET | `/networks/{netId}/switch/accessControlLists` | net |
| update_switch_acls | PUT | `/networks/{netId}/switch/accessControlLists` | net |
| get_vlans | GET | `/networks/{netId}/vlans` | net |
| get_vlan | GET | `/networks/{netId}/vlans/{vlanId}` | net |
| create_vlan | POST | `/networks/{netId}/vlans` | net |
| update_vlan | PUT | `/networks/{netId}/vlans/{vlanId}` | net |
| delete_vlan | DELETE | `/networks/{netId}/vlans/{vlanId}` | net |
| get_qos_rules | GET | `/networks/{netId}/switch/qosRules` | net |
| create_qos_rule | POST | `/networks/{netId}/switch/qosRules` | net |
| update_qos_rule | PUT | `/networks/{netId}/switch/qosRules/{qosRuleId}` | net |
| get_qos_order | GET | `/networks/{netId}/switch/qosRules/order` | net |
| update_qos_order | PUT | `/networks/{netId}/switch/qosRules/order` | net |
| get_stp | GET | `/networks/{netId}/switch/stp` | net |
| update_stp | PUT | `/networks/{netId}/switch/stp` | net |
| get_storm_control | GET | `/networks/{netId}/switch/stormControl` | net |
| update_storm_control | PUT | `/networks/{netId}/switch/stormControl` | net |
| get_port_schedules | GET | `/networks/{netId}/switch/portSchedules` | net |
| create_port_schedule | POST | `/networks/{netId}/switch/portSchedules` | net |
| get_dhcp_server | GET | `/devices/{serial}/switch/routing/interfaces/{interfaceId}/dhcp` | dev |
| update_dhcp_server | PUT | `/devices/{serial}/switch/routing/interfaces/{interfaceId}/dhcp` | dev |

## MR — Wireless

| Tool Name | Method | Endpoint | Scope |
|-----------|--------|----------|-------|
| get_ssids | GET | `/networks/{netId}/wireless/ssids` | net |
| get_ssid | GET | `/networks/{netId}/wireless/ssids/{number}` | net |
| update_ssid | PUT | `/networks/{netId}/wireless/ssids/{number}` | net |
| get_splash_settings | GET | `/networks/{netId}/wireless/ssids/{number}/splash/settings` | net |
| update_splash_settings | PUT | `/networks/{netId}/wireless/ssids/{number}/splash/settings` | net |
| get_rf_profiles | GET | `/networks/{netId}/wireless/rfProfiles` | net |
| create_rf_profile | POST | `/networks/{netId}/wireless/rfProfiles` | net |
| update_rf_profile | PUT | `/networks/{netId}/wireless/rfProfiles/{rfProfileId}` | net |
| get_bluetooth_settings | GET | `/networks/{netId}/wireless/bluetooth/settings` | net |
| update_bluetooth_settings | PUT | `/networks/{netId}/wireless/bluetooth/settings` | net |

## MV — Camera

| Tool Name | Method | Endpoint | Scope |
|-----------|--------|----------|-------|
| get_camera_quality | GET | `/devices/{serial}/camera/qualityAndRetention` | dev |
| update_camera_quality | PUT | `/devices/{serial}/camera/qualityAndRetention` | dev |
| get_camera_zones | GET | `/devices/{serial}/camera/analytics/zones` | dev |
| get_camera_sense | GET | `/devices/{serial}/camera/sense` | dev |
| update_camera_sense | PUT | `/devices/{serial}/camera/sense` | dev |

## Geral — Cross-device

| Tool Name | Method | Endpoint | Scope |
|-----------|--------|----------|-------|
| get_organizations | GET | `/organizations` | — |
| get_networks | GET | `/organizations/{orgId}/networks` | org |
| get_network | GET | `/networks/{netId}` | net |
| get_devices | GET | `/networks/{netId}/devices` | net |
| get_device | GET | `/devices/{serial}` | dev |
| get_device_statuses | GET | `/organizations/{orgId}/devices/statuses` | org |
| get_clients | GET | `/networks/{netId}/clients` | net |
| get_alert_settings | GET | `/networks/{netId}/alerts/settings` | net |
| update_alert_settings | PUT | `/networks/{netId}/alerts/settings` | net |
| get_snmp | GET | `/networks/{netId}/snmp` | net |
| update_snmp | PUT | `/networks/{netId}/snmp` | net |
| get_syslog_servers | GET | `/networks/{netId}/syslogServers` | net |
| update_syslog_servers | PUT | `/networks/{netId}/syslogServers` | net |
| get_firmware_upgrades | GET | `/networks/{netId}/firmwareUpgrades` | net |
| update_firmware_upgrades | PUT | `/networks/{netId}/firmwareUpgrades` | net |
| get_webhooks | GET | `/networks/{netId}/webhooks/httpServers` | net |
| create_webhook | POST | `/networks/{netId}/webhooks/httpServers` | net |
| get_licenses_overview | GET | `/organizations/{orgId}/licenses/overview` | org |

---

## Total: 63 tools mapeadas
