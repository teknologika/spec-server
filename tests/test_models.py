"""
Unit tests for spec-server data models.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from spec_server.models import (
    DEFAULT_DESIGN_TEMPLATE,
    DEFAULT_REQUIREMENTS_TEMPLATE,
    DEFAULT_TASKS_TEMPLATE,
    DocumentTemplate,
    Phase,
    Spec,
    SpecMetadata,
    Task,
    TaskStatus,
)


class TestPhaseEnum:
    """Test Phase enum."""

    def test_phase_values(self):
        """Test that Phase enum has correct values."""
        assert Phase.REQUIREMENTS.value == "requirements"
        assert Phase.DESIGN.value == "design"
        assert Phase.TASKS.value == "tasks"
        assert Phase.COMPLETE.value == "complete"


class TestTaskStatusEnum:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test that TaskStatus enum has correct values."""
        assert TaskStatus.NOT_STARTED.value == "not_started"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"


class TestSpec:
    """Test Spec model."""

    def test_spec_creation_minimal(self):
        """Test creating a Spec with minimal required fields."""
        spec = Spec(
            feature_name="test-feature", base_path=Path("/tmp/specs/test-feature")
        )

        assert spec.feature_name == "test-feature"
        assert spec.current_phase == Phase.REQUIREMENTS
        assert spec.base_path == Path("/tmp/specs/test-feature")
        assert spec.created_at is not None
        assert spec.updated_at is not None

    def test_spec_creation_full(self):
        """Test creating a Spec with all fields."""
        created_time = "2024-01-01T12:00:00"
        updated_time = "2024-01-01T13:00:00"

        spec = Spec(
            feature_name="full-feature",
            current_phase=Phase.DESIGN,
            created_at=created_time,
            updated_at=updated_time,
            base_path=Path("/tmp/specs/full-feature"),
        )

        assert spec.feature_name == "full-feature"
        assert spec.current_phase == "design"
        assert spec.created_at == created_time
        assert spec.updated_at == updated_time
        assert spec.base_path == Path("/tmp/specs/full-feature")

    def test_spec_path_methods(self):
        """Test Spec path helper methods."""
        spec = Spec(feature_name="path-test", base_path=Path("/tmp/specs/path-test"))

        assert spec.get_requirements_path() == Path(
            "/tmp/specs/path-test/requirements.md"
        )
        assert spec.get_design_path() == Path("/tmp/specs/path-test/design.md")
        assert spec.get_tasks_path() == Path("/tmp/specs/path-test/tasks.md")

    def test_spec_update_timestamp(self):
        """Test updating timestamp."""
        spec = Spec(
            feature_name="timestamp-test", base_path=Path("/tmp/specs/timestamp-test")
        )

        original_time = spec.updated_at
        spec.update_timestamp()

        assert spec.updated_at != original_time

    def test_spec_feature_name_validation_empty(self):
        """Test feature name validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Spec(feature_name="", base_path=Path("/tmp/specs/empty"))

        assert "Feature name cannot be empty" in str(exc_info.value)

    def test_spec_feature_name_validation_uppercase(self):
        """Test feature name validation with uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            Spec(feature_name="Test-Feature", base_path=Path("/tmp/specs/test"))

        assert "Feature name must be lowercase" in str(exc_info.value)

    def test_spec_feature_name_validation_invalid_chars(self):
        """Test feature name validation with invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            Spec(feature_name="test@feature", base_path=Path("/tmp/specs/test"))

        assert "alphanumeric characters, hyphens, and underscores" in str(
            exc_info.value
        )

    def test_spec_feature_name_validation_valid(self):
        """Test feature name validation with valid names."""
        valid_names = [
            "test-feature",
            "test_feature",
            "testfeature",
            "test-feature-123",
            "feature123",
        ]

        for name in valid_names:
            spec = Spec(feature_name=name, base_path=Path(f"/tmp/specs/{name}"))
            assert spec.feature_name == name


class TestSpecMetadata:
    """Test SpecMetadata model."""

    def test_spec_metadata_creation(self):
        """Test creating SpecMetadata."""
        metadata = SpecMetadata(
            feature_name="meta-test",
            current_phase=Phase.DESIGN,
            has_requirements=True,
            has_design=True,
            has_tasks=False,
            task_progress="5/10 completed",
            created_at="2024-01-01T12:00:00",
            updated_at="2024-01-01T13:00:00",
        )

        assert metadata.feature_name == "meta-test"
        assert metadata.current_phase == "design"
        assert metadata.has_requirements is True
        assert metadata.has_design is True
        assert metadata.has_tasks is False
        assert metadata.task_progress == "5/10 completed"

    def test_spec_metadata_defaults(self):
        """Test SpecMetadata with default values."""
        metadata = SpecMetadata(
            feature_name="default-test",
            current_phase=Phase.REQUIREMENTS,
            created_at="2024-01-01T12:00:00",
            updated_at="2024-01-01T13:00:00",
        )

        assert metadata.has_requirements is False
        assert metadata.has_design is False
        assert metadata.has_tasks is False
        assert metadata.task_progress is None


class TestTask:
    """Test Task model."""

    def test_task_creation_minimal(self):
        """Test creating a Task with minimal fields."""
        task = Task(identifier="1", description="Test task")

        assert task.identifier == "1"
        assert task.description == "Test task"
        assert task.requirements_refs == []
        assert task.status == TaskStatus.NOT_STARTED
        assert task.parent_task is None
        assert task.sub_tasks == []

    def test_task_creation_full(self):
        """Test creating a Task with all fields."""
        task = Task(
            identifier="1.2",
            description="Full test task",
            requirements_refs=["1.1", "2.3"],
            status=TaskStatus.IN_PROGRESS,
            parent_task="1",
            sub_tasks=["1.2.1", "1.2.2"],
        )

        assert task.identifier == "1.2"
        assert task.description == "Full test task"
        assert task.requirements_refs == ["1.1", "2.3"]
        assert task.status == "in_progress"
        assert task.parent_task == "1"
        assert task.sub_tasks == ["1.2.1", "1.2.2"]

    def test_task_identifier_validation_valid(self):
        """Test task identifier validation with valid identifiers."""
        valid_identifiers = ["1", "1.1", "1.2.3", "10", "1.10.100"]

        for identifier in valid_identifiers:
            task = Task(identifier=identifier, description="Test task")
            assert task.identifier == identifier

    def test_task_identifier_validation_empty(self):
        """Test task identifier validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Task(identifier="", description="Test task")

        assert "Task identifier cannot be empty" in str(exc_info.value)

    def test_task_identifier_validation_invalid(self):
        """Test task identifier validation with invalid identifiers."""
        invalid_identifiers = ["1.a", "a.1", "1..2", ".1", "1.", "1-2"]

        for identifier in invalid_identifiers:
            with pytest.raises(ValidationError) as exc_info:
                Task(identifier=identifier, description="Test task")

            assert "numbers and dots" in str(exc_info.value)


class TestDocumentTemplate:
    """Test DocumentTemplate model."""

    def test_document_template_creation(self):
        """Test creating a DocumentTemplate."""
        template = DocumentTemplate(
            template_type="requirements",
            sections=["Introduction", "Requirements"],
            format_rules={"format": "EARS"},
        )

        assert template.template_type == "requirements"
        assert template.sections == ["Introduction", "Requirements"]
        assert template.format_rules == {"format": "EARS"}

    def test_document_template_validation_valid(self):
        """Test template type validation with valid types."""
        valid_types = ["requirements", "design", "tasks"]

        for template_type in valid_types:
            template = DocumentTemplate(
                template_type=template_type, sections=["Section 1"]
            )
            assert template.template_type == template_type

    def test_document_template_validation_invalid(self):
        """Test template type validation with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentTemplate(template_type="invalid", sections=["Section 1"])

        assert "Template type must be one of" in str(exc_info.value)


class TestDefaultTemplates:
    """Test default document templates."""

    def test_default_requirements_template(self):
        """Test default requirements template."""
        template = DEFAULT_REQUIREMENTS_TEMPLATE

        assert template.template_type == "requirements"
        assert "Introduction" in template.sections
        assert "Requirements" in template.sections
        assert "user_story_format" in template.format_rules

    def test_default_design_template(self):
        """Test default design template."""
        template = DEFAULT_DESIGN_TEMPLATE

        assert template.template_type == "design"
        assert "Overview" in template.sections
        assert "Architecture" in template.sections
        assert "Components and Interfaces" in template.sections
        assert "Data Models" in template.sections
        assert "Error Handling" in template.sections
        assert "Testing Strategy" in template.sections

    def test_default_tasks_template(self):
        """Test default tasks template."""
        template = DEFAULT_TASKS_TEMPLATE

        assert template.template_type == "tasks"
        assert "Implementation Plan" in template.sections
        assert template.format_rules["format"] == "numbered checkboxes"
        assert template.format_rules["max_hierarchy"] == 2
