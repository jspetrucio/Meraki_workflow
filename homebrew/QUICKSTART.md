# CNL Homebrew Formula - Quick Start

> Fast track guide to publishing and distributing CNL via Homebrew

---

## Step 1: Publish to PyPI (Required First)

```bash
cd /Users/josdasil/Documents/Meraki_Workflow

# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI (requires account)
twine upload dist/*
```

**Result:** Package available at `https://pypi.org/project/cnl/`

---

## Step 2: Generate Checksums

```bash
cd homebrew

# Download and calculate SHA256
curl -L https://files.pythonhosted.org/packages/source/c/cnl/cnl-0.1.0.tar.gz -o /tmp/cnl.tar.gz
shasum -a 256 /tmp/cnl.tar.gz

# Copy the SHA256 hash
```

**Update in `cnl.rb`:**
```ruby
sha256 "PASTE_SHA256_HERE"
```

---

## Step 3: Generate Dependency Checksums

```bash
# Install poet
pip install homebrew-pypi-poet

# Generate resource blocks
poet cnl

# Copy output into cnl.rb resources section
```

---

## Step 4: Create Homebrew Tap Repository

```bash
# On GitHub, create repository:
# Name: homebrew-cnl
# Org: cisco (or your organization)

# Clone and setup
git clone https://github.com/cisco/homebrew-cnl
cd homebrew-cnl

# Create Formula directory
mkdir -p Formula

# Copy formula
cp /path/to/Meraki_Workflow/homebrew/cnl.rb Formula/

# Commit
git add Formula/cnl.rb
git commit -m "Add CNL formula v0.1.0"
git push
```

---

## Step 5: Test Installation

```bash
# Add tap
brew tap cisco/cnl

# Install
brew install cnl

# Verify
which cnl
cnl --help
cnl serve

# Test uninstall
brew uninstall cnl
```

---

## Step 6: Setup Auto-Update CI/CD

### In tap repo (cisco/homebrew-cnl):

Create `.github/workflows/update-formula.yml`:

```yaml
name: Update Formula

on:
  repository_dispatch:
    types: [new-release]

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update formula
        env:
          VERSION: ${{ github.event.client_payload.version }}
          SHA256: ${{ github.event.client_payload.sha256 }}
        run: |
          sed -i "s|url \".*\"|url \"https://files.pythonhosted.org/packages/source/c/cnl/cnl-${VERSION}.tar.gz\"|" Formula/cnl.rb
          sed -i "s/sha256 \".*\"/sha256 \"${SHA256}\"/" Formula/cnl.rb

      - name: Commit
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add Formula/cnl.rb
          git commit -m "Update to v${{ github.event.client_payload.version }}"
          git push
```

### In main repo (Meraki_Workflow):

Add to `.github/workflows/release.yml`:

```yaml
- name: Trigger Homebrew update
  uses: peter-evans/repository-dispatch@v2
  with:
    token: ${{ secrets.HOMEBREW_TAP_TOKEN }}
    repository: cisco/homebrew-cnl
    event-type: new-release
    client-payload: |
      {
        "version": "0.1.0",
        "sha256": "${{ steps.checksum.outputs.sha256 }}"
      }
```

---

## Verification Checklist

- [ ] Package published to PyPI
- [ ] SHA256 checksums updated in cnl.rb
- [ ] All dependency resources have checksums
- [ ] Tap repository created on GitHub
- [ ] Formula in tap's `Formula/` directory
- [ ] `brew audit --strict cnl` passes
- [ ] `brew install cisco/cnl/cnl` works
- [ ] `cnl --help` executes successfully
- [ ] CI/CD workflow configured
- [ ] Auto-update tested with new release

---

## Usage After Installation

```bash
# Add tap (first time only)
brew tap cisco/cnl

# Install
brew install cnl

# Use
cnl --help
cnl serve
cnl discover full --client customer1
cnl config ssid -n NET123 --name "Guest" --client customer1

# Update
brew upgrade cnl

# Uninstall
brew uninstall cnl
```

---

## Troubleshooting

### Formula audit fails
```bash
brew audit --strict Formula/cnl.rb
# Fix issues reported
```

### Installation fails
```bash
brew install --verbose --debug cnl
# Check error messages
```

### Checksum mismatch
```bash
# Recalculate SHA256
curl -L [PYPI_URL] | shasum -a 256
# Update in formula
```

---

## Resources

- Main README: [README.md](README.md)
- Homebrew Docs: https://docs.brew.sh
- Python Formula Guide: https://docs.brew.sh/Python-for-Formula-Authors
- PyPI: https://pypi.org/project/cnl/

---

**Created:** 2026-02-05
**Status:** Ready for PyPI publish
