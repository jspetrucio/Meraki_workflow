# CNL pip Distribution

> **Story 6.1** - Package CNL for distribution via pip

---

## Overview

CNL (Cisco Neural Language) is now installable as a Python package via pip. This document describes the packaging structure and usage.

## Installation

### Development Mode (Editable Install)

```bash
cd /path/to/Meraki_Workflow
pip install -e .
```

### From Source

```bash
pip install .
```

### From PyPI (Future)

```bash
pip install cnl
```

---

## Package Structure

```
cnl/
├── pyproject.toml          # Package configuration
├── setup.py                # Fallback for older pip versions
├── MANIFEST.in             # Non-Python file inclusion
├── scripts/
│   ├── __version__.py      # Version (0.1.0)
│   ├── cli.py              # Entry point
│   ├── server.py           # FastAPI server
│   ├── build.sh            # Build script
│   └── ...                 # Other modules
├── templates/              # Workflow templates
├── frontend/dist/          # React build (when available)
└── .claude/agents/         # Agent definitions
```

---

## CLI Commands

### Basic Usage

```bash
# Show version
cnl --version

# Start web server (default behavior)
cnl

# Start server with custom port
cnl serve --port 8000 --host 0.0.0.0

# CLI-only mode (no web server)
cnl --cli
```

### Available Commands

All original CLI commands are preserved:

```bash
# Profile management
cnl profiles list
cnl profiles setup
cnl profiles validate <name>

# Discovery
cnl discover full --client <name>
cnl discover list --client <name>
cnl discover compare --client <name> --old <file> --new <file>

# Configuration
cnl config ssid --network <id> --number <n> --name <name> -c <client>
cnl config firewall --network <id> --policy <allow|deny> -c <client>
cnl config vlan --network <id> --vlan-id <n> --name <name> -c <client>

# Workflows
cnl workflow create --template <name> --client <name>
cnl workflow list --client <name>

# Templates
cnl template list
cnl template info <name>
cnl template clone <name> --client <name> --name <new-name>
cnl template validate <file>

# Reports
cnl report discovery --client <name> [--pdf]
cnl report changes --client <name> [--days <n>]

# Client management
cnl client new <name>
cnl client list
cnl client info <name>

# Server
cnl serve [--host <host>] [--port <port>]
```

---

## Dependencies

### Core Dependencies

- **meraki>=1.53.0** - Cisco Meraki Dashboard API SDK
- **fastapi>=0.115.0** - Web API framework
- **uvicorn>=0.34.0** - ASGI server
- **litellm>=1.50.0** - LLM provider abstraction
- **pydantic>=2.0.0** - Data validation
- **pyyaml>=6.0.0** - YAML configuration
- **cryptography>=42.0.0** - Secure credential storage
- **httpx>=0.27.0** - HTTP client
- **click>=8.1.0** - CLI framework
- **rich>=13.0.0** - Rich terminal output
- **jinja2>=3.1.0** - Template engine
- **python-dotenv>=1.0.0** - Environment variables

### Optional Dependencies

```bash
# PDF report generation
pip install cnl[pdf]

# Development tools
pip install cnl[dev]
```

---

## Building from Source

### Prerequisites

```bash
pip install build wheel
```

### Build Script

```bash
# Build frontend + Python package
./scripts/build.sh

# Or manually
python -m build
```

### Output

```
dist/
├── cnl-0.1.0-py3-none-any.whl    # Wheel (preferred)
└── cnl-0.1.0.tar.gz              # Source distribution
```

---

## Server Behavior

### Default Launch (cnl without arguments)

```bash
cnl
```

**Output:**
```
Starting CNL Server...

Access the web interface at: http://localhost:3141
Press Ctrl+C to stop the server
```

The server will:
1. Load settings from `~/.cnl/settings.yaml`
2. Start FastAPI on port 3141
3. Serve React frontend from `frontend/dist/`
4. Provide REST API at `/api/v1/`

### CLI-Only Mode

```bash
cnl --cli
```

Enters Click CLI without starting the web server. Use this mode for:
- Scripting and automation
- Headless environments
- CI/CD pipelines

### Custom Server Options

```bash
# Custom port
cnl serve --port 8000

# Bind to all interfaces
cnl serve --host 0.0.0.0 --port 3141

# Debug mode
cnl --debug serve
```

---

## Configuration

### Meraki Credentials

Stored in `~/.meraki/credentials`:

```ini
[default]
api_key = YOUR_API_KEY
org_id = YOUR_ORG_ID

[client-name]
api_key = CLIENT_API_KEY
org_id = CLIENT_ORG_ID
```

### Application Settings

Stored in `~/.cnl/settings.yaml` (auto-created on first run):

```yaml
port: 3141
meraki_profile: default
ai_provider: anthropic
ai_api_key: sk-...
n8n_enabled: false
n8n_url: http://localhost:5678
n8n_api_key: ""
```

---

## REST API Endpoints

### Health

```bash
GET /api/v1/health
GET /api/v1/status
```

### Discovery

```bash
POST /api/v1/discovery/run
GET  /api/v1/discovery/snapshots
GET  /api/v1/discovery/snapshots/:id
POST /api/v1/discovery/compare
```

### Configuration

```bash
POST /api/v1/config/ssid
POST /api/v1/config/firewall
POST /api/v1/config/vlan
POST /api/v1/config/acl
```

### Workflows

```bash
GET  /api/v1/workflows
POST /api/v1/workflows
GET  /api/v1/workflows/:id
PUT  /api/v1/workflows/:id
DELETE /api/v1/workflows/:id
```

### Reports

```bash
POST /api/v1/reports/discovery
POST /api/v1/reports/changes
GET  /api/v1/reports/:id
```

### Profiles

```bash
GET  /api/v1/profiles
POST /api/v1/profiles
GET  /api/v1/profiles/:name
PUT  /api/v1/profiles/:name
DELETE /api/v1/profiles/:name
POST /api/v1/profiles/:name/validate
```

### Settings

```bash
GET /api/v1/settings
PUT /api/v1/settings
POST /api/v1/settings/test-n8n
```

---

## Version Information

**Current Version:** 0.1.0

Version is defined in `scripts/__version__.py`:

```python
__version__ = "0.1.0"
```

---

## Frontend Integration

### Development Mode

Frontend runs separately on Vite dev server:

```bash
cd frontend
npm run dev
```

Access at: http://localhost:5173

### Production Build

Frontend is bundled with the Python package:

```bash
cd frontend
npm run build  # Creates frontend/dist/
```

The FastAPI server automatically serves the built frontend at `/`.

### Graceful Degradation

If `frontend/dist/` doesn't exist:
- Server still starts normally
- API endpoints work at `/api/v1/`
- Frontend returns 404 (expected until Story 2.1 is complete)

---

## Publishing to PyPI

### Prerequisites

```bash
pip install twine
```

### Build and Publish

```bash
# Build distributions
python -m build

# Test with TestPyPI first
twine upload --repository testpypi dist/*

# Verify installation
pip install -i https://test.pypi.org/simple/ cnl

# Publish to production PyPI
twine upload dist/*
```

### CI/CD (Story 6.5)

Automated publishing will be implemented in Story 6.5 with:
- GitHub Actions workflow
- Automated version bumping
- TestPyPI validation before production
- Release notes generation

---

## Known Issues

1. **Frontend Not Available Yet** (Story 2.1)
   - Build script gracefully skips frontend build
   - Server handles missing frontend/dist/ gracefully

2. **Browser Auto-Open**
   - Currently server prints URL but doesn't auto-open browser
   - Implement in future version with `webbrowser.open()`

3. **Version Sync**
   - Manual version management for now
   - Will sync with Tauri desktop app in Story 6.5

---

## Development Workflow

### Install in Editable Mode

```bash
pip install -e .
```

Changes to Python code are immediately reflected.

### Run Tests

```bash
pytest tests/ -v
```

### Lint and Format

```bash
ruff check scripts/
ruff format scripts/
```

### Type Checking

```bash
mypy scripts/
```

---

## File Manifest

### Created Files

- `pyproject.toml` - Package configuration
- `scripts/__version__.py` - Version source
- `MANIFEST.in` - File inclusion rules
- `scripts/build.sh` - Build automation

### Modified Files

- `scripts/cli.py` - Entry point with version flag and server launch

### Preserved Files

- `setup.py` - Fallback for older pip versions
- All existing scripts/ modules
- All existing CLI commands

---

## Next Steps

1. **Story 2.1: React Frontend** - Complete UI development
2. **Story 6.5: CI/CD Pipeline** - Automated builds and publishing
3. **PyPI Publication** - Make package publicly available
4. **Documentation** - Comprehensive user and API docs

---

**Last Updated:** 2026-02-05
**Story:** 6.1
**Agent:** @devops (Claude Sonnet 4.5)
