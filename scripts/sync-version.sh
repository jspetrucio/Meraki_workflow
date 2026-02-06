#!/usr/bin/env bash
# Sync version across all CNL project files
# Usage: ./scripts/sync-version.sh 1.0.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Validate argument
if [ $# -ne 1 ]; then
    echo -e "${RED}Error: Version argument required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (semantic versioning)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version must be in semantic versioning format: MAJOR.MINOR.PATCH[-PRERELEASE]"
    echo "Examples: 1.0.0, 2.1.3, 1.0.0-beta.1"
    exit 1
fi

echo -e "${YELLOW}Syncing version to ${NEW_VERSION}...${NC}"

# File paths
TAURI_CONF="${PROJECT_ROOT}/src-tauri/tauri.conf.json"
CARGO_TOML="${PROJECT_ROOT}/src-tauri/Cargo.toml"
PYPROJECT_TOML="${PROJECT_ROOT}/pyproject.toml"
PACKAGE_JSON="${PROJECT_ROOT}/frontend/package.json"
VERSION_PY="${PROJECT_ROOT}/scripts/__version__.py"

# Verify all files exist
for file in "$TAURI_CONF" "$CARGO_TOML" "$PYPROJECT_TOML" "$PACKAGE_JSON" "$VERSION_PY"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: File not found: $file${NC}"
        exit 1
    fi
done

# Function to update file and show result
update_file() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS requires empty string for -i
        sed -i '' "$pattern" "$file"
    else
        # Linux
        sed -i "$pattern" "$file"
    fi

    echo -e "${GREEN}✓${NC} Updated $description: $file"
}

# Update each file
echo ""
echo "Updating version in 5 files:"
echo ""

# 1. src-tauri/tauri.conf.json
update_file "$TAURI_CONF" \
    "s/\"version\": \"[^\"]*\"/\"version\": \"${NEW_VERSION}\"/" \
    "Tauri config"

# 2. src-tauri/Cargo.toml
update_file "$CARGO_TOML" \
    "s/^version = \"[^\"]*\"/version = \"${NEW_VERSION}\"/" \
    "Cargo manifest"

# 3. pyproject.toml
update_file "$PYPROJECT_TOML" \
    "s/^version = \"[^\"]*\"/version = \"${NEW_VERSION}\"/" \
    "Python project"

# 4. frontend/package.json
update_file "$PACKAGE_JSON" \
    "s/\"version\": \"[^\"]*\"/\"version\": \"${NEW_VERSION}\"/" \
    "Frontend package"

# 5. scripts/__version__.py
cat > "$VERSION_PY" << EOF
"""Version information for CNL (Cisco Neural Language)."""

__version__ = "${NEW_VERSION}"
EOF
echo -e "${GREEN}✓${NC} Updated Python version module: $VERSION_PY"

echo ""
echo -e "${GREEN}Success!${NC} All files updated to version ${NEW_VERSION}"
echo ""
echo "Modified files:"
echo "  - src-tauri/tauri.conf.json"
echo "  - src-tauri/Cargo.toml"
echo "  - pyproject.toml"
echo "  - frontend/package.json"
echo "  - scripts/__version__.py"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit: git commit -am 'chore: bump version to ${NEW_VERSION}'"
echo "  3. Tag: git tag v${NEW_VERSION}"
echo "  4. Push: git push && git push --tags"
