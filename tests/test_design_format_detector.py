"""
Unit tests for DesignFormatDetector.

Tests the design format detection and analysis functionality.
"""

from src.spec_server.design_format_detector import DesignFormatDetector
from src.spec_server.models import EnhancedDesignTemplate, FormatAnalysisResult, TechnicalElement


class TestDesignFormatDetector:
    """Test DesignFormatDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DesignFormatDetector()

    def test_initialization(self):
        """Test DesignFormatDetector initialization."""
        assert self.detector.template is not None
        assert len(self.detector.intent_patterns) > 0
        assert len(self.detector.goals_patterns) > 0
        assert len(self.detector.logic_patterns) > 0

    def test_initialization_with_custom_template(self):
        """Test initialization with custom template."""
        custom_template = EnhancedDesignTemplate(element_patterns={"custom": r"custom\s+(\w+)"})
        detector = DesignFormatDetector(custom_template)

        assert detector.template == custom_template
        assert "custom" in detector.template.element_patterns

    def test_detect_technical_elements_empty_content(self):
        """Test detecting elements in empty content."""
        elements = self.detector.detect_technical_elements("")
        assert elements == []

    def test_detect_technical_elements_no_matches(self):
        """Test detecting elements when no technical elements exist."""
        content = """
        # Some Document

        This is just regular text with no technical elements.
        """
        elements = self.detector.detect_technical_elements(content)
        assert elements == []

    def test_detect_interface_elements(self):
        """Test detecting interface elements."""
        content = """
        ## Components and Interfaces

        ### UserService Interface

        This interface handles user operations.

        ### PaymentService

        This service handles payments.
        """
        elements = self.detector.detect_technical_elements(content)

        # Should find UserService as interface
        interface_elements = [e for e in elements if e.element_type == "interface"]
        assert len(interface_elements) >= 1

        user_service = next((e for e in interface_elements if "UserService" in e.element_name), None)
        assert user_service is not None
        assert user_service.element_type == "interface"
        assert "UserService" in user_service.element_name

    def test_detect_component_elements(self):
        """Test detecting component elements."""
        content = """
        ## Components

        ### TaskManager Component

        This component manages tasks.

        ### DataProcessor

        This processes data.
        """
        elements = self.detector.detect_technical_elements(content)

        component_elements = [e for e in elements if e.element_type == "component"]
        assert len(component_elements) >= 1

        task_manager = next((e for e in component_elements if "TaskManager" in e.element_name), None)
        assert task_manager is not None
        assert task_manager.element_type == "component"

    def test_detect_data_model_elements(self):
        """Test detecting data model elements."""
        content = """
        ## Data Models

        ### User Model

        Represents a user in the system.

        ### Task Entity

        Represents a task.
        """
        elements = self.detector.detect_technical_elements(content)

        data_model_elements = [e for e in elements if e.element_type == "data_model"]
        assert len(data_model_elements) >= 1

        user_model = next((e for e in data_model_elements if "User" in e.element_name), None)
        assert user_model is not None
        assert user_model.element_type == "data_model"

    def test_detect_service_elements(self):
        """Test detecting service elements."""
        content = """
        ## Services

        ### EmailService

        Handles email operations.

        ### NotificationManager

        Manages notifications.
        """
        elements = self.detector.detect_technical_elements(content)

        service_elements = [e for e in elements if e.element_type == "service"]
        assert len(service_elements) >= 1

    def test_detect_class_elements(self):
        """Test detecting class elements in code blocks."""
        content = """
        ## Implementation

        ```python
        class UserRepository:
            def __init__(self):
                pass

        class TaskService:
            def process(self):
                pass
        ```
        """
        elements = self.detector.detect_technical_elements(content)

        class_elements = [e for e in elements if e.element_type == "class"]
        assert len(class_elements) >= 1

    def test_check_element_format_with_all_sections(self):
        """Test checking element that has all Intent/Goals/Logic sections."""
        element = TechnicalElement(
            element_type="interface",
            element_name="TestInterface",
            content="""
            ### TestInterface

            **Intent**: This interface provides test functionality.

            **Goals**:
            - Goal 1
            - Goal 2

            **Logic**: This interface works by implementing test methods.
            """,
            line_start=1,
            line_end=10,
        )

        has_format = self.detector.check_element_format(element)
        assert has_format is True
        assert element.has_intent is True
        assert element.has_goals is True
        assert element.has_logic is True

    def test_check_element_format_missing_sections(self):
        """Test checking element that's missing some sections."""
        element = TechnicalElement(
            element_type="component",
            element_name="TestComponent",
            content="""
            ### TestComponent

            **Intent**: This component does testing.

            Some other content without Goals or Logic.
            """,
            line_start=1,
            line_end=8,
        )

        has_format = self.detector.check_element_format(element)
        assert has_format is False
        assert element.has_intent is True
        assert element.has_goals is False
        assert element.has_logic is False

    def test_check_element_format_no_sections(self):
        """Test checking element that has no Intent/Goals/Logic sections."""
        element = TechnicalElement(
            element_type="data_model",
            element_name="TestModel",
            content="""
            ### TestModel

            This is a simple model description without structured sections.
            """,
            line_start=1,
            line_end=5,
        )

        has_format = self.detector.check_element_format(element)
        assert has_format is False
        assert element.has_intent is False
        assert element.has_goals is False
        assert element.has_logic is False

    def test_check_element_format_alternative_section_names(self):
        """Test checking element with alternative section names."""
        element = TechnicalElement(
            element_type="service",
            element_name="TestService",
            content="""
            ### TestService

            **Purpose**: This service handles testing.

            **Objectives**:
            - Objective 1
            - Objective 2

            **Implementation**: The service implements test logic.
            """,
            line_start=1,
            line_end=10,
        )

        has_format = self.detector.check_element_format(element)
        assert has_format is True
        assert element.has_intent is True
        assert element.has_goals is True
        assert element.has_logic is True

    def test_generate_enhancement_summary_empty_list(self):
        """Test generating summary for empty elements list."""
        summary = self.detector.generate_enhancement_summary([])
        assert "All technical elements already have Intent/Goals/Logic format" in summary

    def test_generate_enhancement_summary_single_element(self):
        """Test generating summary for single element."""
        element = TechnicalElement(element_type="interface", element_name="TestInterface", content="test content", has_intent=False, has_goals=False, has_logic=False, line_start=1, line_end=5)

        summary = self.detector.generate_enhancement_summary([element])
        assert "1 technical element need enhancement" in summary
        assert "1 Interface" in summary
        assert "Missing:" in summary

    def test_generate_enhancement_summary_multiple_elements(self):
        """Test generating summary for multiple elements."""
        elements = [
            TechnicalElement(element_type="interface", element_name="Interface1", content="test", has_intent=False, has_goals=True, has_logic=False, line_start=1, line_end=5),
            TechnicalElement(element_type="component", element_name="Component1", content="test", has_intent=True, has_goals=False, has_logic=False, line_start=6, line_end=10),
            TechnicalElement(element_type="interface", element_name="Interface2", content="test", has_intent=False, has_goals=False, has_logic=True, line_start=11, line_end=15),
        ]

        summary = self.detector.generate_enhancement_summary(elements)
        assert "3 technical elements need enhancement" in summary
        assert "2 Interfaces" in summary
        assert "1 Component" in summary

    def test_analyze_design_document_complete(self):
        """Test complete design document analysis."""
        content = """
        # Design Document

        ## Components

        ### TaskManager Component

        **Intent**: Manages task operations.

        **Goals**:
        - Handle task creation
        - Manage task lifecycle

        **Logic**: The component uses a repository pattern.

        ### DataProcessor

        This component processes data but lacks structured format.

        ## Interfaces

        ### UserService Interface

        This interface handles users.
        """

        result = self.detector.analyze_design_document(content)

        assert isinstance(result, FormatAnalysisResult)
        assert result.total_elements >= 2  # At least TaskManager and DataProcessor
        assert result.elements_with_format >= 1  # TaskManager has format
        assert len(result.elements_needing_enhancement) >= 1  # DataProcessor needs enhancement
        assert result.estimated_changes > 0
        assert len(result.enhancement_summary) > 0

    def test_analyze_design_document_empty(self):
        """Test analyzing empty design document."""
        result = self.detector.analyze_design_document("")

        assert result.total_elements == 0
        assert result.elements_with_format == 0
        assert len(result.elements_needing_enhancement) == 0
        assert result.estimated_changes == 0

    def test_analyze_design_document_error_handling(self):
        """Test error handling in document analysis."""
        # This should not raise an exception even with malformed content
        malformed_content = "### Malformed\n**Intent**: Missing closing"

        result = self.detector.analyze_design_document(malformed_content)
        assert isinstance(result, FormatAnalysisResult)

    def test_get_supported_element_types(self):
        """Test getting supported element types."""
        types = self.detector.get_supported_element_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert "interface" in types
        assert "component" in types
        assert "data_model" in types

    def test_update_template(self):
        """Test updating the detector template."""
        new_template = EnhancedDesignTemplate(element_patterns={"custom_type": r"custom\s+(\w+)"})

        self.detector.update_template(new_template)
        assert self.detector.template == new_template
        assert "custom_type" in self.detector.get_supported_element_types()

    def test_find_element_end_line(self):
        """Test finding element end line."""
        lines = ["### Component1", "Content line 1", "Content line 2", "### Component2", "Other content"]

        end_line = self.detector._find_element_end_line(lines, 1, "component")
        assert end_line == 3  # Should stop at Component2

    def test_extract_element_content(self):
        """Test extracting element content."""
        lines = ["### Component1", "Content line 1", "Content line 2", "### Component2"]

        content = self.detector._extract_element_content(lines, 1, 3)
        expected = "### Component1\nContent line 1\nContent line 2"
        assert content == expected

    def test_line_number_tracking(self):
        """Test that line numbers are tracked correctly."""
        content = """Line 1
Line 2
### TestComponent
Component content
Line 5"""

        elements = self.detector.detect_technical_elements(content)

        if elements:
            component = next((e for e in elements if e.element_type == "component"), None)
            if component:
                assert component.line_start == 3  # ### TestComponent is on line 3
                assert component.line_end > component.line_start
