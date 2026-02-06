# CNL Homebrew Formula

> Homebrew formula for installing CNL (Cisco Neural Language) on macOS/Linux

---

## Installation

### Option 1: Direct Formula Install (Development)

For testing the formula locally:

```bash
brew install homebrew/cnl.rb
```

Or from this repository:

```bash
brew install https://raw.githubusercontent.com/jspetrucio/Meraki_workflow/main/homebrew/cnl.rb
```

### Option 2: Custom Tap (Recommended for Distribution)

Create a custom Homebrew tap for easier installation:

1. **Create tap repository** (named `homebrew-cnl`):
   ```bash
   # On GitHub, create repo: cisco/homebrew-cnl (or your-org/homebrew-cnl)
   ```

2. **Add formula to tap**:
   ```bash
   git clone https://github.com/cisco/homebrew-cnl
   cd homebrew-cnl
   mkdir -p Formula
   cp path/to/cnl.rb Formula/
   git add Formula/cnl.rb
   git commit -m "Add CNL formula"
   git push
   ```

3. **Users install via tap**:
   ```bash
   brew tap cisco/cnl
   brew install cnl
   ```

---

## Usage After Installation

Once installed, the `cnl` command is available:

```bash
# Show help
cnl --help

# Start MCP server
cnl serve

# Discovery commands
cnl discover full --client CUSTOMER_NAME

# Configuration commands
cnl config ssid -n NETWORK_ID --name "Guest" --client CUSTOMER_NAME

# Generate reports
cnl report discovery --client CUSTOMER_NAME
```

---

## Updating the Formula

### When Publishing a New Version

1. **Update version in `cnl.rb`**:
   ```ruby
   url "https://files.pythonhosted.org/packages/source/c/cnl/cnl-X.Y.Z.tar.gz"
   ```

2. **Update SHA256 checksum**:
   ```bash
   # Download the package
   curl -L https://files.pythonhosted.org/packages/source/c/cnl/cnl-X.Y.Z.tar.gz -o cnl.tar.gz

   # Calculate SHA256
   shasum -a 256 cnl.tar.gz

   # Update in cnl.rb:
   sha256 "abc123..."
   ```

3. **Update resource checksums** (if dependencies changed):
   ```bash
   # Use homebrew-pypi-poet to auto-generate resources
   pip install homebrew-pypi-poet
   poet cnl

   # Copy output resources into cnl.rb
   ```

4. **Test the formula**:
   ```bash
   brew install --build-from-source homebrew/cnl.rb
   brew test cnl
   brew audit --strict cnl
   ```

5. **Commit and push**:
   ```bash
   git add Formula/cnl.rb
   git commit -m "Update CNL to vX.Y.Z"
   git push
   ```

---

## Publishing to PyPI (Required for Homebrew)

Homebrew formulas typically install from PyPI. To publish CNL to PyPI:

1. **Build the distribution**:
   ```bash
   pip install build twine
   python -m build
   ```

2. **Upload to PyPI**:
   ```bash
   twine upload dist/cnl-X.Y.Z*
   ```

3. **Update Homebrew formula** with PyPI URL and checksum

---

## Automated Formula Updates (CI/CD)

### GitHub Actions Workflow

Create `.github/workflows/update-homebrew.yml` in tap repo:

```yaml
name: Update Homebrew Formula

on:
  repository_dispatch:
    types: [new-release]

jobs:
  update-formula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update formula version
        env:
          VERSION: ${{ github.event.client_payload.version }}
          SHA256: ${{ github.event.client_payload.sha256 }}
        run: |
          sed -i "s|url \".*\"|url \"https://files.pythonhosted.org/packages/source/c/cnl/cnl-${VERSION}.tar.gz\"|" Formula/cnl.rb
          sed -i "s/sha256 \".*\"/sha256 \"${SHA256}\"/" Formula/cnl.rb

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add Formula/cnl.rb
          git commit -m "Update CNL to v${{ github.event.client_payload.version }}"
          git push
```

### Trigger from Main Repo

Add to `.github/workflows/release.yml` in main repository:

```yaml
- name: Trigger Homebrew formula update
  uses: peter-evans/repository-dispatch@v2
  with:
    token: ${{ secrets.HOMEBREW_TAP_TOKEN }}
    repository: cisco/homebrew-cnl
    event-type: new-release
    client-payload: |
      {
        "version": "${{ steps.version.outputs.version }}",
        "sha256": "${{ steps.checksum.outputs.sha256 }}"
      }
```

---

## Troubleshooting

### Formula audit fails

```bash
brew audit --strict cnl
```

Common issues:
- Missing or incorrect SHA256 checksums
- Incorrect URL format
- Missing test block
- Python version compatibility

### Installation fails

```bash
# Install with verbose output
brew install --verbose --debug cnl

# Check formula syntax
brew style cnl
```

### Testing locally

```bash
# Install from local file
brew install --build-from-source homebrew/cnl.rb

# Uninstall
brew uninstall cnl

# Clean up
brew cleanup -s cnl
```

---

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- [homebrew-pypi-poet](https://github.com/tdsmith/homebrew-pypi-poet) - Auto-generate Python resources

---

## License

MIT - Same as CNL project
