"""
Tests for the structured error handling system.
"""

import pytest
from spec_server.errors import (
    ErrorCode, ErrorSeverity, ErrorSuggestion, SpecError, ErrorFactory,
    format_error_response
)


class TestErrorSuggestion:
    """Test cases for ErrorSuggestion model."""

    def test_create_suggestion(self):
        """Test creating an error suggestion."""
        suggestion = ErrorSuggestion(
            action="test_action",
            description="Test description",
            example="test_example()"
        )
        
        assert suggestion.action == "test_action"
        assert suggestion.description == "Test description"
        assert suggestion.example == "test_example()"

    def test_suggestion_without_example(self):
        """Test creating a suggestion without example."""
        suggestion = ErrorSuggestion(
            action="test_action",
            description="Test description"
        )
        
        assert suggestion.action == "test_action"
        assert suggestion.description == "Test description"
        assert suggestion.example is None


class TestSpecError:
    """Test cases for SpecError class."""

    def test_create_basic_error(self):
        """Test creating a basic SpecError."""
        error = SpecError("Test error message")
        
        assert error.message == "Test error message"
        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {}
        assert error.suggestions == []
        assert error.context == {}
        assert error.cause is None

    def test_create_detailed_error(self):
        """Test creating a detailed SpecError."""
        suggestion = ErrorSuggestion(
            action="fix_issue",
            description="Fix the issue",
            example="fix_issue()"
        )
        
        cause = ValueError("Original error")
        
        error = SpecError(
            message="Detailed error",
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"field": "test_field"},
            suggestions=[suggestion],
            context={"operation": "test_op"},
            cause=cause
        )
        
        assert error.message == "Detailed error"
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {"field": "test_field"}
        assert len(error.suggestions) == 1
        assert error.suggestions[0].action == "fix_issue"
        assert error.context == {"operation": "test_op"}
        assert error.cause == cause

    def test_to_dict(self):
        """Test converting SpecError to dictionary."""
        suggestion = ErrorSuggestion(
            action="test_action",
            description="Test description",
            example="test_example()"
        )
        
        error = SpecError(
            message="Test error",
            error_code=ErrorCode.SPEC_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            details={"spec": "test-spec"},
            suggestions=[suggestion],
            context={"operation": "read"},
            cause=FileNotFoundError("File not found")
        )
        
        result = error.to_dict()
        
        assert result["success"] is False
        assert result["error_code"] == "SPEC_NOT_FOUND"
        assert result["message"] == "Test error"
        assert result["severity"] == "medium"
        assert result["details"] == {"spec": "test-spec"}
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["action"] == "test_action"
        assert result["suggestions"][0]["description"] == "Test description"
        assert result["suggestions"][0]["example"] == "test_example()"
        assert result["context"] == {"operation": "read"}
        assert "File not found" in result["cause"]


class TestErrorFactory:
    """Test cases for ErrorFactory class."""

    def test_spec_not_found(self):
        """Test creating spec not found error."""
        error = ErrorFactory.spec_not_found("test-spec")
        
        assert error.error_code == ErrorCode.SPEC_NOT_FOUND
        assert "test-spec" in error.message
        assert error.details["feature_name"] == "test-spec"
        assert len(error.suggestions) == 2
        assert any("create_spec" in s.action for s in error.suggestions)
        assert any("list_specs" in s.action for s in error.suggestions)

    def test_spec_already_exists(self):
        """Test creating spec already exists error."""
        error = ErrorFactory.spec_already_exists("existing-spec")
        
        assert error.error_code == ErrorCode.SPEC_ALREADY_EXISTS
        assert "existing-spec" in error.message
        assert error.details["feature_name"] == "existing-spec"
        assert len(error.suggestions) == 3
        assert any("different_name" in s.action for s in error.suggestions)
        assert any("update_existing" in s.action for s in error.suggestions)
        assert any("delete_existing" in s.action for s in error.suggestions)

    def test_invalid_spec_name(self):
        """Test creating invalid spec name error."""
        error = ErrorFactory.invalid_spec_name("Invalid Name!", "contains special characters")
        
        assert error.error_code == ErrorCode.SPEC_INVALID_NAME
        assert "Invalid Name!" in error.message
        assert "contains special characters" in error.message
        assert error.details["feature_name"] == "Invalid Name!"
        assert error.details["reason"] == "contains special characters"
        assert len(error.suggestions) == 2
        assert any("kebab_case" in s.action for s in error.suggestions)

    def test_document_not_found(self):
        """Test creating document not found error."""
        error = ErrorFactory.document_not_found("test-spec", "invalid-type")
        
        assert error.error_code == ErrorCode.DOCUMENT_NOT_FOUND
        assert "test-spec" in error.message
        assert "invalid-type" in error.message
        assert error.details["feature_name"] == "test-spec"
        assert error.details["document_type"] == "invalid-type"
        assert len(error.suggestions) == 2

    def test_workflow_approval_required(self):
        """Test creating workflow approval required error."""
        error = ErrorFactory.workflow_approval_required("test-spec", "requirements")
        
        assert error.error_code == ErrorCode.WORKFLOW_APPROVAL_REQUIRED
        assert "test-spec" in error.message
        assert "requirements" in error.message
        assert error.details["feature_name"] == "test-spec"
        assert error.details["current_phase"] == "requirements"
        assert len(error.suggestions) == 2
        assert any("approval" in s.action for s in error.suggestions)

    def test_task_not_found(self):
        """Test creating task not found error."""
        error = ErrorFactory.task_not_found("test-spec", "99.99")
        
        assert error.error_code == ErrorCode.TASK_NOT_FOUND
        assert "test-spec" in error.message
        assert "99.99" in error.message
        assert error.details["feature_name"] == "test-spec"
        assert error.details["task_identifier"] == "99.99"
        assert len(error.suggestions) == 2

    def test_validation_error(self):
        """Test creating validation error."""
        error = ErrorFactory.validation_error("test_field", "invalid_value", "must be positive")
        
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert "test_field" in error.message
        assert "must be positive" in error.message
        assert error.details["field"] == "test_field"
        assert error.details["value"] == "invalid_value"
        assert error.details["reason"] == "must be positive"
        assert len(error.suggestions) == 2


class TestFormatErrorResponse:
    """Test cases for format_error_response function."""

    def test_format_spec_error(self):
        """Test formatting a SpecError."""
        error = SpecError(
            message="Test error",
            error_code=ErrorCode.SPEC_NOT_FOUND
        )
        
        result = format_error_response(error)
        
        assert result["success"] is False
        assert result["error_code"] == "SPEC_NOT_FOUND"
        assert result["message"] == "Test error"

    def test_format_generic_exception(self):
        """Test formatting a generic exception."""
        error = ValueError("Generic error")
        
        result = format_error_response(error)
        
        assert result["success"] is False
        assert result["error_code"] == "INTERNAL_ERROR"
        assert result["message"] == "Generic error"
        assert result["severity"] == "high"
        assert result["details"]["error_type"] == "ValueError"
        assert "Generic error" in result["cause"]

    def test_format_none_error(self):
        """Test formatting None as error."""
        result = format_error_response(None)
        
        assert result["success"] is False
        assert result["error_code"] == "INTERNAL_ERROR"
        assert result["message"] == "None"


class TestErrorCodes:
    """Test cases for ErrorCode enum."""

    def test_all_error_codes_exist(self):
        """Test that all expected error codes exist."""
        expected_codes = [
            "INTERNAL_ERROR", "INVALID_INPUT", "VALIDATION_ERROR",
            "SPEC_NOT_FOUND", "SPEC_ALREADY_EXISTS", "SPEC_INVALID_NAME",
            "DOCUMENT_NOT_FOUND", "DOCUMENT_INVALID_TYPE", "DOCUMENT_PARSE_ERROR",
            "WORKFLOW_INVALID_PHASE", "WORKFLOW_TRANSITION_DENIED", "WORKFLOW_APPROVAL_REQUIRED",
            "TASK_NOT_FOUND", "TASK_INVALID_IDENTIFIER", "TASK_ALREADY_COMPLETED",
            "FILE_NOT_FOUND", "FILE_ACCESS_DENIED", "FILE_INVALID_PATH",
            "REFERENCE_NOT_FOUND", "REFERENCE_INVALID_FORMAT", "REFERENCE_CIRCULAR"
        ]
        
        for code in expected_codes:
            assert hasattr(ErrorCode, code)
            assert ErrorCode[code].value == code

    def test_error_severity_levels(self):
        """Test that all severity levels exist."""
        expected_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        for level in expected_levels:
            assert hasattr(ErrorSeverity, level)
            assert ErrorSeverity[level].value == level.lower()