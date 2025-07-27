"""
Unit tests for DesignElementFormatter.

Tests the design element formatting functionality.
"""

from src.spec_server.design_element_formatter import DesignElementFormatter, DesignElementFormattingError
from src.spec_server.models import DesignElementTemplate, EnhancedDesignTemplate, TechnicalElement


class TestDesignElementFormatter:
    """Test DesignElementFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DesignElementFormatter()

    def test_initialization(self):
        """Test DesignElementFormatter initialization."""
        assert self.formatter.template is not None
        assert len(self.formatter.get_supported_element_types()) > 0

    def test_initialization_with_custom_template(self):
        """Test initialization with custom template."""
        custom_template = EnhancedDesignTemplate(
            format_templates={
                "interface": DesignElementTemplate(
                    element_type="interface", intent_template="Custom intent for {element_name}", goals_template="- Custom goal 1\n- Custom goal 2", logic_template="Custom logic for {element_name}"
                )
            }
        )
        formatter = DesignElementFormatter(custom_template)

        assert formatter.template == custom_template
        assert "interface" in formatter.get_supported_element_types()

    def test_format_element_without_existing_format(self):
        """Test formatting element that has no existing Intent/Goals/Logic sections."""
        element = TechnicalElement(
            element_type="interface",
            element_name="UserService",
            content="""### UserService Interface

This interface handles user operations and provides user management functionality.""",
            line_start=1,
            line_end=5,
        )

        formatted = self.formatter.format_element(element)

        assert "**Intent**:" in formatted
        assert "**Goals**:" in formatted
        assert "**Logic**:" in formatted
        assert "UserService" in formatted
        assert "### UserService Interface" in formatted

    def test_format_element_with_existing_sections(self):
        """Test formatting element that already has some Intent/Goals/Logic sections."""
        element = TechnicalElement(
            element_type="component",
            element_name="TaskManager",
            content="""### TaskManager Component

**Intent**: Manages task operations in the system.

This component handles task lifecycle and provides task management capabilities.""",
            line_start=1,
            line_end=7,
        )

        formatted = self.formatter.format_element(element)

        assert "**Intent**: Manages task operations in the system." in formatted
        assert "**Goals**:" in formatted
        assert "**Logic**:" in formatted
        assert "task lifecycle" in formatted  # Should preserve existing content

    def test_format_element_with_all_sections_present(self):
        """Test formatting element that already has all sections."""
        element = TechnicalElement(
            element_type="data_model",
            element_name="User",
            content="""### User Model

**Intent**: Represents user data in the system.

**Goals**:
- Store user information
- Validate user data

**Logic**: The model uses validation rules to ensure data integrity.""",
            line_start=1,
            line_end=10,
            has_intent=True,
            has_goals=True,
            has_logic=True,
        )

        formatted = self.formatter.format_element(element)

        assert "**Intent**: Represents user data in the system." in formatted
        assert "- Store user information" in formatted
        assert "- Validate user data" in formatted
        assert "**Logic**: The model uses validation rules" in formatted

    def test_generate_intent_section(self):
        """Test generating Intent section content."""
        intent = self.formatter.generate_intent_section("interface", "PaymentService", "This interface handles payment processing")

        assert isinstance(intent, str)
        assert len(intent) > 0
        assert "PaymentService" in intent or "interface" in intent

    def test_generate_goals_section(self):
        """Test generating Goals section content."""
        goals = self.formatter.generate_goals_section("component", "DataProcessor", "This component processes data efficiently")

        assert isinstance(goals, list)
        assert len(goals) > 0
        assert all(isinstance(goal, str) for goal in goals)

    def test_generate_logic_section(self):
        """Test generating Logic section content."""
        logic = self.formatter.generate_logic_section("service", "EmailService", "This service sends emails using SMTP")

        assert isinstance(logic, str)
        assert len(logic) > 0
        assert "EmailService" in logic or "service" in logic

    def test_format_element_service_type(self):
        """Test formatting element with service type."""
        element = TechnicalElement(element_type="service", element_name="EmailService", content="### EmailService\n\nSome content here.", line_start=1, line_end=3)

        formatted = self.formatter.format_element(element)

        assert "**Intent**:" in formatted
        assert "**Goals**:" in formatted
        assert "**Logic**:" in formatted
        assert "EmailService" in formatted

    def test_extract_existing_sections_with_intent(self):
        """Test extracting existing Intent section."""
        content = """### Component

**Intent**: This is the existing intent.

**Goals**:
- Some goal

Some other content here."""

        sections = self.formatter._extract_existing_sections(content)

        assert sections["intent"] == "This is the existing intent."
        assert sections["goals"] != ""
        assert sections["logic"] == ""

    def test_extract_existing_sections_with_goals(self):
        """Test extracting existing Goals section."""
        content = """### Component

**Goals**:
- Goal 1
- Goal 2

Some other content."""

        sections = self.formatter._extract_existing_sections(content)

        assert sections["intent"] == ""
        assert "Goal 1" in sections["goals"]
        assert "Goal 2" in sections["goals"]
        assert sections["logic"] == ""

    def test_extract_existing_sections_with_logic(self):
        """Test extracting existing Logic section."""
        content = """### Component

**Logic**: This is how the component works internally.

**Other**: Some other section."""

        sections = self.formatter._extract_existing_sections(content)

        assert sections["intent"] == ""
        assert sections["goals"] == ""
        assert sections["logic"] == "This is how the component works internally."

    def test_extract_existing_sections_all_present(self):
        """Test extracting all existing sections."""
        content = """### Component

**Intent**: Component purpose.

**Goals**:
- Achieve goal 1
- Achieve goal 2

**Logic**: Component implementation details.

**Additional**: Additional content here."""

        sections = self.formatter._extract_existing_sections(content)

        assert sections["intent"] == "Component purpose."
        assert "Achieve goal 1" in sections["goals"]
        assert "Achieve goal 2" in sections["goals"]
        assert sections["logic"] == "Component implementation details."

    def test_parse_goals_template_bullet_points(self):
        """Test parsing goals template with bullet points."""
        goals_content = "- Goal 1\n- Goal 2\n- Goal 3"

        goals = self.formatter._parse_goals_template(goals_content)

        assert goals == ["Goal 1", "Goal 2", "Goal 3"]

    def test_parse_goals_template_mixed_format(self):
        """Test parsing goals template with mixed format."""
        goals_content = "- Goal 1\n* Goal 2\nGoal 3 without bullet"

        goals = self.formatter._parse_goals_template(goals_content)

        assert "Goal 1" in goals
        assert "Goal 2" in goals
        assert "Goal 3 without bullet" in goals

    def test_parse_goals_template_empty(self):
        """Test parsing empty goals template."""
        goals = self.formatter._parse_goals_template("")
        assert goals == []

    def test_enhance_intent_with_context(self):
        """Test enhancing intent with context from existing content."""
        intent = "Simple summary of what this interface provides functionality"
        existing_content = "This interface handles user authentication and manages user sessions."

        enhanced = self.formatter._enhance_intent_with_context(intent, existing_content, "interface")

        # Should enhance with specific purpose found in content
        assert "authentication" in enhanced or "user" in enhanced or enhanced != intent

    def test_enhance_goals_with_context(self):
        """Test enhancing goals with context from existing content."""
        goals = ["Define clear contract", "Ensure type safety"]
        existing_content = "This component is responsible for data validation and ensures data integrity."

        enhanced = self.formatter._enhance_goals_with_context(goals, existing_content, "component")

        # Should include original goals plus context-derived goals
        assert len(enhanced) >= len(goals)
        assert any("validation" in goal or "integrity" in goal for goal in enhanced)

    def test_enhance_logic_with_context(self):
        """Test enhancing logic with context from existing content."""
        logic = "Detailed explanation of how this component works"
        existing_content = "The component uses a repository pattern and implements caching for performance."

        enhanced = self.formatter._enhance_logic_with_context(logic, existing_content, "component")

        # Should include implementation details from context
        assert "repository pattern" in enhanced or "caching" in enhanced

    def test_extract_remaining_content(self):
        """Test extracting content that wasn't part of structured sections."""
        original_content = """### Component

**Intent**: Component purpose.

**Goals**:
- Goal 1

**Logic**: Implementation details.

**Additional**: This is additional content that should be preserved.
It includes multiple lines and should remain intact."""

        existing_sections = {"intent": "Component purpose.", "goals": "- Goal 1", "logic": "Implementation details."}

        remaining = self.formatter._extract_remaining_content(original_content, existing_sections)

        # The remaining content should include the Additional section
        assert "**Additional**:" in remaining or "additional content" in remaining
        assert "**Intent**:" not in remaining
        assert "**Goals**:" not in remaining
        assert "**Logic**:" not in remaining

    def test_format_element_preserves_header_format(self):
        """Test that formatting preserves the original header format."""
        element = TechnicalElement(element_type="interface", element_name="TestInterface", content="#### TestInterface API\n\nInterface description here.", line_start=1, line_end=3)

        formatted = self.formatter.format_element(element)

        assert "#### TestInterface API" in formatted

    def test_format_element_creates_header_if_missing(self):
        """Test that formatting creates a header if none exists."""
        element = TechnicalElement(element_type="component", element_name="TestComponent", content="Just some content without a header.", line_start=1, line_end=1)

        formatted = self.formatter.format_element(element)

        assert "### TestComponent" in formatted

    def test_format_element_error_handling(self):
        """Test error handling in element formatting."""
        # Create an element that might cause issues
        element = TechnicalElement(element_type="interface", element_name="", content="", line_start=1, line_end=1)  # Empty name might cause issues

        # Should handle gracefully and not raise exception
        try:
            formatted = self.formatter.format_element(element)
            assert isinstance(formatted, str)
        except DesignElementFormattingError:
            # This is acceptable - the error should be properly formatted
            pass

    def test_update_template(self):
        """Test updating the formatter template."""
        new_template = EnhancedDesignTemplate(
            format_templates={"service": DesignElementTemplate(element_type="service", intent_template="New intent template", goals_template="- New goal", logic_template="New logic template")}
        )

        self.formatter.update_template(new_template)
        assert self.formatter.template == new_template
        assert "service" in self.formatter.get_supported_element_types()

    def test_get_supported_element_types(self):
        """Test getting supported element types."""
        types = self.formatter.get_supported_element_types()

        assert isinstance(types, list)
        assert len(types) > 0
        # Should include default types from DEFAULT_ENHANCED_DESIGN_TEMPLATE
        assert "interface" in types
        assert "component" in types
        assert "data_model" in types

    def test_format_element_with_custom_section_names(self):
        """Test formatting with custom section names."""
        custom_template = EnhancedDesignTemplate(
            format_templates={
                "interface": DesignElementTemplate(
                    element_type="interface",
                    intent_template="Custom intent",
                    goals_template="- Custom goal",
                    logic_template="Custom logic",
                    section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Implementation"},
                )
            }
        )

        formatter = DesignElementFormatter(custom_template)

        element = TechnicalElement(element_type="interface", element_name="TestInterface", content="### TestInterface\n\nInterface content.", line_start=1, line_end=3)

        formatted = formatter.format_element(element)

        assert "**Purpose**:" in formatted
        assert "**Objectives**:" in formatted
        assert "**Implementation**:" in formatted
        assert "**Intent**:" not in formatted
        assert "**Goals**:" not in formatted
        assert "**Logic**:" not in formatted
