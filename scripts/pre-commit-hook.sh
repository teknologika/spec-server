#!/bin/bash
# Pre-commit hook script that matches GitHub Actions CI pipeline
# This script runs the same checks as the CI to catch issues early

set -e

echo "🔍 Running pre-commit checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Get the project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not detected. Attempting to activate..."
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        print_success "Activated .venv"
    elif [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        print_success "Activated venv"
    else
        print_warning "No virtual environment found. Proceeding with system Python..."
    fi
fi

# Function to run a command and capture its output
run_check() {
    local name="$1"
    local command="$2"

    print_status "Running $name..."

    if eval "$command" > /tmp/pre-commit-$name.log 2>&1; then
        print_success "$name passed"
        return 0
    else
        print_error "$name failed"
        echo "Output:"
        cat /tmp/pre-commit-$name.log
        return 1
    fi
}

# Initialize error counter
ERRORS=0

# 1. Code Formatting Checks
print_status "🎨 Code Formatting Checks"
echo "----------------------------------------"

if ! run_check "black-check" "black --check src tests"; then
    print_error "Code formatting issues found. Run: black src tests"
    ((ERRORS++))
fi

if ! run_check "isort-check" "isort --check-only src tests"; then
    print_error "Import sorting issues found. Run: isort src tests"
    ((ERRORS++))
fi

if ! run_check "flake8" "flake8 --max-line-length 200 src tests"; then
    print_error "Linting issues found. Check output above."
    ((ERRORS++))
fi

# 2. Type Checking
print_status "🔍 Type Checking"
echo "----------------------------------------"

if ! run_check "mypy" "mypy src/spec_server"; then
    print_error "Type checking failed. Check output above."
    ((ERRORS++))
fi

# 3. Security Checks
print_status "🔒 Security Checks"
echo "----------------------------------------"

if command -v bandit >/dev/null 2>&1; then
    if ! run_check "bandit" "bandit -r src/"; then
        print_warning "Security issues found. Review output above."
        # Don't increment errors for security warnings, just warn
    fi
else
    print_warning "bandit not installed. Install with: pip install bandit"
fi

if command -v safety >/dev/null 2>&1; then
    if ! run_check "safety" "safety check"; then
        print_warning "Dependency security issues found. Review output above."
        # Don't increment errors for security warnings, just warn
    fi
else
    print_warning "safety not installed. Install with: pip install safety"
fi

# 4. Package Validation
print_status "📦 Package Validation"
echo "----------------------------------------"

if [[ -f "scripts/validate-package.py" ]]; then
    if ! run_check "package-validation" "python scripts/validate-package.py"; then
        print_error "Package validation failed. Check output above."
        ((ERRORS++))
    fi
else
    print_warning "Package validation script not found"
fi

# 5. Tests
print_status "🧪 Running Tests"
echo "----------------------------------------"

if ! run_check "pytest" "pytest --tb=short -q"; then
    print_error "Tests failed. Run: pytest for detailed output"
    ((ERRORS++))
fi

# 6. Clean up temporary files
rm -f /tmp/pre-commit-*.log

# Final result
echo ""
echo "========================================"
if [[ $ERRORS -eq 0 ]]; then
    print_success "All pre-commit checks passed! 🎉"
    echo "Your commit is ready to be pushed."
    exit 0
else
    print_error "Pre-commit checks failed with $ERRORS error(s)"
    echo ""
    echo "Please fix the issues above before committing."
    echo "You can run individual commands to fix issues:"
    echo "  - Format code: black src tests && isort src tests"
    echo "  - Fix linting: flake8 --max-line-length 200 src tests"
    echo "  - Type check: mypy src/spec_server"
    echo "  - Run tests: pytest"
    echo ""
    echo "Or run all checks manually: ./scripts/build.sh"
    exit 1
fi
