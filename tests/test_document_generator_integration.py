"""Tests for DocumentGenerator integration with standard task format."""
import pytest

from src.spec_server.document_generator import DocumentGenerationError, DocumentGenerator


class TestDocumentGeneratorIntegration:
    """Test DocumentGenerator integration with standard task format."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DocumentGenerator()

        # Sample requirements content
        self.requirements_content = """# Requirements Document

## Introduction
This feature implements user authentication system.

## Requirements

### Requirement 1

**User Story:** As a user, I want to log in securely, so that I can access the system

#### Acceptance Criteria
1. WHEN user enters valid credentials THEN the system SHALL authenticate them
2. WHEN user enters invalid credentials THEN the system SHALL reject them
3. IF user provides malformed input THEN the system SHALL provide clear error messages

### Requirement 2

**User Story:** As a developer, I want to manage user sessions, so that security is maintained

#### Acceptance Criteria
1. WHEN user logs in THEN the system SHALL create a secure session
2. WHEN session expires THEN the system SHALL require re-authentication
"""

        # Sample design content
        self.design_content = """# Design Document

## Overview
The authentication system provides secure user access.

## Architecture
The system follows a layered architecture pattern.

## Components and Interfaces

### Core Components

1. **Authentication Controller**: Handles login/logout requests
2. **Session Manager**: Manages user sessions
3. **User Repository**: Handles user data access

## Data Models
User entity with credentials and session information.

## Error Handling
Comprehensive error handling for authentication failures.

## Testing Strategy
Unit and integration testing for all components.
"""

    def test_generate_tasks_standard_format(self):
        """Test that generate_tasks produces standard format."""
        result = self.generator.generate_tasks(self.requirements_content, self.design_content, "auth-system")

        # Should include standard header
        assert "# Implementation Plan" in result

        # Should use checkbox format
        assert "- [ ] 1." in result
        assert "- [ ] 2." in result

        # Should include requirements references
        assert "_Requirements:" in result

        # Should include proper requirement numbers
        assert "1.1" in result or "2.1" in result

    def test_generate_tasks_with_user_stories(self):
        """Test task generation based on user stories."""
        result = self.generator.generate_tasks(self.requirements_content, self.design_content, "auth-system")

        # Should generate tasks based on user stories
        assert "log in securely" in result or "manage user sessions" in result

        # Should include task details
        assert "Create interface" in result
        assert "Add input validation" in result
        assert "Write unit tests" in result

    def test_generate_tasks_requirements_linking(self):
        """Test that tasks are properly linked to requirements."""
        result = self.generator.generate_tasks(self.requirements_content, self.design_content, "auth-system")

        # Should include requirements references in standard format
        lines = result.split("\n")
        req_lines = [line for line in lines if "_Requirements:" in line]

        assert len(req_lines) > 0

        # Check format of requirements references
        for line in req_lines:
            assert "_Requirements:" in line
            assert "_" in line  # Should be italicized
            # Should contain valid requirement numbers (X.Y format)
            import re

            req_pattern = r"\d+\.\d+"
            assert re.search(req_pattern, line)

    def test_generate_tasks_hierarchical_structure(self):
        """Test that tasks maintain hierarchical structure."""
        result = self.generator.generate_tasks(self.requirements_content, self.design_content, "auth-system")

        lines = result.split("\n")

        # Should have main tasks (not indented)
        main_tasks = [line for line in lines if line.startswith("- [ ]")]
        assert len(main_tasks) > 0

        # Should have sub-items (indented)
        sub_items = [line for line in lines if line.startswith("  -")]
        assert len(sub_items) > 0

    def test_generate_tasks_error_handling(self):
        """Test error handling in task generation."""
        # Test with empty requirements
        with pytest.raises(DocumentGenerationError) as exc_info:
            self.generator.generate_tasks("", self.design_content)

        assert exc_info.value.error_code == "EMPTY_REQUIREMENTS"

        # Test with empty design
        with pytest.raises(DocumentGenerationError) as exc_info:
            self.generator.generate_tasks(self.requirements_content, "")

        assert exc_info.value.error_code == "EMPTY_DESIGN"

    def test_validate_tasks_format(self):
        """Test validation of tasks document format."""
        # Generate a tasks document
        result = self.generator.generate_tasks(self.requirements_content, self.design_content, "auth-system")

        # Should validate successfully
        is_valid = self.generator.validate_document_format("tasks", result)
        assert is_valid is True

    def test_validate_invalid_tasks_format(self):
        """Test validation rejects invalid tasks format."""
        invalid_tasks = """# Wrong Header

Some content without proper task format.
"""

        is_valid = self.generator.validate_document_format("tasks", invalid_tasks)
        assert is_valid is False

    def test_extract_requirement_numbers(self):
        """Test requirement number extraction."""
        parsed_requirements = self.generator._parse_requirements(self.requirements_content)
        requirement_numbers = self.generator._extract_requirement_numbers(parsed_requirements)

        # Should extract requirement numbers based on user stories
        assert len(requirement_numbers) > 0

        # Should be in X.Y format
        for req_num in requirement_numbers:
            assert "." in req_num
            parts = req_num.split(".")
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert parts[1].isdigit()

    def test_format_tasks_standard_format(self):
        """Test the standard format method directly."""
        sample_tasks = [
            {
                "id": "1",
                "description": "Implement authentication",
                "details": ["Create login interface", "Add validation"],
                "requirements_refs": ["1.1", "1.2"],
            },
            {
                "id": "2",
                "description": "Setup testing",
                "details": ["Write unit tests"],
                "requirements_refs": ["2.1"],
            },
        ]

        parsed_requirements = {"user_stories": []}
        result = self.generator._format_tasks_standard_format(sample_tasks, parsed_requirements)

        # Should format correctly
        assert "- [ ] 1. Implement authentication" in result
        assert "- [ ] 2. Setup testing" in result
        assert "_Requirements: 1.1, 1.2_" in result
        assert "_Requirements: 2.1_" in result
        assert "Create login interface" in result
        assert "Write unit tests" in result

    def test_format_tasks_filters_invalid_refs(self):
        """Test that invalid requirement references are filtered out."""
        sample_tasks = [
            {
                "id": "1",
                "description": "Test task",
                "details": ["Some detail"],
                "requirements_refs": ["1.1", "[TBD]", "invalid", "2.1"],
            }
        ]

        parsed_requirements = {"user_stories": []}
        result = self.generator._format_tasks_standard_format(sample_tasks, parsed_requirements)

        # Should only include valid references
        assert "_Requirements: 1.1, 2.1_" in result
        assert "[TBD]" not in result
        assert "invalid" not in result

    def test_generate_tasks_with_no_user_stories(self):
        """Test task generation when no user stories are found."""
        requirements_no_stories = """# Requirements Document

## Introduction
Basic system requirements.

## Requirements
Some general requirements without user stories.
"""

        result = self.generator.generate_tasks(requirements_no_stories, self.design_content, "test-system")

        # Should still generate tasks based on components
        assert "# Implementation Plan" in result
        assert "- [ ] 1." in result
        assert "_Requirements:" in result

    def test_integration_with_existing_workflow(self):
        """Test integration with existing document generation workflow."""
        # Generate requirements
        requirements = self.generator.generate_requirements("Create a user authentication system", "auth-system")

        # Generate design
        design = self.generator.generate_design(requirements, "auth-system")

        # Generate tasks using standard format
        tasks = self.generator.generate_tasks(requirements, design, "auth-system")

        # All should be valid
        assert self.generator.validate_document_format("requirements", requirements)
        assert self.generator.validate_document_format("design", design)
        assert self.generator.validate_document_format("tasks", tasks)

        # Tasks should use standard format
        assert "# Implementation Plan" in tasks
        assert "_Requirements:" in tasks
        assert "- [ ]" in tasks
