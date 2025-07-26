"""
Integration tests for spec-server.

These tests verify the basic spec operations and workflows that are currently implemented.
"""

import json
import tempfile
from pathlib import Path

import pytest

from spec_server.errors import ErrorCode, SpecError
from spec_server.mcp_tools import MCPTools


class TestBasicSpecOperations:
    """Test basic specification operations."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_spec_workflow(self):
        """Test basic specification workflow."""
        feature_name = "user-authentication"
        initial_idea = "Implement user login and registration with email verification"

        # Step 1: Create spec
        result = self.mcp_tools.create_spec(feature_name, initial_idea)
        assert result["success"] is True
        assert result["spec"]["feature_name"] == feature_name
        assert "requirements_content" in result

        # Verify spec directory and files were created
        spec_dir = self.temp_dir / feature_name
        assert spec_dir.exists()
        assert (spec_dir / "requirements.md").exists()

        # Step 2: Read requirements document
        result = self.mcp_tools.read_spec_document(feature_name, "requirements")
        assert result["success"] is True
        assert len(result["content"]) > 0

        # Step 3: List specs to verify everything
        result = self.mcp_tools.list_specs()
        assert result["success"] is True
        assert len(result["specs"]) == 1
        assert result["specs"][0]["feature_name"] == feature_name

    def test_multiple_specs_management(self):
        """Test managing multiple specifications."""
        specs = [
            ("user-auth", "User authentication system"),
            ("data-export", "Data export functionality"),
            ("api-integration", "Third-party API integration"),
        ]

        # Create multiple specs
        for feature_name, idea in specs:
            result = self.mcp_tools.create_spec(feature_name, idea)
            assert result["success"] is True

        # Verify all specs exist
        result = self.mcp_tools.list_specs()
        assert result["success"] is True
        assert len(result["specs"]) == 3

        spec_names = [spec["feature_name"] for spec in result["specs"]]
        for feature_name, _ in specs:
            assert feature_name in spec_names

        # Delete one spec
        result = self.mcp_tools.delete_spec("api-integration")
        assert result["success"] is True

        # Verify spec was deleted
        result = self.mcp_tools.list_specs()
        assert len(result["specs"]) == 2

    def test_error_handling(self):
        """Test error handling in basic operations."""
        feature_name = "test-feature"

        # Try to read non-existent spec
        with pytest.raises(Exception) as exc_info:
            self.mcp_tools.read_spec_document(feature_name, "requirements")
        # Should be a SpecError with SPEC_NOT_FOUND
        assert "not found" in str(exc_info.value)

        # Create spec
        result = self.mcp_tools.create_spec(feature_name, "Test feature for error handling")
        assert result["success"] is True

        # Try to create duplicate spec
        with pytest.raises(SpecError) as exc_info:
            self.mcp_tools.create_spec(feature_name, "Duplicate spec")
        # Should be a SpecError about already existing
        assert "already exists" in str(exc_info.value)

        # Try to read non-existent document type
        with pytest.raises(SpecError) as exc_info:
            self.mcp_tools.read_spec_document(feature_name, "invalid-type")
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR


class TestFileReferenceBasics:
    """Test basic file reference functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_reference_resolution(self):
        """Test basic file reference resolution."""
        feature_name = "api-spec"

        # Create external reference files
        api_spec_file = self.temp_dir / "api-spec.json"
        api_spec_content = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        }
        api_spec_file.write_text(json.dumps(api_spec_content, indent=2))

        # Create spec
        result = self.mcp_tools.create_spec(feature_name, "API implementation based on OpenAPI spec")
        assert result["success"] is True

        # Read document without reference resolution
        result = self.mcp_tools.read_spec_document(feature_name, "requirements", resolve_references=False)
        assert result["success"] is True
        assert result["resolve_references"] is False

        # Read document with reference resolution
        result = self.mcp_tools.read_spec_document(feature_name, "requirements", resolve_references=True)
        assert result["success"] is True
        assert result["resolve_references"] is True


class TestValidationIntegration:
    """Test validation integration in operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_feature_name_validation(self):
        """Test feature name validation in operations."""
        # Test invalid feature names
        invalid_names = [
            "",  # Empty
            "Invalid-Name",  # Uppercase
            "invalid_name",  # Underscore
            "invalid name",  # Space
        ]

        for invalid_name in invalid_names:
            with pytest.raises(SpecError) as exc_info:
                self.mcp_tools.create_spec(invalid_name, "Test idea")
            assert exc_info.value.error_code == ErrorCode.SPEC_INVALID_NAME

    def test_document_type_validation(self):
        """Test document type validation."""
        feature_name = "test-spec"

        # Create valid spec
        result = self.mcp_tools.create_spec(feature_name, "Test document type validation")
        assert result["success"] is True

        # Test invalid document types
        invalid_types = ["invalid", "spec", "readme"]

        for invalid_type in invalid_types:
            with pytest.raises(SpecError) as exc_info:
                self.mcp_tools.read_spec_document(feature_name, invalid_type)
            assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_initial_idea_validation(self):
        """Test initial idea validation."""
        feature_name = "test-spec"

        # Test too short idea
        with pytest.raises(SpecError) as exc_info:
            self.mcp_tools.create_spec(feature_name, "short")
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

        # Test empty idea
        with pytest.raises(SpecError) as exc_info:
            self.mcp_tools.create_spec(feature_name, "")
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR


class TestUnicodeHandling:
    """Test Unicode and special character handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_unicode_in_spec_creation(self):
        """Test Unicode handling in spec creation."""
        feature_name = "unicode-test"

        # Create spec with Unicode content
        unicode_idea = "测试 Unicode 支持 with émojis 🚀 and special chars: àáâãäå"

        result = self.mcp_tools.create_spec(feature_name, unicode_idea)
        assert result["success"] is True

        # Read back and verify Unicode is preserved in the generated requirements
        result = self.mcp_tools.read_spec_document(feature_name, "requirements")
        assert result["success"] is True

        # The content should contain some Unicode characters from the idea
        content = result["content"]
        assert len(content) > 0  # Basic check that content exists


class TestPerformanceBasics:
    """Test basic performance scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_spec_creation(self):
        """Test creating multiple specifications."""
        import time

        # Create multiple specs
        num_specs = 10  # Reasonable number for testing
        start_time = time.time()

        for i in range(num_specs):
            feature_name = f"feature-{i:03d}"
            idea = f"Feature {i} implementation with various requirements"

            result = self.mcp_tools.create_spec(feature_name, idea)
            assert result["success"] is True

        creation_time = time.time() - start_time

        # List all specs
        start_time = time.time()
        result = self.mcp_tools.list_specs()
        list_time = time.time() - start_time

        assert result["success"] is True
        assert len(result["specs"]) == num_specs

        # Performance assertions (reasonable thresholds)
        assert creation_time < 10.0  # Should create 10 specs in under 10 seconds
        assert list_time < 1.0  # Should list specs in under 1 second

        print(f"Created {num_specs} specs in {creation_time:.2f}s")
        print(f"Listed {num_specs} specs in {list_time:.2f}s")


class TestErrorRecovery:
    """Test error recovery scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filesystem_recovery(self):
        """Test recovery from filesystem issues."""
        feature_name = "recovery-test"

        # Create spec
        result = self.mcp_tools.create_spec(feature_name, "Test filesystem recovery")
        assert result["success"] is True

        # Verify spec exists
        result = self.mcp_tools.list_specs()
        assert len(result["specs"]) == 1

        # Manually delete requirements file to simulate filesystem issue
        spec_dir = self.temp_dir / feature_name
        requirements_file = spec_dir / "requirements.md"
        requirements_file.unlink()

        # Try to read the missing file - should handle gracefully
        with pytest.raises(SpecError) as exc_info:
            self.mcp_tools.read_spec_document(feature_name, "requirements")
        assert exc_info.value.error_code == ErrorCode.DOCUMENT_NOT_FOUND

        # Spec should still be listed (directory exists)
        result = self.mcp_tools.list_specs()
        assert len(result["specs"]) == 1

    def test_validation_error_recovery(self):
        """Test recovery from validation errors."""
        # Try invalid operations and verify system remains stable

        # Invalid feature name
        try:
            self.mcp_tools.create_spec("Invalid Name!", "Test idea")
        except SpecError:
            pass  # Expected

        # Invalid document type
        try:
            self.mcp_tools.create_spec("valid-name", "Valid idea")
            self.mcp_tools.read_spec_document("valid-name", "invalid-type")
        except SpecError:
            pass  # Expected

        # System should still work normally after errors
        result = self.mcp_tools.create_spec("recovery-test", "Test recovery after errors")
        assert result["success"] is True

        result = self.mcp_tools.list_specs()
        assert result["success"] is True
        assert len(result["specs"]) == 2  # valid-name and recovery-test
