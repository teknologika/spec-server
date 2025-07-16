#!/bin/bash
# Release script for spec-server package

set -e

# Check if version argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.1"
    exit 1
fi

VERSION=$1

echo "🚀 Preparing release v$VERSION..."

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.0.0)"
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Must be on main branch to create a release. Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "❌ Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Update version in pyproject.toml
echo "📝 Updating version in pyproject.toml..."
sed -i.bak "s/version = \"[^\"]*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Run tests to ensure everything works
echo "🧪 Running tests..."
python -m pytest

# Build the package
echo "🏗️ Building package..."
./scripts/build.sh

# Commit version update
echo "💾 Committing version update..."
git add pyproject.toml
git commit -m "Bump version to $VERSION"

# Create and push tag
echo "🏷️ Creating and pushing tag..."
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin main
git push origin "v$VERSION"

echo "✅ Release v$VERSION prepared successfully!"
echo "🎯 Next steps:"
echo "   1. Go to GitHub and create a release from tag v$VERSION"
echo "   2. The CI/CD pipeline will automatically publish to PyPI"
echo "   3. Update the README.md to remove 'Coming Soon' from PyPI installation"