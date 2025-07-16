"""
Main module for running spec-server as a package.
This allows running the server with:
    python -m spec_server [args]
"""
from .main import main
import sys

if __name__ == "__main__":
    sys.exit(main())