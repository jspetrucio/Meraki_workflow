# @cisco/cnl - Cisco Neural Language

Natural language interface for Cisco Meraki network management.

## Installation

### Prerequisites

- **Python 3.10+** must be installed on your system
- **Node.js 18+** (for npm)

### Install via npm

```bash
# Global installation (recommended)
npm install -g @cisco/cnl

# Or use npx (no installation)
npx @cisco/cnl --help
```

The npm package will automatically:
1. Verify Python 3.10+ is available
2. Install the CNL Python package if not present
3. Set up the `cnl` command

### Install Python Manually

If Python is not installed:

**macOS:**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11
```

**Windows:**
Download from [python.org/downloads](https://www.python.org/downloads/)

## Usage

### Start Web UI

```bash
cnl
```

Opens the web interface at `http://localhost:3141`

### CLI Mode

```bash
cnl --cli --help
```

### Common Commands

```bash
# Show version
cnl --version

# Set up credentials
cnl profiles setup

# Discover network
cnl discover full --client acme

# Configure SSID
cnl config ssid --network N_123 --number 0 --name "Guest" --client acme

# Create workflow
cnl workflow create --template device-offline --client acme

# Generate report
cnl report discovery --client acme
```

## Features

- 🗣️ **Natural Language Interface** - Manage networks using plain English
- 🔍 **Network Discovery** - Automatic inventory of devices, SSIDs, VLANs
- ⚙️ **Configuration Management** - Update ACLs, Firewall rules, SSIDs via CLI
- 🤖 **Workflow Automation** - Create alerts, compliance checks, scheduled reports
- 📊 **Reporting** - Generate HTML/PDF reports for clients
- 🔐 **Multi-Tenant** - Manage multiple Meraki organizations

## Architecture

This npm package is a **thin wrapper** around the Python implementation:

```
@cisco/cnl (npm)
    ↓
  cnl.js (Node.js wrapper)
    ↓
  Python 3.10+ (runtime)
    ↓
  cnl (pip package)
    ↓
  Meraki Dashboard API
```

## Troubleshooting

### "Python 3.10+ not found"

Install Python 3.10 or later (see installation instructions above).

### "CNL package installation failed"

Try installing the Python package manually:

```bash
python3 -m pip install --user cnl
```

### "Command not found: cnl"

If installed globally, make sure npm's global bin directory is in your PATH:

```bash
npm config get prefix
```

Add `<prefix>/bin` to your PATH.

## Documentation

- **Quick Start**: [Quick Start Guide](https://github.com/cisco/cnl/blob/main/docs/quick-start.md)
- **User Manual**: [User Manual](https://github.com/cisco/cnl/blob/main/docs/user_manual.md)
- **API Reference**: [Meraki Dashboard API](https://developer.cisco.com/meraki/api-v1/)

## Support

- **Issues**: [GitHub Issues](https://github.com/cisco/cnl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cisco/cnl/discussions)

## License

MIT License - see [LICENSE](https://github.com/cisco/cnl/blob/main/LICENSE)

## Credits

Built with:
- [Meraki Dashboard API](https://developer.cisco.com/meraki/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Click](https://click.palletsprojects.com/)
- [Rich](https://rich.readthedocs.io/)
