"""
Unit tests for DocumentGenerator class.
"""

import pytest

from spec_server.document_generator import DocumentGenerationError, DocumentGenerator


class TestDocumentGenerator:
    """Test DocumentGenerator class."""

    def test_document_generator_initialization(self):
        """Test DocumentGenerator initialization."""
        generator = DocumentGenerator()

        assert "requirements" in generator.templates
        assert "design" in generator.templates
        assert "tasks" in generator.templates

    def test_generate_requirements_success(self):
        """Test successful requirements generation."""
        generator = DocumentGenerator()

        initial_idea = "A system to manage user authentication and authorization"
        result = generator.generate_requirements(initial_idea, "auth-system")

        assert "# Requirements Document" in result
        assert "## Introduction" in result
        assert "## Requirements" in result
        assert "authentication" in result.lower()
        assert "As a" in result
        assert "WHEN" in result or "IF" in result
        assert "THEN" in result or "SHALL" in result

    def test_generate_requirements_empty_idea(self):
        """Test requirements generation with empty idea."""
        generator = DocumentGenerator()

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.generate_requirements("")

        assert exc_info.value.error_code == "EMPTY_INITIAL_IDEA"

    def test_generate_requirements_whitespace_only(self):
        """Test requirements generation with whitespace-only idea."""
        generator = DocumentGenerator()

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.generate_requirements("   \n\t   ")

        assert exc_info.value.error_code == "EMPTY_INITIAL_IDEA"

    def test_generate_requirements_complex_idea(self):
        """Test requirements generation with complex idea."""
        generator = DocumentGenerator()

        initial_idea = """
        A comprehensive project management system that allows users to create projects,
        manage tasks, track progress, and collaborate with team members. The system
        should support multiple user roles including admin, project manager, and developer.
        """

        result = generator.generate_requirements(initial_idea, "project-mgmt")

        assert "# Requirements Document" in result
        assert "project" in result.lower()
        assert "user" in result.lower()
        assert "manage" in result.lower()
        assert "### Requirement" in result

    def test_generate_design_success(self):
        """Test successful design generation."""
        generator = DocumentGenerator()

        requirements = """
        # Requirements Document
        
        ## Introduction
        
        This system manages user authentication.
        
        ## Requirements
        
        ### Requirement 1
        
        **User Story:** As a user, I want to login, so that I can access the system
        
        #### Acceptance Criteria
        
        1. WHEN user provides valid credentials THEN system SHALL authenticate user
        2. IF user provides invalid credentials THEN system SHALL reject login
        """

        result = generator.generate_design(requirements, "auth-system")

        assert "# Design Document" in result
        assert "## Overview" in result
        assert "## Architecture" in result
        assert "## Components and Interfaces" in result
        assert "## Data Models" in result
        assert "## Error Handling" in result
        assert "## Testing Strategy" in result

    def test_generate_design_empty_requirements(self):
        """Test design generation with empty requirements."""
        generator = DocumentGenerator()

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.generate_design("")

        assert exc_info.value.error_code == "EMPTY_REQUIREMENTS"

    def test_generate_tasks_success(self):
        """Test successful tasks generation."""
        generator = DocumentGenerator()

        requirements = """
        # Requirements Document
        
        ## Requirements
        
        ### Requirement 1
        
        **User Story:** As a user, I want to login, so that I can access the system
        """

        design = """
        # Design Document
        
        ## Overview
        
        Authentication system design.
        
        ## Components and Interfaces
        
        **Auth Controller**: Handles authentication requests
        **User Service**: Manages user data
        **Token Manager**: Handles JWT tokens
        """

        result = generator.generate_tasks(requirements, design, "auth-system")

        assert "# Implementation Plan" in result
        assert "- [ ]" in result
        assert "1." in result
        assert "_Requirements:" in result

    def test_generate_tasks_empty_requirements(self):
        """Test tasks generation with empty requirements."""
        generator = DocumentGenerator()

        design = "# Design Document\n\nSome design content"

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.generate_tasks("", design)

        assert exc_info.value.error_code == "EMPTY_REQUIREMENTS"

    def test_generate_tasks_empty_design(self):
        """Test tasks generation with empty design."""
        generator = DocumentGenerator()

        requirements = "# Requirements\n\nSome requirements"

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.generate_tasks(requirements, "")

        assert exc_info.value.error_code == "EMPTY_DESIGN"

    def test_validate_document_format_requirements_valid(self):
        """Test validation of valid requirements document."""
        generator = DocumentGenerator()

        valid_requirements = """
        # Requirements Document
        
        ## Introduction
        
        This is a test feature.
        
        ## Requirements
        
        ### Requirement 1
        
        **User Story:** As a user, I want to test, so that I can verify functionality
        
        #### Acceptance Criteria
        
        1. WHEN user performs action THEN system SHALL respond
        """

        result = generator.validate_document_format("requirements", valid_requirements)
        assert result is True

    def test_validate_document_format_requirements_invalid(self):
        """Test validation of invalid requirements document."""
        generator = DocumentGenerator()

        invalid_requirements = """
        # Some Document
        
        This is not a proper requirements document.
        """

        result = generator.validate_document_format(
            "requirements", invalid_requirements
        )
        assert result is False

    def test_validate_document_format_design_valid(self):
        """Test validation of valid design document."""
        generator = DocumentGenerator()

        valid_design = """
        # Design Document
        
        ## Overview
        
        System overview.
        
        ## Architecture
        
        System architecture.
        
        ## Components and Interfaces
        
        System components.
        
        ## Data Models
        
        Data models.
        
        ## Error Handling
        
        Error handling.
        
        ## Testing Strategy
        
        Testing strategy.
        """

        result = generator.validate_document_format("design", valid_design)
        assert result is True

    def test_validate_document_format_design_invalid(self):
        """Test validation of invalid design document."""
        generator = DocumentGenerator()

        invalid_design = """
        # Some Document
        
        ## Overview
        
        Missing required sections.
        """

        result = generator.validate_document_format("design", invalid_design)
        assert result is False

    def test_validate_document_format_tasks_valid(self):
        """Test validation of valid tasks document."""
        generator = DocumentGenerator()

        valid_tasks = """
        # Implementation Plan
        
        - [ ] 1. First task
        - [ ] 2. Second task
        """

        result = generator.validate_document_format("tasks", valid_tasks)
        assert result is True

    def test_validate_document_format_tasks_invalid(self):
        """Test validation of invalid tasks document."""
        generator = DocumentGenerator()

        invalid_tasks = """
        # Some Plan
        
        - First task (no checkbox)
        - Second task (no checkbox)
        """

        result = generator.validate_document_format("tasks", invalid_tasks)
        assert result is False

    def test_validate_document_format_unknown_type(self):
        """Test validation with unknown document type."""
        generator = DocumentGenerator()

        with pytest.raises(DocumentGenerationError) as exc_info:
            generator.validate_document_format("unknown", "content")

        assert exc_info.value.error_code == "UNKNOWN_DOCUMENT_TYPE"

    def test_extract_concepts_from_idea(self):
        """Test concept extraction from initial idea."""
        generator = DocumentGenerator()

        idea = "As a user, I want to create and manage projects so that I can track development progress"
        concepts = generator._extract_concepts_from_idea(idea)

        assert "actors" in concepts
        assert "actions" in concepts
        assert "objects" in concepts
        assert "user" in concepts["actors"]
        assert any(
            "create" in action or "manage" in action for action in concepts["actions"]
        )

    def test_parse_requirements(self):
        """Test requirements parsing."""
        generator = DocumentGenerator()

        requirements = """
        ### Requirement 1
        
        **User Story:** As a developer, I want to write code, so that I can build features
        
        #### Acceptance Criteria
        
        1. WHEN developer writes code THEN system SHALL compile successfully
        2. IF code has errors THEN system SHALL show error messages
        """

        parsed = generator._parse_requirements(requirements)

        assert "user_stories" in parsed
        assert "acceptance_criteria" in parsed
        assert "actors" in parsed
        assert len(parsed["user_stories"]) > 0
        assert len(parsed["acceptance_criteria"]) > 0
        assert "developer" in parsed["actors"]

    def test_parse_design(self):
        """Test design parsing."""
        generator = DocumentGenerator()

        design = """
        # Design Document
        
        ## Overview
        
        System overview
        
        ## Components and Interfaces
        
        **Main Controller**: Handles requests
        **Service Layer**: Business logic
        **Data Layer**: Persistence
        """

        parsed = generator._parse_design(design)

        assert "components" in parsed
        assert "sections" in parsed
        assert "Overview" in parsed["sections"]
        assert "Components and Interfaces" in parsed["sections"]
        assert len(parsed["components"]) > 0

    def test_format_tasks_as_checkboxes(self):
        """Test task formatting as checkboxes."""
        generator = DocumentGenerator()

        tasks = [
            {
                "id": "1",
                "description": "First task",
                "details": ["Detail 1", "Detail 2"],
                "requirements_refs": ["1.1", "1.2"],
            },
            {
                "id": "2",
                "description": "Second task",
                "details": ["Detail A"],
                "requirements_refs": ["2.1"],
            },
        ]

        result = generator._format_tasks_as_checkboxes(tasks)

        assert "- [ ] 1. First task" in result
        assert "- [ ] 2. Second task" in result
        assert "Detail 1" in result
        assert "_Requirements: 1.1, 1.2_" in result
        assert "_Requirements: 2.1_" in result

    def test_generate_requirements_with_various_concepts(self):
        """Test requirements generation with different types of concepts."""
        generator = DocumentGenerator()

        test_cases = [
            "A user management system for administrators",
            "API server to handle client requests",
            "Dashboard for monitoring system performance",
            "Mobile app for customer support",
        ]

        for idea in test_cases:
            result = generator.generate_requirements(idea)

            assert "# Requirements Document" in result
            assert "## Introduction" in result
            assert "## Requirements" in result
            assert "As a" in result
            assert len(result) > 100  # Should generate substantial content

    def test_generate_design_with_various_requirements(self):
        """Test design generation with different requirement patterns."""
        generator = DocumentGenerator()

        requirements_templates = [
            """
            ## Requirements
            **User Story:** As a user, I want to login, so that I can access features
            1. WHEN user enters credentials THEN system SHALL authenticate
            """,
            """
            ## Requirements
            **User Story:** As an admin, I want to manage users, so that I can control access
            1. IF admin has permissions THEN system SHALL allow user management
            """,
        ]

        for req in requirements_templates:
            result = generator.generate_design(req)

            assert "# Design Document" in result
            assert "## Overview" in result
            assert len(result) > 200  # Should generate substantial content

    def test_error_handling_in_generation(self):
        """Test error handling during document generation."""
        generator = DocumentGenerator()

        # Test with malformed input that might cause parsing issues
        malformed_requirements = "This is not a proper requirements document at all"

        # Should not raise exception, but handle gracefully
        try:
            result = generator.generate_design(malformed_requirements)
            assert "# Design Document" in result
        except DocumentGenerationError:
            # This is acceptable - the generator detected invalid input
            pass


class TestDocumentGenerationError:
    """Test DocumentGenerationError exception class."""

    def test_document_generation_error_basic(self):
        """Test basic DocumentGenerationError creation."""
        error = DocumentGenerationError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "DOCUMENT_GENERATION_ERROR"
        assert error.details == {}

    def test_document_generation_error_with_code_and_details(self):
        """Test DocumentGenerationError with custom code and details."""
        details = {"input": "test", "context": "generation"}
        error = DocumentGenerationError(
            "Custom error message", error_code="CUSTOM_ERROR", details=details
        )

        assert error.message == "Custom error message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details
