"""
Unit tests for DesignTemplateManager.

Tests the design template management functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.spec_server.design_template_manager import DesignTemplateManager, DesignTemplateManagerError
from src.spec_server.models import DesignElementTemplate, EnhancedDesignTemplate, TemplateConfig


class TestDesignTemplateManager:
    """Test DesignTemplateManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DesignTemplateManager()

    def test_initialization(self):
        """Test DesignTemplateManager initialization."""
        assert self.manager.template_config is not None
        assert self.manager.enhanced_template is not None
        assert len(self.manager.get_supported_element_types()) > 0

    def test_initialization_with_config_path(self):
        """Test initialization with configuration file."""
        # Create temporary config file
        config_data = {
            "section_names": {"intent": "Purpose", "goals": "Objectives", "logic": "Implementation"},
            "element_types": ["interface", "component"],
            "format_rules": {"custom_rule": True},
            "custom_templates": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            manager = DesignTemplateManager(config_path)

            assert manager.template_config.section_names["intent"] == "Purpose"
            assert manager.template_config.section_names["goals"] == "Objectives"
            assert manager.template_config.section_names["logic"] == "Implementation"
            assert manager.template_config.element_types == ["interface", "component"]

        finally:
            config_path.unlink()

    def test_get_element_template_existing_type(self):
        """Test getting template for existing element type."""
        template = self.manager.get_element_template("interface")

        assert isinstance(template, DesignElementTemplate)
        assert template.element_type == "interface"
        assert template.intent_template
        assert template.goals_template
        assert template.logic_template

    def test_get_element_template_custom_type(self):
        """Test getting template after adding custom template."""
        custom_template = DesignElementTemplate(
            element_type="service", intent_template="Custom service intent", goals_template="- Custom goal 1\n- Custom goal 2", logic_template="Custom service logic"
        )

        self.manager.add_custom_template("service", custom_template)
        retrieved_template = self.manager.get_element_template("service")

        assert retrieved_template.intent_template == "Custom service intent"
        assert "Custom goal 1" in retrieved_template.goals_template

    def test_get_element_template_unknown_type(self):
        """Test getting template for unknown type creates default."""
        # This should work with the fallback mechanism
        template = self.manager.get_element_template("service")

        assert isinstance(template, DesignElementTemplate)
        assert template.intent_template
        assert template.goals_template
        assert template.logic_template

    def test_update_template_config(self):
        """Test updating template configuration."""
        new_config = TemplateConfig(
            section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Details"}, element_types=["interface", "component", "service"], format_rules={"new_rule": True}
        )

        self.manager.update_template_config(new_config)

        assert self.manager.template_config.section_names["intent"] == "Purpose"
        assert self.manager.template_config.section_names["goals"] == "Objectives"
        assert self.manager.template_config.section_names["logic"] == "Details"
        assert "service" in self.manager.template_config.element_types

    def test_update_template_config_invalid(self):
        """Test updating with invalid configuration raises error."""
        # Create invalid config (missing required section)
        invalid_config = TemplateConfig(section_names={"intent": "Purpose"}, element_types=["interface"])  # Missing goals and logic

        with pytest.raises(DesignTemplateManagerError):
            self.manager.update_template_config(invalid_config)

    def test_validate_template_format_valid(self):
        """Test validating valid template format."""
        template = DesignElementTemplate(
            element_type="interface", intent_template="Test intent with {element_name}", goals_template="- Goal 1\n- Goal 2", logic_template="Test logic for {element_name}"
        )

        is_valid = self.manager.validate_template_format(template)
        assert is_valid is True

    def test_validate_template_format_invalid(self):
        """Test validating invalid template format."""
        template = DesignElementTemplate(element_type="interface", intent_template="", goals_template="- Goal 1", logic_template="Test logic")  # Empty intent template

        is_valid = self.manager.validate_template_format(template)
        assert is_valid is False

    def test_validate_template_config_valid(self):
        """Test validating valid template configuration."""
        config = TemplateConfig(section_names={"intent": "Intent", "goals": "Goals", "logic": "Logic"}, element_types=["interface", "component"], format_rules={}, custom_templates={})

        is_valid = self.manager.validate_template_config(config)
        assert is_valid is True

    def test_validate_template_config_invalid(self):
        """Test validating invalid template configuration."""
        config = TemplateConfig(section_names={"intent": "Intent"}, element_types=["interface"], format_rules={}, custom_templates={})  # Missing goals and logic

        is_valid = self.manager.validate_template_config(config)
        assert is_valid is False

    def test_load_configuration_valid_file(self):
        """Test loading configuration from valid file."""
        config_data = {
            "section_names": {"intent": "Purpose", "goals": "Objectives", "logic": "Implementation"},
            "element_types": ["interface", "component", "service"],
            "format_rules": {"test_rule": True},
            "custom_templates": {
                "interface": {
                    "intent_template": "Custom interface intent",
                    "goals_template": "- Custom goal",
                    "logic_template": "Custom logic",
                    "section_names": {"intent": "Purpose", "goals": "Objectives", "logic": "Implementation"},
                    "validation_rules": [],
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            self.manager.load_configuration(config_path)

            assert self.manager.template_config.section_names["intent"] == "Purpose"
            assert "service" in self.manager.template_config.element_types
            assert "interface" in self.manager.template_config.custom_templates

            interface_template = self.manager.get_element_template("interface")
            assert interface_template.intent_template == "Custom interface intent"

        finally:
            config_path.unlink()

    def test_load_configuration_nonexistent_file(self):
        """Test loading configuration from nonexistent file raises error."""
        nonexistent_path = Path("/nonexistent/config.json")

        with pytest.raises(DesignTemplateManagerError) as exc_info:
            self.manager.load_configuration(nonexistent_path)

        assert "not found" in str(exc_info.value)

    def test_load_configuration_invalid_json(self):
        """Test loading configuration from invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            config_path = Path(f.name)

        try:
            with pytest.raises(DesignTemplateManagerError) as exc_info:
                self.manager.load_configuration(config_path)

            assert "Invalid JSON" in str(exc_info.value)

        finally:
            config_path.unlink()

    def test_save_configuration(self):
        """Test saving configuration to file."""
        # Modify configuration
        custom_template = DesignElementTemplate(element_type="service", intent_template="Test intent", goals_template="- Test goal", logic_template="Test logic")
        self.manager.add_custom_template("service", custom_template)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            self.manager.save_configuration(config_path)

            # Verify file was created and contains expected data
            assert config_path.exists()

            with open(config_path, "r") as f:
                saved_data = json.load(f)

            assert "section_names" in saved_data
            assert "element_types" in saved_data
            assert "custom_templates" in saved_data
            assert "service" in saved_data["custom_templates"]

        finally:
            config_path.unlink()

    def test_get_supported_element_types(self):
        """Test getting supported element types."""
        types = self.manager.get_supported_element_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert "interface" in types
        assert "component" in types
        assert "data_model" in types

    def test_add_custom_template(self):
        """Test adding custom template."""
        template = DesignElementTemplate(element_type="service", intent_template="Custom service intent", goals_template="- Custom goal 1\n- Custom goal 2", logic_template="Custom service logic")

        self.manager.add_custom_template("service", template)

        # Verify template was added
        retrieved = self.manager.get_element_template("service")
        assert retrieved.intent_template == "Custom service intent"

        # Verify element type was added to supported types
        assert "service" in self.manager.get_supported_element_types()

    def test_add_custom_template_invalid(self):
        """Test adding invalid custom template raises error."""
        invalid_template = DesignElementTemplate(element_type="service", intent_template="", goals_template="- Goal", logic_template="Logic")  # Empty intent

        with pytest.raises(DesignTemplateManagerError):
            self.manager.add_custom_template("service", invalid_template)

    def test_remove_custom_template(self):
        """Test removing custom template."""
        # First add a custom template
        template = DesignElementTemplate(element_type="service", intent_template="Custom intent", goals_template="- Custom goal", logic_template="Custom logic")
        self.manager.add_custom_template("service", template)

        # Verify it exists
        retrieved = self.manager.get_element_template("service")
        assert retrieved.intent_template == "Custom intent"

        # Remove it
        self.manager.remove_custom_template("service")

        # Verify it's gone (should fall back to default)
        retrieved_after = self.manager.get_element_template("service")
        assert retrieved_after.intent_template != "Custom intent"

    def test_remove_custom_template_nonexistent(self):
        """Test removing nonexistent custom template doesn't raise error."""
        # Should not raise an error
        self.manager.remove_custom_template("nonexistent_type")

    def test_get_template_config(self):
        """Test getting template configuration."""
        config = self.manager.get_template_config()

        assert isinstance(config, TemplateConfig)
        assert config.section_names
        assert config.element_types
        assert isinstance(config.custom_templates, dict)

    def test_get_enhanced_template(self):
        """Test getting enhanced template."""
        template = self.manager.get_enhanced_template()

        assert isinstance(template, EnhancedDesignTemplate)
        assert template.template_type == "design"
        assert template.enhanced_format_enabled is True
        assert template.format_templates

    def test_template_updates_propagate(self):
        """Test that template updates propagate to enhanced template."""
        # Add custom template
        custom_template = DesignElementTemplate(element_type="service", intent_template="Updated intent", goals_template="- Updated goal", logic_template="Updated logic")
        self.manager.add_custom_template("service", custom_template)

        # Check that enhanced template was updated
        enhanced = self.manager.get_enhanced_template()
        assert "service" in enhanced.format_templates
        assert enhanced.format_templates["service"].intent_template == "Updated intent"

    def test_section_names_update_propagates(self):
        """Test that section name updates propagate to all templates."""
        # Update section names
        new_config = TemplateConfig(section_names={"intent": "Purpose", "goals": "Objectives", "logic": "Details"}, element_types=["interface", "component", "service"], format_rules={})
        self.manager.update_template_config(new_config)

        # Check that existing templates use new section names
        interface_template = self.manager.get_element_template("interface")
        assert interface_template.section_names["intent"] == "Purpose"
        assert interface_template.section_names["goals"] == "Objectives"
        assert interface_template.section_names["logic"] == "Details"

    def test_create_default_template(self):
        """Test creating default template for unknown types."""
        # This tests the internal method through get_element_template
        template = self.manager.get_element_template("service")

        assert isinstance(template, DesignElementTemplate)
        assert template.intent_template
        assert template.goals_template
        assert template.logic_template
        assert template.section_names == self.manager.template_config.section_names

    def test_parse_config_data(self):
        """Test parsing configuration data."""
        config_data = {
            "section_names": {"intent": "Purpose", "goals": "Objectives", "logic": "Details"},
            "element_types": ["interface", "component"],
            "format_rules": {"rule1": True},
            "custom_templates": {
                "interface": {
                    "intent_template": "Test intent",
                    "goals_template": "- Test goal",
                    "logic_template": "Test logic",
                    "section_names": {"intent": "Purpose", "goals": "Objectives", "logic": "Details"},
                    "validation_rules": ["rule1"],
                }
            },
        }

        config = self.manager._parse_config_data(config_data)

        assert config.section_names["intent"] == "Purpose"
        assert config.element_types == ["interface", "component"]
        assert config.format_rules["rule1"] is True
        assert "interface" in config.custom_templates

    def test_serialize_config(self):
        """Test serializing configuration."""
        # Add custom template
        template = DesignElementTemplate(element_type="service", intent_template="Test intent", goals_template="- Test goal", logic_template="Test logic")
        self.manager.add_custom_template("service", template)

        serialized = self.manager._serialize_config()

        assert "section_names" in serialized
        assert "element_types" in serialized
        assert "format_rules" in serialized
        assert "custom_templates" in serialized
        assert "service" in serialized["custom_templates"]
        assert serialized["custom_templates"]["service"]["intent_template"] == "Test intent"
