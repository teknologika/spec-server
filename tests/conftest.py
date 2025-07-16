"""
Pytest configuration and fixtures for spec-server tests.
"""

import tempfile
from pathlib import Path

import pytest

from spec_server.mcp_tools import MCPTools
from tests.fixtures import MockFileSystem, SpecTestFixtures, TestDataGenerator


@pytest.fixture
def temp_specs_dir():
    """Provide a temporary directory for spec testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    
# Keep the old fixture name for backward compatibility
@pytest.fixture
def temp_spec_dir():
    """Provide a temporary directory for spec testing (alias for temp_specs_dir)."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mcp_tools(temp_specs_dir):
    """Provide MCPTools instance with temporary directory."""
    return MCPTools(base_path=temp_specs_dir)


@pytest.fixture
def spec_fixtures(temp_specs_dir):
    """Provide SpecTestFixtures instance."""
    fixtures = SpecTestFixtures(base_path=temp_specs_dir)
    yield fixtures
    fixtures.cleanup()


@pytest.fixture
def sample_spec(spec_fixtures):
    """Provide a sample specification for testing."""
    result = spec_fixtures.create_sample_spec("test-feature")
    return result


@pytest.fixture
def spec_with_tasks(spec_fixtures):
    """Provide a specification advanced to tasks phase."""
    result = spec_fixtures.get_spec_with_tasks("task-test-feature")
    return result


@pytest.fixture
def multiple_specs(spec_fixtures):
    """Provide multiple sample specifications."""
    results = spec_fixtures.create_multiple_specs(count=3)
    return results


@pytest.fixture
def mock_filesystem():
    """Provide a mock file system for testing."""
    return MockFileSystem()


@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator()
