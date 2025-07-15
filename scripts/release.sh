#!/bin/bash
# Release script for spec-server

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.0"
    exit 1
fi

VERSION=$1

echo "🚀 Preparing release v$VERSION"

# Check if we're on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Must be on main branch to release. Current branch: $BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean. Please commit or stash changes."
    git status --short
    exit 1
fi

# Update version in pyproject.toml
echo "📝 Updating version in pyproject.toml..."
if command -v python3 &> /dev/null; then
    python3 -c "
import toml
with open('pyproject.toml', 'r') as f:
    data = toml.load(f)
data['project']['version'] = '$VERSION'
with open('pyproject.toml', 'w') as f:
    toml.dump(data, f)
print('✅ Updated pyproject.toml')
"
else
    echo "❌ Python3 not found. Please install Python3 or update version manually."
    exit 1
fi

# Update version in __init__.py
echo "📝 Updating version in __init__.py..."
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/spec_server/__init__.py
rm src/spec_server/__init__.py.bak

# Run tests
echo "🧪 Running tests..."
python3 -m pytest --cov=spec_server

# Run type checking
echo "🔍 Running type checks..."
mypy src

# Run linting
echo "🧹 Running linting..."
black --check src tests
isort --check-only src tests

# Build package
echo "📦 Building package..."
python3 -m build

# Check package
echo "✅ Checking package..."
twine check dist/*

echo ""
echo "🎉 Release v$VERSION is ready!"
echo ""
echo "Next steps:"
echo "1. Review the changes:"
echo "   git diff"
echo ""
echo "2. Commit the version bump:"
echo "   git add -A"
echo "   git commit -m 'Bump version to v$VERSION'"
echo "   git push origin main"
echo ""
echo "3. Create and push the tag:"
echo "   git tag v$VERSION"
echo "   git push origin v$VERSION"
echo ""
echo "4. Or use GitHub's manual publish workflow:"
echo "   Go to Actions → Manual Publish to PyPI → Run workflow"
echo "   Enter version: $VERSION"
echo ""
echo "The GitHub Action will handle PyPI publishing and release creation."