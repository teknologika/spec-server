"""
Integration tests for MCP tools.
"""

import tempfile
from pathlib import Path

import pytest

from spec_server.errors import ErrorCode, SpecError
from spec_server.mcp_tools import MCPTools, MCPToolsError
from spec_server.models import Phase, TaskStatus


class TestMCPTools:
    """Test MCP tools functionality."""

    @pytest.fixture
    def temp_specs_dir(self):
        """Create a temporary directory for specs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mcp_tools(self, temp_specs_dir):
        """Create MCPTools instance with temporary directory."""
        return MCPTools(temp_specs_dir)

    def test_create_spec_success(self, mcp_tools):
        """Test successful spec creation."""
        result = mcp_tools.create_spec("test-feature", "A simple test feature")

        assert result["success"] is True
        assert result["spec"]["feature_name"] == "test-feature"
        assert result["spec"]["current_phase"] == Phase.REQUIREMENTS.value
        assert "requirements_content" in result
        assert "# Requirements Document" in result["requirements_content"]

    def test_create_spec_empty_feature_name(self, mcp_tools):
        """Test spec creation with empty feature name."""
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.create_spec("", "A test feature")

        assert exc_info.value.error_code == ErrorCode.SPEC_INVALID_NAME

    def test_create_spec_empty_initial_idea(self, mcp_tools):
        """Test spec creation with empty initial idea."""
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.create_spec("test-feature", "")

        assert exc_info.value.error_code == "VALIDATION_ERROR"

    def test_create_spec_already_exists(self, mcp_tools):
        """Test spec creation when spec already exists."""
        # Create first spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Try to create same spec again
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.create_spec("test-feature", "Another test feature")

        assert exc_info.value.error_code == "SPEC_ALREADY_EXISTS"

    def test_list_specs_empty(self, mcp_tools):
        """Test listing specs when none exist."""
        result = mcp_tools.list_specs()

        assert result["success"] is True
        assert result["specs"] == []
        assert result["total_count"] == 0

    def test_list_specs_with_specs(self, mcp_tools):
        """Test listing specs when some exist."""
        # Create a few specs
        mcp_tools.create_spec("feature-1", "First feature")
        mcp_tools.create_spec("feature-2", "Second feature")

        result = mcp_tools.list_specs()

        assert result["success"] is True
        assert result["total_count"] == 2
        assert len(result["specs"]) == 2

        # Check spec details
        spec_names = [spec["feature_name"] for spec in result["specs"]]
        assert "feature-1" in spec_names
        assert "feature-2" in spec_names

    def test_read_spec_document_requirements(self, mcp_tools):
        """Test reading requirements document."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Read requirements
        result = mcp_tools.read_spec_document("test-feature", "requirements")

        assert result["success"] is True
        assert result["document_type"] == "requirements"
        assert result["feature_name"] == "test-feature"
        assert "# Requirements Document" in result["content"]

    def test_read_spec_document_not_found(self, mcp_tools):
        """Test reading document from non-existent spec."""
        with pytest.raises(SpecError) as exc_info:
            mcp_tools.read_spec_document("non-existent", "requirements")
        
        assert exc_info.value.error_code == ErrorCode.SPEC_NOT_FOUND

    def test_read_spec_document_invalid_type(self, mcp_tools):
        """Test reading document with invalid type."""
        mcp_tools.create_spec("test-feature", "A test feature")

        with pytest.raises(SpecError) as exc_info:
            mcp_tools.read_spec_document("test-feature", "invalid")

        assert "Invalid document type" in str(exc_info.value)

    def test_read_spec_document_missing_file(self, mcp_tools):
        """Test reading document that doesn't exist."""
        mcp_tools.create_spec("test-feature", "A test feature")

        with pytest.raises(SpecError) as exc_info:
            mcp_tools.read_spec_document("test-feature", "design")

        assert "Document 'design' not found" in str(exc_info.value)

    def test_update_spec_document_requirements(self, mcp_tools):
        """Test updating requirements document."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Update requirements
        new_content = """# Requirements Document

## Introduction

Updated requirements for the test feature.

## Requirements

### Requirement 1

**User Story:** As a user, I want updated functionality, so that I can test updates.

#### Acceptance Criteria

1. WHEN user updates requirements THEN system SHALL accept the changes
"""

        result = mcp_tools.update_spec_document(
            "test-feature", "requirements", new_content
        )

        assert result["success"] is True
        assert result["document_type"] == "requirements"
        assert result["current_phase"] == Phase.REQUIREMENTS.value

    def test_update_spec_document_with_approval(self, mcp_tools):
        """Test updating document with phase approval."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Update requirements with approval
        new_content = """# Requirements Document

## Introduction

Test requirements for approval.

## Requirements

### Requirement 1

**User Story:** As a user, I want to test approval, so that I can advance phases.

#### Acceptance Criteria

1. WHEN user approves requirements THEN system SHALL advance to design phase
"""

        result = mcp_tools.update_spec_document(
            "test-feature", "requirements", new_content, phase_approval=True
        )

        assert result["success"] is True
        assert result["current_phase"] == Phase.DESIGN.value
        assert "advanced to design phase" in result["message"]

    def test_update_spec_document_invalid_type(self, mcp_tools):
        """Test updating document with invalid type."""
        mcp_tools.create_spec("test-feature", "A test feature")

        with pytest.raises(SpecError) as exc_info:
            mcp_tools.update_spec_document("test-feature", "invalid", "content")

        assert "Invalid document type" in str(exc_info.value)

    def test_update_spec_document_empty_content(self, mcp_tools):
        """Test updating document with empty content."""
        mcp_tools.create_spec("test-feature", "A test feature")

        # Empty content is now allowed, so we just verify it works
        result = mcp_tools.update_spec_document("test-feature", "requirements", "")
        assert result["success"] is True
        assert result["document_type"] == "requirements"
        assert result["content"] == ""

    def test_delete_spec_success(self, mcp_tools):
        """Test successful spec deletion."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Verify it exists
        result = mcp_tools.list_specs()
        assert result["total_count"] == 1

        # Delete spec
        delete_result = mcp_tools.delete_spec("test-feature")

        assert delete_result["success"] is True
        assert delete_result["deleted_spec"]["feature_name"] == "test-feature"
        assert "requirements.md" in delete_result["deleted_files"]

        # Verify it's gone
        result = mcp_tools.list_specs()
        assert result["total_count"] == 0

    def test_delete_spec_not_found(self, mcp_tools):
        """Test deleting non-existent spec."""
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.delete_spec("non-existent")

        assert exc_info.value.error_code == "SPEC_NOT_FOUND"

    def test_execute_task_no_tasks_file(self, mcp_tools):
        """Test executing task when tasks file doesn't exist."""
        mcp_tools.create_spec("test-feature", "A test feature")

        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.execute_task("test-feature")

        assert exc_info.value.error_code == "TASKS_NOT_FOUND"

    def test_execute_task_with_tasks(self, mcp_tools, temp_specs_dir):
        """Test executing task when tasks exist."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Create tasks file manually
        spec_dir = temp_specs_dir / "test-feature"
        tasks_content = """# Implementation Plan

- [ ] 1 First task
  - Implement the first task
  - _Requirements: 1.1_

- [ ] 2 Second task
  - Implement the second task
  - _Requirements: 1.2_
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        # Execute task
        result = mcp_tools.execute_task("test-feature")

        assert result["success"] is True
        assert result["task"]["identifier"] == "1"
        assert result["task"]["status"] == TaskStatus.IN_PROGRESS.value
        assert result["execution_context"]["has_requirements"] is True

    def test_execute_specific_task(self, mcp_tools, temp_specs_dir):
        """Test executing a specific task."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Create tasks file
        spec_dir = temp_specs_dir / "test-feature"
        tasks_content = """# Implementation Plan

- [ ] 1 First task
  - _Requirements: 1.1_

- [ ] 2 Second task
  - _Requirements: 1.2_
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        # Execute specific task
        result = mcp_tools.execute_task("test-feature", "2")

        assert result["success"] is True
        assert result["task"]["identifier"] == "2"
        assert result["task"]["status"] == TaskStatus.IN_PROGRESS.value

    def test_execute_task_not_found(self, mcp_tools, temp_specs_dir):
        """Test executing non-existent task."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Create tasks file
        spec_dir = temp_specs_dir / "test-feature"
        tasks_content = """# Implementation Plan

- [ ] 1 First task
  - _Requirements: 1.1_
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        # Try to execute non-existent task
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.execute_task("test-feature", "999")

        assert exc_info.value.error_code == "TASK_NOT_FOUND"

    def test_complete_task_success(self, mcp_tools, temp_specs_dir):
        """Test completing a task successfully."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Create tasks file
        spec_dir = temp_specs_dir / "test-feature"
        tasks_content = """# Implementation Plan

- [-] 1 First task (in progress)
  - _Requirements: 1.1_

- [ ] 2 Second task
  - _Requirements: 1.2_
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        # Complete task
        result = mcp_tools.complete_task("test-feature", "1")

        assert result["success"] is True
        assert result["completed_task"]["identifier"] == "1"
        assert result["completed_task"]["status"] == TaskStatus.COMPLETED.value
        assert result["progress"]["completed"] == 1
        assert result["progress"]["total"] == 2
        assert result["next_task"]["identifier"] == "2"

    def test_complete_task_not_found(self, mcp_tools, temp_specs_dir):
        """Test completing non-existent task."""
        # Create spec
        mcp_tools.create_spec("test-feature", "A test feature")

        # Create tasks file
        spec_dir = temp_specs_dir / "test-feature"
        tasks_content = """# Implementation Plan

- [ ] 1 First task
  - _Requirements: 1.1_
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        # Try to complete non-existent task
        with pytest.raises(MCPToolsError) as exc_info:
            mcp_tools.complete_task("test-feature", "999")

        assert exc_info.value.error_code == "TASK_NOT_FOUND"


class TestMCPToolsWorkflow:
    """Test complete workflow scenarios."""

    @pytest.fixture
    def temp_specs_dir(self):
        """Create a temporary directory for specs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mcp_tools(self, temp_specs_dir):
        """Create MCPTools instance with temporary directory."""
        return MCPTools(temp_specs_dir)

    def test_complete_workflow(self, mcp_tools):
        """Test complete spec workflow from creation to task execution."""
        # 1. Create spec
        create_result = mcp_tools.create_spec(
            "user-auth", "Implement user authentication with login and registration"
        )
        assert create_result["success"] is True

        # 2. List specs
        list_result = mcp_tools.list_specs()
        assert list_result["total_count"] == 1
        assert list_result["specs"][0]["current_phase"] == Phase.REQUIREMENTS.value

        # 3. Read requirements
        read_result = mcp_tools.read_spec_document("user-auth", "requirements")
        assert read_result["success"] is True
        assert "authentication" in read_result["content"].lower()

        # 4. Update requirements with approval
        updated_requirements = """# Requirements Document

## Introduction

This feature implements user authentication with secure login and registration capabilities.

## Requirements

### Requirement 1

**User Story:** As a user, I want to register for an account, so that I can access the application.

#### Acceptance Criteria

1. WHEN user provides valid registration details THEN system SHALL create new account
2. WHEN user provides invalid email THEN system SHALL reject registration
3. WHEN user provides weak password THEN system SHALL require stronger password

### Requirement 2

**User Story:** As a user, I want to login to my account, so that I can access protected features.

#### Acceptance Criteria

1. WHEN user provides correct credentials THEN system SHALL authenticate user
2. WHEN user provides incorrect credentials THEN system SHALL reject login
3. WHEN user is authenticated THEN system SHALL provide access token
"""

        update_result = mcp_tools.update_spec_document(
            "user-auth", "requirements", updated_requirements, phase_approval=True
        )
        assert update_result["success"] is True
        assert update_result["current_phase"] == Phase.DESIGN.value

        # 5. Read generated design
        design_result = mcp_tools.read_spec_document("user-auth", "design")
        assert design_result["success"] is True
        assert "# Design Document" in design_result["content"]

        # 6. Update design with approval
        updated_design = """# Design Document

## Overview

User authentication system with JWT tokens and bcrypt password hashing.

## Architecture

- REST API endpoints for registration and login
- JWT token-based authentication
- Password hashing with bcrypt
- User data storage in database

## Components and Interfaces

### AuthController
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout

### UserService
- createUser(userData)
- authenticateUser(credentials)
- hashPassword(password)

## Data Models

### User
- id: string
- email: string
- passwordHash: string
- createdAt: datetime

## Error Handling

- Invalid credentials: 401 Unauthorized
- Validation errors: 400 Bad Request
- Server errors: 500 Internal Server Error

## Testing Strategy

- Unit tests for all service methods
- Integration tests for API endpoints
- Security testing for authentication flows
"""

        design_update_result = mcp_tools.update_spec_document(
            "user-auth", "design", updated_design, phase_approval=True
        )
        assert design_update_result["success"] is True
        assert design_update_result["current_phase"] == Phase.TASKS.value

        # 7. Read generated tasks
        tasks_result = mcp_tools.read_spec_document("user-auth", "tasks")
        assert tasks_result["success"] is True
        assert "# Implementation Plan" in tasks_result["content"]
        assert "- [ ]" in tasks_result["content"]  # Should have checkbox tasks

        # 8. Execute first task
        execute_result = mcp_tools.execute_task("user-auth")
        assert execute_result["success"] is True
        assert execute_result["task"]["status"] == TaskStatus.IN_PROGRESS.value

        # 9. Complete the task
        task_id = execute_result["task"]["identifier"]
        complete_result = mcp_tools.complete_task("user-auth", task_id)
        assert complete_result["success"] is True
        assert complete_result["completed_task"]["status"] == TaskStatus.COMPLETED.value

        # 10. Final verification
        final_list = mcp_tools.list_specs()
        assert final_list["specs"][0]["current_phase"] == Phase.TASKS.value
        assert final_list["specs"][0]["has_requirements"] is True
        assert final_list["specs"][0]["has_design"] is True
        assert final_list["specs"][0]["has_tasks"] is True

    def test_workflow_with_file_references(self, mcp_tools, temp_specs_dir):
        """Test workflow with file references."""
        # Create spec first
        mcp_tools.create_spec("api-feature", "Feature with API references")

        # Create a reference file in the spec directory
        spec_dir = temp_specs_dir / "api-feature"
        ref_file = spec_dir / "api-spec.md"
        ref_file.write_text(
            """# API Specification

## Authentication Endpoints

- POST /auth/login
- POST /auth/register
- POST /auth/logout
"""
        )

        # Update requirements with file reference
        requirements_with_ref = """# Requirements Document

## Introduction

This feature implements API functionality as specified in the external document.

See API specification: #[[file:api-spec.md]]

## Requirements

### Requirement 1

**User Story:** As a developer, I want to implement the API, so that it matches the specification.

#### Acceptance Criteria

1. WHEN API is implemented THEN it SHALL match the specification
"""

        update_result = mcp_tools.update_spec_document(
            "api-feature", "requirements", requirements_with_ref
        )
        assert update_result["success"] is True

        # Read with reference resolution
        read_result = mcp_tools.read_spec_document(
            "api-feature", "requirements", resolve_references=True
        )
        assert read_result["success"] is True
        assert (
            "POST /auth/login" in read_result["content"]
        )  # Reference should be resolved
        assert len(read_result["reference_errors"]) == 0

    def test_error_handling_scenarios(self, mcp_tools):
        """Test various error scenarios."""
        # Test operations on non-existent spec
        with pytest.raises(SpecError):
            mcp_tools.read_spec_document("non-existent", "requirements")

        with pytest.raises(SpecError):
            mcp_tools.update_spec_document("non-existent", "requirements", "content")

        with pytest.raises(MCPToolsError):
            mcp_tools.execute_task("non-existent")

        with pytest.raises(MCPToolsError):
            mcp_tools.complete_task("non-existent", "1")

        with pytest.raises(MCPToolsError):
            mcp_tools.delete_spec("non-existent")

        # Test invalid parameters
        with pytest.raises(MCPToolsError):
            mcp_tools.create_spec("", "idea")

        with pytest.raises(MCPToolsError):
            mcp_tools.create_spec("feature", "")

        # Create a spec for further testing
        mcp_tools.create_spec("test-feature", "A test feature")

        with pytest.raises(MCPToolsError):
            mcp_tools.update_spec_document("test-feature", "invalid-type", "content")

        with pytest.raises(MCPToolsError):
            mcp_tools.update_spec_document("test-feature", "requirements", "")

        with pytest.raises(MCPToolsError):
            mcp_tools.read_spec_document("test-feature", "invalid-type")


class TestMCPToolsEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def temp_specs_dir(self):
        """Create a temporary directory for specs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mcp_tools(self, temp_specs_dir):
        """Create MCPTools instance with temporary directory."""
        return MCPTools(temp_specs_dir)

    def test_feature_name_validation(self, mcp_tools):
        """Test feature name validation edge cases."""
        # Valid names should work - only use kebab-case names
        valid_names = [
            "simple-feature",
            "feature-123",
            "a",  # Single character
            "very-long-feature-name-with-many-parts",
        ]

        for name in valid_names:
            result = mcp_tools.create_spec(name, "Test feature")
            assert result["success"] is True
            mcp_tools.delete_spec(name)  # Clean up

        # Test whitespace handling
        result = mcp_tools.create_spec("  spaced-name  ", "  spaced idea  ")
        assert result["success"] is True
        assert result["spec"]["feature_name"] == "spaced-name"

    def test_large_content_handling(self, mcp_tools):
        """Test handling of large document content."""
        mcp_tools.create_spec("large-feature", "A feature with large content")

        # Create large content (but still reasonable)
        large_content = "# Requirements Document\n\n"
        large_content += "## Introduction\n\n"
        large_content += "This is a large requirements document.\n\n"
        large_content += "## Requirements\n\n"

        for i in range(50):  # 50 requirements
            large_content += f"""### Requirement {i+1}

**User Story:** As a user, I want feature {i+1}, so that I can accomplish task {i+1}.

#### Acceptance Criteria

1. WHEN user performs action {i+1} THEN system SHALL respond appropriately
2. WHEN user provides input {i+1} THEN system SHALL validate correctly

"""

        result = mcp_tools.update_spec_document(
            "large-feature", "requirements", large_content
        )
        assert result["success"] is True

        # Verify we can read it back
        read_result = mcp_tools.read_spec_document("large-feature", "requirements")
        assert read_result["success"] is True
        assert len(read_result["content"]) > 1000  # Should be substantial

    def test_concurrent_operations_simulation(self, mcp_tools):
        """Test operations that might conflict (simulated concurrency)."""
        # Create spec
        mcp_tools.create_spec("concurrent-test", "Test concurrent operations")

        # Simulate rapid updates (in real concurrency, these might conflict)
        for i in range(5):
            content = f"""# Requirements Document

## Introduction

Updated requirements version {i+1}.

## Requirements

### Requirement 1

**User Story:** As a user, I want version {i+1}, so that I can test updates.

#### Acceptance Criteria

1. WHEN user updates to version {i+1} THEN system SHALL handle it correctly
"""
            result = mcp_tools.update_spec_document(
                "concurrent-test", "requirements", content
            )
            assert result["success"] is True

        # Verify final state
        read_result = mcp_tools.read_spec_document("concurrent-test", "requirements")
        assert "version 5" in read_result["content"]

    def test_unicode_and_special_characters(self, mcp_tools):
        """Test handling of unicode and special characters."""
        # Create spec with unicode content
        unicode_idea = "Feature with émojis 🚀 and spëcial characters: àáâãäå"
        result = mcp_tools.create_spec("unicode-feature", unicode_idea)
        assert result["success"] is True

        # Update with more unicode content
        unicode_content = """# Requirements Document

## Introduction

This feature handles unicode: 中文, العربية, русский, 日本語

Special symbols: ©®™ ±×÷ ←→↑↓ ♠♣♥♦

## Requirements

### Requirement 1

**User Story:** As a user, I want unicode support 🌍, so that I can use international characters.

#### Acceptance Criteria

1. WHEN user enters unicode text THEN system SHALL preserve encoding correctly
2. WHEN system displays unicode THEN it SHALL render properly
"""

        update_result = mcp_tools.update_spec_document(
            "unicode-feature", "requirements", unicode_content
        )
        assert update_result["success"] is True

        # Verify unicode is preserved
        read_result = mcp_tools.read_spec_document("unicode-feature", "requirements")
        assert "🌍" in read_result["content"]
        assert "中文" in read_result["content"]
