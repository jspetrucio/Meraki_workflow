#!/bin/bash
# Generate SHA256 checksums for CNL Homebrew formula
# Usage: ./generate-checksums.sh VERSION

set -e

VERSION=${1:-"0.1.0"}

echo "=== Generating SHA256 Checksums for CNL v${VERSION} ==="
echo ""

# Main package
MAIN_URL="https://files.pythonhosted.org/packages/source/c/cnl/cnl-${VERSION}.tar.gz"
echo "Downloading main package..."
curl -L "$MAIN_URL" -o /tmp/cnl-${VERSION}.tar.gz
MAIN_SHA=$(shasum -a 256 /tmp/cnl-${VERSION}.tar.gz | awk '{print $1}')
echo "✅ Main package SHA256: $MAIN_SHA"
echo ""

# Generate resource checksums using homebrew-pypi-poet
echo "Generating dependency checksums..."
echo "Install homebrew-pypi-poet if not installed:"
echo "  pip install homebrew-pypi-poet"
echo ""
echo "Then run:"
echo "  poet cnl"
echo ""
echo "This will output all resource blocks with correct checksums."
echo ""

# Update formula
echo "=== Update cnl.rb with checksums ==="
echo ""
echo "1. Replace main package checksum:"
echo "   sha256 \"$MAIN_SHA\""
echo ""
echo "2. Replace URL:"
echo "   url \"$MAIN_URL\""
echo ""
echo "3. Update resource checksums from poet output"
echo ""

# Clean up
rm -f /tmp/cnl-${VERSION}.tar.gz

echo "=== Next Steps ==="
echo ""
echo "1. Update cnl.rb with checksums above"
echo "2. Test installation: brew install homebrew/cnl.rb"
echo "3. Commit to tap repo: git add Formula/cnl.rb && git commit -m 'Update to v${VERSION}'"
echo "4. Push: git push"
echo ""
