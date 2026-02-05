# Meraki Workflow - Quick Start Guide

> Get up and running in 10 minutes. Copy, paste, execute.

---

## 1. INSTALLATION (2 min)

### Prerequisites

- Python 3.10 or higher
- Git
- Access to Cisco Meraki Dashboard

### Install

```bash
# Clone the repository
git clone https://github.com/jspetrucio/Meraki_workflow.git
cd Meraki_workflow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install package
pip install -e .
```

### Verify Installation

```bash
meraki --help
```

Expected output: List of available commands (profiles, discover, config, workflow, report, client).

---

## 2. GET CREDENTIALS (5 min)

### Get Your API Key

1. Go to [Meraki Dashboard](https://dashboard.meraki.com)
2. Navigate to **Organization > Settings**
3. Scroll to **Dashboard API access**
4. Check **Enable access to the Cisco Meraki Dashboard API**
5. Click **Generate new API key**
6. **COPY THE KEY IMMEDIATELY** (it only appears once!)

### Get Your Organization ID

**Option 1 - From URL:**
```
https://dashboard.meraki.com/o/123456/...
                               ^^^^^^
                               This is your Org ID
```

**Option 2 - Via API:**
```bash
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
     https://api.meraki.com/api/v1/organizations
```

### Configure Credentials

```bash
# Create credentials directory
mkdir -p ~/.meraki

# Create credentials file
cat > ~/.meraki/credentials << 'EOF'
[default]
api_key = YOUR_API_KEY_HERE
org_id = YOUR_ORG_ID_HERE

[client-name]
api_key = CLIENT_API_KEY
org_id = CLIENT_ORG_ID
EOF
```

Or use the interactive setup:

```bash
meraki profiles setup
```

### Validate Credentials

```bash
meraki profiles list
meraki profiles validate default
```

---

## 3. CLIENT ONBOARDING (3 min)

### Create Client Structure

```bash
meraki client new acme --profile default
```

This creates:
```
clients/acme/
├── discovery/     # Network snapshots
├── workflows/     # Automation workflows
├── reports/       # HTML/PDF reports
├── backups/       # Configuration backups
├── .env           # Client profile
└── changelog.md   # Change history
```

### Run Discovery

```bash
meraki discover full --client acme
```

### Generate First Report

```bash
meraki report discovery --client acme
```

---

## 4. NATURAL LANGUAGE EXAMPLES

### How It Works

When using Claude Code with this project, you speak naturally and the AI translates your intent into Meraki API calls.

```
You say: "Block device 192.168.1.50 from accessing youtube.com"
   ↓
AI Agent understands your intent
   ↓
Translates to: L7 firewall rule blocking youtube.com for that IP
   ↓
Executes via Meraki API
```

### Security Examples

| What You Say | What Happens |
|--------------|--------------|
| "Block traffic from device 192.168.1.50 to youtube.com" | Creates L7 firewall rule |
| "Deny telnet access on all switches" | Creates ACL blocking port 23 |
| "Block social media for the guest network" | L7 rule blocking social media category |
| "Allow only HTTPS from the server VLAN" | Firewall rule allowing only port 443 |
| "Block BitTorrent across the organization" | L7 application block |
| "Deny ICMP from external networks" | L3 firewall rule blocking ping |

### WiFi Examples

| What You Say | What Happens |
|--------------|--------------|
| "Create a guest WiFi with captive portal" | Configures SSID with splash page |
| "Set password 'Welcome2024' for SSID Corporate" | Updates PSK authentication |
| "Limit guest WiFi to 10Mbps per client" | Applies traffic shaping rule |
| "Hide the management SSID from broadcast" | Sets SSID visibility to hidden |
| "Enable WPA3 on the secure network" | Updates encryption settings |
| "Disable SSID number 3" | Disables the specified SSID |

### Network Examples

| What You Say | What Happens |
|--------------|--------------|
| "Create VLAN 100 for IoT devices at 10.100.0.0/24" | Creates VLAN with DHCP |
| "Set port 1 on Core-SW to VLAN 50" | Updates switch port configuration |
| "Enable PoE on ports 1-8 of Floor2-SW" | Enables Power over Ethernet |
| "Block VLAN 100 from reaching VLAN 10" | Creates inter-VLAN ACL rule |
| "Set port 24 as trunk with VLANs 10,20,30" | Configures trunk port |

### Monitoring Examples

| What You Say | What Happens |
|--------------|--------------|
| "Alert me when any device goes offline" | Creates monitoring workflow |
| "Show all offline devices" | Runs discovery and filters results |
| "Generate a network health report" | Creates HTML/PDF report |
| "Check firmware compliance" | Discovery + compliance analysis |
| "Compare network state from last week" | Compares two snapshots |
| "What problems did you find?" | Lists security and performance issues |

---

## 5. CLI COMMANDS REFERENCE

### Profile Management

```bash
# List all profiles
meraki profiles list

# Validate a specific profile
meraki profiles validate default

# Interactive credential setup
meraki profiles setup
```

### Client Management

```bash
# Create new client
meraki client new CLIENT_NAME --profile PROFILE_NAME

# List all clients
meraki client list

# Show client details
meraki client info CLIENT_NAME
```

### Discovery

```bash
# Full network discovery (saves snapshot)
meraki discover full --client CLIENT_NAME

# List saved snapshots
meraki discover list --client CLIENT_NAME

# Compare two snapshots
meraki discover compare --client CLIENT_NAME \
  --old snapshot_20240101_120000.json \
  --new snapshot_20240115_120000.json
```

### SSID Configuration

```bash
# Configure SSID with PSK
meraki config ssid -n N_123456789 --number 0 --name "Guest WiFi" \
  --enabled --auth psk --psk "SecurePassword123" -c CLIENT_NAME

# Disable an SSID
meraki config ssid -n N_123456789 --number 3 --disabled -c CLIENT_NAME

# Set VLAN for SSID
meraki config ssid -n N_123456789 --number 1 --vlan 100 -c CLIENT_NAME
```

### Firewall Configuration

```bash
# Block telnet (port 23)
meraki config firewall -n N_123456789 --policy deny --protocol tcp \
  --port 23 --comment "Block telnet" -c CLIENT_NAME

# Allow specific source to destination
meraki config firewall -n N_123456789 --policy allow --protocol tcp \
  --src 10.0.0.0/8 --dest 192.168.1.100/32 --port 443 -c CLIENT_NAME

# Block all ICMP
meraki config firewall -n N_123456789 --policy deny --protocol icmp -c CLIENT_NAME
```

### VLAN Configuration

```bash
# Create new VLAN
meraki config vlan -n N_123456789 --vlan-id 100 --name "IoT Devices" \
  --subnet 10.100.0.0/24 --gateway 10.100.0.1 -c CLIENT_NAME
```

### Workflows

```bash
# Create device offline alert workflow
meraki workflow create -t device-offline -c CLIENT_NAME --slack-channel "#alerts"

# Create firmware compliance workflow
meraki workflow create -t firmware-compliance -c CLIENT_NAME --email admin@company.com

# List workflows for client
meraki workflow list -c CLIENT_NAME
```

### Template Workflows (Clone + Patch)

```bash
# List available templates
meraki template list

# Get template details
meraki template info "Device Offline Handler"

# Clone template with custom variables
meraki template clone "Device Offline Handler" -c CLIENT_NAME \
  -n "ACME Offline Alert" -v slack_channel=#acme-alerts

# Validate a workflow JSON file
meraki template validate ./my-workflow.json
```

### Reports

```bash
# Generate HTML/PDF reports
meraki report discovery -c CLIENT_NAME          # HTML
meraki report discovery -c CLIENT_NAME --pdf    # PDF
meraki report changes -c CLIENT_NAME --days 30  # Changes report
```

### Debug Mode

Add `--debug` for verbose output: `meraki --debug discover full --client NAME`

---

## 6. CHEAT SHEET

| Task | Command |
|------|---------|
| Setup credentials | `meraki profiles setup` |
| Validate profile | `meraki profiles validate default` |
| New client | `meraki client new NAME --profile PROFILE` |
| List clients | `meraki client list` |
| Full discovery | `meraki discover full -c NAME` |
| List snapshots | `meraki discover list -c NAME` |
| Configure SSID | `meraki config ssid -n NET --number 0 --name "X" -c NAME` |
| Firewall rule | `meraki config firewall -n NET --policy deny --protocol tcp --port 23 -c NAME` |
| Create VLAN | `meraki config vlan -n NET --vlan-id 100 --name "X" --subnet X/24 --gateway X.1 -c NAME` |
| Create workflow | `meraki workflow create -t device-offline -c NAME` |
| Clone template | `meraki template clone "Name" -c NAME -n "New Name"` |
| HTML report | `meraki report discovery -c NAME` |
| PDF report | `meraki report discovery -c NAME --pdf` |

---

## 7. QUICK TROUBLESHOOTING

| Error | Solution |
|-------|----------|
| "API key not found" | Run `meraki profiles setup` or check `~/.meraki/credentials` |
| "Invalid API key" | Verify API enabled in Dashboard > Organization > Settings |
| "Rate limit exceeded" | Wait and retry (limit: 10 req/s, SDK handles automatically) |
| "Network not found" | Run `meraki discover full -c NAME` to see available networks |
| "Module not found" | Activate venv: `source venv/bin/activate && pip install -e .` |
| "Permission denied" | Run `chmod 600 ~/.meraki/credentials` |
| PDF not generating | Install WeasyPrint: `pip install weasyprint` |

### Workflow not appearing in Dashboard

Workflows cannot be created via API. You must:
1. Generate JSON with `meraki workflow create`
2. Go to **Dashboard > Organization > Configure > Workflows**
3. Click **Import Workflow** and select the JSON file

---

## Next Steps

- Read the full [User Manual](./user_manual.md) for advanced features
- Check [Workflow Design](./Workflow_Design.md) for automation patterns
- Explore the [Agent Instructions](./agents_instructions.md) for Claude Code integration

---

## Quick Links

- [Meraki Dashboard API Docs](https://developer.cisco.com/meraki/api-v1/)
- [Meraki Python SDK](https://github.com/meraki/dashboard-api-python)
- [Meraki Workflows Documentation](https://documentation.meraki.com/Platform_Management/Workflows)

---

**Developed with Claude Code (Opus 4.5)**
