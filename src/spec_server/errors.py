"""
Structured error handling for spec-server.

This module provides comprehensive error classes and error response formatting
for the MCP protocol with helpful error messages and suggestions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standard error codes for spec-server operations."""

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Spec-related errors
    SPEC_NOT_FOUND = "SPEC_NOT_FOUND"
    SPEC_ALREADY_EXISTS = "SPEC_ALREADY_EXISTS"
    SPEC_INVALID_NAME = "SPEC_INVALID_NAME"

    # Document-related errors
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_INVALID_TYPE = "DOCUMENT_INVALID_TYPE"
    DOCUMENT_PARSE_ERROR = "DOCUMENT_PARSE_ERROR"

    # Workflow-related errors
    WORKFLOW_INVALID_PHASE = "WORKFLOW_INVALID_PHASE"
    WORKFLOW_TRANSITION_DENIED = "WORKFLOW_TRANSITION_DENIED"
    WORKFLOW_APPROVAL_REQUIRED = "WORKFLOW_APPROVAL_REQUIRED"

    # Task-related errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_INVALID_IDENTIFIER = "TASK_INVALID_IDENTIFIER"
    TASK_ALREADY_COMPLETED = "TASK_ALREADY_COMPLETED"
    TASKS_NOT_FOUND = "TASKS_NOT_FOUND"

    # File system errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_INVALID_PATH = "FILE_INVALID_PATH"

    # Reference errors
    REFERENCE_NOT_FOUND = "REFERENCE_NOT_FOUND"
    REFERENCE_INVALID_FORMAT = "REFERENCE_INVALID_FORMAT"
    REFERENCE_CIRCULAR = "REFERENCE_CIRCULAR"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorSuggestion(BaseModel):
    """Suggestion for resolving an error."""

    action: str
    description: str
    example: Optional[str] = None


class SpecError(Exception):
    """
    Structured error class for spec-server operations.

    Provides comprehensive error information including error codes,
    helpful messages, suggestions, and context.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[ErrorSuggestion]] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.suggestions = suggestions or []
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for MCP response."""
        return {
            "success": False,
            "error_code": self.error_code.value,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
            "suggestions": [
                {"action": s.action, "description": s.description, "example": s.example}
                for s in self.suggestions
            ],
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
        }


class ErrorFactory:
    """Factory for creating common spec-server errors with helpful suggestions."""

    @staticmethod
    def spec_not_found(feature_name: str) -> SpecError:
        """Create a spec not found error with suggestions."""
        return SpecError(
            message=f"Specification '{feature_name}' not found",
            error_code=ErrorCode.SPEC_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name},
            suggestions=[
                ErrorSuggestion(
                    action="create_spec",
                    description="Create the specification first",
                    example=f"create_spec('{feature_name}', 'Your feature description')",
                ),
                ErrorSuggestion(
                    action="list_specs",
                    description="List all available specifications",
                    example="list_specs()",
                ),
            ],
            context={"available_action": "create_spec"},
        )

    @staticmethod
    def spec_already_exists(feature_name: str) -> SpecError:
        """Create a spec already exists error with suggestions."""
        return SpecError(
            message=f"Specification '{feature_name}' already exists",
            error_code=ErrorCode.SPEC_ALREADY_EXISTS,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name},
            suggestions=[
                ErrorSuggestion(
                    action="use_different_name",
                    description="Choose a different feature name",
                    example=f"create_spec('{feature_name}-v2', 'Your feature description')",
                ),
                ErrorSuggestion(
                    action="update_existing",
                    description="Update the existing specification instead",
                    example=f"update_spec_document('{feature_name}', 'requirements', 'Updated content')",
                ),
                ErrorSuggestion(
                    action="delete_existing",
                    description="Delete the existing specification first",
                    example=f"delete_spec('{feature_name}')",
                ),
            ],
        )

    @staticmethod
    def invalid_spec_name(feature_name: str, reason: str) -> SpecError:
        """Create an invalid spec name error with suggestions."""
        return SpecError(
            message=f"Invalid specification name '{feature_name}': {reason}",
            error_code=ErrorCode.SPEC_INVALID_NAME,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name, "reason": reason},
            suggestions=[
                ErrorSuggestion(
                    action="use_kebab_case",
                    description="Use kebab-case format (lowercase with hyphens)",
                    example="user-authentication, data-export, api-integration",
                ),
                ErrorSuggestion(
                    action="avoid_special_chars",
                    description="Avoid special characters except hyphens",
                    example="my-feature (good) vs my_feature! (bad)",
                ),
            ],
        )

    @staticmethod
    def document_not_found(feature_name: str, document_type: str) -> SpecError:
        """Create a document not found error with suggestions."""
        return SpecError(
            message=f"Document '{document_type}' not found for specification '{feature_name}'",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name, "document_type": document_type},
            suggestions=[
                ErrorSuggestion(
                    action="check_spec_exists",
                    description="Verify the specification exists",
                    example=f"list_specs() # Check if '{feature_name}' is listed",
                ),
                ErrorSuggestion(
                    action="check_document_type",
                    description="Use valid document types: requirements, design, tasks",
                    example="read_spec_document('feature-name', 'requirements')",
                ),
            ],
        )

    @staticmethod
    def workflow_approval_required(feature_name: str, current_phase: str) -> SpecError:
        """Create a workflow approval required error with suggestions."""
        return SpecError(
            message=f"Approval required to advance from {current_phase} phase for '{feature_name}'",
            error_code=ErrorCode.WORKFLOW_APPROVAL_REQUIRED,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name, "current_phase": current_phase},
            suggestions=[
                ErrorSuggestion(
                    action="provide_approval",
                    description="Set phase_approval=True to advance to next phase",
                    example=f"update_spec_document('{feature_name}', '{current_phase}', content, phase_approval=True)",
                ),
                ErrorSuggestion(
                    action="review_document",
                    description="Review the current document before approving",
                    example=f"read_spec_document('{feature_name}', '{current_phase}')",
                ),
            ],
        )

    @staticmethod
    def task_not_found(feature_name: str, task_identifier: str) -> SpecError:
        """Create a task not found error with suggestions."""
        return SpecError(
            message=f"Task '{task_identifier}' not found in specification '{feature_name}'",
            error_code=ErrorCode.TASK_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            details={"feature_name": feature_name, "task_identifier": task_identifier},
            suggestions=[
                ErrorSuggestion(
                    action="check_task_list",
                    description="View all available tasks",
                    example=f"read_spec_document('{feature_name}', 'tasks')",
                ),
                ErrorSuggestion(
                    action="get_next_task",
                    description="Get the next available task",
                    example=f"execute_task('{feature_name}')  # Without task_identifier",
                ),
            ],
        )

    @staticmethod
    def validation_error(field: str, value: Any, reason: str) -> SpecError:
        """Create a validation error with suggestions."""
        return SpecError(
            message=f"Validation error for field '{field}': {reason}",
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details={"field": field, "value": str(value), "reason": reason},
            suggestions=[
                ErrorSuggestion(
                    action="check_format",
                    description="Verify the input format matches requirements",
                    example="Refer to the API documentation for expected formats",
                ),
                ErrorSuggestion(
                    action="check_constraints",
                    description="Ensure the value meets all constraints",
                    example="Check length, type, and format requirements",
                ),
            ],
        )


def format_error_response(error: Union[SpecError, Exception]) -> Dict[str, Any]:
    """
    Format an error for MCP response.

    Args:
        error: The error to format

    Returns:
        Formatted error response dictionary
    """
    if isinstance(error, SpecError):
        return error.to_dict()
    else:
        # Handle unexpected errors
        return SpecError(
            message=str(error),
            error_code=ErrorCode.INTERNAL_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"error_type": type(error).__name__},
            cause=error,
        ).to_dict()
