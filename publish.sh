#!/bin/bash
set -e

echo "Publishing ChimeraDB to PyPI..."
echo ""

# Clean previous builds
echo "→ Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build package
echo "→ Building package..."
python -m build

# Check package
echo "→ Checking package with twine..."
twine check dist/*

# Upload to PyPI (or use --repository testpypi for testing)
echo "→ Uploading to PyPI..."
echo "   Use: twine upload dist/*"
echo "   Or for TestPyPI: twine upload --repository testpypi dist/*"
echo ""
echo "Run the upload command manually to proceed."
