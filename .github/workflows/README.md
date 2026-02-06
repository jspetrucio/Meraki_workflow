# GitHub Actions Workflows

This directory contains CI/CD workflows for the CNL (Cisco Neural Language) project.

## Workflows

### 1. CI (`ci.yml`)

**Trigger:** Push to `main` branch, pull requests to `main`

**Purpose:** Continuous integration checks for all components

**Jobs:**
- **frontend-tests**: Lint and build the React frontend
- **python-tests**: Run Python tests across multiple Python versions (3.10, 3.11, 3.12)
- **rust-check**: Format, lint (Clippy), and test Rust code
- **integration**: Full integration build to verify all components work together

**Duration:** ~8-12 minutes

### 2. Release (`release.yml`)

**Trigger:** Push tags matching `v*` (e.g., `v0.1.0`, `v1.0.0-rc1`)

**Purpose:** Build and publish Tauri desktop app for all platforms

**Platforms:**
- macOS (Apple Silicon - aarch64)
- macOS (Intel - x86_64)
- Linux (x86_64)
- Windows (x86_64)

**Jobs:**
1. **build-and-release**: Build Tauri app for all platforms in parallel
2. **notify-homebrew**: Trigger Homebrew formula update (only for stable releases)

**Duration:** ~12-15 minutes per platform

**Artifacts:**
- macOS: `.dmg` and `.app` bundles
- Linux: `.AppImage` and `.deb` packages
- Windows: `.msi` and `.exe` installers
- `latest.json` for auto-updater

## Creating a Release

### 1. Ensure version is synced
```bash
# The sync-version.sh script will be called automatically by CI
# But you can run it manually to verify:
bash scripts/sync-version.sh 0.2.0
```

### 2. Create and push a tag
```bash
# For stable release
git tag v0.2.0
git push origin v0.2.0

# For pre-release (release candidate)
git tag v0.2.0-rc1
git push origin v0.2.0-rc1
```

### 3. Monitor the workflow
```bash
gh run watch
```

### 4. Check the release
```bash
gh release view v0.2.0
```

## Required Secrets

### For All Releases

- **GITHUB_TOKEN**: Automatically provided by GitHub Actions
- **TAURI_SIGNING_PRIVATE_KEY**: Private key for Tauri updater signing
- **TAURI_SIGNING_PRIVATE_KEY_PASSWORD**: Password for the signing key

### For macOS Code Signing (Optional - Currently Disabled)

- **APPLE_CERTIFICATE**: Base64-encoded .p12 certificate
- **APPLE_CERTIFICATE_PASSWORD**: Password for the certificate
- **APPLE_SIGNING_IDENTITY**: Developer ID Application identity
- **APPLE_ID**: Apple ID email
- **APPLE_PASSWORD**: App-specific password

### For Homebrew Integration (Optional)

- **HOMEBREW_PAT**: Personal access token with `repo` scope for homebrew-cnl repo

## Setting Up Secrets

### 1. Generate Tauri Signing Key

```bash
# Install Tauri CLI if not already installed
npm install -g @tauri-apps/cli

# Generate key pair
tauri signer generate -w ~/.tauri/myapp.key

# This creates:
# - myapp.key (private key - keep secret!)
# - myapp.key.pub (public key - add to tauri.conf.json)
```

### 2. Add Secrets to GitHub

```bash
# Add the private key
gh secret set TAURI_SIGNING_PRIVATE_KEY < ~/.tauri/myapp.key

# Add the password (if you set one)
gh secret set TAURI_SIGNING_PRIVATE_KEY_PASSWORD

# Update tauri.conf.json with the public key
# Copy the contents of myapp.key.pub to plugins.updater.pubkey
```

### 3. Update tauri.conf.json

Replace the `pubkey` value in `src-tauri/tauri.conf.json`:

```json
{
  "plugins": {
    "updater": {
      "pubkey": "CONTENTS_OF_YOUR_PUBLIC_KEY"
    }
  }
}
```

## Pre-release vs Stable Release

### Pre-release (marked as pre-release on GitHub)
- Tags containing: `-rc`, `-beta`, `-alpha`
- Examples: `v1.0.0-rc1`, `v2.0.0-beta1`, `v1.5.0-alpha`
- Will NOT trigger Homebrew update

### Stable Release (marked as latest)
- Clean version tags: `v1.0.0`, `v2.5.3`
- Will trigger Homebrew formula update (if configured)

## Auto-Updater

The app includes an auto-updater that checks for new releases.

**How it works:**
1. App checks: `https://github.com/jspetrucio/Meraki_workflow/releases/latest/download/latest.json`
2. If a newer version is found, user is notified
3. Update is downloaded and signature verified
4. App restarts with new version

**Configuration:** See `src-tauri/tauri.conf.json` → `plugins.updater`

## Caching Strategy

### Node.js Dependencies
- **Key:** `node-{platform}-{hash(package-lock.json)}`
- **Paths:** `frontend/node_modules`, `~/.npm`

### Rust Dependencies
- **Key:** `rust-{target}-{hash(Cargo.lock)}`
- **Paths:** `~/.cargo/registry`, `~/.cargo/git`, `src-tauri/target`

### Python Dependencies
- **Key:** Handled automatically by `actions/setup-python@v5`
- **Paths:** pip cache directory

## Troubleshooting

### Build fails on macOS
- Check that both targets (aarch64, x86_64) are supported
- Verify Xcode Command Line Tools are available in runner

### Build fails on Linux
- Verify all system dependencies are installed
- Check `libwebkit2gtk-4.1-dev` version

### Signing fails
- Verify `TAURI_SIGNING_PRIVATE_KEY` is set correctly
- Check that the private key matches the public key in tauri.conf.json
- Ensure the password is correct (if set)

### Release not created
- Check that the tag matches `v*` pattern
- Verify `GITHUB_TOKEN` has `contents: write` permission
- Check workflow logs for errors

### Homebrew not notified
- Verify `github.repository` matches expected value
- Check that `HOMEBREW_PAT` secret is set
- Ensure homebrew-cnl repository exists

## Performance Optimization

Current build times (approximate):

| Platform | Time |
|----------|------|
| macOS (both targets) | ~12-15 min |
| Linux | ~10-12 min |
| Windows | ~10-12 min |

**Optimization strategies:**
- Aggressive caching of Rust and Node.js dependencies
- Parallel matrix builds
- Cached frontend build artifacts
- Skip unnecessary steps (e.g., code signing when disabled)

## References

- [Tauri Action](https://github.com/tauri-apps/tauri-action)
- [Tauri Updater](https://tauri.app/v1/guides/distribution/updater)
- [GitHub Actions](https://docs.github.com/en/actions)
