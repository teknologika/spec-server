#!/bin/bash
# Setup script for pre-commit hooks

set -e

echo "🔧 Setting up pre-commit hooks for spec-server..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get the project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please run this from within a git repository."
    exit 1
fi

# Install pre-commit framework if not already installed
if ! command -v pre-commit >/dev/null 2>&1; then
    print_status "Installing pre-commit framework..."
    pip install pre-commit
    print_success "pre-commit framework installed"
else
    print_status "pre-commit framework already installed"
fi

# Install pre-commit hooks from .pre-commit-config.yaml
if [[ -f ".pre-commit-config.yaml" ]]; then
    print_status "Installing pre-commit hooks from .pre-commit-config.yaml..."
    pre-commit install
    print_success "Pre-commit hooks installed from configuration"

    # Install commit-msg hook as well
    pre-commit install --hook-type commit-msg

    # Run pre-commit on all files to set up the environment
    print_status "Running pre-commit on all files to set up environment..."
    pre-commit run --all-files || true
    print_success "Pre-commit environment setup complete"
else
    print_warning ".pre-commit-config.yaml not found"
fi

# Also set up the manual Git hook as a backup
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
PRE_COMMIT_HOOK="$GIT_HOOKS_DIR/pre-commit"

if [[ -f "scripts/pre-commit-hook.sh" ]]; then
    print_status "Setting up manual Git pre-commit hook..."

    # Create hooks directory if it doesn't exist
    mkdir -p "$GIT_HOOKS_DIR"

    # Create or update the pre-commit hook
    cat > "$PRE_COMMIT_HOOK" << 'EOF'
#!/bin/bash
# Git pre-commit hook for spec-server
# This runs the same checks as the CI pipeline

# Get the project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Run the pre-commit script
exec "$PROJECT_ROOT/scripts/pre-commit-hook.sh"
EOF

    chmod +x "$PRE_COMMIT_HOOK"
    print_success "Manual Git pre-commit hook installed"
else
    print_warning "scripts/pre-commit-hook.sh not found"
fi

# Install additional development dependencies if needed
print_status "Checking development dependencies..."

MISSING_DEPS=()

# Check for required tools
if ! command -v black >/dev/null 2>&1; then
    MISSING_DEPS+=("black")
fi

if ! command -v isort >/dev/null 2>&1; then
    MISSING_DEPS+=("isort")
fi

if ! command -v flake8 >/dev/null 2>&1; then
    MISSING_DEPS+=("flake8")
fi

if ! command -v mypy >/dev/null 2>&1; then
    MISSING_DEPS+=("mypy")
fi

if ! command -v bandit >/dev/null 2>&1; then
    MISSING_DEPS+=("bandit")
fi

if ! command -v safety >/dev/null 2>&1; then
    MISSING_DEPS+=("safety")
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    print_status "Installing missing development dependencies: ${MISSING_DEPS[*]}"
    pip install "${MISSING_DEPS[@]}"
    print_success "Development dependencies installed"
else
    print_success "All development dependencies are already installed"
fi

echo ""
echo "🎉 Pre-commit setup complete!"
echo ""
echo "What was installed:"
echo "  ✅ pre-commit framework hooks (from .pre-commit-config.yaml)"
echo "  ✅ Manual Git pre-commit hook (scripts/pre-commit-hook.sh)"
echo "  ✅ Development dependencies (black, isort, flake8, mypy, etc.)"
echo ""
echo "How it works:"
echo "  • Every commit will automatically run code formatting, linting, type checking, and tests"
echo "  • If any check fails, the commit will be blocked until issues are fixed"
echo "  • This matches the same checks that run in GitHub Actions CI"
echo ""
echo "Manual commands:"
echo "  • Test pre-commit: ./scripts/pre-commit-hook.sh"
echo "  • Run pre-commit on all files: pre-commit run --all-files"
echo "  • Skip pre-commit for a commit: git commit --no-verify"
echo ""
echo "Happy coding! 🚀"
