"""
Data models for spec-server using Pydantic.

This module contains all the core data models including:
- Phase, TaskStatus enums
- Spec, SpecMetadata, Task models
- DocumentTemplate models
"""

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Phase(Enum):
    """Represents the current phase of a specification in the workflow."""

    REQUIREMENTS = "requirements"  # Initial phase - gathering and defining requirements
    DESIGN = "design"  # Second phase - creating technical design
    TASKS = "tasks"  # Final phase - implementation task planning
    COMPLETE = "complete"  # All phases completed and approved


class TaskStatus(Enum):
    """Tracks the completion status of individual implementation tasks."""

    NOT_STARTED = "not_started"  # Task has not been started
    IN_PROGRESS = "in_progress"  # Task is currently being worked on
    COMPLETED = "completed"  # Task has been finished


class Spec(BaseModel):
    """Core model representing a complete feature specification."""

    feature_name: str = Field(..., description="Kebab-case identifier for the feature")
    current_phase: Phase = Field(default=Phase.REQUIREMENTS, description="Current workflow phase")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of spec creation",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of last modification",
    )
    base_path: Path = Field(..., description="File system path to spec directory")

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    @field_validator("feature_name")
    @classmethod
    def validate_feature_name(cls, v: str) -> str:
        """Validate that feature name follows kebab-case convention."""
        if not v:
            raise ValueError("Feature name cannot be empty")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Feature name must contain only alphanumeric characters, hyphens, and underscores")
        if v != v.lower():
            raise ValueError("Feature name must be lowercase")
        return v

    def get_requirements_path(self) -> Path:
        """Returns path to requirements.md file."""
        return self.base_path / "requirements.md"

    def get_design_path(self) -> Path:
        """Returns path to design.md file."""
        return self.base_path / "design.md"

    def get_tasks_path(self) -> Path:
        """Returns path to tasks.md file."""
        return self.base_path / "tasks.md"

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now().isoformat()


class SpecMetadata(BaseModel):
    """Lightweight model for listing specs without loading full content."""

    feature_name: str = Field(..., description="Kebab-case identifier for the feature")
    current_phase: Phase = Field(..., description="Current workflow phase")
    has_requirements: bool = Field(default=False, description="Whether requirements.md exists")
    has_design: bool = Field(default=False, description="Whether design.md exists")
    has_tasks: bool = Field(default=False, description="Whether tasks.md exists")
    task_progress: Optional[str] = Field(default=None, description="Progress summary like '3/10 completed'")
    created_at: str = Field(..., description="ISO timestamp of spec creation")
    updated_at: str = Field(..., description="ISO timestamp of last modification")

    model_config = ConfigDict(use_enum_values=True)


class Task(BaseModel):
    """Represents an individual implementation task from tasks.md."""

    identifier: str = Field(..., description="Task number like '1.2' or '3'")
    description: str = Field(..., description="Task description/objective")
    requirements_refs: List[str] = Field(default_factory=list, description="References to specific requirements")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Current completion status")
    parent_task: Optional[str] = Field(default=None, description="Parent task identifier if this is a sub-task")
    sub_tasks: List[str] = Field(default_factory=list, description="List of sub-task identifiers")

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate task identifier format."""
        if not v:
            raise ValueError("Task identifier cannot be empty")
        # Allow formats like "1", "1.1", "1.2.3", etc.
        parts = v.split(".")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Task identifier must contain only numbers and dots")
        return v


# New models for task formatting feature


class TaskItem(BaseModel):
    """Enhanced task model for the task formatting pipeline."""

    identifier: str = Field(..., description="Task number like '1.2' or '3'")
    description: str = Field(..., description="Task description/objective")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Current completion status")
    requirements_refs: List[str] = Field(
        default_factory=list,
        description="References to specific requirements like ['2.1', '2.2', '3.1']",
    )
    parent_task: Optional[str] = Field(default=None, description="Parent task identifier if this is a sub-task")
    sub_tasks: List[str] = Field(default_factory=list, description="List of sub-task identifiers")
    content_type: str = Field(
        default="task",
        description="Content type: 'task', 'requirement', 'design', 'other'",
    )
    original_line: int = Field(
        default=0,
        description="Original line number in source document for error reporting",
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate task identifier format."""
        if not v:
            raise ValueError("Task identifier cannot be empty")

        # Allow numeric hierarchical formats like "1", "1.1", "1.2.3"
        if re.match(r"^\d+(?:\.\d+)*$", v):
            return v

        # Allow auto-generated identifiers like "line_5"
        if re.match(r"^line_\d+$", v):
            return v

        # Allow alphanumeric identifiers with underscores and hyphens
        if re.match(r"^[a-zA-Z0-9_-]+$", v):
            return v

        raise ValueError("Task identifier must be alphanumeric with dots, underscores, or hyphens")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        valid_types = ["task", "requirement", "design", "other"]
        if v not in valid_types:
            raise ValueError(f"Content type must be one of: {valid_types}")
        return v


class ContentBlock(BaseModel):
    """Represents a block of content for classification and redistribution."""

    content: str = Field(..., description="The actual content text")
    content_type: str = Field(
        ...,
        description="Classified type: 'task', 'requirement', 'design', 'header', 'other'",
    )
    confidence: float = Field(..., description="Classification confidence from 0.0 to 1.0", ge=0.0, le=1.0)
    suggested_location: str = Field(
        ...,
        description="Suggested document location: 'tasks', 'requirements', 'design'",
    )
    line_number: int = Field(..., description="Line number in original document", ge=0)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        valid_types = ["task", "requirement", "design", "header", "other"]
        if v not in valid_types:
            raise ValueError(f"Content type must be one of: {valid_types}")
        return v

    @field_validator("suggested_location")
    @classmethod
    def validate_suggested_location(cls, v: str) -> str:
        """Validate suggested location."""
        valid_locations = ["tasks", "requirements", "design"]
        if v not in valid_locations:
            raise ValueError(f"Suggested location must be one of: {valid_locations}")
        return v


class FormattingResult(BaseModel):
    """Result of task document formatting operation."""

    formatted_tasks: str = Field(..., description="Formatted task document content")
    moved_content: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Content moved to other documents: document_type -> content_blocks",
    )
    requirements_added: List[str] = Field(
        default_factory=list,
        description="Task identifiers that received requirements references",
    )
    changes_made: List[str] = Field(default_factory=list, description="Human-readable descriptions of changes made")
    errors: List[str] = Field(default_factory=list, description="Error messages encountered during formatting")


class TaskValidationResult(BaseModel):
    """Result of LLM-based task completion validation."""

    is_complete: bool = Field(..., description="Whether the task is considered complete")
    confidence: float = Field(..., description="LLM confidence in the completion assessment", ge=0.0, le=1.0)
    feedback: str = Field(..., description="LLM explanation of completion status")
    missing_items: List[str] = Field(
        default_factory=list,
        description="Specific items that need attention if incomplete",
    )
    validation_prompt: str = Field(..., description="Prompt used for LLM validation")
    llm_response: str = Field(..., description="Full LLM response for debugging")


class DocumentTemplate(BaseModel):
    """Template configuration for generating spec documents."""

    template_type: str = Field(..., description="Type: 'requirements', 'design', or 'tasks'")
    sections: List[str] = Field(..., description="Required sections for this document type")
    format_rules: dict = Field(default_factory=dict, description="Formatting rules and validation patterns")

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v: str) -> str:
        """Validate template type."""
        valid_types = ["requirements", "design", "tasks"]
        if v not in valid_types:
            raise ValueError(f"Template type must be one of: {valid_types}")
        return v


# Default document templates
DEFAULT_REQUIREMENTS_TEMPLATE = DocumentTemplate(
    template_type="requirements",
    sections=["Introduction", "Requirements"],
    format_rules={
        "user_story_format": "As a [role], I want [feature], so that [benefit]",
        "acceptance_criteria_format": "EARS format (WHEN/IF/THEN/SHALL)",
        "numbering": "hierarchical",
    },
)

DEFAULT_DESIGN_TEMPLATE = DocumentTemplate(
    template_type="design",
    sections=[
        "Overview",
        "Architecture",
        "Components and Interfaces",
        "Data Models",
        "Error Handling",
        "Testing Strategy",
    ],
    format_rules={"include_diagrams": True, "reference_requirements": True},
)

DEFAULT_TASKS_TEMPLATE = DocumentTemplate(
    template_type="tasks",
    sections=["Implementation Plan"],
    format_rules={
        "format": "numbered checkboxes",
        "max_hierarchy": 2,
        "require_requirements_refs": True,
        "focus": "coding tasks only",
    },
)


class FileReference(BaseModel):
    """Represents a file reference found in spec documents."""

    reference_text: str = Field(..., description="Original reference text like '#[[file:path/to/file.md]]'")
    file_path: Path = Field(..., description="Parsed file path from the reference")
    resolved_content: Optional[str] = Field(default=None, description="Content of the referenced file")
    exists: bool = Field(default=False, description="Whether the referenced file exists")
    error_message: Optional[str] = Field(default=None, description="Error message if file cannot be resolved")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("reference_text")
    @classmethod
    def validate_reference_text(cls, v: str) -> str:
        """Validate that reference text follows the expected format."""
        if not v:
            raise ValueError("Reference text cannot be empty")

        # Check if it matches the expected pattern #[[file:path]]
        pattern = r"#\[\[file:[^\]]+\]\]"
        if not re.match(pattern, v):
            raise ValueError("Reference text must follow format '#[[file:path]]'")

        return v

    @classmethod
    def from_reference_text(cls, reference_text: str, base_path: Optional[Path] = None) -> "FileReference":
        """Create a FileReference from reference text."""
        # Extract the file path from the reference text
        match = re.match(r"#\[\[file:([^\]]+)\]\]", reference_text)
        if not match:
            raise ValueError(f"Invalid reference format: {reference_text}")

        file_path_str = match.group(1)
        file_path = Path(file_path_str)

        # Make path relative to base_path if provided
        if base_path and not file_path.is_absolute():
            file_path = base_path / file_path

        return cls(reference_text=reference_text, file_path=file_path)


class FileReferenceResolver:
    """Handles parsing and resolution of file references in spec documents."""

    # Regex pattern to match file references: #[[file:path/to/file.ext]]
    FILE_REFERENCE_PATTERN = re.compile(r"#\[\[file:([^\]]+)\]\]")

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the resolver with an optional base path for relative references."""
        self.base_path = base_path or Path.cwd()

    def extract_references(self, content: str) -> List[FileReference]:
        """Extract all file references from the given content."""
        references = []

        for match in self.FILE_REFERENCE_PATTERN.finditer(content):
            reference_text = match.group(0)
            try:
                file_ref = FileReference.from_reference_text(reference_text, self.base_path)
                references.append(file_ref)
            except ValueError as e:
                # Create a reference with error information
                file_ref = FileReference(
                    reference_text=reference_text,
                    file_path=Path("invalid"),
                    error_message=str(e),
                )
                references.append(file_ref)

        return references

    def resolve_reference(self, file_ref: FileReference) -> FileReference:
        """Resolve a single file reference by reading its content."""
        try:
            if file_ref.file_path.exists() and file_ref.file_path.is_file():
                with open(file_ref.file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_ref.resolved_content = content
                file_ref.exists = True
                file_ref.error_message = None
            else:
                file_ref.exists = False
                file_ref.error_message = f"File not found: {file_ref.file_path}"

        except Exception as e:
            file_ref.exists = False
            file_ref.error_message = f"Error reading file: {str(e)}"

        return file_ref

    def resolve_all_references(self, references: List[FileReference]) -> List[FileReference]:
        """Resolve all file references in the list."""
        return [self.resolve_reference(ref) for ref in references]

    def substitute_references(self, content: str, resolve_content: bool = True) -> str:
        """
        Substitute file references in content with their resolved content.

        Args:
            content: The content containing file references
            resolve_content: If True, substitute with file content. If False, substitute with placeholder.

        Returns:
            Content with file references substituted
        """
        references = self.extract_references(content)

        if resolve_content:
            references = self.resolve_all_references(references)

        result_content = content

        for ref in references:
            if resolve_content and ref.resolved_content is not None:
                # Replace with actual file content
                result_content = result_content.replace(ref.reference_text, ref.resolved_content)
            elif resolve_content and ref.error_message:
                # Replace with error message
                error_placeholder = f"[ERROR: {ref.error_message}]"
                result_content = result_content.replace(ref.reference_text, error_placeholder)
            else:
                # Replace with placeholder showing the file path
                placeholder = f"[File: {ref.file_path}]"
                result_content = result_content.replace(ref.reference_text, placeholder)

        return result_content

    def validate_references(self, content: str) -> List[str]:
        """
        Validate all file references in content and return list of error messages.

        Returns:
            List of error messages for invalid or missing references
        """
        references = self.extract_references(content)
        references = self.resolve_all_references(references)

        errors = []
        for ref in references:
            if ref.error_message:
                errors.append(f"Reference '{ref.reference_text}': {ref.error_message}")

        return errors


# Enhanced Design Format Models


class DesignElementTemplate(BaseModel):
    """Template for formatting technical elements with Intent/Goals/Logic sections."""

    element_type: str = Field(..., description="Type: 'interface', 'component', 'data_model', 'service', 'class', 'architecture'")
    intent_template: str = Field(..., description="Template for Intent section content")
    goals_template: str = Field(..., description="Template for Goals section content")
    logic_template: str = Field(..., description="Template for Logic section content")
    section_names: Dict[str, str] = Field(default_factory=lambda: {"intent": "Intent", "goals": "Goals", "logic": "Logic"}, description="Customizable section names")
    validation_rules: List[str] = Field(default_factory=list, description="Rules for validating generated content")

    @field_validator("element_type")
    @classmethod
    def validate_element_type(cls, v: str) -> str:
        """Validate element type."""
        valid_types = ["interface", "component", "data_model", "service", "class", "architecture"]
        if v not in valid_types:
            raise ValueError(f"Element type must be one of: {valid_types}")
        return v


class TemplateConfig(BaseModel):
    """Configuration model for customizing the Intent/Goals/Logic format structure."""

    section_names: Dict[str, str] = Field(default_factory=lambda: {"intent": "Intent", "goals": "Goals", "logic": "Logic"}, description="Customizable section names")
    element_types: List[str] = Field(default_factory=lambda: ["interface", "component", "data_model", "service", "class", "architecture"], description="Supported element types")
    format_rules: Dict[str, Any] = Field(default_factory=dict, description="Formatting rules and patterns")
    custom_templates: Dict[str, DesignElementTemplate] = Field(default_factory=dict, description="Custom templates for specific element types")

    @field_validator("element_types")
    @classmethod
    def validate_element_types(cls, v: List[str]) -> List[str]:
        """Validate element types list."""
        valid_types = ["interface", "component", "data_model", "service", "class", "architecture"]
        for element_type in v:
            if element_type not in valid_types:
                raise ValueError(f"Element type '{element_type}' must be one of: {valid_types}")
        return v


class TechnicalElement(BaseModel):
    """Represents a detected technical element in a design document."""

    element_type: str = Field(..., description="Type: 'interface', 'component', 'data_model', etc.")
    element_name: str = Field(..., description="Name of the element")
    content: str = Field(..., description="Original content of the element")
    has_intent: bool = Field(default=False, description="Whether Intent section exists")
    has_goals: bool = Field(default=False, description="Whether Goals section exists")
    has_logic: bool = Field(default=False, description="Whether Logic section exists")
    line_start: int = Field(..., description="Starting line number in document", ge=0)
    line_end: int = Field(..., description="Ending line number in document", ge=0)

    @field_validator("element_type")
    @classmethod
    def validate_element_type(cls, v: str) -> str:
        """Validate element type."""
        valid_types = ["interface", "component", "data_model", "service", "class", "architecture"]
        if v not in valid_types:
            raise ValueError(f"Element type must be one of: {valid_types}")
        return v

    @field_validator("line_end")
    @classmethod
    def validate_line_end(cls, v: int, info) -> int:
        """Validate that line_end is greater than or equal to line_start."""
        if hasattr(info, "data") and "line_start" in info.data:
            line_start = info.data["line_start"]
            if v < line_start:
                raise ValueError("line_end must be greater than or equal to line_start")
        return v


class FormatAnalysisResult(BaseModel):
    """Result of analyzing a design document for Intent/Goals/Logic format."""

    total_elements: int = Field(..., description="Total technical elements found", ge=0)
    elements_with_format: int = Field(..., description="Elements already having Intent/Goals/Logic", ge=0)
    elements_needing_enhancement: List[TechnicalElement] = Field(default_factory=list, description="Elements missing format")
    enhancement_summary: str = Field(..., description="Human-readable summary of changes")
    estimated_changes: int = Field(..., description="Number of sections to be added", ge=0)

    @field_validator("elements_with_format")
    @classmethod
    def validate_elements_with_format(cls, v: int, info) -> int:
        """Validate that elements_with_format doesn't exceed total_elements."""
        if hasattr(info, "data") and "total_elements" in info.data:
            total_elements = info.data["total_elements"]
            if v > total_elements:
                raise ValueError("elements_with_format cannot exceed total_elements")
        return v


class EnhancedDesignTemplate(DocumentTemplate):
    """Extended design template that includes Intent/Goals/Logic formatting rules."""

    element_patterns: Dict[str, str] = Field(default_factory=dict, description="Regex patterns to identify different element types")
    format_templates: Dict[str, DesignElementTemplate] = Field(default_factory=dict, description="Templates for each element type")
    enhanced_format_enabled: bool = Field(default=True, description="Whether enhanced formatting is enabled")
    template_config: TemplateConfig = Field(default_factory=TemplateConfig, description="Configuration for template customization")

    def __init__(self, **data):
        """Initialize with enhanced design template defaults."""
        if "template_type" not in data:
            data["template_type"] = "design"
        if "sections" not in data:
            data["sections"] = ["Overview", "Architecture", "Components and Interfaces", "Data Models", "Error Handling", "Testing Strategy"]
        if "format_rules" not in data:
            data["format_rules"] = {"include_diagrams": True, "reference_requirements": True, "enhanced_format": True}
        super().__init__(**data)


# Default enhanced design template
DEFAULT_ENHANCED_DESIGN_TEMPLATE = EnhancedDesignTemplate(
    template_type="design",
    sections=["Overview", "Architecture", "Components and Interfaces", "Data Models", "Error Handling", "Testing Strategy"],
    format_rules={"include_diagrams": True, "reference_requirements": True, "enhanced_format": True},
    element_patterns={
        "interface": r"###\s+([A-Za-z][A-Za-z0-9_]*)\s*(?:Interface)?",
        "component": r"###\s+([A-Za-z][A-Za-z0-9_]*)\s*(?:Component)?",
        "data_model": r"###\s+([A-Za-z][A-Za-z0-9_]*)\s*(?:Model|Entity|Schema)?",
        "service": r"###\s+([A-Za-z][A-Za-z0-9_]*)\s*(?:Service|Manager|Handler)?",
        "class": r"class\s+([A-Za-z][A-Za-z0-9_]*)",
        "architecture": r"###\s+([A-Za-z][A-Za-z0-9_\s]*)\s*(?:Architecture|System|Integration)",
    },
    format_templates={
        "interface": DesignElementTemplate(
            element_type="interface",
            intent_template="Simple summary of what this interface provides",
            goals_template="- Define clear contract for {element_name}\n- Ensure type safety and validation\n- Support extensibility and maintainability",
            logic_template="Detailed explanation of how this interface works, its methods, parameters, and expected behavior",
        ),
        "component": DesignElementTemplate(
            element_type="component",
            intent_template="Core functionality provided by this component",
            goals_template="- Implement specific business logic for {element_name}\n- Maintain separation of concerns\n- Provide reliable and testable functionality",
            logic_template="Explanation of the component's internal workings, dependencies, and how it integrates with other system parts",
        ),
        "data_model": DesignElementTemplate(
            element_type="data_model",
            intent_template="Data structure and relationships for {element_name}",
            goals_template="- Define clear data schema and validation rules\n- Support data integrity and consistency\n- Enable efficient data operations",
            logic_template="Description of the data model's fields, relationships, constraints, and how it supports the business domain",
        ),
    },
)
