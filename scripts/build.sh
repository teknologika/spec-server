#!/bin/bash
# Build script for spec-server package

set -e

echo "🔧 Building spec-server package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
rm -rf build/
rm -rf src/spec_server.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
python -m pip install --upgrade build twine

# Run tests before building
echo "🧪 Running tests..."
python -m pytest

# Run type checking
echo "🔍 Running type checking..."
python -m mypy src/spec_server

# Run linting
echo "✨ Running code formatting checks..."
python -m black --check src tests
python -m isort --check-only src tests
python -m flake8 src tests

# Build the package
echo "🏗️ Building package..."
python -m build

# Verify the build
echo "✅ Verifying build..."
python -m twine check dist/*

echo "🎉 Build completed successfully!"
echo "📁 Built packages are in the dist/ directory:"
ls -la dist/