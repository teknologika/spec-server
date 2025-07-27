"""
Unit tests for enhanced design format data models.

Tests the new models added for the Intent/Goals/Logic format feature.
"""

import pytest
from pydantic import ValidationError

from src.spec_server.models import DEFAULT_ENHANCED_DESIGN_TEMPLATE, DesignElementTemplate, EnhancedDesignTemplate, FormatAnalysisResult, TechnicalElement, TemplateConfig


class TestDesignElementTemplate:
    """Test DesignElementTemplate model."""

    def test_valid_design_element_template(self):
        """Test creating a valid DesignElementTemplate."""
        template = DesignElementTemplate(
            element_type="interface", intent_template="Simple summary of {element_name}", goals_template="- Goal 1\n- Goal 2", logic_template="Detailed explanation of {element_name}"
        )

        assert template.element_type == "interface"
        assert template.intent_template == "Simple summary of {element_name}"
        assert template.goals_template == "- Goal 1\n- Goal 2"
        assert template.logic_template == "Detailed explanation of {element_name}"
        assert template.section_names == {"intent": "Intent", "goals": "Goals", "logic": "Logic"}
        assert template.validation_rules == []

    def test_invalid_element_type(self):
        """Test that invalid element types raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DesignElementTemplate(element_type="invalid_type", intent_template="Test", goals_template="Test", logic_template="Test")

        assert "Element type must be one of" in str(exc_info.value)

    def test_custom_section_names(self):
        """Test custom section names."""
        template = DesignElementTemplate(
            element_type="component", intent_template="Test", goals_template="Test", logic_template="Test", section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Implementation"}
        )

        assert template.section_names["intent"] == "Purpose"
        assert template.section_names["goals"] == "Objectives"
        assert template.section_names["logic"] == "Implementation"

    def test_validation_rules(self):
        """Test validation rules field."""
        template = DesignElementTemplate(element_type="data_model", intent_template="Test", goals_template="Test", logic_template="Test", validation_rules=["rule1", "rule2"])

        assert template.validation_rules == ["rule1", "rule2"]


class TestTemplateConfig:
    """Test TemplateConfig model."""

    def test_default_template_config(self):
        """Test default TemplateConfig values."""
        config = TemplateConfig()

        assert config.section_names == {"intent": "Intent", "goals": "Goals", "logic": "Logic"}
        assert "interface" in config.element_types
        assert "component" in config.element_types
        assert "data_model" in config.element_types
        assert config.format_rules == {}
        assert config.custom_templates == {}

    def test_custom_template_config(self):
        """Test custom TemplateConfig values."""
        custom_template = DesignElementTemplate(element_type="interface", intent_template="Custom intent", goals_template="Custom goals", logic_template="Custom logic")

        config = TemplateConfig(
            section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Details"},
            element_types=["interface", "component"],
            format_rules={"custom_rule": True},
            custom_templates={"interface": custom_template},
        )

        assert config.section_names["intent"] == "Purpose"
        assert config.element_types == ["interface", "component"]
        assert config.format_rules["custom_rule"] is True
        assert config.custom_templates["interface"] == custom_template

    def test_invalid_element_types(self):
        """Test that invalid element types raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(element_types=["invalid_type"])

        assert "must be one of" in str(exc_info.value)


class TestTechnicalElement:
    """Test TechnicalElement model."""

    def test_valid_technical_element(self):
        """Test creating a valid TechnicalElement."""
        element = TechnicalElement(
            element_type="interface", element_name="UserService", content="interface UserService { ... }", has_intent=True, has_goals=False, has_logic=True, line_start=10, line_end=20
        )

        assert element.element_type == "interface"
        assert element.element_name == "UserService"
        assert element.content == "interface UserService { ... }"
        assert element.has_intent is True
        assert element.has_goals is False
        assert element.has_logic is True
        assert element.line_start == 10
        assert element.line_end == 20

    def test_invalid_element_type(self):
        """Test that invalid element types raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalElement(element_type="invalid_type", element_name="Test", content="Test", line_start=1, line_end=2)

        assert "Element type must be one of" in str(exc_info.value)

    def test_invalid_line_range(self):
        """Test that line_end < line_start raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalElement(element_type="component", element_name="Test", content="Test", line_start=10, line_end=5)

        assert "line_end must be greater than or equal to line_start" in str(exc_info.value)

    def test_default_format_flags(self):
        """Test default values for format flags."""
        element = TechnicalElement(element_type="data_model", element_name="User", content="class User { ... }", line_start=1, line_end=5)

        assert element.has_intent is False
        assert element.has_goals is False
        assert element.has_logic is False


class TestFormatAnalysisResult:
    """Test FormatAnalysisResult model."""

    def test_valid_format_analysis_result(self):
        """Test creating a valid FormatAnalysisResult."""
        element = TechnicalElement(element_type="interface", element_name="TestInterface", content="interface TestInterface { ... }", line_start=1, line_end=5)

        result = FormatAnalysisResult(total_elements=5, elements_with_format=2, elements_needing_enhancement=[element], enhancement_summary="3 elements need enhancement", estimated_changes=9)

        assert result.total_elements == 5
        assert result.elements_with_format == 2
        assert len(result.elements_needing_enhancement) == 1
        assert result.enhancement_summary == "3 elements need enhancement"
        assert result.estimated_changes == 9

    def test_invalid_elements_with_format(self):
        """Test that elements_with_format > total_elements raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            FormatAnalysisResult(total_elements=3, elements_with_format=5, enhancement_summary="Test", estimated_changes=0)

        assert "elements_with_format cannot exceed total_elements" in str(exc_info.value)

    def test_negative_values(self):
        """Test that negative values raise validation error."""
        with pytest.raises(ValidationError):
            FormatAnalysisResult(total_elements=-1, elements_with_format=0, enhancement_summary="Test", estimated_changes=0)

    def test_empty_elements_needing_enhancement(self):
        """Test default empty list for elements_needing_enhancement."""
        result = FormatAnalysisResult(total_elements=0, elements_with_format=0, enhancement_summary="No elements found", estimated_changes=0)

        assert result.elements_needing_enhancement == []


class TestEnhancedDesignTemplate:
    """Test EnhancedDesignTemplate model."""

    def test_default_enhanced_design_template(self):
        """Test default EnhancedDesignTemplate values."""
        template = EnhancedDesignTemplate()

        assert template.template_type == "design"
        assert "Overview" in template.sections
        assert "Architecture" in template.sections
        assert "Components and Interfaces" in template.sections
        assert template.enhanced_format_enabled is True
        assert isinstance(template.template_config, TemplateConfig)

    def test_custom_enhanced_design_template(self):
        """Test custom EnhancedDesignTemplate values."""
        custom_config = TemplateConfig(section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Details"})

        template = EnhancedDesignTemplate(template_type="design", sections=["Custom Section"], enhanced_format_enabled=False, template_config=custom_config)

        assert template.sections == ["Custom Section"]
        assert template.enhanced_format_enabled is False
        assert template.template_config.section_names["intent"] == "Purpose"

    def test_element_patterns(self):
        """Test element patterns configuration."""
        template = EnhancedDesignTemplate(element_patterns={"interface": r"interface\s+(\w+)", "component": r"component\s+(\w+)"})

        assert "interface" in template.element_patterns
        assert "component" in template.element_patterns

    def test_format_templates(self):
        """Test format templates configuration."""
        interface_template = DesignElementTemplate(element_type="interface", intent_template="Test intent", goals_template="Test goals", logic_template="Test logic")

        template = EnhancedDesignTemplate(format_templates={"interface": interface_template})

        assert "interface" in template.format_templates
        assert template.format_templates["interface"].intent_template == "Test intent"


class TestDefaultEnhancedDesignTemplate:
    """Test the default enhanced design template instance."""

    def test_default_template_structure(self):
        """Test that the default template has expected structure."""
        template = DEFAULT_ENHANCED_DESIGN_TEMPLATE

        assert template.template_type == "design"
        assert template.enhanced_format_enabled is True
        assert len(template.sections) == 6
        assert "Overview" in template.sections
        assert "Architecture" in template.sections

    def test_default_element_patterns(self):
        """Test that default element patterns are configured."""
        template = DEFAULT_ENHANCED_DESIGN_TEMPLATE

        assert "interface" in template.element_patterns
        assert "component" in template.element_patterns
        assert "data_model" in template.element_patterns
        assert "service" in template.element_patterns
        assert "class" in template.element_patterns
        assert "architecture" in template.element_patterns

    def test_default_format_templates(self):
        """Test that default format templates are configured."""
        template = DEFAULT_ENHANCED_DESIGN_TEMPLATE

        assert "interface" in template.format_templates
        assert "component" in template.format_templates
        assert "data_model" in template.format_templates

        interface_template = template.format_templates["interface"]
        assert interface_template.element_type == "interface"
        assert "interface provides" in interface_template.intent_template
        assert "Define clear contract" in interface_template.goals_template
        assert "how this interface works" in interface_template.logic_template

    def test_default_format_rules(self):
        """Test that default format rules are configured."""
        template = DEFAULT_ENHANCED_DESIGN_TEMPLATE

        assert template.format_rules["include_diagrams"] is True
        assert template.format_rules["reference_requirements"] is True
        assert template.format_rules["enhanced_format"] is True
