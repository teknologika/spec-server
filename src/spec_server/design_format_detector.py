"""
DesignFormatDetector implementation for analyzing design documents.

This module provides the DesignFormatDetector class which analyzes existing design
documents to identify technical elements and detect which ones lack Intent/Goals/Logic
sections for automatic enhancement.
"""

import re
from typing import Dict, List

from .models import DEFAULT_ENHANCED_DESIGN_TEMPLATE, EnhancedDesignTemplate, FormatAnalysisResult, TechnicalElement


class DesignFormatDetectionError(Exception):
    """Exception raised when design format detection fails."""

    def __init__(self, message: str, error_code: str = "DETECTION_ERROR", details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DesignFormatDetector:
    """
    Detects existing technical elements in design documents and identifies which ones
    lack Intent/Goals/Logic sections for automatic enhancement.
    """

    def __init__(self, template: EnhancedDesignTemplate = None):
        """Initialize the detector with an enhanced design template."""
        self.template = template or DEFAULT_ENHANCED_DESIGN_TEMPLATE
        self.intent_patterns = [r"\*\*Intent\*\*:", r"## Intent", r"### Intent", r"\*\*Purpose\*\*:", r"## Purpose", r"### Purpose"]
        self.goals_patterns = [r"\*\*Goals\*\*:", r"## Goals", r"### Goals", r"\*\*Objectives\*\*:", r"## Objectives", r"### Objectives"]
        self.logic_patterns = [
            r"\*\*Logic\*\*:",
            r"## Logic",
            r"### Logic",
            r"\*\*Implementation\*\*:",
            r"## Implementation",
            r"### Implementation",
            r"\*\*Details\*\*:",
            r"## Details",
            r"### Details",
        ]

    def analyze_design_document(self, content: str) -> FormatAnalysisResult:
        """
        Analyze a design document to identify technical elements and their format status.

        Args:
            content: The design document content to analyze

        Returns:
            FormatAnalysisResult with analysis details

        Raises:
            DesignFormatDetectionError: If analysis fails
        """
        try:
            # Detect all technical elements in the document
            elements = self.detect_technical_elements(content)

            # Check format status for each element
            elements_with_format = 0
            elements_needing_enhancement = []

            for element in elements:
                has_format = self.check_element_format(element)
                if has_format:
                    elements_with_format += 1
                else:
                    elements_needing_enhancement.append(element)

            # Generate enhancement summary
            enhancement_summary = self.generate_enhancement_summary(elements_needing_enhancement)

            # Calculate estimated changes (3 sections per element needing enhancement)
            estimated_changes = len(elements_needing_enhancement) * 3

            return FormatAnalysisResult(
                total_elements=len(elements),
                elements_with_format=elements_with_format,
                elements_needing_enhancement=elements_needing_enhancement,
                enhancement_summary=enhancement_summary,
                estimated_changes=estimated_changes,
            )

        except Exception as e:
            raise DesignFormatDetectionError(f"Failed to analyze design document: {str(e)}", error_code="ANALYSIS_FAILED", details={"content_length": len(content), "error": str(e)})

    def detect_technical_elements(self, content: str) -> List[TechnicalElement]:
        """
        Detect technical elements (interfaces, components, etc.) in design document content.

        Args:
            content: The design document content to analyze

        Returns:
            List of detected TechnicalElement objects
        """
        elements = []
        lines = content.split("\n")

        # Process each element type pattern
        for element_type, pattern in self.template.element_patterns.items():
            elements.extend(self._find_elements_by_pattern(content, lines, element_type, pattern))

        # Sort elements by line position
        elements.sort(key=lambda x: x.line_start)

        return elements

    def check_element_format(self, element: TechnicalElement) -> bool:
        """
        Check if a technical element already has Intent/Goals/Logic format.

        Args:
            element: The TechnicalElement to check

        Returns:
            True if element has Intent/Goals/Logic format, False otherwise
        """
        content = element.content.lower()

        # Check for Intent section
        has_intent = any(re.search(pattern.lower(), content) for pattern in self.intent_patterns)

        # Check for Goals section
        has_goals = any(re.search(pattern.lower(), content) for pattern in self.goals_patterns)

        # Check for Logic section
        has_logic = any(re.search(pattern.lower(), content) for pattern in self.logic_patterns)

        # Update element format flags
        element.has_intent = has_intent
        element.has_goals = has_goals
        element.has_logic = has_logic

        # Element has format if it has all three sections
        return has_intent and has_goals and has_logic

    def generate_enhancement_summary(self, elements: List[TechnicalElement]) -> str:
        """
        Generate a human-readable summary of proposed enhancements.

        Args:
            elements: List of elements needing enhancement

        Returns:
            Human-readable enhancement summary
        """
        if not elements:
            return "All technical elements already have Intent/Goals/Logic format."

        # Count elements by type
        type_counts = {}
        missing_sections = {"intent": 0, "goals": 0, "logic": 0}

        for element in elements:
            element_type = element.element_type
            type_counts[element_type] = type_counts.get(element_type, 0) + 1

            if not element.has_intent:
                missing_sections["intent"] += 1
            if not element.has_goals:
                missing_sections["goals"] += 1
            if not element.has_logic:
                missing_sections["logic"] += 1

        # Build summary
        summary_parts = []

        # Overall count
        total_elements = len(elements)
        summary_parts.append(f"{total_elements} technical element{'s' if total_elements != 1 else ''} need enhancement:")

        # Breakdown by type
        type_breakdown = []
        for element_type, count in sorted(type_counts.items()):
            type_name = element_type.replace("_", " ").title()
            type_breakdown.append(f"{count} {type_name}{'s' if count != 1 else ''}")

        if type_breakdown:
            summary_parts.append("- " + ", ".join(type_breakdown))

        # Missing sections summary
        missing_parts = []
        for section, count in missing_sections.items():
            if count > 0:
                missing_parts.append(f"{count} {section.title()} section{'s' if count != 1 else ''}")

        if missing_parts:
            summary_parts.append(f"Missing: {', '.join(missing_parts)}")

        return "\n".join(summary_parts)

    def _find_elements_by_pattern(self, content: str, lines: List[str], element_type: str, pattern: str) -> List[TechnicalElement]:
        """
        Find technical elements of a specific type using regex pattern.

        Args:
            content: Full document content
            lines: Document lines for line number tracking
            element_type: Type of element to find
            pattern: Regex pattern to match elements

        Returns:
            List of TechnicalElement objects found
        """
        elements = []

        try:
            # Find all matches with their positions
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element_name = match.group(1) if match.groups() else "Unknown"
                start_pos = match.start()

                # Find line numbers
                line_start = content[:start_pos].count("\n") + 1
                line_end = self._find_element_end_line(lines, line_start, element_type)

                # Extract element content
                element_content = self._extract_element_content(lines, line_start, line_end)

                element = TechnicalElement(element_type=element_type, element_name=element_name.strip(), content=element_content, line_start=line_start, line_end=line_end)

                elements.append(element)

        except re.error:
            # Log regex error but continue processing
            pass

        return elements

    def _find_element_end_line(self, lines: List[str], start_line: int, element_type: str) -> int:
        """
        Find the end line of a technical element by looking for the next section or element.

        Args:
            lines: Document lines
            start_line: Starting line number (1-based)
            element_type: Type of element

        Returns:
            End line number (1-based)
        """
        # Convert to 0-based indexing
        start_idx = start_line - 1

        # Look for next section header or element
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()

            # Check for section headers (## or ###)
            if re.match(r"^#{2,3}\s+", line):
                return i  # Return 0-based index + 1 for 1-based line number

            # Check for other technical elements
            for pattern in self.template.element_patterns.values():
                if re.search(pattern, line, re.IGNORECASE):
                    return i

        # If no end found, use last line
        return len(lines)

    def _extract_element_content(self, lines: List[str], start_line: int, end_line: int) -> str:
        """
        Extract the content of a technical element between specified lines.

        Args:
            lines: Document lines
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)

        Returns:
            Element content as string
        """
        # Convert to 0-based indexing and extract content
        start_idx = start_line - 1
        end_idx = min(end_line, len(lines))

        element_lines = lines[start_idx:end_idx]
        return "\n".join(element_lines)

    def get_supported_element_types(self) -> List[str]:
        """
        Get list of supported technical element types.

        Returns:
            List of supported element type names
        """
        return list(self.template.element_patterns.keys())

    def update_template(self, template: EnhancedDesignTemplate) -> None:
        """
        Update the template used for element detection.

        Args:
            template: New enhanced design template to use
        """
        self.template = template
