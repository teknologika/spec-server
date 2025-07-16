"""
Tests for the input validation and sanitization system.
"""

# No path import needed

import pytest

from spec_server.errors import ErrorCode, SpecError
from spec_server.validation import (
    InputValidator,
    ValidationResult,
    validate_create_spec_params,
    validate_read_spec_params,
    validate_task_params,
    validate_update_spec_params,
)


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_validate_feature_name_valid(self):
        """Test validating valid feature names."""
        valid_names = [
            "user-auth",
            "data-export",
            "api-v2",
            "simple-feature",
            "feature123",
            "a",
            "test-feature-with-multiple-parts",
        ]

        for name in valid_names:
            result = InputValidator.validate_feature_name(name)
            assert result.is_valid, f"'{name}' should be valid"
            assert result.sanitized_value == name.lower()

    def test_validate_feature_name_invalid(self):
        """Test validating invalid feature names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "User-Auth",  # Uppercase
            "user_auth",  # Underscore
            "user auth",  # Space
            "user-",  # Trailing hyphen
            "-user",  # Leading hyphen
            "user--auth",  # Double hyphen
            "user.auth",  # Dot
            "user@auth",  # Special character
            "a" * 51,  # Too long
        ]

        for name in invalid_names:
            result = InputValidator.validate_feature_name(name)
            assert not result.is_valid, f"'{name}' should be invalid"
            assert result.sanitized_value is None

    def test_validate_feature_name_sanitization(self):
        """Test feature name sanitization."""
        # Test with valid input that needs sanitization
        result = InputValidator.validate_feature_name("  user-auth  ")
        assert result.is_valid
        assert result.sanitized_value == "user-auth"

        # Test that invalid format (uppercase) is rejected even with whitespace
        result = InputValidator.validate_feature_name("  User-Auth  ")
        assert not result.is_valid

    def test_validate_feature_name_reserved_warning(self):
        """Test warning for reserved feature names."""
        result = InputValidator.validate_feature_name("test")
        assert result.is_valid
        assert len(result.warnings) > 0
        assert "reserved name" in result.warnings[0]

    def test_validate_document_type_valid(self):
        """Test validating valid document types."""
        valid_types = ["requirements", "design", "tasks"]

        for doc_type in valid_types:
            result = InputValidator.validate_document_type(doc_type)
            assert result.is_valid
            assert result.sanitized_value == doc_type

    def test_validate_document_type_case_insensitive(self):
        """Test document type validation is case insensitive."""
        result = InputValidator.validate_document_type("REQUIREMENTS")
        assert result.is_valid
        assert result.sanitized_value == "requirements"

    def test_validate_document_type_invalid(self):
        """Test validating invalid document types."""
        invalid_types = ["", "invalid", "spec", "readme", None]

        for doc_type in invalid_types:
            result = InputValidator.validate_document_type(doc_type)
            assert not result.is_valid

    def test_validate_document_content_valid(self):
        """Test validating valid document content."""
        valid_content = [
            "# Simple content",
            "Multi-line\ncontent\nwith\nnewlines",
            "Content with special chars: !@#$%^&*()",
            "A" * 1000,  # Long but not too long
        ]

        for content in valid_content:
            result = InputValidator.validate_document_content(content)
            assert result.is_valid
            assert result.sanitized_value is not None

    def test_validate_document_content_line_ending_normalization(self):
        """Test document content line ending normalization."""
        content_with_crlf = "Line 1\r\nLine 2\r\nLine 3"
        result = InputValidator.validate_document_content(content_with_crlf)
        assert result.is_valid
        assert "\r\n" not in result.sanitized_value
        assert result.sanitized_value == "Line 1\nLine 2\nLine 3"

    def test_validate_document_content_too_large(self):
        """Test document content that's too large."""
        large_content = "A" * (InputValidator.MAX_DOCUMENT_CONTENT_LENGTH + 1)
        result = InputValidator.validate_document_content(large_content)
        assert not result.is_valid
        assert "too large" in result.errors[0]

    def test_validate_document_content_dangerous_patterns(self):
        """Test detection of dangerous patterns in content."""
        dangerous_content = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
        ]

        for content in dangerous_content:
            result = InputValidator.validate_document_content(content)
            assert result.is_valid  # Still valid but with warnings
            assert len(result.warnings) > 0

    def test_validate_initial_idea_valid(self):
        """Test validating valid initial ideas."""
        valid_ideas = [
            "This is a simple feature idea that meets minimum length",
            "A" * 100,  # Long idea
            "Feature with special chars: !@#$%^&*()",
        ]

        for idea in valid_ideas:
            result = InputValidator.validate_initial_idea(idea)
            assert result.is_valid
            assert result.sanitized_value == idea.strip()

    def test_validate_initial_idea_invalid(self):
        """Test validating invalid initial ideas."""
        invalid_ideas = [
            "",  # Empty
            "   ",  # Whitespace only
            "short",  # Too short
            "A" * (InputValidator.MAX_IDEA_LENGTH + 1),  # Too long
            None,  # None
        ]

        for idea in invalid_ideas:
            result = InputValidator.validate_initial_idea(idea)
            assert not result.is_valid

    def test_validate_task_identifier_valid(self):
        """Test validating valid task identifiers."""
        valid_identifiers = [
            None,  # None is valid (means get next task)
            "1",
            "1.2",
            "2.3.1",
            "10.20.30",
        ]

        for task_id in valid_identifiers:
            result = InputValidator.validate_task_identifier(task_id)
            assert result.is_valid
            assert result.sanitized_value == task_id

    def test_validate_task_identifier_invalid(self):
        """Test validating invalid task identifiers."""
        invalid_identifiers = [
            "",  # Empty string
            "   ",  # Whitespace only
            "a",  # Non-numeric
            "1.a",  # Mixed
            "1.",  # Trailing dot
            ".1",  # Leading dot
            "1..2",  # Double dot
            "A" * 25,  # Too long
        ]

        for task_id in invalid_identifiers:
            result = InputValidator.validate_task_identifier(task_id)
            assert not result.is_valid

    def test_validate_file_path_valid(self):
        """Test validating valid file paths."""
        valid_paths = [
            "file.txt",
            "dir/file.txt",
            "deep/nested/path/file.md",
            "file-with-hyphens.txt",
        ]

        for path in valid_paths:
            result = InputValidator.validate_file_path(path)
            assert result.is_valid

    def test_validate_file_path_dangerous(self):
        """Test detecting dangerous file paths."""
        dangerous_paths = [
            "../../../etc/passwd",  # Directory traversal
            "/etc/passwd",  # Absolute path
            "~/secret.txt",  # Home directory
            "file; rm -rf /",  # Command injection
            "file | cat",  # Pipe
            "file && rm file",  # Command chaining
        ]

        for path in dangerous_paths:
            result = InputValidator.validate_file_path(path)
            assert not result.is_valid

    def test_validate_file_path_suspicious_extensions(self):
        """Test warning for suspicious file extensions."""
        suspicious_files = ["script.exe", "batch.bat", "shell.sh", "powershell.ps1"]

        for path in suspicious_files:
            result = InputValidator.validate_file_path(path, allow_absolute=True)
            # Should be valid but with warnings
            assert len(result.warnings) > 0

    def test_validate_boolean_valid(self):
        """Test validating boolean values."""
        true_values = [True, "true", "1", "yes", "on", 1, 1.0]
        false_values = [False, "false", "0", "no", "off", "", 0, 0.0, None]

        for value in true_values:
            result = InputValidator.validate_boolean(value, "test_field")
            assert result.is_valid
            assert result.sanitized_value is True

        for value in false_values:
            result = InputValidator.validate_boolean(value, "test_field")
            assert result.is_valid
            assert result.sanitized_value is False

    def test_validate_boolean_invalid(self):
        """Test validating invalid boolean values."""
        invalid_values = ["maybe", "invalid", [], {}]

        for value in invalid_values:
            result = InputValidator.validate_boolean(value, "test_field")
            assert not result.is_valid


class TestValidationFunctions:
    """Test cases for validation helper functions."""

    def test_validate_create_spec_params_valid(self):
        """Test validating valid create_spec parameters."""
        result = validate_create_spec_params(
            "test-feature", "This is a valid feature idea"
        )

        assert result["feature_name"] == "test-feature"
        assert result["initial_idea"] == "This is a valid feature idea"

    def test_validate_create_spec_params_invalid_name(self):
        """Test validating create_spec with invalid feature name."""
        with pytest.raises(SpecError) as exc_info:
            validate_create_spec_params("Invalid Name!", "Valid idea")

        assert exc_info.value.error_code == ErrorCode.SPEC_INVALID_NAME

    def test_validate_create_spec_params_invalid_idea(self):
        """Test validating create_spec with invalid initial idea."""
        with pytest.raises(SpecError) as exc_info:
            validate_create_spec_params("valid-name", "short")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_validate_update_spec_params_valid(self):
        """Test validating valid update_spec_document parameters."""
        result = validate_update_spec_params(
            "test-feature", "requirements", "# Requirements\n\nValid content", True
        )

        assert result["feature_name"] == "test-feature"
        assert result["document_type"] == "requirements"
        assert result["content"] == "# Requirements\n\nValid content"
        assert result["phase_approval"] is True

    def test_validate_update_spec_params_invalid_type(self):
        """Test validating update_spec_document with invalid document type."""
        with pytest.raises(SpecError) as exc_info:
            validate_update_spec_params("valid-name", "invalid-type", "content", False)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_validate_read_spec_params_valid(self):
        """Test validating valid read_spec_document parameters."""
        result = validate_read_spec_params("test-feature", "design", False)

        assert result["feature_name"] == "test-feature"
        assert result["document_type"] == "design"
        assert result["resolve_references"] is False

    def test_validate_task_params_valid(self):
        """Test validating valid task parameters."""
        result = validate_task_params("test-feature", "1.2")

        assert result["feature_name"] == "test-feature"
        assert result["task_identifier"] == "1.2"

    def test_validate_task_params_none_identifier(self):
        """Test validating task parameters with None identifier."""
        result = validate_task_params("test-feature", None)

        assert result["feature_name"] == "test-feature"
        assert result["task_identifier"] is None

    def test_validate_task_params_invalid_identifier(self):
        """Test validating task parameters with invalid identifier."""
        with pytest.raises(SpecError) as exc_info:
            validate_task_params("valid-name", "invalid-id")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR


class TestValidationResult:
    """Test cases for ValidationResult model."""

    def test_create_valid_result(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(
            is_valid=True, sanitized_value="test-value", errors=[], warnings=["warning"]
        )

        assert result.is_valid is True
        assert result.sanitized_value == "test-value"
        assert result.errors == []
        assert result.warnings == ["warning"]

    def test_create_invalid_result(self):
        """Test creating an invalid ValidationResult."""
        result = ValidationResult(is_valid=False, errors=["error1", "error2"])

        assert result.is_valid is False
        assert result.sanitized_value is None
        assert result.errors == ["error1", "error2"]
        assert result.warnings == []
