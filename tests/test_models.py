"""
Unit tests for spec-server data models.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spec_server.models import (
    DEFAULT_DESIGN_TEMPLATE,
    DEFAULT_REQUIREMENTS_TEMPLATE,
    DEFAULT_TASKS_TEMPLATE,
    DocumentTemplate,
    FileReference,
    FileReferenceResolver,
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


class TestFileReference:
    """Test FileReference model."""

    def test_file_reference_creation(self):
        """Test creating a FileReference."""
        file_ref = FileReference(
            reference_text="#[[file:test.md]]",
            file_path=Path("test.md"),
            resolved_content="Test content",
            exists=True,
        )

        assert file_ref.reference_text == "#[[file:test.md]]"
        assert file_ref.file_path == Path("test.md")
        assert file_ref.resolved_content == "Test content"
        assert file_ref.exists is True
        assert file_ref.error_message is None

    def test_file_reference_defaults(self):
        """Test FileReference with default values."""
        file_ref = FileReference(
            reference_text="#[[file:test.md]]", file_path=Path("test.md")
        )

        assert file_ref.resolved_content is None
        assert file_ref.exists is False
        assert file_ref.error_message is None

    def test_file_reference_validation_empty_text(self):
        """Test FileReference validation with empty reference text."""
        with pytest.raises(ValidationError) as exc_info:
            FileReference(reference_text="", file_path=Path("test.md"))

        assert "Reference text cannot be empty" in str(exc_info.value)

    def test_file_reference_validation_invalid_format(self):
        """Test FileReference validation with invalid format."""
        invalid_formats = [
            "file:test.md",
            "#[file:test.md]",
            "#[[test.md]]",
            "#[[file:]]",
            "[[file:test.md]]",
        ]

        for invalid_format in invalid_formats:
            with pytest.raises(ValidationError) as exc_info:
                FileReference(reference_text=invalid_format, file_path=Path("test.md"))

            assert "Reference text must follow format" in str(exc_info.value)

    def test_file_reference_validation_valid_formats(self):
        """Test FileReference validation with valid formats."""
        valid_formats = [
            "#[[file:test.md]]",
            "#[[file:path/to/file.txt]]",
            "#[[file:../relative/path.json]]",
            "#[[file:/absolute/path.yaml]]",
            "#[[file:file-with-dashes.md]]",
            "#[[file:file_with_underscores.txt]]",
        ]

        for valid_format in valid_formats:
            file_ref = FileReference(
                reference_text=valid_format, file_path=Path("dummy.md")
            )
            assert file_ref.reference_text == valid_format

    def test_file_reference_from_reference_text(self):
        """Test creating FileReference from reference text."""
        reference_text = "#[[file:docs/api.md]]"
        file_ref = FileReference.from_reference_text(reference_text)

        assert file_ref.reference_text == reference_text
        assert file_ref.file_path == Path("docs/api.md")
        assert file_ref.resolved_content is None
        assert file_ref.exists is False

    def test_file_reference_from_reference_text_with_base_path(self):
        """Test creating FileReference with base path."""
        reference_text = "#[[file:api.md]]"
        base_path = Path("/project/docs")
        file_ref = FileReference.from_reference_text(reference_text, base_path)

        assert file_ref.reference_text == reference_text
        assert file_ref.file_path == Path("/project/docs/api.md")

    def test_file_reference_from_reference_text_absolute_path(self):
        """Test creating FileReference with absolute path ignores base path."""
        reference_text = "#[[file:/absolute/path/api.md]]"
        base_path = Path("/project/docs")
        file_ref = FileReference.from_reference_text(reference_text, base_path)

        assert file_ref.file_path == Path("/absolute/path/api.md")

    def test_file_reference_from_reference_text_invalid(self):
        """Test creating FileReference from invalid reference text."""
        with pytest.raises(ValueError) as exc_info:
            FileReference.from_reference_text("invalid format")

        assert "Invalid reference format" in str(exc_info.value)


class TestFileReferenceResolver:
    """Test FileReferenceResolver class."""

    def test_resolver_initialization_default(self):
        """Test FileReferenceResolver initialization with defaults."""
        resolver = FileReferenceResolver()
        assert resolver.base_path == Path.cwd()

    def test_resolver_initialization_with_base_path(self):
        """Test FileReferenceResolver initialization with base path."""
        base_path = Path("/project")
        resolver = FileReferenceResolver(base_path)
        assert resolver.base_path == base_path

    def test_extract_references_no_references(self):
        """Test extracting references from content with no references."""
        resolver = FileReferenceResolver()
        content = "This is regular content with no file references."

        references = resolver.extract_references(content)
        assert len(references) == 0

    def test_extract_references_single_reference(self):
        """Test extracting a single reference from content."""
        resolver = FileReferenceResolver()
        content = "See the API documentation: #[[file:api.md]] for details."

        references = resolver.extract_references(content)
        assert len(references) == 1
        assert references[0].reference_text == "#[[file:api.md]]"
        assert references[0].file_path.name == "api.md"

    def test_extract_references_multiple_references(self):
        """Test extracting multiple references from content."""
        resolver = FileReferenceResolver()
        content = """
        Check the API docs: #[[file:api.md]]
        And the schema: #[[file:schema/user.json]]
        Also see: #[[file:../README.md]]
        """

        references = resolver.extract_references(content)
        assert len(references) == 3

        expected_files = ["api.md", "schema/user.json", "../README.md"]
        actual_files = [str(ref.file_path) for ref in references]

        for expected in expected_files:
            assert any(expected in actual for actual in actual_files)

    def test_extract_references_invalid_format(self):
        """Test extracting references with invalid format - they should be ignored by regex."""
        resolver = FileReferenceResolver()
        content = "Invalid reference: #[[file:]] should be ignored."

        # The regex pattern requires at least one character after 'file:'
        # so #[[file:]] should not match and should be ignored
        references = resolver.extract_references(content)
        assert len(references) == 0

    def test_resolve_reference_existing_file(self, temp_specs_dir):
        """Test resolving a reference to an existing file."""
        # Create a test file
        test_file = temp_specs_dir / "test.md"
        test_content = "# Test File\n\nThis is test content."
        test_file.write_text(test_content)

        resolver = FileReferenceResolver(temp_specs_dir)
        file_ref = FileReference(
            reference_text="#[[file:test.md]]", file_path=test_file
        )

        resolved_ref = resolver.resolve_reference(file_ref)

        assert resolved_ref.exists is True
        assert resolved_ref.resolved_content == test_content
        assert resolved_ref.error_message is None

    def test_resolve_reference_missing_file(self, temp_specs_dir):
        """Test resolving a reference to a missing file."""
        resolver = FileReferenceResolver(temp_specs_dir)
        file_ref = FileReference(
            reference_text="#[[file:missing.md]]",
            file_path=temp_specs_dir / "missing.md",
        )

        resolved_ref = resolver.resolve_reference(file_ref)

        assert resolved_ref.exists is False
        assert resolved_ref.resolved_content is None
        assert "File not found" in resolved_ref.error_message

    def test_resolve_reference_permission_error(self, temp_specs_dir):
        """Test resolving a reference with permission error."""
        # Create a file and make it unreadable (Unix-like systems)
        test_file = temp_specs_dir / "unreadable.md"
        test_file.write_text("content")

        resolver = FileReferenceResolver(temp_specs_dir)
        file_ref = FileReference(
            reference_text="#[[file:unreadable.md]]", file_path=test_file
        )

        # Try to make file unreadable (may not work on all systems)
        try:
            test_file.chmod(0o000)
            resolved_ref = resolver.resolve_reference(file_ref)

            # Should handle the permission error gracefully
            assert resolved_ref.exists is False
            assert "Error reading file" in resolved_ref.error_message
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except Exception:
                pass

    def test_resolve_all_references(self, temp_specs_dir):
        """Test resolving multiple references."""
        # Create test files
        file1 = temp_specs_dir / "file1.md"
        file2 = temp_specs_dir / "file2.md"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        resolver = FileReferenceResolver(temp_specs_dir)
        references = [
            FileReference(reference_text="#[[file:file1.md]]", file_path=file1),
            FileReference(reference_text="#[[file:file2.md]]", file_path=file2),
            FileReference(
                reference_text="#[[file:missing.md]]",
                file_path=temp_specs_dir / "missing.md",
            ),
        ]

        resolved_refs = resolver.resolve_all_references(references)

        assert len(resolved_refs) == 3
        assert resolved_refs[0].resolved_content == "Content 1"
        assert resolved_refs[1].resolved_content == "Content 2"
        assert resolved_refs[2].exists is False

    def test_substitute_references_with_content(self, temp_specs_dir):
        """Test substituting references with actual file content."""
        # Create test file
        test_file = temp_specs_dir / "api.md"
        test_content = "# API Documentation\n\nThis is the API."
        test_file.write_text(test_content)

        resolver = FileReferenceResolver(temp_specs_dir)
        content = "See the API docs:\n\n#[[file:api.md]]\n\nEnd of document."

        result = resolver.substitute_references(content, resolve_content=True)

        expected = f"See the API docs:\n\n{test_content}\n\nEnd of document."
        assert result == expected

    def test_substitute_references_with_placeholders(self, temp_specs_dir):
        """Test substituting references with placeholders."""
        resolver = FileReferenceResolver(temp_specs_dir)
        content = "See the API docs: #[[file:api.md]] for details."

        result = resolver.substitute_references(content, resolve_content=False)

        expected = f"See the API docs: [File: {temp_specs_dir / 'api.md'}] for details."
        assert result == expected

    def test_substitute_references_with_errors(self, temp_specs_dir):
        """Test substituting references that have errors."""
        resolver = FileReferenceResolver(temp_specs_dir)
        content = "See the missing file: #[[file:missing.md]] for details."

        result = resolver.substitute_references(content, resolve_content=True)

        assert "[ERROR:" in result
        assert "File not found" in result

    def test_validate_references_all_valid(self, temp_specs_dir):
        """Test validating references with all valid files."""
        # Create test files
        file1 = temp_specs_dir / "file1.md"
        file2 = temp_specs_dir / "file2.md"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        resolver = FileReferenceResolver(temp_specs_dir)
        content = "File 1: #[[file:file1.md]] and File 2: #[[file:file2.md]]"

        errors = resolver.validate_references(content)
        assert len(errors) == 0

    def test_validate_references_with_errors(self, temp_specs_dir):
        """Test validating references with missing files."""
        resolver = FileReferenceResolver(temp_specs_dir)
        content = "Missing: #[[file:missing1.md]] and #[[file:missing2.md]]"

        errors = resolver.validate_references(content)
        assert len(errors) == 2
        assert all("File not found" in error for error in errors)

    def test_file_reference_pattern_matching(self):
        """Test the regex pattern matches expected formats."""
        resolver = FileReferenceResolver()
        pattern = resolver.FILE_REFERENCE_PATTERN

        # Valid patterns
        valid_patterns = [
            "#[[file:test.md]]",
            "#[[file:path/to/file.txt]]",
            "#[[file:../relative.json]]",
            "#[[file:/absolute/path.yaml]]",
        ]

        for pattern_text in valid_patterns:
            match = pattern.search(pattern_text)
            assert match is not None
            assert match.group(0) == pattern_text

        # Invalid patterns
        invalid_patterns = [
            "file:test.md",
            "#[file:test.md]",
            "#[[test.md]]",
            "[[file:test.md]]",
        ]

        for pattern_text in invalid_patterns:
            match = pattern.search(pattern_text)
            assert match is None
