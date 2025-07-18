#!/bin/bash
# Development environment setup script for spec-server

set -e

echo "🚀 Setting up spec-server development environment..."

# Check if Python 3.12+ is available
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or later is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -e ".[dev]"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p specs
mkdir -p backups
mkdir -p logs

# Create example configuration file
echo "⚙️ Creating example configuration file..."
cat > spec-server.example.json << 'EOF'
{
  "_comments": {
    "host": "Host to bind to for SSE transport",
    "port": "Port to listen on for SSE transport",
    "transport": "Transport protocol: 'stdio' or 'sse'",
    "specs_dir": "Directory where specifications are stored",
    "max_specs": "Maximum number of specifications allowed",
    "max_document_size": "Maximum size of a single document in bytes",
    "auto_backup": "Whether to automatically backup specifications",
    "backup_dir": "Directory for storing backups",
    "strict_validation": "Enable strict input validation",
    "allow_dangerous_paths": "Allow potentially dangerous file paths (not recommended)",
    "log_level": "Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    "log_file": "Path to log file (null for console only)",
    "cache_enabled": "Enable caching for better performance",
    "cache_size": "Maximum number of items in cache"
  },
  "host": "127.0.0.1",
  "port": 8000,
  "transport": "stdio",
  "specs_dir": "specs",
  "max_specs": 1000,
  "max_document_size": 1000000,
  "auto_backup": true,
  "backup_dir": "backups",
  "strict_validation": true,
  "allow_dangerous_paths": false,
  "log_level": "INFO",
  "log_file": null,
  "cache_enabled": true,
  "cache_size": 100
}
EOF

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
python -m pytest --tb=short

# Check code quality
echo "✨ Checking code quality..."
python -m black --check src tests || echo "⚠️ Code formatting issues found. Run 'python -m black src tests' to fix."
python -m isort --check-only src tests || echo "⚠️ Import sorting issues found. Run 'python -m isort src tests' to fix."
python -m flake8 src tests || echo "⚠️ Linting issues found."

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate the virtual environment: source .venv/bin/activate"
echo "   2. Run the server: spec-server"
echo "   3. Or run with SSE transport: spec-server sse --port 8000"
echo "   4. Run tests: python -m pytest"
echo "   5. Format code: python -m black src tests"
echo "   6. Sort imports: python -m isort src tests"
echo ""
echo "📖 For more information, see README.md"
