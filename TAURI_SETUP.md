# Tauri Setup Guide for CNL

This guide walks through setting up the Tauri desktop application for local development.

## Quick Start

```bash
# 1. Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 2. Install Tauri CLI
npm install

# 3. Run in development mode
npm run dev
```

That's it! The app should launch with the FastAPI backend running automatically.

## Detailed Setup

### 1. Install Rust

#### macOS/Linux
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Follow the prompts. When done:
```bash
source $HOME/.cargo/env
rustc --version  # Verify installation
```

#### Windows
Download and run: https://rustup.rs/

### 2. System Dependencies

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    file \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

### 3. Verify Prerequisites

```bash
# Check Rust
rustc --version
cargo --version

# Check Node.js
node --version
npm --version

# Check Python
python3 --version

# Check uvicorn
python3 -m pip show uvicorn
```

### 4. Install Project Dependencies

```bash
# Install Tauri CLI
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install Python dependencies
pip install -r requirements.txt
```

## Development Workflow

### Running the App

```bash
# Method 1: Using npm scripts
npm run dev

# Method 2: Using tauri CLI directly
npm run tauri dev
```

### What Happens When You Run `npm run dev`:

1. Vite dev server starts on `http://localhost:5173`
2. Tauri builds and launches the desktop app
3. Tauri spawns FastAPI backend on `http://127.0.0.1:3141`
4. App WebView loads the Vite dev server
5. Hot Module Replacement (HMR) works for frontend changes

### Development Tips

**Frontend Development:**
- Edit files in `frontend/src/`
- Changes hot-reload automatically via Vite HMR
- No app restart needed

**Rust/Tauri Changes:**
- Edit files in `src-tauri/src/`
- Requires app restart (Ctrl+C and re-run)
- Cargo recompiles changed code

**Backend Changes:**
- Edit files in `scripts/`
- Backend must be restarted manually
- Or run backend separately with `--reload`:
  ```bash
  python3 -m uvicorn scripts.server:app --host 127.0.0.1 --port 3141 --reload
  ```

### Running Components Separately

Sometimes useful for debugging:

```bash
# Terminal 1: Frontend only
cd frontend
npm run dev

# Terminal 2: Backend only
python3 -m uvicorn scripts.server:app --host 127.0.0.1 --port 3141 --reload

# Terminal 3: Tauri (will connect to running services)
npm run tauri dev
```

## Building for Production

### Build Everything

```bash
npm run build
```

This runs:
1. `cd frontend && npm run build` → creates `frontend/dist/`
2. `tauri build` → creates native app bundles

### Build Output

**macOS:**
```
src-tauri/target/release/bundle/
├── macos/
│   └── CNL.app              # Application bundle
└── dmg/
    └── CNL_0.1.0_aarch64.dmg    # Installer (Apple Silicon)
    └── CNL_0.1.0_x86_64.dmg     # Installer (Intel)
```

### Testing the Production Build

```bash
# Run the .app directly
open src-tauri/target/release/bundle/macos/CNL.app

# Or install from DMG
open src-tauri/target/release/bundle/dmg/CNL_*.dmg
```

### Build Sizes

Expected sizes:
- `.app` bundle: ~15-20 MB
- `.dmg` installer: ~10-15 MB

To reduce size:
- Rust is compiled with `opt-level = "s"` (size optimization)
- Strip symbols enabled in release mode
- Frontend is minified by Vite

## Troubleshooting

### "Command not found: cargo"

**Fix:**
```bash
source $HOME/.cargo/env
# Or restart your terminal
```

### "Python not found" Error

**Fix:**
Ensure Python 3.10+ is installed:
```bash
python3 --version
which python3
```

If not installed:
```bash
# macOS
brew install python3

# Linux
sudo apt install python3 python3-pip
```

### Port 3141 Already in Use

**Find and kill the process:**
```bash
# macOS/Linux
lsof -i :3141
kill -9 <PID>
```

### Backend Fails to Start

**Check uvicorn is installed:**
```bash
python3 -m pip install uvicorn fastapi pydantic
```

**Check working directory:**
The backend expects to be run from the project root where `scripts/` exists.

### App Window is Blank

**Causes:**
1. Frontend didn't build correctly
2. Vite dev server isn't running
3. CSP (Content Security Policy) is blocking resources

**Fix:**
```bash
# Check Vite is running
curl http://localhost:5173

# Check browser console in app (enable dev tools):
# In tauri.conf.json, add to app.security:
"devTools": true
```

### Build Fails on macOS

**"xcode-select: error: tool 'xcodebuild' requires Xcode"**

**Fix:**
```bash
xcode-select --install
```

### Build Fails: "linker `cc` not found"

**Fix:**
Install build tools:
```bash
# macOS
xcode-select --install

# Linux
sudo apt install build-essential
```

## Project Structure Reference

```
Meraki_Workflow/
├── frontend/                   # React frontend
│   ├── src/
│   ├── dist/                  # Built frontend (created by npm run build)
│   └── package.json
│
├── scripts/                   # FastAPI backend
│   └── server.py
│
├── src-tauri/                 # Tauri desktop app
│   ├── src/
│   │   ├── main.rs           # App entry point
│   │   ├── lib.rs
│   │   └── sidecar.rs        # Backend process manager
│   ├── tauri.conf.json       # Tauri config
│   ├── Cargo.toml            # Rust dependencies
│   └── target/               # Build output (gitignored)
│       └── release/
│           └── bundle/       # Platform-specific bundles
│
└── package.json              # Root scripts (tauri commands)
```

## Next Steps

Once Tauri is running:

1. **Test the integration**: Verify all frontend features work in Tauri
2. **Add custom icons**: Replace placeholder icons in `src-tauri/icons/`
3. **Configure app**: Adjust window size, title, etc. in `tauri.conf.json`
4. **Build installer**: Test the `.dmg` installer on a clean machine

## Resources

- [Tauri Documentation](https://v2.tauri.app)
- [Tauri Prerequisites](https://v2.tauri.app/start/prerequisites/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- Story 4.1: `docs/stories/4.1.story.md`

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Check `src-tauri/README.md` for architecture details
3. Review Story 4.1 in `docs/stories/4.1.story.md`
4. Check Tauri docs: https://v2.tauri.app
5. Check Rust errors carefully - they're usually very informative

## Notes

- The app runs FastAPI as a child process (sidecar)
- On app close, the backend is automatically terminated
- In production, frontend assets are embedded in the `.app` bundle
- Backend scripts are bundled as resources (not embedded in binary)
