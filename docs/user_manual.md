# Meraki Workflow - User Manual

> **Complete Guide to Configuring Meraki Networks Using Natural Language**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Supported Configurations](#2-supported-configurations)
3. [Not Supported / Limitations](#3-not-supported--limitations)
4. [Natural Language Examples](#4-natural-language-examples)
5. [Quick Reference Table](#5-quick-reference-table)
6. [Appendix](#6-appendix)

---

## 1. Introduction

### 1.1 What is Meraki Workflow?

Meraki Workflow is an automation system that allows you to configure Cisco Meraki networks using **natural language commands**. Instead of navigating through the Meraki Dashboard or writing API calls manually, you simply describe what you want to do in plain English.

**Example:**
```
"Block telnet on all switches"
```
This command automatically translates to the appropriate API calls to create ACL rules blocking TCP port 23 across your switch infrastructure.

### 1.2 How It Works

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Natural        │      │  AI Agent       │      │  Meraki API     │
│  Language       │ ───► │  (Specialist)   │ ───► │  (Dashboard)    │
│  Command        │      │  Translation    │      │  Execution      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **You speak naturally** → "Create a guest WiFi with captive portal"
2. **AI Agent interprets** → Understands intent, identifies parameters
3. **API executes** → Calls appropriate Meraki Dashboard API endpoints
4. **Confirmation returned** → You see the result and any issues

### 1.3 Getting Started

#### Prerequisites
- Meraki Dashboard API Key
- Organization ID
- Python 3.8+ installed

#### Initial Setup
```bash
# 1. Install the package
pip install -e .

# 2. Configure credentials
mkdir -p ~/.meraki
cat > ~/.meraki/credentials << 'EOF'
[your-client-name]
api_key = YOUR_API_KEY_HERE
org_id = YOUR_ORG_ID_HERE
EOF

# 3. Run discovery
meraki discover full --client your-client-name

# 4. View report
meraki report discovery --client your-client-name
```

---

## 2. Supported Configurations

### 2.1 MX - Security Appliance

The MX security appliance supports comprehensive configuration via API.

#### Firewall L3 Rules ✓

Configure Layer 3 firewall rules to control traffic flow.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Create rule | ✓ | Full support |
| Read rules | ✓ | Full support |
| Update rule | ✓ | Full support |
| Delete rule | ✓ | Full support |
| Reorder rules | ✓ | Full support |

**Example Commands:**
```
"Block all traffic from 192.168.1.0/24 to 10.0.0.0/8"
"Allow HTTPS (port 443) from any source"
"Create a deny-all default rule at the end"
"Block TCP ports 20-23 for the entire network"
```

#### Firewall L7 Rules ✓

Layer 7 application-aware firewall rules.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Read rules | ✓ | Full support |
| Update rules | ✓ | Full support |
| Application blocking | ✓ | By category or specific app |

**Example Commands:**
```
"Block BitTorrent traffic"
"Deny access to social media category"
"Block YouTube during business hours"
```

#### VLANs ✓

Full VLAN management for network segmentation.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Create VLAN | ✓ | Full support |
| Read VLANs | ✓ | Full support |
| Update VLAN | ✓ | Full support |
| Delete VLAN | ✓ | Full support |

**Example Commands:**
```
"Create VLAN 100 named 'IoT-Devices' with subnet 10.100.0.0/24"
"Update VLAN 50 to use DNS servers 8.8.8.8 and 8.8.4.4"
"Delete VLAN 200"
"List all VLANs in the network"
```

#### Traffic Shaping ✓

Bandwidth management and QoS rules.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Per-client limits | ✓ | Upload/Download |
| Application shaping | ✓ | By category |
| Custom rules | ✓ | Full support |

**Example Commands:**
```
"Limit each client to 10Mbps download"
"Prioritize VoIP traffic"
"Throttle video streaming to 5Mbps"
```

#### NAT Configuration ✓

Network Address Translation settings.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| 1:1 NAT | ✓ | Full support |
| 1:Many NAT | ✓ | Full support |
| Port Forwarding | ✓ | Full support |

**Example Commands:**
```
"Forward external port 8080 to internal 192.168.1.100:80"
"Create 1:1 NAT for server 10.0.0.50 to public IP"
```

---

### 2.2 MS - Switch

Meraki switches support extensive configuration through the API.

#### Access Control Lists (ACLs) ✓

Full ACL management for Layer 2/3 traffic control.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Create ACL | ✓ | Full support |
| Read ACLs | ✓ | Full support |
| Update ACL | ✓ | Full support |
| Delete ACL | ✓ | Full support |

**Example Commands:**
```
"Block port 23 (telnet) on all switches"
"Allow only VLAN 10 to communicate with VLAN 20"
"Create ACL to deny ICMP from guest network"
"Block all traffic from MAC address AA:BB:CC:DD:EE:FF"
```

#### Port Configuration ✓

Individual switch port settings.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Read port config | ✓ | Full support |
| Update port config | ✓ | Full support |
| VLAN assignment | ✓ | Access/Trunk |
| PoE settings | ✓ | Enable/Disable |
| Port enable/disable | ✓ | Full support |

**Example Commands:**
```
"Set port 1 on switch 'Core-SW' to VLAN 100"
"Configure ports 1-24 as access ports on VLAN 10"
"Enable PoE on ports 1-8"
"Disable port 48 on switch 'Floor2-SW'"
"Set port 25 as trunk allowing VLANs 10,20,30"
```

#### QoS Settings ✓

Quality of Service configuration.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| DSCP marking | ✓ | Full support |
| CoS mapping | ✓ | Full support |
| Trust settings | ✓ | Full support |

**Example Commands:**
```
"Set DSCP 46 for VoIP traffic on VLAN 100"
"Configure QoS trust mode on uplink ports"
```

#### STP Configuration ✓

Spanning Tree Protocol settings.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| STP enable/disable | ✓ | Full support |
| Root guard | ✓ | Per-port |
| BPDU guard | ✓ | Per-port |

**Example Commands:**
```
"Enable BPDU guard on access ports 1-24"
"Configure root guard on uplink port 48"
```

---

### 2.3 MR - Wireless

Comprehensive wireless configuration support.

#### SSID Configuration ✓

Manage up to 15 SSIDs (0-14) per network.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Create/Enable SSID | ✓ | SSIDs 0-14 |
| Disable SSID | ✓ | Full support |
| Update settings | ✓ | Full support |
| VLAN tagging | ✓ | Full support |

**Example Commands:**
```
"Create SSID 'Guest-WiFi' on slot 2"
"Enable SSID 'Corporate' and assign to VLAN 10"
"Disable SSID 5"
"Rename SSID 0 to 'Main-Office'"
```

#### Authentication ✓

Multiple authentication methods supported.

| Method | Supported | Notes |
|--------|-----------|-------|
| Open | ✓ | No authentication |
| PSK (WPA2/WPA3) | ✓ | Pre-shared key |
| 802.1X | ✓ | RADIUS integration |
| MAC-based | ✓ | Whitelist/Blacklist |

**Example Commands:**
```
"Set SSID 'Corporate' to use WPA2 with password 'SecurePass123'"
"Configure SSID 'Enterprise' with 802.1X using RADIUS server 10.0.0.100"
"Enable WPA3 on SSID 'Secure-Net'"
"Create open SSID 'Lobby' for guests"
```

#### Splash Pages ✓

Captive portal configuration.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Enable splash | ✓ | Full support |
| Click-through | ✓ | Simple acceptance |
| Sign-on | ✓ | Credentials required |
| Custom URL | ✓ | External portal |

**Example Commands:**
```
"Enable captive portal on SSID 'Guest'"
"Configure click-through splash page for visitors"
"Set custom splash URL to https://portal.company.com"
```

#### Bandwidth Limits ✓

Per-SSID and per-client bandwidth control.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Per-client limit | ✓ | Up/Down separate |
| Per-SSID limit | ✓ | Aggregate |
| Time-based | ✓ | Scheduling |

**Example Commands:**
```
"Limit guest WiFi clients to 5Mbps download, 2Mbps upload"
"Set maximum bandwidth for SSID 'IoT' to 100Mbps aggregate"
"Apply 10Mbps limit during business hours only"
```

#### Band Steering ✓

Optimize client distribution across bands.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Enable/Disable | ✓ | Full support |
| Mode selection | ✓ | Prefer 5GHz/6GHz |

**Example Commands:**
```
"Enable band steering on SSID 'Corporate'"
"Prefer 5GHz band for all SSIDs"
```

---

### 2.4 MV - Camera

Meraki cameras support configuration via API.

#### Quality & Resolution ✓

Video quality settings.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Resolution | ✓ | 720p to 4K |
| Quality mode | ✓ | Standard/Enhanced |
| Frame rate | ✓ | Full support |

**Example Commands:**
```
"Set camera 'Entrance-Cam' to 1080p resolution"
"Configure all cameras to enhanced quality mode"
"Set frame rate to 15fps for storage optimization"
```

#### Retention Settings ✓

Video storage configuration.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Retention days | ✓ | Based on license |
| Cloud archive | ✓ | If licensed |

**Example Commands:**
```
"Set retention to 30 days for all cameras"
"Configure camera 'Server-Room' for maximum retention"
```

#### Motion Detection ✓

Motion-based recording and alerts.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Enable/Disable | ✓ | Full support |
| Sensitivity | ✓ | Adjustable |
| Zones | ✓ | Define areas |

**Example Commands:**
```
"Enable motion detection on camera 'Parking-Lot'"
"Set high sensitivity for 'Warehouse' camera"
"Disable motion alerts for 'Lobby' camera"
```

---

### 2.5 Organization-Wide Settings

Settings that apply across the entire organization.

#### Alerts ✓

Network and device alerting.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Email alerts | ✓ | Full support |
| Webhook alerts | ✓ | Full support |
| Alert types | ✓ | Configurable |

**Example Commands:**
```
"Enable email alerts for device offline events"
"Configure webhook to https://alerts.company.com/meraki"
"Set alert for when APs go offline"
```

#### SNMP/Syslog ✓

Monitoring and logging configuration.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| SNMP v2c/v3 | ✓ | Full support |
| Syslog servers | ✓ | Multiple servers |

**Example Commands:**
```
"Enable SNMP v3 with user 'monitor'"
"Configure syslog server at 10.0.0.200"
"Add secondary syslog to 192.168.1.100"
```

#### Tags ✓

Device and network tagging.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| Add tags | ✓ | Full support |
| Remove tags | ✓ | Full support |
| Tag-based filtering | ✓ | Full support |

**Example Commands:**
```
"Tag all floor 2 switches with 'floor-2'"
"Remove tag 'legacy' from all devices"
"List all devices tagged 'critical'"
```

#### Firmware ✓

Firmware management.

| Operation | Supported | Notes |
|-----------|-----------|-------|
| View versions | ✓ | Full support |
| Schedule upgrade | ✓ | Full support |
| Check compliance | ✓ | Full support |

**Example Commands:**
```
"Check firmware versions for all MR devices"
"Schedule firmware upgrade for next maintenance window"
"Show devices with outdated firmware"
```

---

## 3. Not Supported / Limitations

### 3.1 Workflows (JSON Export Only) ✗

**Limitation:** Workflows cannot be created or modified via the Meraki Dashboard API.

**Workaround:**
1. Use the `workflow-creator` agent to generate workflow JSON
2. Manually import the JSON into Meraki Dashboard
3. Navigate to: Organization → Workflows → Import

**Example:**
```
"Create a workflow for device offline notification"
→ Generates JSON file at clients/{name}/workflows/
→ You must import this manually into Dashboard
```

### 3.2 Organization Creation ✗

**Limitation:** New organizations cannot be created via API.

**Workaround:** Create organizations through Meraki Dashboard manually.

### 3.3 Network Creation ✗

**Limitation:** New networks cannot be created via API for most use cases.

**Note:** Some MSP accounts may have limited network creation capabilities.

### 3.4 License Modifications ✗

**Limitation:** License management is not available through the API.

**Workaround:** Manage licenses through Meraki Dashboard or Meraki support.

### 3.5 Advanced RF Features ✗

**Limitation:** Some advanced RF tuning features have limited API support.

| Feature | Status |
|---------|--------|
| Manual channel selection | Partial |
| Power level fine-tuning | Partial |
| Antenna configuration | Limited |
| RF profiles | Limited |

### 3.6 Rate Limits

**Constraint:** Meraki API has a rate limit of **10 requests per second per organization**.

**Impact:**
- Large bulk operations may take longer
- The SDK handles rate limiting automatically
- Discovery of large networks is batched

---

## 4. Natural Language Examples

### 4.1 SSID Commands

```
# Creating SSIDs
"Create SSID 'Guest-WiFi' with captive portal"
"Set up a new SSID called 'Corporate' with WPA2"
"Enable SSID 3 and name it 'IoT-Network'"

# Configuring Authentication
"Set password 'Welcome123' for SSID 'Guest'"
"Enable WPA3 on SSID 2"
"Configure 802.1X for SSID 'Enterprise' using RADIUS 10.0.0.100"

# Bandwidth Management
"Set bandwidth limit of 10Mbps for SSID 0"
"Limit guest WiFi to 5Mbps download per client"
"Remove bandwidth limits from SSID 'Corporate'"

# VLAN Assignment
"Assign SSID 'Guest' to VLAN 100"
"Tag SSID 'IoT' with VLAN 200"
"Use VLAN 10 for SSID 'Corporate'"

# Visibility and Status
"Hide SSID 'Management' from broadcast"
"Disable SSID 5"
"Enable all SSIDs on the network"
```

### 4.2 Firewall Commands

```
# Blocking Traffic
"Block telnet on all networks"
"Deny SSH access from external sources"
"Block all traffic to IP 192.168.1.100"
"Deny TCP port range 135-139"

# Allowing Traffic
"Allow HTTPS from 10.0.0.0/8"
"Permit SSH only from management VLAN"
"Allow ping to 8.8.8.8 for testing"

# Application Filtering (L7)
"Block BitTorrent across the organization"
"Deny access to social media"
"Block gaming applications"
"Restrict video streaming bandwidth"

# Default Rules
"Create deny-all default rule"
"Set default action to allow with logging"
```

### 4.3 VLAN Commands

```
# Creating VLANs
"Create VLAN 100 for IoT at 10.100.0.0/24"
"Add VLAN 50 named 'Servers' with subnet 10.50.0.0/24"
"Set up VLAN 200 for guest network"

# Modifying VLANs
"Update VLAN 50 DNS to 8.8.8.8"
"Change VLAN 100 gateway to 10.100.0.1"
"Rename VLAN 50 to 'Data-Center'"

# DHCP Settings
"Enable DHCP on VLAN 100 with range 10.100.0.100-10.100.0.200"
"Set DHCP lease time to 8 hours for VLAN 50"
"Add DHCP reservation for MAC AA:BB:CC:DD:EE:FF on VLAN 10"

# Deleting VLANs
"Delete VLAN 200"
"Remove unused VLANs"
```

### 4.4 ACL Commands

```
# Basic Blocking
"Block port 23 on switches"
"Deny telnet and SSH from guest VLAN"
"Block all traffic from MAC AA:BB:CC:DD:EE:FF"

# Inter-VLAN Rules
"Allow only VLAN 10 to access VLAN 20"
"Block VLAN 100 from reaching VLAN 10"
"Permit VLAN 50 to access servers on VLAN 60"

# Protocol-Specific
"Block ICMP from guest network"
"Allow only HTTP and HTTPS from VLAN 100"
"Deny UDP port 53 except to approved DNS servers"

# IP-Based Rules
"Block access to 192.168.1.0/24 from guest network"
"Allow 10.0.0.0/8 to communicate with 172.16.0.0/12"
```

### 4.5 Switch Port Commands

```
# VLAN Assignment
"Set port 1 to VLAN 100"
"Configure ports 1-24 as access ports on VLAN 10"
"Set port 48 as trunk allowing VLANs 10,20,30"

# PoE Management
"Enable PoE on ports 1-8"
"Disable PoE on port 24"
"Set PoE priority to high on ports 1-4"

# Port Status
"Disable port 12 on switch Core-SW"
"Enable all ports on Floor-2 switch"
"Show status of all ports"

# Link Configuration
"Set port 48 to 10Gbps"
"Configure port 25 for auto-negotiation"
"Enable jumbo frames on uplink ports"

# Security
"Enable BPDU guard on ports 1-24"
"Configure root guard on port 48"
"Enable storm control on access ports"
```

### 4.6 Camera Commands

```
# Quality Settings
"Set camera 'Entrance' to 1080p"
"Configure 4K resolution for 'Server-Room' camera"
"Reduce quality to 720p for bandwidth savings"

# Motion Detection
"Enable motion detection on all cameras"
"Set high sensitivity for 'Warehouse' camera"
"Configure motion zones for 'Parking' camera"

# Retention
"Set 30-day retention for all cameras"
"Configure maximum retention for critical areas"

# Status
"Show all offline cameras"
"List cameras with storage warnings"
```

### 4.7 Discovery Commands

```
# Full Discovery
"Analyze this client's network"
"Run complete discovery for client 'acme'"
"Show me everything about this organization"

# Device Status
"Show all offline devices"
"List devices that haven't checked in recently"
"Find devices with issues"

# Specific Queries
"List all switches in the network"
"Show MR access points and their status"
"Count devices by type"

# Compliance Checks
"Check firmware compliance"
"Show devices with outdated firmware"
"List security issues found"

# Reporting
"Generate network report"
"Create PDF summary of the network"
"Export discovery results to HTML"
```

---

## 5. Quick Reference Table

### Feature Support Matrix

| Category | Feature | Create | Read | Update | Delete |
|----------|---------|--------|------|--------|--------|
| **MX Firewall** | L3 Rules | ✓ | ✓ | ✓ | ✓ |
| | L7 Rules | - | ✓ | ✓ | - |
| | VLANs | ✓ | ✓ | ✓ | ✓ |
| | Traffic Shaping | ✓ | ✓ | ✓ | ✓ |
| | NAT/Port Forward | ✓ | ✓ | ✓ | ✓ |
| **MS Switch** | ACLs | ✓ | ✓ | ✓ | ✓ |
| | Port Config | - | ✓ | ✓ | - |
| | QoS | ✓ | ✓ | ✓ | ✓ |
| | STP Settings | - | ✓ | ✓ | - |
| **MR Wireless** | SSIDs (0-14) | ✓ | ✓ | ✓ | ✓* |
| | Authentication | ✓ | ✓ | ✓ | - |
| | Splash Pages | ✓ | ✓ | ✓ | ✓ |
| | Bandwidth Limits | ✓ | ✓ | ✓ | ✓ |
| | Band Steering | - | ✓ | ✓ | - |
| **MV Camera** | Quality/Resolution | - | ✓ | ✓ | - |
| | Retention | - | ✓ | ✓ | - |
| | Motion Detection | - | ✓ | ✓ | - |
| **Organization** | Alerts | ✓ | ✓ | ✓ | ✓ |
| | SNMP/Syslog | ✓ | ✓ | ✓ | ✓ |
| | Tags | ✓ | ✓ | ✓ | ✓ |
| | Firmware | - | ✓ | ✓ | - |

*SSIDs can be disabled but not truly deleted (slots 0-14 always exist)

### Not Supported Features

| Feature | Reason | Workaround |
|---------|--------|------------|
| Workflows | No API support | JSON export + manual import |
| Organization Creation | Dashboard only | Create manually |
| Network Creation | Limited API | Dashboard or MSP portal |
| License Management | No API support | Dashboard or support |
| Advanced RF Tuning | Partial support | Use Dashboard |

---

## 6. Appendix

### 6.1 API Rate Limits

| Metric | Limit |
|--------|-------|
| Requests per second | 10 per organization |
| Burst allowance | Short bursts allowed |
| Daily limit | None (based on rate) |

**Best Practices:**
- The Meraki Python SDK handles rate limiting automatically
- Large operations are batched to stay within limits
- Discovery operations may take longer for large networks

### 6.2 Error Handling

| Error | Meaning | Solution |
|-------|---------|----------|
| 401 Unauthorized | Invalid API key | Check credentials in ~/.meraki/credentials |
| 403 Forbidden | No permission | Verify API key has required permissions |
| 404 Not Found | Resource doesn't exist | Verify network/device ID |
| 429 Too Many Requests | Rate limited | Wait and retry (SDK handles this) |
| 500 Server Error | Meraki API issue | Retry or check status.meraki.com |

### 6.3 Troubleshooting

#### "API key not found"
```bash
# Verify credentials file exists
cat ~/.meraki/credentials

# Should show:
# [profile-name]
# api_key = your_key_here
# org_id = your_org_id
```

#### "Organization not found"
```bash
# Verify org ID is correct
# Find it in Dashboard URL: dashboard.meraki.com/o/XXXXXX/...
# The XXXXXX is your org ID
```

#### "Network not found"
```bash
# Run discovery to get network IDs
meraki discover full --client your-client

# Check clients/your-client/discovery/ for results
```

#### "Rate limit exceeded"
- The SDK handles this automatically
- For bulk operations, expect some delay
- Check Meraki Dashboard for API call analytics

### 6.4 Getting Help

- **Meraki API Documentation:** https://developer.cisco.com/meraki/api-v1/
- **Meraki Community:** https://community.meraki.com/
- **API Status:** https://status.meraki.com/

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-04 | Initial release |

---

**Developed with Claude Code (Opus 4.5)**
