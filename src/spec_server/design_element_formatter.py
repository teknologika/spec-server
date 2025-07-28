"""
DesignElementFormatter implementation for formatting technical elements.

This module provides the DesignElementFormatter class which formats individual
technical elements (interfaces, components, etc.) with Intent/Goals/Logic sections
while preserving existing content.
"""

import re
from typing import Dict, List, Optional

from .models import DEFAULT_ENHANCED_DESIGN_TEMPLATE, DesignElementTemplate, EnhancedDesignTemplate, TechnicalElement


class DesignElementFormattingError(Exception):
    """Exception raised when design element formatting fails."""

    def __init__(self, message: str, error_code: str = "FORMATTING_ERROR", details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DesignElementFormatter:
    """
    Formats individual technical elements (interfaces, components, etc.) with
    Intent/Goals/Logic sections while preserving existing content.
    """

    def __init__(self, template: Optional[EnhancedDesignTemplate] = None):
        """Initialize the formatter with an enhanced design template."""
        self.template = template or DEFAULT_ENHANCED_DESIGN_TEMPLATE

    def format_element(self, element: TechnicalElement) -> str:
        """
        Format a technical element with Intent/Goals/Logic sections.

        Args:
            element: The TechnicalElement to format

        Returns:
            Formatted element content with Intent/Goals/Logic sections

        Raises:
            DesignElementFormattingError: If formatting fails
        """
        try:
            # Get the appropriate template for this element type
            element_template = self._get_element_template(element.element_type)

            # Extract existing content sections
            existing_sections = self._extract_existing_sections(element.content)

            # Generate missing sections
            formatted_content = self._build_formatted_content(element, element_template, existing_sections)

            return formatted_content

        except Exception as e:
            raise DesignElementFormattingError(
                f"Failed to format element '{element.element_name}': {str(e)}",
                error_code="ELEMENT_FORMATTING_FAILED",
                details={"element_type": element.element_type, "element_name": element.element_name, "error": str(e)},
            )

    def generate_intent_section(self, element_type: str, element_name: str, existing_content: str = "") -> str:
        """
        Generate Intent section content for a technical element.

        Args:
            element_type: Type of the element (interface, component, etc.)
            element_name: Name of the element
            existing_content: Existing element content for context

        Returns:
            Generated Intent section content
        """
        element_template = self._get_element_template(element_type)

        # Use template to generate intent content
        intent_content = element_template.intent_template.format(element_name=element_name, element_type=element_type)

        # Enhance with context from existing content if available
        if existing_content:
            intent_content = self._enhance_intent_with_context(intent_content, existing_content, element_type)

        return intent_content

    def generate_goals_section(self, element_type: str, element_name: str, existing_content: str = "") -> List[str]:
        """
        Generate Goals section content for a technical element.

        Args:
            element_type: Type of the element (interface, component, etc.)
            element_name: Name of the element
            existing_content: Existing element content for context

        Returns:
            List of goal bullet points
        """
        element_template = self._get_element_template(element_type)

        # Use template to generate goals content
        goals_content = element_template.goals_template.format(element_name=element_name, element_type=element_type)

        # Parse into bullet points
        goals_list = self._parse_goals_template(goals_content)

        # Enhance with context from existing content if available
        if existing_content:
            goals_list = self._enhance_goals_with_context(goals_list, existing_content, element_type)

        return goals_list

    def generate_logic_section(self, element_type: str, element_name: str, existing_content: str = "") -> str:
        """
        Generate Logic section content for a technical element.

        Args:
            element_type: Type of the element (interface, component, etc.)
            element_name: Name of the element
            existing_content: Existing element content for context

        Returns:
            Generated Logic section content
        """
        element_template = self._get_element_template(element_type)

        # Use template to generate logic content
        logic_content = element_template.logic_template.format(element_name=element_name, element_type=element_type)

        # Enhance with context from existing content if available
        if existing_content:
            logic_content = self._enhance_logic_with_context(logic_content, existing_content, element_type)

        return logic_content

    def _get_element_template(self, element_type: str) -> DesignElementTemplate:
        """Get the template for a specific element type."""
        if element_type in self.template.format_templates:
            return self.template.format_templates[element_type]

        # Return a default template if specific type not found
        return DesignElementTemplate(
            element_type=element_type,
            intent_template=f"Core functionality provided by this {element_type.replace('_', ' ')}",
            goals_template=f"- Implement {element_type.replace('_', ' ')} functionality\n- Maintain system integrity\n- Provide reliable operation",
            logic_template=f"This {element_type.replace('_', ' ')} works by implementing the required functionality and integrating with other system components.",
        )

    def _extract_existing_sections(self, content: str) -> Dict[str, str]:
        """Extract existing Intent/Goals/Logic sections from content."""
        sections = {"intent": "", "goals": "", "logic": "", "other": content}  # Store original content as fallback

        # Patterns for extracting sections
        intent_pattern = r"\*\*Intent\*\*:\s*(.*?)(?=\n\s*\*\*|\n\s*##|\n\s*###|$)"
        goals_pattern = r"\*\*Goals\*\*:\s*(.*?)(?=\n\s*\*\*|\n\s*##|\n\s*###|$)"
        logic_pattern = r"\*\*Logic\*\*:\s*(.*?)(?=\n\s*\*\*|\n\s*##|\n\s*###|$)"

        # Extract Intent section
        intent_match = re.search(intent_pattern, content, re.DOTALL | re.IGNORECASE)
        if intent_match:
            sections["intent"] = intent_match.group(1).strip()

        # Extract Goals section
        goals_match = re.search(goals_pattern, content, re.DOTALL | re.IGNORECASE)
        if goals_match:
            sections["goals"] = goals_match.group(1).strip()

        # Extract Logic section
        logic_match = re.search(logic_pattern, content, re.DOTALL | re.IGNORECASE)
        if logic_match:
            sections["logic"] = logic_match.group(1).strip()

        return sections

    def _build_formatted_content(self, element: TechnicalElement, template: DesignElementTemplate, existing_sections: Dict[str, str]) -> str:
        """Build the formatted content with Intent/Goals/Logic sections."""
        lines = []

        # Start with element header (preserve original header format)
        header_match = re.search(r"^(#{1,6}\s+.*?)$", element.content, re.MULTILINE)
        if header_match:
            lines.append(header_match.group(1))
        else:
            # Create a default header if none exists
            lines.append(f"### {element.element_name}")

        lines.append("")  # Empty line after header

        # Add Intent section
        intent_content = existing_sections.get("intent")
        if not intent_content:
            intent_content = self.generate_intent_section(element.element_type, element.element_name, element.content)

        section_names = template.section_names
        lines.append(f"**{section_names.get('intent', 'Intent')}**: {intent_content}")
        lines.append("")

        # Add Goals section
        goals_content = existing_sections.get("goals")
        if not goals_content:
            goals_list = self.generate_goals_section(element.element_type, element.element_name, element.content)
            goals_content = "\n".join(f"- {goal}" for goal in goals_list)

        lines.append(f"**{section_names.get('goals', 'Goals')}**:")
        if goals_content.startswith("-"):
            lines.append(goals_content)
        else:
            lines.append(f"- {goals_content}")
        lines.append("")

        # Add Logic section
        logic_content = existing_sections.get("logic")
        if not logic_content:
            logic_content = self.generate_logic_section(element.element_type, element.element_name, element.content)

        lines.append(f"**{section_names.get('logic', 'Logic')}**: {logic_content}")

        # Add any remaining content that wasn't part of the structured sections
        remaining_content = self._extract_remaining_content(element.content, existing_sections)
        if remaining_content.strip():
            lines.append("")
            lines.append(remaining_content.strip())

        return "\n".join(lines)

    def _enhance_intent_with_context(self, intent_content: str, existing_content: str, element_type: str) -> str:
        """Enhance intent content using context from existing content."""
        # Look for key phrases that might indicate the element's purpose
        purpose_indicators = [r"handles?\s+(\w+)", r"manages?\s+(\w+)", r"provides?\s+(\w+)", r"implements?\s+(\w+)", r"processes?\s+(\w+)"]

        for pattern in purpose_indicators:
            match = re.search(pattern, existing_content, re.IGNORECASE)
            if match:
                purpose = match.group(1)
                # Enhance the template with specific purpose
                if "functionality" in intent_content:
                    intent_content = intent_content.replace("functionality", f"{purpose} functionality")
                break

        return intent_content

    def _enhance_goals_with_context(self, goals_list: List[str], existing_content: str, element_type: str) -> List[str]:
        """Enhance goals list using context from existing content."""
        # Look for specific responsibilities mentioned in the content
        responsibility_patterns = [r"responsible for\s+([^.]+)", r"ensures?\s+([^.]+)", r"maintains?\s+([^.]+)", r"supports?\s+([^.]+)"]

        enhanced_goals = goals_list.copy()

        for pattern in responsibility_patterns:
            matches = re.findall(pattern, existing_content, re.IGNORECASE)
            for match in matches:
                responsibility = match.strip()
                if responsibility and len(responsibility) < 100:  # Avoid overly long matches
                    goal = f"Ensure {responsibility}"
                    if goal not in enhanced_goals:
                        enhanced_goals.append(goal)

        return enhanced_goals[:5]  # Limit to 5 goals to keep it manageable

    def _enhance_logic_with_context(self, logic_content: str, existing_content: str, element_type: str) -> str:
        """Enhance logic content using context from existing content."""
        # Look for implementation details or technical approaches
        implementation_patterns = [r"uses?\s+([^.]+)", r"implements?\s+([^.]+)", r"follows?\s+([^.]+)", r"applies?\s+([^.]+)"]

        implementation_details = []
        for pattern in implementation_patterns:
            matches = re.findall(pattern, existing_content, re.IGNORECASE)
            for match in matches:
                detail = match.strip()
                if detail and len(detail) < 100:  # Avoid overly long matches
                    implementation_details.append(detail)

        if implementation_details:
            # Enhance the logic content with specific implementation details
            enhanced_logic = logic_content
            if implementation_details:
                details_text = ", ".join(implementation_details[:3])  # Limit to 3 details
                enhanced_logic += f" It uses {details_text} to achieve its objectives."
            return enhanced_logic

        return logic_content

    def _parse_goals_template(self, goals_content: str) -> List[str]:
        """Parse goals template content into a list of bullet points."""
        if not goals_content:
            return []

        # Split by newlines and extract bullet points
        lines = goals_content.split("\n")
        goals = []

        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                goals.append(line[2:].strip())
            elif line.startswith("* "):
                goals.append(line[2:].strip())
            elif line and not line.startswith("-") and not line.startswith("*"):
                # If it's not a bullet point but has content, treat as a single goal
                goals.append(line)

        return [goal for goal in goals if goal]  # Filter out empty goals

    def _extract_remaining_content(self, original_content: str, existing_sections: Dict[str, str]) -> str:
        """Extract content that wasn't part of the structured sections."""
        # Remove the header
        content_without_header = re.sub(r"^#{1,6}\s+.*?$", "", original_content, flags=re.MULTILINE)

        # Remove existing Intent/Goals/Logic sections more precisely
        patterns_to_remove = [
            r"\*\*Intent\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
            r"\*\*Goals\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
            r"\*\*Logic\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
            r"\*\*Purpose\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
            r"\*\*Objectives\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
            r"\*\*Implementation\*\*:.*?(?=\n\s*\*\*|\n\s*##|\n\s*###|$)",
        ]

        remaining_content = content_without_header
        for pattern in patterns_to_remove:
            remaining_content = re.sub(pattern, "", remaining_content, flags=re.DOTALL | re.IGNORECASE)

        # Clean up extra whitespace
        remaining_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", remaining_content)
        remaining_content = re.sub(r"^\s*\n+", "", remaining_content)

        return remaining_content.strip()

    def update_template(self, template: EnhancedDesignTemplate) -> None:
        """
        Update the template used for element formatting.

        Args:
            template: New enhanced design template to use
        """
        self.template = template

    def get_supported_element_types(self) -> List[str]:
        """
        Get list of supported technical element types.

        Returns:
            List of supported element type names
        """
        return list(self.template.format_templates.keys())
