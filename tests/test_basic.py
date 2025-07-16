"""
Basic tests to verify project structure and imports.
"""

from spec_server import __author__, __version__
from spec_server.main import main
from spec_server.server import create_server


def test_version():
    """Test that version is defined."""
    assert __version__ == "v0.2.0"


def test_author():
    """Test that author is defined."""
    assert __author__ == "Teknologika"


def test_create_server():
    """Test that server can be created."""
    server = create_server()
    assert server is not None
    assert server.name == "spec-server"


def test_main_function_exists():
    """Test that main function exists and is callable."""
    assert callable(main)
