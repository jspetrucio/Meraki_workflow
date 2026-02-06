# CNL Tauri Application

This directory contains the Tauri 2.0 desktop application wrapper for CNL.

## Architecture

```
┌─────────────────────────────────────────┐
│           Tauri Application              │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │         Rust Backend              │   │
│  │  ┌──────────┐                    │   │
│  │  │Sidecar   │                    │   │
│  │  │Manager   │                    │   │
│  │  │(spawns   │                    │   │
│  │  │ FastAPI) │                    │   │
│  │  └────┬─────┘                    │   │
│  └───────┼──────────────────────────┘   │
│          │                               │
│  ┌───────▼──────────────────────────┐   │
│  │      FastAPI Process              │   │
│  │      (localhost:3141)             │   │
│  └───────▲──────────────────────────┘   │
│          │                               │
│  ┌───────┼──────────────────────────┐   │
│  │      WebView                      │   │
│  │      (React Frontend)             │   │
│  │      http://localhost:5173 (dev)  │   │
│  │      asset://localhost (prod)     │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Prerequisites

### Required Tools

1. **Rust** (1.70+)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Node.js** (18+)
   ```bash
   # Already installed for frontend development
   ```

3. **Python** (3.10+)
   ```bash
   # Already installed for FastAPI backend
   ```

4. **System Dependencies** (macOS)
   ```bash
   # Xcode Command Line Tools
   xcode-select --install
   ```

## Development

### First Time Setup

1. Install Tauri CLI:
   ```bash
   npm install
   ```

2. Install Rust dependencies (happens automatically on first build):
   ```bash
   cd src-tauri
   cargo fetch
   ```

### Running in Development Mode

```bash
# From project root
npm run dev

# Or using tauri directly
npm run tauri dev
```

This will:
1. Start Vite dev server on port 5173
2. Start Tauri app
3. Tauri spawns FastAPI backend on port 3141
4. WebView loads http://localhost:5173

### Hot Reload

- **Frontend changes**: Vite HMR works automatically
- **Rust changes**: Requires app restart
- **Backend changes**: Run backend with --reload for auto-restart

## Building for Production

### macOS

```bash
# Build everything
npm run build

# Output in: src-tauri/target/release/bundle/
# - CNL.app        (application bundle)
# - dmg/CNL.dmg    (disk image installer)
```

### Build Process

1. `frontend/` builds to `frontend/dist/`
2. Tauri embeds `dist/` as assets
3. Tauri bundles Rust binary + assets → `.app`
4. DMG creator wraps `.app` → `.dmg`

## Project Structure

```
src-tauri/
├── build.rs                 # Build script
├── Cargo.toml              # Rust dependencies
├── tauri.conf.json         # Tauri configuration
├── capabilities/           # Tauri 2.0 security
│   └── default.json        # Default permissions
├── permissions/            # Custom permissions
│   └── backend.toml        # Backend commands
├── icons/                  # Application icons
│   ├── README.md
│   ├── 32x32.png
│   ├── 128x128.png
│   ├── 128x128@2x.png
│   ├── icon.icns
│   └── icon.ico
└── src/
    ├── main.rs            # Main Tauri app
    ├── lib.rs             # Library entry
    └── sidecar.rs         # FastAPI process manager
```

## Configuration

### Window Settings

- Default: 1200x800
- Minimum: 800x600
- Resizable: Yes
- Title: "CNL - Cisco Neural Language"

### Backend Settings

- Host: 127.0.0.1
- Port: 3141
- Startup timeout: 10 seconds
- Health check: GET /api/v1/health

### Security

Tauri 2.0 uses a capability-based security model:

- **Capabilities**: Define what the app can do
- **Permissions**: Granular access control
- **CSP**: Content Security Policy for web content

See:
- `capabilities/default.json`
- `permissions/backend.toml`

## Troubleshooting

### Backend Fails to Start

```bash
# Check Python is available
python3 --version

# Check uvicorn is installed
python3 -m pip list | grep uvicorn

# Try starting backend manually
cd /path/to/project
python3 -m uvicorn scripts.server:app --host 127.0.0.1 --port 3141
```

### Port 3141 Already in Use

```bash
# Find process using port
lsof -i :3141

# Kill it
kill -9 <PID>
```

### App Won't Build

```bash
# Clean and rebuild
cd src-tauri
cargo clean
cargo build
```

### Icons Not Showing

- Ensure all icon files exist in `icons/`
- Check `tauri.conf.json` icon paths
- Rebuild app (icons are embedded at build time)

## Sidecar Manager

The `sidecar.rs` module manages the FastAPI backend:

### Features

- **Auto-discovery**: Finds Python in system
- **Health checks**: Waits for backend to be ready
- **Graceful shutdown**: Kills backend on app close
- **Error handling**: Shows dialogs if backend fails

### API

```rust
// In Rust
let manager = SidecarManager::new();
manager.start()?;
manager.wait_for_health().await?;
manager.stop();
```

```javascript
// From frontend
import { invoke } from '@tauri-apps/api/core';

// Check backend health
const result = await invoke('check_backend_health');

// Check if running
const running = await invoke('is_backend_running');
```

## Testing

### Manual Testing

1. **Startup Test**:
   - Run app
   - Verify FastAPI starts within 3 seconds
   - Verify UI loads correctly

2. **Functionality Test**:
   - Test all UI features
   - Verify API calls work
   - Test WebSocket connections

3. **Shutdown Test**:
   - Close app
   - Check no orphan Python processes:
     ```bash
     ps aux | grep uvicorn
     ```

### Automated Tests

```bash
# Run Rust tests
cd src-tauri
cargo test
```

## Resources

- [Tauri Documentation](https://v2.tauri.app)
- [Tauri 2.0 Migration Guide](https://v2.tauri.app/start/migrate/from-tauri-1/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)

## Notes

- **Do NOT** commit `target/` directory (in .gitignore)
- **Do NOT** commit `Cargo.lock` for libraries (already in .gitignore)
- Icons are placeholders - replace with branded icons for production
- Backend must be in project root (not embedded in .app for MVP)
