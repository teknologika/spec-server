"""
Test fixtures and utilities for spec-server tests.

This module provides reusable test fixtures, sample data, and utility functions
for testing spec-server functionality.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from spec_server.mcp_tools import MCPTools


class SpecTestData:
    """Sample specification data for testing."""

    # Sample feature ideas
    FEATURE_IDEAS = {
        "user-auth": "Implement user authentication with login, registration, and password reset",
        "data-export": "Create data export functionality with multiple formats (CSV, JSON, PDF)",
        "api-integration": "Integrate with third-party APIs for data synchronization",
        "notification-system": "Build notification system with email, SMS, and push notifications",
        "file-upload": "Implement secure file upload with virus scanning and storage",
        "search-engine": "Create full-text search with filtering and sorting capabilities",
        "reporting-dashboard": "Build analytics dashboard with charts and metrics",
        "user-management": "Admin panel for user management and role-based access control",
        "payment-processing": "Integrate payment gateway for subscription billing",
        "audit-logging": "Comprehensive audit logging for security and compliance",
    }

    # Sample requirements document
    SAMPLE_REQUIREMENTS = """# Requirements Document

## Introduction

This feature implements a comprehensive user authentication system with modern security practices.

## Requirements

### Requirement 1

**User Story:** As a user, I want to register with email and password, so that I can create an account

#### Acceptance Criteria

1. WHEN user provides valid email and password THEN system SHALL create account
2. WHEN user provides invalid email THEN system SHALL show validation error
3. WHEN user provides weak password THEN system SHALL show password requirements

### Requirement 2

**User Story:** As a user, I want to login with my credentials, so that I can access the system

#### Acceptance Criteria

1. WHEN user provides correct credentials THEN system SHALL authenticate user
2. WHEN user provides incorrect credentials THEN system SHALL show error message
3. WHEN user fails login 3 times THEN system SHALL temporarily lock account

### Requirement 3

**User Story:** As a user, I want to reset my password, so that I can regain access if I forget it

#### Acceptance Criteria

1. WHEN user requests password reset THEN system SHALL send reset email
2. WHEN user clicks reset link THEN system SHALL allow password change
3. WHEN reset link expires THEN system SHALL require new reset request
"""

    # Sample design document
    SAMPLE_DESIGN = """# Design Document

## Overview

User authentication system with JWT tokens, bcrypt password hashing, and email verification.

## Architecture

### High-Level Architecture
- Frontend: React SPA with authentication context
- Backend: FastAPI with JWT middleware
- Database: PostgreSQL with user tables
- Email: SMTP service for notifications

### Security Considerations
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with 1-hour expiration
- HTTPS required for all authentication endpoints
- Rate limiting on login attempts

## Components and Interfaces

### AuthService
- `register_user(email: str, password: str) -> UserResponse`
- `login_user(email: str, password: str) -> TokenResponse`
- `reset_password(email: str) -> ResetResponse`
- `verify_token(token: str) -> UserResponse`

### UserRepository
- `create_user(user_data: UserCreate) -> User`
- `get_user_by_email(email: str) -> Optional[User]`
- `update_user(user_id: int, updates: UserUpdate) -> User`

## Data Models

### User
- id: int (primary key)
- email: str (unique, indexed)
- password_hash: str
- is_verified: bool
- created_at: datetime
- updated_at: datetime

### PasswordReset
- id: int (primary key)
- user_id: int (foreign key)
- token: str (unique)
- expires_at: datetime
- used: bool

## Error Handling

Standard HTTP status codes with JSON error responses:
- 400: Bad Request (validation errors)
- 401: Unauthorized (authentication failed)
- 403: Forbidden (insufficient permissions)
- 409: Conflict (email already exists)
- 429: Too Many Requests (rate limiting)

## Testing Strategy

### Unit Tests
- Test all service methods with mocked dependencies
- Test password hashing and verification
- Test JWT token generation and validation

### Integration Tests
- Test complete authentication flows
- Test database operations
- Test email sending functionality

### Security Tests
- Test password strength requirements
- Test rate limiting effectiveness
- Test token expiration handling
"""

    # Sample tasks document
    SAMPLE_TASKS = """# Implementation Plan

- [ ] 1. Set up project structure and dependencies
  - Create FastAPI project with authentication dependencies
  - Set up PostgreSQL database with user tables
  - Configure JWT and bcrypt libraries
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 2. Implement core authentication models
- [ ] 2.1 Create User data model
  - Define User SQLAlchemy model with validation
  - Add email uniqueness constraint and indexing
  - Implement password hashing methods
  - _Requirements: 1.1, 2.1_

- [ ] 2.2 Create PasswordReset model
  - Define PasswordReset model with token generation
  - Add expiration logic and cleanup methods
  - Implement secure token generation
  - _Requirements: 3.1_

- [ ] 3. Implement authentication services
- [ ] 3.1 Create AuthService class
  - Implement user registration with validation
  - Add login functionality with JWT generation
  - Create password reset request handling
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 3.2 Implement JWT token management
  - Create token generation and validation functions
  - Add token refresh mechanism
  - Implement token blacklisting for logout
  - _Requirements: 2.1_

- [ ] 4. Create API endpoints
- [ ] 4.1 Implement registration endpoint
  - Create POST /auth/register endpoint
  - Add input validation and error handling
  - Return appropriate success/error responses
  - _Requirements: 1.1_

- [ ] 4.2 Implement login endpoint
  - Create POST /auth/login endpoint
  - Add rate limiting for security
  - Return JWT token on successful authentication
  - _Requirements: 2.1_

- [ ] 4.3 Implement password reset endpoints
  - Create POST /auth/reset-request endpoint
  - Create POST /auth/reset-confirm endpoint
  - Add email sending functionality
  - _Requirements: 3.1_

- [ ] 5. Add security middleware
- [ ] 5.1 Implement JWT authentication middleware
  - Create middleware to validate JWT tokens
  - Add user context injection
  - Handle token expiration gracefully
  - _Requirements: 2.1_

- [ ] 5.2 Add rate limiting middleware
  - Implement rate limiting for authentication endpoints
  - Add IP-based and user-based limits
  - Configure appropriate limits and timeouts
  - _Requirements: 2.1_

- [ ] 6. Create comprehensive tests
- [ ] 6.1 Write unit tests for services
  - Test AuthService methods with mocked dependencies
  - Test password hashing and verification
  - Test JWT token operations
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 6.2 Write integration tests
  - Test complete authentication workflows
  - Test API endpoints with real database
  - Test email functionality
  - _Requirements: 1.1, 2.1, 3.1_
"""

    @classmethod
    def get_feature_idea(cls, feature_name: str) -> str:
        """Get a sample feature idea by name."""
        return cls.FEATURE_IDEAS.get(
            feature_name, f"Sample feature idea for {feature_name}"
        )

    @classmethod
    def get_all_feature_names(cls) -> List[str]:
        """Get all available feature names."""
        return list(cls.FEATURE_IDEAS.keys())


class SpecTestFixtures:
    """Test fixtures for creating and managing test specifications."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize test fixtures with optional base path."""
        self.base_path = base_path or Path(tempfile.mkdtemp())
        self.mcp_tools = MCPTools(base_path=self.base_path)
        self.created_specs: List[str] = []

    def create_sample_spec(
        self, feature_name: str, phase: str = "requirements"
    ) -> Dict[str, Any]:
        """
        Create a sample specification for testing.

        Args:
            feature_name: Name of the feature to create
            phase: Phase to advance the spec to ("requirements", "design", "tasks")

        Returns:
            Dictionary with spec creation result
        """
        # Get sample idea
        idea = SpecTestData.get_feature_idea(feature_name)

        # Create the spec
        result = self.mcp_tools.create_spec(feature_name, idea)
        if result["success"]:
            self.created_specs.append(feature_name)

        # Advance to requested phase if needed
        if phase == "design" and result["success"]:
            # Update requirements and advance to design
            self.mcp_tools.update_spec_document(
                feature_name,
                "requirements",
                SpecTestData.SAMPLE_REQUIREMENTS,
                phase_approval=True,
            )
        elif phase == "tasks" and result["success"]:
            # Advance through requirements and design to tasks
            self.mcp_tools.update_spec_document(
                feature_name,
                "requirements",
                SpecTestData.SAMPLE_REQUIREMENTS,
                phase_approval=True,
            )
            self.mcp_tools.update_spec_document(
                feature_name, "design", SpecTestData.SAMPLE_DESIGN, phase_approval=True
            )

        return result

    def create_multiple_specs(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Create multiple sample specifications for testing.

        Args:
            count: Number of specs to create

        Returns:
            List of spec creation results
        """
        results = []
        feature_names = SpecTestData.get_all_feature_names()[:count]

        for feature_name in feature_names:
            result = self.create_sample_spec(feature_name)
            results.append(result)

        return results

    def create_spec_with_file_references(self, feature_name: str) -> Dict[str, Any]:
        """
        Create a spec with file references for testing.

        Args:
            feature_name: Name of the feature to create

        Returns:
            Dictionary with spec creation result
        """
        # Create external reference files
        api_spec_file = self.base_path / "api-spec.json"
        api_spec_content = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"summary": "Get users"}},
                "/auth": {"post": {"summary": "Authenticate user"}},
            },
        }
        api_spec_file.write_text(json.dumps(api_spec_content, indent=2))

        readme_file = self.base_path / "README.md"
        readme_file.write_text(
            "# API Documentation\n\nThis is the main API documentation."
        )

        # Create spec
        result = self.create_sample_spec(feature_name)

        if result["success"]:
            # Update requirements with file references
            requirements_with_refs = """# Requirements Document

## Introduction

This feature implements an API based on the OpenAPI specification.

## API Specification

#[[file:api-spec.json]]

## Additional Documentation

#[[file:README.md]]

## Requirements

### Requirement 1

**User Story:** As a developer, I want to implement the API endpoints, so that clients can access the service

#### Acceptance Criteria

1. WHEN client calls GET /users THEN system SHALL return user list
2. WHEN invalid request is made THEN system SHALL return appropriate error
"""

            self.mcp_tools.update_spec_document(
                feature_name, "requirements", requirements_with_refs
            )

        return result

    def get_spec_with_tasks(self, feature_name: str) -> Dict[str, Any]:
        """
        Get or create a spec advanced to tasks phase.

        Args:
            feature_name: Name of the feature

        Returns:
            Dictionary with spec information
        """
        # Try to get existing spec
        try:
            self.mcp_tools.read_spec_document(feature_name, "tasks")
            return {"success": True, "feature_name": feature_name}
        except Exception:
            # Create new spec advanced to tasks phase
            return self.create_sample_spec(feature_name, phase="tasks")

    def cleanup(self):
        """Clean up all created test specifications."""
        for feature_name in self.created_specs:
            try:
                self.mcp_tools.delete_spec(feature_name)
            except Exception:
                pass  # Ignore cleanup errors

        # Clean up temporary directory
        import shutil

        if self.base_path.exists():
            shutil.rmtree(self.base_path, ignore_errors=True)


class MockFileSystem:
    """Mock file system for isolated testing."""

    def __init__(self):
        """Initialize mock file system."""
        self.files: Dict[str, str] = {}
        self.directories: set = set()

    def create_file(self, path: str, content: str):
        """Create a mock file with content."""
        self.files[path] = content
        # Add parent directories
        parent = str(Path(path).parent)
        if parent != ".":
            self.directories.add(parent)

    def read_file(self, path: str) -> str:
        """Read content from mock file."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]

    def file_exists(self, path: str) -> bool:
        """Check if mock file exists."""
        return path in self.files

    def delete_file(self, path: str):
        """Delete mock file."""
        if path in self.files:
            del self.files[path]

    def list_files(self) -> List[str]:
        """List all mock files."""
        return list(self.files.keys())

    def clear(self):
        """Clear all mock files and directories."""
        self.files.clear()
        self.directories.clear()


class TestDataGenerator:
    """Generator for various test data scenarios."""

    @staticmethod
    def generate_feature_names(count: int) -> List[str]:
        """Generate a list of valid feature names."""
        base_names = [
            "user-auth",
            "data-export",
            "api-integration",
            "notification-system",
            "file-upload",
            "search-engine",
            "reporting-dashboard",
            "user-management",
            "payment-processing",
            "audit-logging",
            "content-management",
            "workflow-engine",
            "email-service",
            "backup-system",
            "monitoring-dashboard",
            "cache-layer",
            "message-queue",
            "image-processing",
            "document-converter",
            "analytics-engine",
        ]

        if count <= len(base_names):
            return base_names[:count]

        # Generate additional names if needed
        additional = []
        for i in range(count - len(base_names)):
            additional.append(f"feature-{i+1:03d}")

        return base_names + additional

    @staticmethod
    def generate_feature_ideas(count: int) -> List[str]:
        """Generate a list of feature ideas."""
        ideas = [
            "Implement user authentication with OAuth2 and JWT tokens",
            "Create data export functionality with multiple output formats",
            "Build API integration layer for third-party services",
            "Develop notification system with multiple delivery channels",
            "Implement secure file upload with virus scanning",
            "Create full-text search with advanced filtering",
            "Build analytics dashboard with real-time metrics",
            "Develop user management system with role-based access",
            "Integrate payment processing with multiple gateways",
            "Implement comprehensive audit logging system",
            "Create content management system with versioning",
            "Build workflow engine for business processes",
            "Develop email service with template management",
            "Implement automated backup and recovery system",
            "Create monitoring dashboard with alerting",
            "Build distributed cache layer for performance",
            "Implement message queue for async processing",
            "Create image processing service with transformations",
            "Build document converter for multiple formats",
            "Develop analytics engine for data insights",
        ]

        if count <= len(ideas):
            return ideas[:count]

        # Generate additional ideas if needed
        additional = []
        for i in range(count - len(ideas)):
            additional.append(
                f"Feature {i+1} implementation with comprehensive functionality"
            )

        return ideas + additional

    @staticmethod
    def generate_unicode_content() -> str:
        """Generate content with Unicode characters for testing."""
        return """# Requirements Document 📋

## Introduction 🌟

This feature supports international users with Unicode characters:
- Chinese: 中文测试内容
- Arabic: اختبار المحتوى العربي
- Russian: Тестовый контент на русском
- Japanese: 日本語のテストコンテンツ
- Emoji: 🚀 🎉 ✅ 🔒 📊

## Requirements

### Requirement 1 ✅

**User Story:** As an international user, I want to use my native language, so that I can understand the interface

#### Acceptance Criteria

1. WHEN user enters Unicode text THEN system SHALL handle correctly ✓
2. WHEN special characters are used THEN system SHALL preserve them 🔒
3. WHEN emoji are included THEN system SHALL display properly 😊
"""

    @staticmethod
    def generate_large_content(size_kb: int = 100) -> str:
        """Generate large content for performance testing."""
        base_content = """# Large Requirements Document

## Introduction

This is a large document generated for performance testing purposes.

"""

        # Calculate how many requirements needed to reach target size
        requirement_template = """### Requirement {num}

**User Story:** As a user, I want feature {num}, so that I can accomplish task {num}

#### Acceptance Criteria

1. WHEN condition {num} is met THEN system SHALL respond appropriately
2. WHEN error occurs in feature {num} THEN system SHALL handle gracefully
3. WHEN user interacts with feature {num} THEN system SHALL provide feedback

"""

        content = base_content
        requirement_num = 1

        while len(content.encode("utf-8")) < size_kb * 1024:
            content += requirement_template.format(num=requirement_num)
            requirement_num += 1

        return content


# Pytest fixtures are moved to conftest.py
