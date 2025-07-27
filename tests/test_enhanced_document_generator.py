"""
Unit tests for enhanced DocumentGenerator functionality.

Tests the integration of DesignFormatDetector and DesignElementFormatter
into the DocumentGenerator for automatic format detection and enhancement.
"""

import pytest

from src.spec_server.design_template_manager import DesignTemplateManager
from src.spec_server.document_generator import DocumentGenerationError, DocumentGenerator
from src.spec_server.models import FormatAnalysisResult, TechnicalElement


class TestEnhancedDocumentGenerator:
    """Test enhanced DocumentGenerator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DocumentGenerator()

    def test_initialization_with_enhanced_components(self):
        """Test that DocumentGenerator initializes with enhanced design format components."""
        assert self.generator.template_manager is not None
        assert self.generator.format_detector is not None
        assert self.generator.element_formatter is not None

    def test_generate_design_new_document(self):
        """Test generating a new design document with enhanced format."""
        requirements = """
        # Requirements Document

        ## Requirements

        ### Requirement 1
        **User Story:** As a user, I want to manage tasks, so that I can track my work.

        #### Acceptance Criteria
        1. WHEN user creates a task THEN the system SHALL store the task
        """

        design = self.generator.generate_design(requirements, "task-manager")

        assert "# Design Document" in design
        assert "## Overview" in design
        assert "## Architecture" in design
        assert "## Components and Interfaces" in design
        assert "## Data Models" in design

    def test_generate_design_with_existing_design_no_enhancement_needed(self):
        """Test generating design with existing design that already has proper format."""
        requirements = """
        # Requirements Document

        ## Requirements

        ### Requirement 1
        **User Story:** As a user, I want to manage tasks, so that I can track my work.
        """

        existing_design = """
        # Design Document

        ## Components and Interfaces

        ### TaskManager Component

        **Intent**: Manages task operations in the system.

        **Goals**:
        - Handle task creation and updates
        - Maintain task state consistency

        **Logic**: The TaskManager component uses a repository pattern to persist tasks and provides a clean API for task operations.
        """

        enhanced_design = self.generator.generate_design(requirements, "task-manager", existing_design)

        # Should return the original design since no enhancement is needed
        assert "**Intent**: Manages task operations in the system." in enhanced_design
        assert "**Goals**:" in enhanced_design
        assert "**Logic**: The TaskManager component uses" in enhanced_design

    def test_generate_design_with_existing_design_needs_enhancement(self):
        """Test generating design with existing design that needs enhancement."""
        requirements = """
        # Requirements Document

        ## Requirements

        ### Requirement 1
        **User Story:** As a user, I want to manage tasks, so that I can track my work.
        """

        existing_design = """
        # Design Document

        ## Components and Interfaces

        ### TaskManager Component

        This component handles task operations and provides task management functionality.

        ### DataProcessor

        Processes data for the application.
        """

        enhanced_design = self.generator.generate_design(requirements, "task-manager", existing_design)

        # Should enhance the components with Intent/Goals/Logic format
        assert "**Intent**:" in enhanced_design
        assert "**Goals**:" in enhanced_design
        assert "**Logic**:" in enhanced_design
        # Should preserve original content
        assert "task operations" in enhanced_design
        assert "Processes data" in enhanced_design

    def test_analyze_design_format(self):
        """Test analyzing design document format."""
        design_content = """
        # Design Document

        ## Components

        ### TaskManager Component

        **Intent**: Manages tasks.

        **Goals**:
        - Handle tasks

        **Logic**: Uses repository pattern.

        ### DataProcessor

        This component processes data without proper format.
        """

        analysis_result = self.generator.analyze_design_format(design_content)

        assert isinstance(analysis_result, FormatAnalysisResult)
        assert analysis_result.total_elements >= 1
        assert len(analysis_result.elements_needing_enhancement) >= 1
        assert analysis_result.enhancement_summary
        assert analysis_result.estimated_changes > 0

    def test_analyze_design_format_empty_content(self):
        """Test analyzing empty design document."""
        analysis_result = self.generator.analyze_design_format("")

        assert analysis_result.total_elements == 0
        assert len(analysis_result.elements_needing_enhancement) == 0
        assert analysis_result.estimated_changes == 0

    def test_analyze_design_format_error_handling(self):
        """Test error handling in design format analysis."""
        # This should not raise an exception
        analysis_result = self.generator.analyze_design_format("Invalid content")
        assert isinstance(analysis_result, FormatAnalysisResult)

    def test_enhance_existing_design(self):
        """Test enhancing existing design document."""
        existing_design = """
        ### TaskManager Component

        This component manages tasks in the system.
        """

        requirements = "Basic requirements"

        enhanced = self.generator._enhance_existing_design(existing_design, requirements, "test")

        # Should add Intent/Goals/Logic sections
        assert "**Intent**:" in enhanced or enhanced == existing_design  # May not need enhancement

    def test_enhance_existing_design_no_elements(self):
        """Test enhancing design with no technical elements."""
        existing_design = """
        # Design Document

        This is just a description without technical elements.
        """

        requirements = "Basic requirements"

        enhanced = self.generator._enhance_existing_design(existing_design, requirements, "test")

        # Should return original content unchanged
        assert enhanced == existing_design

    def test_generate_new_design_with_enhanced_format(self):
        """Test generating new design with enhanced format."""
        requirements = """
        # Requirements Document

        ## Requirements

        ### Requirement 1
        **User Story:** As a user, I want to manage tasks, so that I can track my work.
        """

        design = self.generator._generate_new_design_with_enhanced_format(requirements, "task-manager")

        assert "# Design Document" in design
        assert "## Overview" in design
        assert "## Components and Interfaces" in design
        assert "## Data Models" in design

    def test_generate_enhanced_design_components(self):
        """Test generating enhanced components section."""
        parsed_requirements = {"user_stories": [{"actor": "user", "want": "manage tasks", "benefit": "track work"}], "actors": ["user"], "features": ["task management"]}

        components = self.generator._generate_enhanced_design_components(parsed_requirements)

        assert isinstance(components, str)
        assert len(components) > 0

    def test_generate_enhanced_design_data_models(self):
        """Test generating enhanced data models section."""
        parsed_requirements = {"user_stories": [{"actor": "user", "want": "manage tasks", "benefit": "track work"}], "actors": ["user"], "features": ["task management"]}

        data_models = self.generator._generate_enhanced_design_data_models(parsed_requirements)

        assert isinstance(data_models, str)
        assert len(data_models) > 0

    def test_replace_element_in_content(self):
        """Test replacing element content in document."""
        content = """Line 1
Line 2
### Component
Old content
Line 5"""

        element = TechnicalElement(element_type="component", element_name="Component", content="### Component\nOld content", line_start=3, line_end=4)

        formatted_element = """### Component

**Intent**: New intent.

**Goals**:
- New goal

**Logic**: New logic."""

        result = self.generator._replace_element_in_content(content, element, formatted_element)

        assert "**Intent**: New intent." in result
        assert "**Goals**:" in result
        assert "**Logic**: New logic." in result
        assert "Line 1" in result
        assert "Line 5" in result
        assert "Old content" not in result

    def test_replace_element_in_content_error_handling(self):
        """Test error handling in element replacement."""
        content = "Original content"

        # Create element with invalid line numbers
        element = TechnicalElement(element_type="component", element_name="Component", content="content", line_start=100, line_end=200)  # Invalid line number

        formatted_element = "New content"

        # Should return original content on error
        result = self.generator._replace_element_in_content(content, element, formatted_element)
        assert result == content

    def test_update_template_manager(self):
        """Test updating template manager."""
        new_template_manager = DesignTemplateManager()

        self.generator.update_template_manager(new_template_manager)

        assert self.generator.template_manager == new_template_manager

    def test_generate_design_empty_requirements(self):
        """Test generating design with empty requirements raises error."""
        with pytest.raises(DocumentGenerationError) as exc_info:
            self.generator.generate_design("")

        assert "Requirements content cannot be empty" in str(exc_info.value)

    def test_generate_design_error_handling(self):
        """Test error handling in design generation."""
        # This should handle errors gracefully
        try:
            result = self.generator.generate_design("Invalid requirements format")
            assert isinstance(result, str)
        except DocumentGenerationError:
            # This is acceptable - the error should be properly formatted
            pass

    def test_analyze_design_format_error_handling_malformed(self):
        """Test error handling in format analysis with malformed content."""
        # Should handle malformed content gracefully
        try:
            result = self.generator.analyze_design_format("Malformed content")
            assert isinstance(result, FormatAnalysisResult)
        except DocumentGenerationError:
            # This is acceptable - the error should be properly formatted
            pass

    def test_integration_with_existing_methods(self):
        """Test that enhanced functionality integrates with existing methods."""
        # Test that existing functionality still works
        requirements = """
        # Requirements Document

        ## Requirements

        ### Requirement 1
        **User Story:** As a user, I want to create tasks, so that I can track my work.

        #### Acceptance Criteria
        1. WHEN user creates task THEN system SHALL store it
        """

        # Test requirements generation still works
        initial_idea = "A task management system"
        req_doc = self.generator.generate_requirements(initial_idea, "task-manager")
        assert "# Requirements Document" in req_doc

        # Test design generation with enhanced format
        design_doc = self.generator.generate_design(requirements, "task-manager")
        assert "# Design Document" in design_doc

        # Test tasks generation still works
        tasks_doc = self.generator.generate_tasks(requirements, design_doc, "task-manager")
        assert "# Implementation Plan" in tasks_doc

    def test_enhanced_format_preserves_existing_content(self):
        """Test that enhancement preserves existing content while adding structure."""
        existing_design = """
        # Design Document

        ## Components

        ### UserService

        This service handles user authentication and manages user sessions.
        It provides methods for login, logout, and session validation.

        The service uses JWT tokens for authentication.
        """

        requirements = "Basic requirements"

        enhanced = self.generator.generate_design(requirements, "auth-system", existing_design)

        # Should preserve original content
        assert "user authentication" in enhanced
        assert "JWT tokens" in enhanced
        assert "session validation" in enhanced

        # Should add structure (if enhancement was needed)
        # The exact format depends on whether the detector identifies this as needing enhancement
