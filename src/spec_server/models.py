"""
Data models for spec-server using Pydantic.

This module contains all the core data models including:
- Phase, TaskStatus enums
- Spec, SpecMetadata, Task models
- DocumentTemplate models
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

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
    current_phase: Phase = Field(
        default=Phase.REQUIREMENTS, description="Current workflow phase"
    )
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
            raise ValueError(
                "Feature name must contain only alphanumeric characters, hyphens, and underscores"
            )
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
    has_requirements: bool = Field(
        default=False, description="Whether requirements.md exists"
    )
    has_design: bool = Field(default=False, description="Whether design.md exists")
    has_tasks: bool = Field(default=False, description="Whether tasks.md exists")
    task_progress: Optional[str] = Field(
        default=None, description="Progress summary like '3/10 completed'"
    )
    created_at: str = Field(..., description="ISO timestamp of spec creation")
    updated_at: str = Field(..., description="ISO timestamp of last modification")

    model_config = ConfigDict(use_enum_values=True)


class Task(BaseModel):
    """Represents an individual implementation task from tasks.md."""

    identifier: str = Field(..., description="Task number like '1.2' or '3'")
    description: str = Field(..., description="Task description/objective")
    requirements_refs: List[str] = Field(
        default_factory=list, description="References to specific requirements"
    )
    status: TaskStatus = Field(
        default=TaskStatus.NOT_STARTED, description="Current completion status"
    )
    parent_task: Optional[str] = Field(
        default=None, description="Parent task identifier if this is a sub-task"
    )
    sub_tasks: List[str] = Field(
        default_factory=list, description="List of sub-task identifiers"
    )

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


class DocumentTemplate(BaseModel):
    """Template configuration for generating spec documents."""

    template_type: str = Field(
        ..., description="Type: 'requirements', 'design', or 'tasks'"
    )
    sections: List[str] = Field(
        ..., description="Required sections for this document type"
    )
    format_rules: dict = Field(
        default_factory=dict, description="Formatting rules and validation patterns"
    )

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
