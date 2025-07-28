"""
DesignTemplateManager implementation for managing design templates.

This module provides the DesignTemplateManager class which manages configurable
templates for the Intent/Goals/Logic format, including loading, validation, and
customization of templates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import DEFAULT_ENHANCED_DESIGN_TEMPLATE, DesignElementTemplate, EnhancedDesignTemplate, TemplateConfig


class DesignTemplateManagerError(Exception):
    """Exception raised when design template management fails."""

    def __init__(self, message: str, error_code: str = "TEMPLATE_MANAGER_ERROR", details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DesignTemplateManager:
    """
    Manages configurable templates for the Intent/Goals/Logic format.

    Handles template loading, validation, customization, and provides access
    to element-specific templates with fallback to defaults.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the template manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.template_config = TemplateConfig()
        self.enhanced_template = DEFAULT_ENHANCED_DESIGN_TEMPLATE

        # Load configuration if path provided
        if config_path and config_path.exists():
            self.load_configuration(config_path)

    def get_element_template(self, element_type: str) -> DesignElementTemplate:
        """
        Get the template for a specific element type.

        Args:
            element_type: Type of element (interface, component, etc.)

        Returns:
            DesignElementTemplate for the specified type

        Raises:
            DesignTemplateManagerError: If template retrieval fails
        """
        try:
            # Check custom templates first
            if element_type in self.template_config.custom_templates:
                return self.template_config.custom_templates[element_type]

            # Check enhanced template format templates
            if element_type in self.enhanced_template.format_templates:
                return self.enhanced_template.format_templates[element_type]

            # Return default template for unknown types
            return self._create_default_template(element_type)

        except Exception as e:
            raise DesignTemplateManagerError(
                f"Failed to get template for element type '{element_type}': {str(e)}", error_code="TEMPLATE_RETRIEVAL_FAILED", details={"element_type": element_type, "error": str(e)}
            )

    def update_template_config(self, config: TemplateConfig) -> None:
        """
        Update the template configuration.

        Args:
            config: New template configuration

        Raises:
            DesignTemplateManagerError: If configuration update fails
        """
        try:
            # Validate the configuration
            if not self.validate_template_config(config):
                raise DesignTemplateManagerError("Invalid template configuration", error_code="INVALID_CONFIGURATION")

            self.template_config = config

            # Update enhanced template with new configuration
            self._update_enhanced_template()

        except Exception as e:
            raise DesignTemplateManagerError(f"Failed to update template configuration: {str(e)}", error_code="CONFIG_UPDATE_FAILED", details={"error": str(e)})

    def validate_template_format(self, template: DesignElementTemplate) -> bool:
        """
        Validate that a template follows the expected format.

        Args:
            template: Template to validate

        Returns:
            True if template is valid

        Raises:
            DesignTemplateManagerError: If validation fails
        """
        try:
            # Check required fields
            if not template.element_type:
                return False

            if not template.intent_template:
                return False

            if not template.goals_template:
                return False

            if not template.logic_template:
                return False

            # Check element type is supported
            if template.element_type not in self.template_config.element_types:
                return False

            # Check section names are valid
            required_sections = ["intent", "goals", "logic"]
            for section in required_sections:
                if section not in template.section_names:
                    return False

            # Validate template content (basic checks)
            if "{element_name}" not in template.intent_template and "{element_type}" not in template.intent_template:
                # Template should reference element name or type
                pass  # This is optional, not required

            return True

        except Exception as e:
            raise DesignTemplateManagerError(f"Template validation failed: {str(e)}", error_code="TEMPLATE_VALIDATION_FAILED", details={"template_type": template.element_type, "error": str(e)})

    def validate_template_config(self, config: TemplateConfig) -> bool:
        """
        Validate a template configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid
        """
        try:
            # Check section names
            required_sections = ["intent", "goals", "logic"]
            for section in required_sections:
                if section not in config.section_names:
                    return False

            # Check element types
            if not config.element_types:
                return False

            # Validate custom templates
            for element_type, template in config.custom_templates.items():
                if element_type not in config.element_types:
                    return False

                if not self.validate_template_format(template):
                    return False

            return True

        except Exception:
            return False

    def load_configuration(self, config_path: Path) -> None:
        """
        Load template configuration from file.

        Args:
            config_path: Path to configuration file

        Raises:
            DesignTemplateManagerError: If loading fails
        """
        try:
            if not config_path.exists():
                raise DesignTemplateManagerError(f"Configuration file not found: {config_path}", error_code="CONFIG_FILE_NOT_FOUND", details={"config_path": str(config_path)})

            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Parse configuration
            config = self._parse_config_data(config_data)

            # Validate and update
            self.update_template_config(config)

        except json.JSONDecodeError as e:
            raise DesignTemplateManagerError(f"Invalid JSON in configuration file: {str(e)}", error_code="INVALID_JSON", details={"config_path": str(config_path), "error": str(e)})
        except Exception as e:
            raise DesignTemplateManagerError(f"Failed to load configuration: {str(e)}", error_code="CONFIG_LOAD_FAILED", details={"config_path": str(config_path), "error": str(e)})

    def save_configuration(self, config_path: Path) -> None:
        """
        Save current template configuration to file.

        Args:
            config_path: Path where to save configuration

        Raises:
            DesignTemplateManagerError: If saving fails
        """
        try:
            # Convert configuration to serializable format
            config_data = self._serialize_config()

            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write configuration
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise DesignTemplateManagerError(f"Failed to save configuration: {str(e)}", error_code="CONFIG_SAVE_FAILED", details={"config_path": str(config_path), "error": str(e)})

    def get_supported_element_types(self) -> List[str]:
        """
        Get list of supported element types.

        Returns:
            List of supported element type names
        """
        return self.template_config.element_types.copy()

    def add_custom_template(self, element_type: str, template: DesignElementTemplate) -> None:
        """
        Add a custom template for an element type.

        Args:
            element_type: Element type name
            template: Template to add

        Raises:
            DesignTemplateManagerError: If adding template fails
        """
        try:
            # Validate template
            if not self.validate_template_format(template):
                raise DesignTemplateManagerError(f"Invalid template format for element type '{element_type}'", error_code="INVALID_TEMPLATE_FORMAT", details={"element_type": element_type})

            # Add to custom templates
            self.template_config.custom_templates[element_type] = template

            # Ensure element type is in supported types
            if element_type not in self.template_config.element_types:
                self.template_config.element_types.append(element_type)

            # Update enhanced template
            self._update_enhanced_template()

        except Exception as e:
            raise DesignTemplateManagerError(f"Failed to add custom template: {str(e)}", error_code="ADD_TEMPLATE_FAILED", details={"element_type": element_type, "error": str(e)})

    def remove_custom_template(self, element_type: str) -> None:
        """
        Remove a custom template for an element type.

        Args:
            element_type: Element type name

        Raises:
            DesignTemplateManagerError: If removal fails
        """
        try:
            if element_type in self.template_config.custom_templates:
                del self.template_config.custom_templates[element_type]
                self._update_enhanced_template()

        except Exception as e:
            raise DesignTemplateManagerError(f"Failed to remove custom template: {str(e)}", error_code="REMOVE_TEMPLATE_FAILED", details={"element_type": element_type, "error": str(e)})

    def get_template_config(self) -> TemplateConfig:
        """
        Get the current template configuration.

        Returns:
            Current TemplateConfig
        """
        return self.template_config

    def get_enhanced_template(self) -> EnhancedDesignTemplate:
        """
        Get the current enhanced design template.

        Returns:
            Current EnhancedDesignTemplate
        """
        return self.enhanced_template

    def _create_default_template(self, element_type: str) -> DesignElementTemplate:
        """Create a default template for unknown element types."""
        element_display = element_type.replace("_", " ").title()

        return DesignElementTemplate(
            element_type=element_type if element_type in ["interface", "component", "data_model", "service", "class", "architecture"] else "component",
            intent_template=f"Core functionality provided by this {element_display.lower()}",
            goals_template=f"- Implement {element_display.lower()} functionality\n- Maintain system integrity\n- Provide reliable operation",
            logic_template=f"This {element_display.lower()} works by implementing the required functionality and integrating with other system components.",
            section_names=self.template_config.section_names.copy(),
        )

    def _update_enhanced_template(self) -> None:
        """Update the enhanced template with current configuration."""
        # Create new format templates combining defaults and custom
        format_templates = {}

        # Start with default templates
        for element_type, template in DEFAULT_ENHANCED_DESIGN_TEMPLATE.format_templates.items():
            # Update section names from configuration
            updated_template = DesignElementTemplate(
                element_type=template.element_type,
                intent_template=template.intent_template,
                goals_template=template.goals_template,
                logic_template=template.logic_template,
                section_names=self.template_config.section_names.copy(),
                validation_rules=template.validation_rules.copy(),
            )
            format_templates[element_type] = updated_template

        # Override with custom templates
        for element_type, template in self.template_config.custom_templates.items():
            format_templates[element_type] = template

        # Update enhanced template
        self.enhanced_template = EnhancedDesignTemplate(
            template_type="design",
            sections=DEFAULT_ENHANCED_DESIGN_TEMPLATE.sections.copy(),
            format_rules=DEFAULT_ENHANCED_DESIGN_TEMPLATE.format_rules.copy(),
            element_patterns=DEFAULT_ENHANCED_DESIGN_TEMPLATE.element_patterns.copy(),
            format_templates=format_templates,
            enhanced_format_enabled=True,
            template_config=self.template_config,
        )

    def _parse_config_data(self, config_data: Dict) -> TemplateConfig:
        """Parse configuration data from JSON."""
        # Extract section names
        section_names = config_data.get("section_names", {"intent": "Intent", "goals": "Goals", "logic": "Logic"})

        # Extract element types
        element_types = config_data.get("element_types", ["interface", "component", "data_model", "service", "class", "architecture"])

        # Extract format rules
        format_rules = config_data.get("format_rules", {})

        # Parse custom templates
        custom_templates = {}
        custom_templates_data = config_data.get("custom_templates", {})

        for element_type, template_data in custom_templates_data.items():
            template = DesignElementTemplate(
                element_type=element_type,
                intent_template=template_data.get("intent_template", ""),
                goals_template=template_data.get("goals_template", ""),
                logic_template=template_data.get("logic_template", ""),
                section_names=template_data.get("section_names", section_names),
                validation_rules=template_data.get("validation_rules", []),
            )
            custom_templates[element_type] = template

        return TemplateConfig(section_names=section_names, element_types=element_types, format_rules=format_rules, custom_templates=custom_templates)

    def _serialize_config(self) -> Dict:
        """Serialize current configuration to JSON-compatible format."""
        # Serialize custom templates
        custom_templates_data = {}
        for element_type, template in self.template_config.custom_templates.items():
            custom_templates_data[element_type] = {
                "intent_template": template.intent_template,
                "goals_template": template.goals_template,
                "logic_template": template.logic_template,
                "section_names": template.section_names,
                "validation_rules": template.validation_rules,
            }

        return {
            "section_names": self.template_config.section_names,
            "element_types": self.template_config.element_types,
            "format_rules": self.template_config.format_rules,
            "custom_templates": custom_templates_data,
        }
