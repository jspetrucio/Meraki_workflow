#!/bin/bash
# Script to verify and test the CNL Homebrew formula

set -e

echo "=== CNL Homebrew Formula Verification ==="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Install from https://brew.sh"
    exit 1
fi

echo "✅ Homebrew installed"

# Check Ruby syntax
echo ""
echo "Checking formula syntax..."
ruby -c cnl.rb
echo "✅ Formula syntax valid"

# Try to install formula locally (dry-run style check)
echo ""
echo "Running Homebrew audit..."
brew audit --strict --online cnl.rb || echo "⚠️  Audit warnings (expected until published to PyPI)"

echo ""
echo "=== Manual Testing Steps ==="
echo ""
echo "1. Install formula:"
echo "   brew install --build-from-source homebrew/cnl.rb"
echo ""
echo "2. Test CLI:"
echo "   cnl --help"
echo ""
echo "3. Verify installation:"
echo "   which cnl"
echo "   cnl --version"
echo ""
echo "4. Test functionality:"
echo "   cnl serve  # Start MCP server"
echo ""
echo "5. Uninstall:"
echo "   brew uninstall cnl"
echo ""
echo "6. Verify clean removal:"
echo "   which cnl  # Should return 'not found'"
echo ""

echo "=== PyPI Publishing Required ==="
echo ""
echo "Before formula can be used, publish to PyPI:"
echo ""
echo "  cd /Users/josdasil/Documents/Meraki_Workflow"
echo "  pip install build twine"
echo "  python -m build"
echo "  twine upload dist/*"
echo ""
echo "Then update SHA256 checksums in cnl.rb"
echo ""
