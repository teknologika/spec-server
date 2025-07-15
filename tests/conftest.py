"""
Pytest configuration and fixtures for spec-server tests.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_specs_dir():
    """Create a temporary directory for specs during testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_spec_data():
    """Provide sample spec data for testing."""
    return {
        "feature_name": "test-feature",
        "initial_idea": "A test feature for unit testing purposes",
        "requirements": "# Test Requirements\n\nThis is a test requirements document.",
        "design": "# Test Design\n\nThis is a test design document.",
        "tasks": "# Test Tasks\n\n- [ ] 1. First test task\n- [ ] 2. Second test task",
    }
