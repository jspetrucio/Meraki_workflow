#!/usr/bin/env bash
# Build script for CNL package
set -e

echo "=== CNL Build Script ==="

# Build frontend (if available)
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo ""
    echo "Building frontend..."
    cd frontend && npm run build && cd ..
    echo "✓ Frontend built successfully"
else
    echo ""
    echo "⚠ Frontend not found (Story 2.1 not complete yet) - skipping frontend build"
fi

# Build Python package
echo ""
echo "Building Python package..."
python -m build

echo ""
echo "✓ Build complete!"
echo ""
echo "Packages created in dist/:"
ls -lh dist/

echo ""
echo "To install locally: pip install -e ."
echo "To publish to PyPI: twine upload dist/*"
