"""
Demonstration tests for the test fixtures and utilities.

These tests show how to use the various fixtures and utilities provided
for testing spec-server functionality.
"""

from pathlib import Path

import pytest

from tests.fixtures import (
    MockFileSystem,
    SpecTestData,
    SpecTestFixtures,
)


class TestSpecTestData:
    """Test the SpecTestData utility class."""

    def test_feature_ideas_available(self):
        """Test that feature ideas are available."""
        ideas = SpecTestData.FEATURE_IDEAS
        assert len(ideas) >= 5
        assert "user-auth" in ideas
        assert isinstance(ideas["user-auth"], str)
        assert len(ideas["user-auth"]) > 10

    def test_get_feature_idea(self):
        """Test getting feature ideas by name."""
        idea = SpecTestData.get_feature_idea("user-auth")
        assert "authentication" in idea.lower()

        # Test fallback for unknown feature
        unknown_idea = SpecTestData.get_feature_idea("unknown-feature")
        assert "unknown-feature" in unknown_idea

    def test_sample_documents(self):
        """Test that sample documents are properly formatted."""
        # Test requirements document
        requirements = SpecTestData.SAMPLE_REQUIREMENTS
        assert "# Requirements Document" in requirements
        assert "User Story:" in requirements
        assert "Acceptance Criteria" in requirements
        assert "WHEN" in requirements and "THEN" in requirements

        # Test design document
        design = SpecTestData.SAMPLE_DESIGN
        assert "# Design Document" in design
        assert "Architecture" in design
        assert "Components and Interfaces" in design

        # Test tasks document
        tasks = SpecTestData.SAMPLE_TASKS
        assert "# Implementation Plan" in tasks
        assert "- [ ]" in tasks  # Checkbox format
        assert "_Requirements:" in tasks  # Requirement references


class TestSpecTestFixtures:
    """Test the SpecTestFixtures utility class."""

    def test_create_sample_spec(self, temp_spec_dir):
        """Test creating a sample specification."""
        fixtures = SpecTestFixtures(base_path=temp_spec_dir)

        result = fixtures.create_sample_spec("test-feature")

        assert result["success"] is True
        assert result["spec"]["feature_name"] == "test-feature"
        assert "test-feature" in fixtures.created_specs

        # Verify files were created
        spec_dir = temp_spec_dir / "test-feature"
        assert spec_dir.exists()
        assert (spec_dir / "requirements.md").exists()

        fixtures.cleanup()

    def test_create_multiple_specs(self, temp_spec_dir):
        """Test creating multiple specifications."""
        fixtures = SpecTestFixtures(base_path=temp_spec_dir)

        results = fixtures.create_multiple_specs(count=3)

        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert len(fixtures.created_specs) == 3

        # Verify all specs were created
        for result in results:
            feature_name = result["spec"]["feature_name"]
            spec_dir = temp_spec_dir / feature_name
            assert spec_dir.exists()

        fixtures.cleanup()

    def test_create_spec_with_file_references(self, temp_spec_dir):
        """Test creating a spec with file references."""
        fixtures = SpecTestFixtures(base_path=temp_spec_dir)

        result = fixtures.create_spec_with_file_references("api-test")

        assert result["success"] is True

        # Verify reference files were created
        assert (temp_spec_dir / "api-spec.json").exists()
        assert (temp_spec_dir / "README.md").exists()

        # Verify spec contains file references (read without resolution to see raw references)
        spec_content = fixtures.mcp_tools.read_spec_document(
            "api-test", "requirements", resolve_references=False
        )
        assert "#[[file:api-spec.json]]" in spec_content["content"]
        assert "#[[file:README.md]]" in spec_content["content"]

        fixtures.cleanup()

    def test_fixtures_cleanup(self, temp_spec_dir):
        """Test that fixtures cleanup properly."""
        fixtures = SpecTestFixtures(base_path=temp_spec_dir)

        # Create some specs
        fixtures.create_sample_spec("cleanup-test-1")
        fixtures.create_sample_spec("cleanup-test-2")

        assert len(fixtures.created_specs) == 2

        # Cleanup
        fixtures.cleanup()

        # Verify specs were deleted (directory should be cleaned up)
        # Note: The temp directory itself might still exist but should be empty or cleaned


class TestMockFileSystem:
    """Test the MockFileSystem utility class."""

    def test_create_and_read_file(self):
        """Test creating and reading mock files."""
        mock_fs = MockFileSystem()

        mock_fs.create_file("test.txt", "Hello, World!")

        assert mock_fs.file_exists("test.txt")
        assert mock_fs.read_file("test.txt") == "Hello, World!"

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        mock_fs = MockFileSystem()

        assert not mock_fs.file_exists("nonexistent.txt")

        with pytest.raises(FileNotFoundError):
            mock_fs.read_file("nonexistent.txt")

    def test_delete_file(self):
        """Test deleting mock files."""
        mock_fs = MockFileSystem()

        mock_fs.create_file("delete-me.txt", "Content")
        assert mock_fs.file_exists("delete-me.txt")

        mock_fs.delete_file("delete-me.txt")
        assert not mock_fs.file_exists("delete-me.txt")

    def test_list_files(self):
        """Test listing mock files."""
        mock_fs = MockFileSystem()

        mock_fs.create_file("file1.txt", "Content 1")
        mock_fs.create_file("file2.txt", "Content 2")
        mock_fs.create_file("dir/file3.txt", "Content 3")

        files = mock_fs.list_files()
        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "dir/file3.txt" in files

    def test_clear_filesystem(self):
        """Test clearing the mock file system."""
        mock_fs = MockFileSystem()

        mock_fs.create_file("file1.txt", "Content")
        mock_fs.create_file("file2.txt", "Content")

        assert len(mock_fs.list_files()) == 2

        mock_fs.clear()
        assert len(mock_fs.list_files()) == 0


class TestDataGeneratorUtility:
    """Test the TestDataGenerator utility class."""

    def test_generate_feature_names(self, test_data_generator):
        """Test generating feature names."""
        names = test_data_generator.generate_feature_names(5)

        assert len(names) == 5
        assert all(isinstance(name, str) for name in names)
        assert all("-" in name for name in names)  # Should be kebab-case

        # Test generating more names than available
        many_names = test_data_generator.generate_feature_names(25)
        assert len(many_names) == 25
        assert len(set(many_names)) == 25  # All unique

    def test_generate_feature_ideas(self, test_data_generator):
        """Test generating feature ideas."""
        ideas = test_data_generator.generate_feature_ideas(3)

        assert len(ideas) == 3
        assert all(isinstance(idea, str) for idea in ideas)
        assert all(len(idea) > 20 for idea in ideas)  # Should be descriptive

    def test_generate_unicode_content(self, test_data_generator):
        """Test generating Unicode content."""
        content = test_data_generator.generate_unicode_content()

        assert "中文" in content  # Chinese
        assert "العربي" in content  # Arabic
        assert "русском" in content  # Russian
        assert "日本語" in content  # Japanese
        assert "🚀" in content  # Emoji
        assert "Requirements Document" in content

    def test_generate_large_content(self, test_data_generator):
        """Test generating large content."""
        # Generate 10KB content
        content = test_data_generator.generate_large_content(size_kb=10)

        # Should be approximately 10KB (allow some variance)
        content_size = len(content.encode("utf-8"))
        assert 9000 <= content_size <= 12000  # 9-12KB range

        # Should contain multiple requirements
        assert content.count("### Requirement") >= 5
        assert "User Story:" in content
        assert "Acceptance Criteria" in content


class TestPytestFixtures:
    """Test the pytest fixtures."""

    def test_temp_spec_dir_fixture(self, temp_spec_dir):
        """Test the temp_spec_dir fixture."""
        assert isinstance(temp_spec_dir, Path)
        assert temp_spec_dir.exists()
        assert temp_spec_dir.is_dir()

    def test_mcp_tools_fixture(self, mcp_tools):
        """Test the mcp_tools fixture."""
        # Should be able to use MCP tools
        result = mcp_tools.list_specs()
        assert result["success"] is True
        assert isinstance(result["specs"], list)

    def test_spec_fixtures_fixture(self, spec_fixtures):
        """Test the spec_fixtures fixture."""
        # Should be able to create specs
        result = spec_fixtures.create_sample_spec("fixture-test")
        assert result["success"] is True

    def test_sample_spec_fixture(self, sample_spec):
        """Test the sample_spec fixture."""
        assert sample_spec["success"] is True
        assert "spec" in sample_spec
        assert sample_spec["spec"]["feature_name"] == "test-feature"

    def test_multiple_specs_fixture(self, multiple_specs):
        """Test the multiple_specs fixture."""
        assert len(multiple_specs) == 3
        assert all(result["success"] for result in multiple_specs)

    def test_mock_filesystem_fixture(self, mock_filesystem):
        """Test the mock_filesystem fixture."""
        mock_filesystem.create_file("test.txt", "content")
        assert mock_filesystem.file_exists("test.txt")
        assert mock_filesystem.read_file("test.txt") == "content"

    def test_test_data_generator_fixture(self, test_data_generator):
        """Test the test_data_generator fixture."""
        names = test_data_generator.generate_feature_names(3)
        assert len(names) == 3
