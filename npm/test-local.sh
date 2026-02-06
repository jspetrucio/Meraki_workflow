#!/bin/bash
# Local test script for npm package
# Tests the package locally before publishing

set -e

echo "=== Testing @cisco/cnl npm package ==="
echo ""

# Step 1: Check Python
echo "1. Checking Python..."
node lib/check-python.js
echo ""

# Step 2: Test npm pack
echo "2. Creating package tarball..."
npm pack
echo ""

# Step 3: Show package contents
echo "3. Package contents:"
tar -tzf cisco-cnl-*.tgz | head -20
echo ""

# Step 4: Check package size
SIZE=$(du -h cisco-cnl-*.tgz | cut -f1)
echo "4. Package size: $SIZE"
echo ""

echo "=== Tests Complete ==="
echo ""
echo "To test installation:"
echo "  npm install -g ./cisco-cnl-*.tgz"
echo "  cnl --help"
echo ""
echo "To uninstall:"
echo "  npm uninstall -g @cisco/cnl"
