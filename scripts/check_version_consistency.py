#!/usr/bin/env python3
"""
Script to check version consistency across the project.

This script verifies that the version in test_basic.py matches the version in pyproject.toml.
It's designed to be used as a pre-commit hook to prevent version mismatch issues.
"""

import re
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent

# Paths to files containing version information
pyproject_path = project_root / "pyproject.toml"
test_basic_path = project_root / "tests" / "test_basic.py"
init_path = project_root / "src" / "spec_server" / "__init__.py"
server_path = project_root / "src" / "spec_server" / "server.py"

# Regular expressions to extract version information
pyproject_version_pattern = r'version\s*=\s*"(v\d+\.\d+\.\d+)"'
test_version_pattern = r'assert __version__ == "(v\d+\.\d+\.\d+)"'
init_version_pattern = r'__version__ = "(v\d+\.\d+\.\d+)"'
server_version_pattern = r'version="(v?\d+\.\d+\.\d+)"'


def extract_version(file_path, pattern):
    """Extract version from a file using a regex pattern."""
    try:
        content = file_path.read_text()
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def main():
    """Main function to check version consistency."""
    # Extract versions
    pyproject_version = extract_version(pyproject_path, pyproject_version_pattern)
    test_version = extract_version(test_basic_path, test_version_pattern)
    init_version = extract_version(init_path, init_version_pattern)
    server_version = extract_version(server_path, server_version_pattern)

    # Normalize server version (add 'v' prefix if missing)
    if server_version and not server_version.startswith("v"):
        server_version = f"v{server_version}"

    # Print versions for debugging
    print(f"pyproject.toml version: {pyproject_version}")
    print(f"test_basic.py version: {test_version}")
    print(f"__init__.py version: {init_version}")
    print(f"server.py version: {server_version}")

    # Check for consistency
    versions = [
        v for v in [pyproject_version, test_version, init_version, server_version] if v
    ]
    if not versions:
        print("Error: Could not extract version information from any file")
        return 1

    reference_version = versions[0]
    consistent = all(v == reference_version for v in versions)

    if not consistent:
        print("\nERROR: Version mismatch detected!")
        if pyproject_version != reference_version:
            print(
                f"  - pyproject.toml: {pyproject_version} (expected: {reference_version})"
            )
        if test_version != reference_version:
            print(f"  - test_basic.py: {test_version} (expected: {reference_version})")
        if init_version != reference_version:
            print(f"  - __init__.py: {init_version} (expected: {reference_version})")
        if server_version != reference_version:
            print(f"  - server.py: {server_version} (expected: {reference_version})")
        print("\nPlease update all version references to be consistent.")
        return 1

    print("\nSuccess: All version references are consistent!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
