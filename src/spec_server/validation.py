"""
Input validation and sanitization for spec-server.

This module provides comprehensive validation for all MCP tool parameters,
including file path sanitization and security checks.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

from .errors import ErrorFactory, SpecError, ErrorCode


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    
    is_valid: bool
    sanitized_value: Any = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class InputValidator:
    """Comprehensive input validator for spec-server operations."""
    
    # Valid feature name pattern (kebab-case)
    FEATURE_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
    
    # Valid document types
    VALID_DOCUMENT_TYPES = {"requirements", "design", "tasks"}
    
    # Maximum lengths for various inputs
    MAX_FEATURE_NAME_LENGTH = 50
    MAX_DOCUMENT_CONTENT_LENGTH = 1_000_000  # 1MB
    MAX_IDEA_LENGTH = 10_000
    MAX_TASK_IDENTIFIER_LENGTH = 20
    
    # Dangerous path patterns to block
    DANGEROUS_PATH_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'\.\.\\',  # Windows directory traversal
        r'^/',     # Absolute paths
        r'^[A-Z]:',  # Windows drive letters
        r'~/',     # Home directory
        r'\$',     # Environment variables
        r'`',      # Command substitution
        r';',      # Command chaining
        r'\|',     # Pipes
        r'&',      # Background processes
    ]
    
    @classmethod
    def validate_feature_name(cls, feature_name: str) -> ValidationResult:
        """
        Validate and sanitize a feature name.
        
        Args:
            feature_name: The feature name to validate
            
        Returns:
            ValidationResult with validation status and sanitized value
        """
        errors = []
        warnings = []
        
        # Check if feature_name is provided
        if not feature_name:
            errors.append("Feature name is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check type
        if not isinstance(feature_name, str):
            errors.append("Feature name must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check format first (before sanitization to catch case issues)
        if not cls.FEATURE_NAME_PATTERN.match(feature_name.strip()):
            errors.append(
                "Feature name must be in kebab-case format (lowercase letters, numbers, and hyphens only). "
                "Examples: 'user-auth', 'data-export', 'api-v2'"
            )
        
        # Sanitize: strip whitespace and convert to lowercase
        sanitized = feature_name.strip().lower()
        
        # Check length
        if len(sanitized) > cls.MAX_FEATURE_NAME_LENGTH:
            errors.append(f"Feature name too long (max {cls.MAX_FEATURE_NAME_LENGTH} characters)")
        
        # Check for reserved names
        reserved_names = {"test", "spec", "server", "admin", "root", "config"}
        if sanitized in reserved_names:
            warnings.append(f"'{sanitized}' is a reserved name, consider using a more specific name")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_document_type(cls, document_type: str) -> ValidationResult:
        """
        Validate a document type.
        
        Args:
            document_type: The document type to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        if not document_type:
            errors.append("Document type is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        if not isinstance(document_type, str):
            errors.append("Document type must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        sanitized = document_type.strip().lower()
        
        if sanitized not in cls.VALID_DOCUMENT_TYPES:
            errors.append(
                f"Invalid document type '{document_type}'. "
                f"Valid types: {', '.join(sorted(cls.VALID_DOCUMENT_TYPES))}"
            )
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors
        )
    
    @classmethod
    def validate_document_content(cls, content: str) -> ValidationResult:
        """
        Validate document content.
        
        Args:
            content: The document content to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        if not isinstance(content, str):
            errors.append("Document content must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check length
        if len(content) > cls.MAX_DOCUMENT_CONTENT_LENGTH:
            errors.append(f"Document content too large (max {cls.MAX_DOCUMENT_CONTENT_LENGTH} characters)")
        
        # Check for potentially dangerous content
        dangerous_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',    # JavaScript URLs
            r'data:text/html', # Data URLs with HTML
            r'vbscript:',      # VBScript URLs
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"Content contains potentially dangerous pattern: {pattern}")
        
        # Sanitize: normalize line endings
        sanitized = content.replace('\r\n', '\n').replace('\r', '\n')
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_initial_idea(cls, idea: str) -> ValidationResult:
        """
        Validate an initial idea string.
        
        Args:
            idea: The initial idea to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        if not idea:
            errors.append("Initial idea is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        if not isinstance(idea, str):
            errors.append("Initial idea must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        sanitized = idea.strip()
        
        if len(sanitized) < 10:
            errors.append("Initial idea too short (minimum 10 characters)")
        
        if len(sanitized) > cls.MAX_IDEA_LENGTH:
            errors.append(f"Initial idea too long (max {cls.MAX_IDEA_LENGTH} characters)")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors
        )
    
    @classmethod
    def validate_task_identifier(cls, task_id: Optional[str]) -> ValidationResult:
        """
        Validate a task identifier.
        
        Args:
            task_id: The task identifier to validate (can be None)
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        # None is valid (means get next task)
        if task_id is None:
            return ValidationResult(is_valid=True, sanitized_value=None)
        
        if not isinstance(task_id, str):
            errors.append("Task identifier must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        sanitized = task_id.strip()
        
        if not sanitized:
            errors.append("Task identifier cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)
        
        if len(sanitized) > cls.MAX_TASK_IDENTIFIER_LENGTH:
            errors.append(f"Task identifier too long (max {cls.MAX_TASK_IDENTIFIER_LENGTH} characters)")
        
        # Validate format (should be like "1", "1.2", "2.3.1", etc.)
        if not re.match(r'^\d+(\.\d+)*$', sanitized):
            errors.append("Task identifier must be in format like '1', '1.2', '2.3.1', etc.")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors
        )
    
    @classmethod
    def validate_file_path(cls, file_path: str, allow_absolute: bool = False) -> ValidationResult:
        """
        Validate and sanitize a file path for security.
        
        Args:
            file_path: The file path to validate
            allow_absolute: Whether to allow absolute paths
            
        Returns:
            ValidationResult with validation status and sanitized path
        """
        errors = []
        warnings = []
        
        if not file_path:
            errors.append("File path is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        if not isinstance(file_path, str):
            errors.append("File path must be a string")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, file_path):
                errors.append(f"File path contains dangerous pattern: {pattern}")
        
        # Normalize path without resolving to absolute
        try:
            path = Path(file_path)
            sanitized = str(path)
        except Exception as e:
            errors.append(f"Invalid file path: {e}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check if absolute path is allowed
        if path.is_absolute() and not allow_absolute:
            errors.append("Absolute paths are not allowed for security reasons")
        
        # Check for suspicious extensions
        suspicious_extensions = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js'}
        if path.suffix.lower() in suspicious_extensions:
            warnings.append(f"File has potentially dangerous extension: {path.suffix}")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized if is_valid else None,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_boolean(cls, value: Any, field_name: str) -> ValidationResult:
        """
        Validate a boolean value.
        
        Args:
            value: The value to validate as boolean
            field_name: Name of the field for error messages
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        if value is None:
            # None is often acceptable for optional boolean fields
            return ValidationResult(is_valid=True, sanitized_value=False)
        
        if isinstance(value, bool):
            return ValidationResult(is_valid=True, sanitized_value=value)
        
        # Try to convert string representations
        if isinstance(value, str):
            lower_value = value.lower().strip()
            if lower_value in ('true', '1', 'yes', 'on'):
                return ValidationResult(is_valid=True, sanitized_value=True)
            elif lower_value in ('false', '0', 'no', 'off', ''):
                return ValidationResult(is_valid=True, sanitized_value=False)
        
        # Try to convert numeric values
        if isinstance(value, (int, float)):
            return ValidationResult(is_valid=True, sanitized_value=bool(value))
        
        errors.append(f"{field_name} must be a boolean value (true/false)")
        return ValidationResult(is_valid=False, errors=errors)


def validate_create_spec_params(feature_name: str, initial_idea: str) -> Dict[str, Any]:
    """
    Validate parameters for create_spec operation.
    
    Args:
        feature_name: Feature name to validate
        initial_idea: Initial idea to validate
        
    Returns:
        Dictionary with sanitized parameters
        
    Raises:
        SpecError: If validation fails
    """
    # Validate feature name
    name_result = InputValidator.validate_feature_name(feature_name)
    if not name_result.is_valid:
        raise ErrorFactory.invalid_spec_name(feature_name, "; ".join(name_result.errors))
    
    # Validate initial idea
    idea_result = InputValidator.validate_initial_idea(initial_idea)
    if not idea_result.is_valid:
        raise ErrorFactory.validation_error("initial_idea", initial_idea, "; ".join(idea_result.errors))
    
    return {
        "feature_name": name_result.sanitized_value,
        "initial_idea": idea_result.sanitized_value
    }


def validate_update_spec_params(
    feature_name: str, 
    document_type: str, 
    content: str, 
    phase_approval: Any = False
) -> Dict[str, Any]:
    """
    Validate parameters for update_spec_document operation.
    
    Args:
        feature_name: Feature name to validate
        document_type: Document type to validate
        content: Document content to validate
        phase_approval: Phase approval flag to validate
        
    Returns:
        Dictionary with sanitized parameters
        
    Raises:
        SpecError: If validation fails
    """
    # Validate feature name
    name_result = InputValidator.validate_feature_name(feature_name)
    if not name_result.is_valid:
        raise ErrorFactory.invalid_spec_name(feature_name, "; ".join(name_result.errors))
    
    # Validate document type
    type_result = InputValidator.validate_document_type(document_type)
    if not type_result.is_valid:
        raise ErrorFactory.validation_error("document_type", document_type, "; ".join(type_result.errors))
    
    # Validate content
    content_result = InputValidator.validate_document_content(content)
    if not content_result.is_valid:
        raise ErrorFactory.validation_error("content", "document content", "; ".join(content_result.errors))
    
    # Validate phase approval
    approval_result = InputValidator.validate_boolean(phase_approval, "phase_approval")
    if not approval_result.is_valid:
        raise ErrorFactory.validation_error("phase_approval", phase_approval, "; ".join(approval_result.errors))
    
    return {
        "feature_name": name_result.sanitized_value,
        "document_type": type_result.sanitized_value,
        "content": content_result.sanitized_value,
        "phase_approval": approval_result.sanitized_value
    }


def validate_read_spec_params(
    feature_name: str, 
    document_type: str, 
    resolve_references: Any = True
) -> Dict[str, Any]:
    """
    Validate parameters for read_spec_document operation.
    
    Args:
        feature_name: Feature name to validate
        document_type: Document type to validate
        resolve_references: Whether to resolve references
        
    Returns:
        Dictionary with sanitized parameters
        
    Raises:
        SpecError: If validation fails
    """
    # Validate feature name
    name_result = InputValidator.validate_feature_name(feature_name)
    if not name_result.is_valid:
        raise ErrorFactory.invalid_spec_name(feature_name, "; ".join(name_result.errors))
    
    # Validate document type
    type_result = InputValidator.validate_document_type(document_type)
    if not type_result.is_valid:
        raise ErrorFactory.validation_error("document_type", document_type, "; ".join(type_result.errors))
    
    # Validate resolve_references
    resolve_result = InputValidator.validate_boolean(resolve_references, "resolve_references")
    if not resolve_result.is_valid:
        raise ErrorFactory.validation_error("resolve_references", resolve_references, "; ".join(resolve_result.errors))
    
    return {
        "feature_name": name_result.sanitized_value,
        "document_type": type_result.sanitized_value,
        "resolve_references": resolve_result.sanitized_value
    }


def validate_task_params(feature_name: str, task_identifier: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate parameters for task operations.
    
    Args:
        feature_name: Feature name to validate
        task_identifier: Task identifier to validate (optional)
        
    Returns:
        Dictionary with sanitized parameters
        
    Raises:
        SpecError: If validation fails
    """
    # Validate feature name
    name_result = InputValidator.validate_feature_name(feature_name)
    if not name_result.is_valid:
        raise ErrorFactory.invalid_spec_name(feature_name, "; ".join(name_result.errors))
    
    # Validate task identifier
    task_result = InputValidator.validate_task_identifier(task_identifier)
    if not task_result.is_valid:
        raise ErrorFactory.validation_error("task_identifier", task_identifier, "; ".join(task_result.errors))
    
    return {
        "feature_name": name_result.sanitized_value,
        "task_identifier": task_result.sanitized_value
    }