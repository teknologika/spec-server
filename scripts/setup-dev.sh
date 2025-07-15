#!/bin/bash
# Development environment setup script

set -e

echo "Setting up spec-server development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing development dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo "✓ Dependencies installed"

# Create specs directory if it doesn't exist
mkdir -p specs

echo "✓ Specs directory created"

# Run initial tests to verify setup
echo "Running initial tests..."
python -m pytest tests/ -v || echo "Note: Some tests may fail until implementation is complete"

echo "✓ Development environment setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "Next steps:"
echo "1. Run tests: pytest"
echo "2. Format code: black src tests"
echo "3. Check types: mypy src"
echo "4. Start development server: spec-server"