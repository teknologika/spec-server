"""Error handling for task formatting functionality."""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskFormattingErrorCode(Enum):
    """Error codes for task formatting operations."""

    # Parsing errors
    TASK_PARSING_FAILED = "TASK_PARSING_FAILED"
    INVALID_TASK_FORMAT = "INVALID_TASK_FORMAT"
    MALFORMED_CONTENT = "MALFORMED_CONTENT"

    # Classification errors
    CONTENT_CLASSIFICATION_FAILED = "CONTENT_CLASSIFICATION_FAILED"
    CLASSIFICATION_CONFIDENCE_TOO_LOW = "CLASSIFICATION_CONFIDENCE_TOO_LOW"

    # Requirements linking errors
    REQUIREMENTS_LINKING_FAILED = "REQUIREMENTS_LINKING_FAILED"
    REQUIREMENTS_DOCUMENT_NOT_FOUND = "REQUIREMENTS_DOCUMENT_NOT_FOUND"
    REQUIREMENTS_PARSING_FAILED = "REQUIREMENTS_PARSING_FAILED"
    NO_RELEVANT_REQUIREMENTS_FOUND = "NO_RELEVANT_REQUIREMENTS_FOUND"

    # Rendering errors
    TASK_RENDERING_FAILED = "TASK_RENDERING_FAILED"
    INVALID_TASK_HIERARCHY = "INVALID_TASK_HIERARCHY"

    # LLM validation errors
    LLM_VALIDATION_FAILED = "LLM_VALIDATION_FAILED"
    LLM_RESPONSE_PARSING_FAILED = "LLM_RESPONSE_PARSING_FAILED"
    LLM_SERVICE_UNAVAILABLE = "LLM_SERVICE_UNAVAILABLE"
    VALIDATION_TIMEOUT = "VALIDATION_TIMEOUT"

    # File operation errors
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

    # Configuration errors
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    CONFIGURATION_LOAD_FAILED = "CONFIGURATION_LOAD_FAILED"

    # System errors
    MEMORY_ERROR = "MEMORY_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class TaskFormattingError:
    """Detailed error information for task formatting operations."""

    error_code: TaskFormattingErrorCode
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    traceback_info: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    suggested_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback_info": self.traceback_info,
            "context": self.context,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action,
        }

    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.error_code.value}] {self.message}"


class TaskFormattingException(Exception):
    """Base exception for task formatting operations."""

    def __init__(self, error: TaskFormattingError, cause: Optional[Exception] = None):
        self.error = error
        self.cause = cause
        super().__init__(str(error))


class TaskParsingException(TaskFormattingException):
    """Exception raised during task parsing operations."""

    pass


class ContentClassificationException(TaskFormattingException):
    """Exception raised during content classification operations."""

    pass


class RequirementsLinkingException(TaskFormattingException):
    """Exception raised during requirements linking operations."""

    pass


class TaskRenderingException(TaskFormattingException):
    """Exception raised during task rendering operations."""

    pass


class LLMValidationException(TaskFormattingException):
    """Exception raised during LLM validation operations."""

    pass


class TaskFormattingErrorHandler:
    """Centralized error handling for task formatting operations."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: List[TaskFormattingError] = []
        self.max_history_size = 1000

    def handle_error(
        self,
        error_code: TaskFormattingErrorCode,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        suggested_action: Optional[str] = None,
    ) -> TaskFormattingError:
        """Handle and log an error."""

        error = TaskFormattingError(
            error_code=error_code,
            message=message,
            details=details or {},
            context=context or {},
            recoverable=recoverable,
            suggested_action=suggested_action,
            traceback_info=traceback.format_exc() if exception else None,
        )

        # Log the error
        log_level = logging.ERROR if not recoverable else logging.WARNING
        self.logger.log(
            log_level,
            f"Task formatting error: {error}",
            extra={
                "error_code": error_code.value,
                "context": context,
                "details": details,
                "recoverable": recoverable,
            },
        )

        # Add to history
        self._add_to_history(error)

        return error

    def handle_parsing_error(
        self,
        message: str,
        content: str,
        line_number: Optional[int] = None,
        exception: Optional[Exception] = None,
    ) -> TaskFormattingError:
        """Handle task parsing errors."""
        return self.handle_error(
            error_code=TaskFormattingErrorCode.TASK_PARSING_FAILED,
            message=message,
            exception=exception,
            context={"content_length": len(content), "line_number": line_number},
            details={"content_preview": content[:200] if content else ""},
            suggested_action="Check task format and syntax",
        )

    def handle_classification_error(
        self,
        message: str,
        content: str,
        confidence: Optional[float] = None,
        exception: Optional[Exception] = None,
    ) -> TaskFormattingError:
        """Handle content classification errors."""
        return self.handle_error(
            error_code=TaskFormattingErrorCode.CONTENT_CLASSIFICATION_FAILED,
            message=message,
            exception=exception,
            context={"content_length": len(content), "confidence": confidence},
            details={"content_preview": content[:200] if content else ""},
            suggested_action="Review content classification thresholds",
        )

    def handle_requirements_linking_error(
        self,
        message: str,
        task_description: str,
        requirements_available: int = 0,
        exception: Optional[Exception] = None,
    ) -> TaskFormattingError:
        """Handle requirements linking errors."""
        return self.handle_error(
            error_code=TaskFormattingErrorCode.REQUIREMENTS_LINKING_FAILED,
            message=message,
            exception=exception,
            context={
                "task_description": task_description,
                "requirements_available": requirements_available,
            },
            suggested_action="Check requirements document format and content",
        )

    def handle_llm_validation_error(
        self,
        message: str,
        task_id: str,
        validation_attempt: int = 1,
        exception: Optional[Exception] = None,
    ) -> TaskFormattingError:
        """Handle LLM validation errors."""
        return self.handle_error(
            error_code=TaskFormattingErrorCode.LLM_VALIDATION_FAILED,
            message=message,
            exception=exception,
            context={"task_id": task_id, "validation_attempt": validation_attempt},
            suggested_action="Check LLM service availability and configuration",
        )

    def handle_file_error(
        self,
        message: str,
        file_path: str,
        operation: str,
        exception: Optional[Exception] = None,
    ) -> TaskFormattingError:
        """Handle file operation errors."""
        error_code = TaskFormattingErrorCode.FILE_READ_ERROR
        if "write" in operation.lower():
            error_code = TaskFormattingErrorCode.FILE_WRITE_ERROR
        elif "permission" in str(exception).lower() if exception else False:
            error_code = TaskFormattingErrorCode.FILE_PERMISSION_ERROR
        elif "not found" in str(exception).lower() if exception else False:
            error_code = TaskFormattingErrorCode.FILE_NOT_FOUND

        return self.handle_error(
            error_code=error_code,
            message=message,
            exception=exception,
            context={"file_path": file_path, "operation": operation},
            recoverable=error_code != TaskFormattingErrorCode.FILE_PERMISSION_ERROR,
            suggested_action="Check file permissions and path",
        )

    def create_fallback_result(
        self,
        original_content: str,
        error: TaskFormattingError,
        fallback_message: str = "Formatting failed, returning original content",
    ) -> str:
        """Create a fallback result when formatting fails."""
        self.logger.info(f"Creating fallback result: {fallback_message}")

        # Add error information as comment in the content
        error_comment = f"\n<!-- Formatting Error: {error.error_code.value} - {error.message} -->\n"

        return original_content + error_comment

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}, "recent_errors": []}

        error_types: Dict[str, int] = {}
        for error in self.error_history:
            error_code = error.error_code.value
            error_types[error_code] = error_types.get(error_code, 0) + 1

        recent_errors = [error.to_dict() for error in self.error_history[-10:]]  # Last 10 errors

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "recent_errors": recent_errors,
        }

    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
        self.logger.info("Error history cleared")

    def _add_to_history(self, error: TaskFormattingError) -> None:
        """Add error to history with size limit."""
        self.error_history.append(error)

        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size :]


class TaskFormattingMetrics:
    """Metrics collection for task formatting operations."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.metrics: Dict[str, Any] = {
            "operations_total": 0,
            "operations_successful": 0,
            "operations_failed": 0,
            "parsing_operations": 0,
            "classification_operations": 0,
            "linking_operations": 0,
            "rendering_operations": 0,
            "validation_operations": 0,
            "average_processing_time": 0.0,
            "error_counts": {},
            "last_reset": datetime.now().isoformat(),
        }
        self.processing_times: List[float] = []

    def record_operation(
        self,
        operation_type: str,
        success: bool,
        processing_time: float,
        error_code: Optional[TaskFormattingErrorCode] = None,
    ) -> None:
        """Record an operation for metrics."""
        self.metrics["operations_total"] += 1

        if success:
            self.metrics["operations_successful"] += 1
        else:
            self.metrics["operations_failed"] += 1

            if error_code:
                error_key = error_code.value
                self.metrics["error_counts"][error_key] = self.metrics["error_counts"].get(error_key, 0) + 1

        # Record operation type
        operation_key = f"{operation_type}_operations"
        if operation_key in self.metrics:
            self.metrics[operation_key] += 1

        # Record processing time
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 1000:  # Keep last 1000 times
            self.processing_times = self.processing_times[-1000:]

        # Update average processing time
        if self.processing_times:
            self.metrics["average_processing_time"] = sum(self.processing_times) / len(self.processing_times)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_severity": {},
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }


# Global error handler and metrics instances
_error_handler: Optional[TaskFormattingErrorHandler] = None
_metrics: Optional[TaskFormattingMetrics] = None


def get_error_handler() -> TaskFormattingErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = TaskFormattingErrorHandler()
    return _error_handler


def get_metrics() -> TaskFormattingMetrics:
    """Get the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = TaskFormattingMetrics()
    return _metrics


def handle_error(error_code: TaskFormattingErrorCode, message: str, **kwargs: Any) -> TaskFormattingError:
    """Convenience function to handle errors."""
    return get_error_handler().handle_error(error_code, message, **kwargs)


def record_operation(
    operation_type: str,
    success: bool,
    processing_time: float,
    error_code: Optional[TaskFormattingErrorCode] = None,
) -> None:
    """Convenience function to record operations."""
    get_metrics().record_operation(operation_type, success, processing_time, error_code)
