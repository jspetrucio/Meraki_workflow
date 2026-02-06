# CNL Tauri Desktop App - Quick Reference

## 🚀 Quick Start

```bash
# First time setup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh  # Install Rust
npm install                                                      # Install deps

# Development
npm run dev                                                      # Run app in dev mode

# Production
npm run build                                                    # Build .app + .dmg
```

---

## 📁 Project Structure

```
src-tauri/
├── src/
│   ├── main.rs       # App entry + sidecar lifecycle
│   ├── lib.rs        # Library entry
│   └── sidecar.rs    # FastAPI process manager
├── tauri.conf.json   # Main config (window, bundle, CSP)
├── Cargo.toml        # Rust dependencies
├── capabilities/     # Tauri 2.0 security
└── permissions/      # Custom permissions
```

---

## 🎯 Key Components

### SidecarManager (sidecar.rs)
```rust
let manager = SidecarManager::new();
manager.start()?;                    // Spawn FastAPI
manager.wait_for_health().await?;    // Wait until ready
manager.stop();                      // Cleanup
```

### Tauri Commands (main.rs)
```javascript
import { invoke } from '@tauri-apps/api/core';

await invoke('check_backend_health');  // Poll /api/v1/health
await invoke('is_backend_running');    // Check process status
```

---

## 🔧 Configuration

### Window Settings (tauri.conf.json)
```json
{
  "title": "CNL - Cisco Neural Language",
  "width": 1200,
  "height": 800,
  "minWidth": 800,
  "minHeight": 600
}
```

### Backend (sidecar.rs)
```
Host: 127.0.0.1
Port: 3141
Health: GET /api/v1/health
Timeout: 10 seconds
```

### Build Paths
```
Dev:  http://localhost:5173 (Vite)
Prod: ../frontend/dist (embedded)
```

---

## 🏗️ Build Outputs

```
src-tauri/target/release/bundle/
├── macos/
│   └── CNL.app              # Application bundle
└── dmg/
    └── CNL_0.1.0_*.dmg      # Installer
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python
python3 --version

# Check uvicorn
python3 -m pip show uvicorn

# Test manually
python3 -m uvicorn scripts.server:app --host 127.0.0.1 --port 3141
```

### Port 3141 In Use
```bash
lsof -i :3141          # Find process
kill -9 <PID>          # Kill it
```

### Rust Not Found
```bash
source $HOME/.cargo/env    # Activate Rust
rustc --version            # Verify
```

### Build Fails
```bash
cd src-tauri
cargo clean
cargo build
```

---

## 📝 npm Scripts

| Command | Action |
|---------|--------|
| `npm run dev` | Development mode (Vite + Tauri + FastAPI) |
| `npm run build` | Production build (.app + .dmg) |
| `npm run tauri` | Run Tauri CLI directly |

---

## 🔐 Security

### CSP Policy
```
connect-src: localhost:3141 ws://localhost:3141
script-src: 'self' 'unsafe-inline' 'unsafe-eval'
```

### Permissions
- Window control (close, minimize, maximize)
- App info (version, name)
- Backend health check
- Backend status check

---

## 📦 Dependencies

### Rust (Cargo.toml)
```toml
tauri = "2"
serde = "1"
tokio = "1"
reqwest = "0.12"
```

### Node (package.json)
```json
{
  "@tauri-apps/cli": "^2.0.0"
}
```

---

## 🎨 Icons

Required files in `src-tauri/icons/`:
- 32x32.png
- 128x128.png
- 128x128@2x.png
- icon.icns (macOS)
- icon.ico (Windows)

Generate from 1024x1024 source using ImageMagick or online tools.

---

## ⚡ Performance

### Release Optimizations (Cargo.toml)
```toml
[profile.release]
opt-level = "s"    # Size optimization
lto = true         # Link-time optimization
strip = true       # Strip symbols
```

Expected sizes:
- `.app` bundle: ~15-20 MB
- `.dmg` installer: ~10-15 MB

---

## 🧪 Testing

### Manual Tests
```bash
# Run app
npm run dev

# Check backend
curl http://localhost:3141/api/v1/health

# Close app
# Verify no orphans:
ps aux | grep uvicorn    # Should be empty
```

### Unit Tests
```bash
cd src-tauri
cargo test
```

---

## 📚 Documentation

| Document | Location |
|----------|----------|
| Setup Guide | `TAURI_SETUP.md` |
| Architecture | `src-tauri/README.md` |
| Icon Guide | `src-tauri/icons/README.md` |
| Completion Report | `STORY_4.1_COMPLETION.md` |
| File Structure | `.tauri-structure.md` |

---

## 🔗 Resources

- [Tauri Docs](https://v2.tauri.app)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- Story: `docs/stories/4.1.story.md`

---

## 🚨 Common Issues

| Issue | Fix |
|-------|-----|
| `cargo not found` | `source $HOME/.cargo/env` |
| `Python not found` | Install Python 3.10+ |
| Port 3141 busy | `lsof -i :3141 && kill -9 <PID>` |
| Backend timeout | Check uvicorn is installed |
| Blank window | Check Vite is running on 5173 |

---

## 🎯 Next Steps

1. ✅ Configuration created (Story 4.1)
2. ⬜ Install Rust toolchain
3. ⬜ Generate app icons
4. ⬜ Run `npm run dev` to test
5. ⬜ Build production: `npm run build`
6. ⬜ Test .app on clean machine
7. ⬜ Story 4.2: System tray (optional)

---

**Quick Help**: `tauri --help` | `cargo --help`
**Status**: Configuration complete, ready for compilation
**Story**: 4.1 - Tauri App Shell ✅ DONE

---

*CNL - Cisco Neural Language | Tauri 2.0 Desktop App*
