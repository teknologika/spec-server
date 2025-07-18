#!/bin/bash
# Installation script for spec-server

set -e

echo "🚀 Installing spec-server..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
REQUIRED_VERSION="3.12"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
    echo "❌ Python 3.12 or higher is required. Found: Python $PYTHON_VERSION"
    echo "Please install Python 3.12+ and try again."
    exit 1
fi

echo "✅ Python version check passed: Python $PYTHON_VERSION"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not available. Please install pip and try again."
    exit 1
fi

# Install spec-server
echo "📦 Installing spec-server from PyPI..."
pip3 install spec-server

# Verify installation
echo "🔍 Verifying installation..."
if command -v spec-server &> /dev/null; then
    echo "✅ spec-server installed successfully!"
    echo "📋 Version: $(spec-server --version)"
else
    echo "❌ Installation verification failed. spec-server command not found."
    exit 1
fi

# Create default configuration directory
CONFIG_DIR="$HOME/.spec-server"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "📁 Creating configuration directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Create default specs directory
SPECS_DIR="$HOME/specs"
if [ ! -d "$SPECS_DIR" ]; then
    echo "📁 Creating specs directory: $SPECS_DIR"
    mkdir -p "$SPECS_DIR"
fi

# Create sample configuration file
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚙️ Creating sample configuration file: $CONFIG_FILE"
    cat > "$CONFIG_FILE" << EOF
{
  "specs_dir": "$SPECS_DIR",
  "backup_dir": "$CONFIG_DIR/backups",
  "host": "127.0.0.1",
  "port": 8765,
  "transport": "stdio",
  "log_level": "INFO",
  "auto_backup": true,
  "cache_enabled": true,
  "max_specs": 1000,
  "strict_validation": true
}
EOF
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📖 Quick Start:"
echo "   1. Test the installation:"
echo "      spec-server --help"
echo ""
echo "   2. Start the server with stdio transport:"
echo "      spec-server"
echo ""
echo "   3. Start the server with SSE transport:"
echo "      spec-server sse 8765"
echo ""
echo "   4. Configuration file: $CONFIG_FILE"
echo "   5. Specs directory: $SPECS_DIR"
echo ""
echo "📚 For more information, visit:"
echo "   https://github.com/teknologika/spec-server"
