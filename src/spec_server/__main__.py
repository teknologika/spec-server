"""
Main module for running spec-server as a package.
This allows running the server with:
    python -m spec_server [args]
"""

import sys

from .main import main

if __name__ == "__main__":
    main()
    sys.exit(0)
