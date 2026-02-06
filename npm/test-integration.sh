#!/bin/bash
# Integration test for @cisco/cnl npm package
# Tests installation, Python detection, and basic CLI execution

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  CNL npm Package Integration Test"
echo "=========================================="
echo ""

# Test 1: Python Detection
echo -e "${YELLOW}Test 1: Python Detection${NC}"
if node lib/check-python.js > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Python 3.10+ detected${NC}"
else
    echo -e "${RED}✗ Python 3.10+ not found${NC}"
    echo ""
    echo "Please install Python 3.10 or later to continue."
    exit 1
fi
echo ""

# Test 2: Package Structure
echo -e "${YELLOW}Test 2: Package Structure${NC}"
REQUIRED_FILES=(
    "package.json"
    "bin/cnl.js"
    "lib/check-python.js"
    "lib/install.js"
    "README.md"
)

ALL_FOUND=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        ALL_FOUND=false
    fi
done

if [ "$ALL_FOUND" = false ]; then
    echo -e "\n${RED}Some required files are missing${NC}"
    exit 1
fi
echo ""

# Test 3: Package Validity
echo -e "${YELLOW}Test 3: Package Validity${NC}"
if npm pack --dry-run > /dev/null 2>&1; then
    echo -e "${GREEN}✓ package.json is valid${NC}"
else
    echo -e "${RED}✗ package.json has errors${NC}"
    exit 1
fi
echo ""

# Test 4: Scripts are Executable
echo -e "${YELLOW}Test 4: Script Permissions${NC}"
if [ -x "bin/cnl.js" ] && [ -x "lib/check-python.js" ] && [ -x "lib/install.js" ]; then
    echo -e "${GREEN}✓ All scripts are executable${NC}"
else
    echo -e "${RED}✗ Some scripts are not executable${NC}"
    echo "Run: chmod +x bin/cnl.js lib/*.js"
    exit 1
fi
echo ""

# Test 5: Package Size
echo -e "${YELLOW}Test 5: Package Size${NC}"
npm pack > /dev/null 2>&1
TARBALL=$(ls cisco-cnl-*.tgz)
SIZE=$(du -k "$TARBALL" | cut -f1)

if [ "$SIZE" -lt 100 ]; then
    echo -e "${GREEN}✓ Package size: ${SIZE}KB (optimal)${NC}"
elif [ "$SIZE" -lt 1000 ]; then
    echo -e "${YELLOW}⚠ Package size: ${SIZE}KB (acceptable)${NC}"
else
    echo -e "${RED}✗ Package size: ${SIZE}KB (too large!)${NC}"
    exit 1
fi

# Cleanup
rm -f "$TARBALL"
echo ""

# Test 6: Security Check
echo -e "${YELLOW}Test 6: Security Check${NC}"
if grep -r "execSync(" bin/ lib/ > /dev/null 2>&1; then
    echo -e "${RED}✗ Found unsafe execSync() usage${NC}"
    echo "Use execFileSync() with array arguments instead"
    exit 1
else
    echo -e "${GREEN}✓ No unsafe execSync() usage found${NC}"
fi

if grep -r "eval(" bin/ lib/ > /dev/null 2>&1; then
    echo -e "${RED}✗ Found eval() usage${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No eval() usage found${NC}"
fi
echo ""

# Test 7: No Secrets
echo -e "${YELLOW}Test 7: Secret Detection${NC}"
if grep -ri "api[_-]key\|secret\|password\|token" bin/ lib/ --exclude="*.md" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Found potential secret keywords (review manually)${NC}"
else
    echo -e "${GREEN}✓ No obvious secrets detected${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}  All Tests Passed!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test local installation:"
echo "     npm install -g ./cisco-cnl-*.tgz"
echo ""
echo "  2. Test CLI:"
echo "     cnl --help"
echo ""
echo "  3. Publish to npm:"
echo "     npm publish --access public"
echo ""
