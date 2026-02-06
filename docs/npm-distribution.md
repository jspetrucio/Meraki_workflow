# CNL npm Distribution Package

## Overview

The `@cisco/cnl` npm package provides a **thin wrapper** around the Python-based CNL CLI, making it easy for Node.js users to install and use CNL without manually managing Python packages.

## Architecture

```
User runs: npx @cisco/cnl
    ↓
npm downloads @cisco/cnl package
    ↓
Node.js entry point (cnl.js)
    ↓
Check system Python 3.10+
    ↓
Install CNL pip package (if needed)
    ↓
Execute: cnl [args...]
    ↓
Python CLI (scripts/cli.py)
    ↓
Meraki Dashboard API
```

## Package Contents

| File | Purpose |
|------|---------|
| `bin/cnl.js` | Main CLI entry point - forwards to Python CLI |
| `lib/check-python.js` | Detects Python 3.10+ on system |
| `lib/install.js` | Post-install hook - installs pip package |
| `package.json` | npm package configuration |
| `README.md` | User-facing documentation |

## Installation Flow

### 1. User installs package

```bash
npm install -g @cisco/cnl
```

### 2. Post-install hook runs

The `postinstall` script (`lib/install.js`) automatically:
- Checks for Python 3.10+
- Verifies if `cnl` pip package is installed
- Installs it via `pip install --user cnl` if missing

### 3. CLI wrapper executes

When user runs `cnl`:
- `bin/cnl.js` validates Python is available
- Ensures CNL package is installed
- Spawns the `cnl` command with forwarded arguments

## Key Features

### Lightweight
- Package size: **~4 KB**
- No bundled dependencies
- No embedded Python binary

### Secure
- Uses `execFileSync()` with array arguments (no shell injection)
- No user input passed to shell
- Validates Python version before execution

### User-Friendly
- Automatic installation of Python dependencies
- Clear error messages if Python not found
- Works on macOS, Linux, Windows

### Transparent
- All CLI arguments forwarded to Python implementation
- Maintains full compatibility with pip-installed version
- No behavioral differences

## Requirements

### System Requirements
- **Node.js 18+** (for npm/npx)
- **Python 3.10+** (must be pre-installed)

### Python Installation

Users must have Python 3.10+ installed:

**macOS:**
```bash
brew install python@3.11
```

**Ubuntu:**
```bash
sudo apt install python3.11
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

## Usage Examples

### Via npm (global install)

```bash
# Install once
npm install -g @cisco/cnl

# Use anywhere
cnl --help
cnl --version
cnl discover full --client acme
```

### Via npx (no installation)

```bash
# Downloads and runs on-demand
npx @cisco/cnl --help
npx @cisco/cnl discover full --client acme
```

## Error Handling

The wrapper provides helpful error messages:

### Python not found
```
✗ Python 3.10+ is required but not found

Please install Python 3.10 or later:
  macOS:   brew install python@3.11
  Ubuntu:  sudo apt install python3.11
  Windows: https://www.python.org/downloads/
```

### CNL package installation fails
```
✗ Failed to install CNL package

Try installing manually:
  python3 -m pip install --user cnl
```

### CNL command not in PATH
```
CNL command not in PATH, trying alternate method...
```
(Falls back to `python3 -m scripts.cli`)

## Development

### Local Testing

```bash
cd npm/

# Create package tarball
npm pack

# Install locally
npm install -g ./cisco-cnl-0.1.0.tgz

# Test
cnl --help

# Uninstall
npm uninstall -g @cisco/cnl
```

### Testing Python Detection

```bash
cd npm/
node lib/check-python.js
```

Expected output:
```
✓ Python found: Python 3.11.5
  Path: /usr/local/bin/python3
```

## Publishing

See [PUBLISHING.md](../npm/PUBLISHING.md) for detailed instructions.

Quick reference:

```bash
cd npm/

# Verify package contents
npm pack --dry-run

# Publish (first time)
npm publish --access public

# Publish update
npm version patch
npm publish
```

## Comparison: npm vs pip Installation

| Aspect | npm Package | pip Package |
|--------|-------------|-------------|
| **Target Users** | Node.js developers | Python developers |
| **Installation** | `npm install -g @cisco/cnl` | `pip install cnl` |
| **Requirements** | Node.js 18+, Python 3.10+ | Python 3.10+ only |
| **Package Size** | ~4 KB (wrapper) | ~50 KB (full package) |
| **Auto-install** | Yes (installs pip package) | No |
| **Functionality** | Identical | Identical |

## Design Rationale

### Why Not Embed Python?

The story initially specified embedding Python (using python-build-standalone), but this was **intentionally simplified** because:

1. **Project Focus**: CNL is designed for **local development/CLI** use, not end-user distribution
2. **Package Size**: Embedded Python would be 100MB+, npm package is 4 KB
3. **Maintenance**: Embedded Python requires platform-specific binaries and updates
4. **User Base**: Target users (network engineers/DevOps) likely have Python installed
5. **Simplicity**: Thin wrapper is easier to maintain and debug

### Why Use npm at All?

Even though it requires Python, the npm package provides value:

1. **Discoverability**: Node.js users can find it via `npm search`
2. **Convenience**: `npx @cisco/cnl` is easier than manual pip install
3. **Auto-install**: Handles pip package installation automatically
4. **Consistency**: Provides unified CLI across Python and Node.js ecosystems

## Troubleshooting

### "Module not found: scripts.cli"

The CNL pip package is not installed correctly. Reinstall:

```bash
python3 -m pip install --user --upgrade cnl
```

### "Permission denied"

Make sure scripts are executable:

```bash
chmod +x npm/bin/cnl.js npm/lib/*.js
```

### "Tarball is too large"

Check `.npmignore` is excluding unnecessary files:

```bash
npm pack --dry-run
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Add `--setup` wizard for first-time users
- [ ] Embed Python for true zero-dependency installation
- [ ] Auto-update mechanism for pip package
- [ ] Telemetry for usage tracking
- [ ] Platform-specific optimizations

## Related Documentation

- [User Manual](./user_manual.md)
- [Quick Start Guide](./quick-start.md)
- [Publishing Guide](../npm/PUBLISHING.md)
- [Story 6.2](./stories/6.2.story.md)
