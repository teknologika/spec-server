"""
Unit tests for SpecManager class.
"""

import json
import shutil
from pathlib import Path

import pytest

from spec_server.models import Phase, SpecMetadata
from spec_server.spec_manager import SpecError, SpecManager


class TestSpecManager:
    """Test SpecManager class."""

    def test_spec_manager_initialization_default(self):
        """Test SpecManager initialization with default path."""
        manager = SpecManager()
        # The default path is determined by get_effective_specs_dir() which may return
        # either the workspace-relative .specs directory or the fallback specs directory
        # Just check that the base_path is set and the metadata file is in the right place
        assert manager.base_path is not None
        assert manager.metadata_file == manager.base_path / ".spec-metadata.json"

    def test_spec_manager_initialization_custom_path(self, temp_specs_dir):
        """Test SpecManager initialization with custom path."""
        manager = SpecManager(temp_specs_dir)
        assert manager.base_path == temp_specs_dir
        assert manager.metadata_file == temp_specs_dir / ".spec-metadata.json"

    def test_ensure_base_directory_creates_directory(self, temp_specs_dir):
        """Test that base directory is created if it doesn't exist."""
        # Remove the directory
        if temp_specs_dir.exists():
            shutil.rmtree(temp_specs_dir)

        SpecManager(temp_specs_dir)
        assert temp_specs_dir.exists()
        assert temp_specs_dir.is_dir()

    def test_create_spec_success(self, temp_specs_dir):
        """Test successful spec creation."""
        manager = SpecManager(temp_specs_dir)

        spec = manager.create_spec("test-feature", "A test feature for testing")

        assert spec.feature_name == "test-feature"
        assert spec.current_phase == "requirements"
        assert spec.base_path == temp_specs_dir / "test-feature"
        assert spec.created_at is not None
        assert spec.updated_at is not None

        # Check directory was created
        spec_dir = temp_specs_dir / "test-feature"
        assert spec_dir.exists()
        assert spec_dir.is_dir()

        # Check metadata registry was updated
        metadata_file = temp_specs_dir / ".spec-metadata.json"
        assert metadata_file.exists()

        with open(metadata_file, "r") as f:
            registry = json.load(f)

        assert "test-feature" in registry
        assert registry["test-feature"]["initial_idea"] == "A test feature for testing"

    def test_create_spec_already_exists(self, temp_specs_dir):
        """Test creating a spec that already exists."""
        manager = SpecManager(temp_specs_dir)

        # Create first spec
        manager.create_spec("test-feature", "First creation")

        # Try to create again
        with pytest.raises(SpecError) as exc_info:
            manager.create_spec("test-feature", "Second creation")

        assert exc_info.value.error_code == "SPEC_ALREADY_EXISTS"
        assert "already exists" in exc_info.value.message

    def test_create_spec_invalid_name(self, temp_specs_dir):
        """Test creating a spec with invalid name."""
        manager = SpecManager(temp_specs_dir)

        with pytest.raises(Exception):  # Should be caught by Pydantic validation
            manager.create_spec("Invalid@Name", "Test feature")

    def test_get_spec_success(self, temp_specs_dir):
        """Test successfully getting an existing spec."""
        manager = SpecManager(temp_specs_dir)

        # Create a spec first
        created_spec = manager.create_spec("test-feature", "A test feature")

        # Get the spec
        retrieved_spec = manager.get_spec("test-feature")

        assert retrieved_spec.feature_name == created_spec.feature_name
        assert retrieved_spec.current_phase == created_spec.current_phase
        assert retrieved_spec.base_path == created_spec.base_path

    def test_get_spec_not_found(self, temp_specs_dir):
        """Test getting a spec that doesn't exist."""
        manager = SpecManager(temp_specs_dir)

        with pytest.raises(SpecError) as exc_info:
            manager.get_spec("nonexistent-feature")

        assert exc_info.value.error_code == "SPEC_NOT_FOUND"
        assert "not found" in exc_info.value.message

    def test_get_spec_with_files(self, temp_specs_dir):
        """Test getting a spec with various files present."""
        manager = SpecManager(temp_specs_dir)

        # Create spec and add files
        manager.create_spec("test-feature", "Test")
        spec_dir = temp_specs_dir / "test-feature"

        # Create requirements file
        (spec_dir / "requirements.md").write_text("# Requirements")

        # Get spec - should detect REQUIREMENTS phase
        retrieved_spec = manager.get_spec("test-feature")
        assert retrieved_spec.current_phase == "requirements"

        # Add design file
        (spec_dir / "design.md").write_text("# Design")
        retrieved_spec = manager.get_spec("test-feature")
        assert retrieved_spec.current_phase == "design"

        # Add tasks file
        (spec_dir / "tasks.md").write_text("# Tasks")
        retrieved_spec = manager.get_spec("test-feature")
        assert retrieved_spec.current_phase == "tasks"

    def test_list_specs_empty(self, temp_specs_dir):
        """Test listing specs when none exist."""
        manager = SpecManager(temp_specs_dir)

        specs = manager.list_specs()
        assert len(specs) == 0

    def test_list_specs_single(self, temp_specs_dir):
        """Test listing specs with one spec."""
        manager = SpecManager(temp_specs_dir)

        # Create a spec
        manager.create_spec("test-feature", "Test feature")

        specs = manager.list_specs()
        assert len(specs) == 1

        spec_meta = specs[0]
        assert isinstance(spec_meta, SpecMetadata)
        assert spec_meta.feature_name == "test-feature"
        assert spec_meta.current_phase == "requirements"
        assert spec_meta.has_requirements is False  # No files created yet
        assert spec_meta.has_design is False
        assert spec_meta.has_tasks is False

    def test_list_specs_multiple(self, temp_specs_dir):
        """Test listing multiple specs."""
        manager = SpecManager(temp_specs_dir)

        # Create multiple specs
        manager.create_spec("feature-1", "First feature")
        manager.create_spec("feature-2", "Second feature")
        manager.create_spec("feature-3", "Third feature")

        specs = manager.list_specs()
        assert len(specs) == 3

        feature_names = [spec.feature_name for spec in specs]
        assert "feature-1" in feature_names
        assert "feature-2" in feature_names
        assert "feature-3" in feature_names

    def test_list_specs_with_files(self, temp_specs_dir):
        """Test listing specs with various files present."""
        manager = SpecManager(temp_specs_dir)

        # Create spec and add files
        manager.create_spec("test-feature", "Test")
        spec_dir = temp_specs_dir / "test-feature"

        # Add requirements and design files
        (spec_dir / "requirements.md").write_text("# Requirements")
        (spec_dir / "design.md").write_text("# Design")

        specs = manager.list_specs()
        assert len(specs) == 1

        spec_meta = specs[0]
        assert spec_meta.has_requirements is True
        assert spec_meta.has_design is True
        assert spec_meta.has_tasks is False
        assert spec_meta.current_phase == "design"

    def test_list_specs_with_task_progress(self, temp_specs_dir):
        """Test listing specs with task progress calculation."""
        manager = SpecManager(temp_specs_dir)

        # Create spec and add tasks file
        manager.create_spec("test-feature", "Test")
        spec_dir = temp_specs_dir / "test-feature"

        tasks_content = """
# Tasks

- [x] 1. Completed task
- [ ] 2. Incomplete task
- [x] 3. Another completed task
- [ ] 4. Another incomplete task
"""
        (spec_dir / "tasks.md").write_text(tasks_content)

        specs = manager.list_specs()
        spec_meta = specs[0]

        assert spec_meta.task_progress == "2/4 completed"

    def test_delete_spec_success(self, temp_specs_dir):
        """Test successful spec deletion."""
        manager = SpecManager(temp_specs_dir)

        # Create a spec
        manager.create_spec("test-feature", "Test feature")
        spec_dir = temp_specs_dir / "test-feature"

        # Verify it exists
        assert spec_dir.exists()
        assert manager.spec_exists("test-feature")

        # Delete it
        result = manager.delete_spec("test-feature")

        assert result is True
        assert not spec_dir.exists()
        assert not manager.spec_exists("test-feature")

        # Check metadata registry was updated
        metadata_file = temp_specs_dir / ".spec-metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                registry = json.load(f)
            assert "test-feature" not in registry

    def test_delete_spec_not_found(self, temp_specs_dir):
        """Test deleting a spec that doesn't exist."""
        manager = SpecManager(temp_specs_dir)

        with pytest.raises(SpecError) as exc_info:
            manager.delete_spec("nonexistent-feature")

        assert exc_info.value.error_code == "SPEC_NOT_FOUND"

    def test_delete_spec_with_files(self, temp_specs_dir):
        """Test deleting a spec with multiple files."""
        manager = SpecManager(temp_specs_dir)

        # Create spec and add files
        manager.create_spec("test-feature", "Test")
        spec_dir = temp_specs_dir / "test-feature"

        # Add multiple files
        (spec_dir / "requirements.md").write_text("# Requirements")
        (spec_dir / "design.md").write_text("# Design")
        (spec_dir / "tasks.md").write_text("# Tasks")
        (spec_dir / "extra.txt").write_text("Extra file")

        # Delete spec
        manager.delete_spec("test-feature")

        # Verify everything is gone
        assert not spec_dir.exists()

    def test_update_spec_metadata(self, temp_specs_dir):
        """Test updating spec metadata."""
        manager = SpecManager(temp_specs_dir)

        # Create a spec
        manager.create_spec("test-feature", "Test feature")

        # Update metadata
        manager.update_spec_metadata("test-feature", custom_field="custom_value")

        # Check metadata was updated
        metadata_file = temp_specs_dir / ".spec-metadata.json"
        with open(metadata_file, "r") as f:
            registry = json.load(f)

        assert registry["test-feature"]["custom_field"] == "custom_value"
        assert "updated_at" in registry["test-feature"]

    def test_update_spec_metadata_not_found(self, temp_specs_dir):
        """Test updating metadata for nonexistent spec."""
        manager = SpecManager(temp_specs_dir)

        with pytest.raises(SpecError) as exc_info:
            manager.update_spec_metadata("nonexistent", field="value")

        assert exc_info.value.error_code == "SPEC_NOT_FOUND"

    def test_spec_exists(self, temp_specs_dir):
        """Test checking if spec exists."""
        manager = SpecManager(temp_specs_dir)

        # Initially doesn't exist
        assert not manager.spec_exists("test-feature")

        # Create spec
        manager.create_spec("test-feature", "Test")

        # Now exists
        assert manager.spec_exists("test-feature")

        # Delete spec
        manager.delete_spec("test-feature")

        # Doesn't exist again
        assert not manager.spec_exists("test-feature")

    def test_get_spec_files_status(self, temp_specs_dir):
        """Test getting spec files status."""
        manager = SpecManager(temp_specs_dir)

        # Create spec
        manager.create_spec("test-feature", "Test")
        spec_dir = temp_specs_dir / "test-feature"

        # Initially no files
        status = manager.get_spec_files_status("test-feature")
        assert status == {"requirements": False, "design": False, "tasks": False}

        # Add requirements file
        (spec_dir / "requirements.md").write_text("# Requirements")
        status = manager.get_spec_files_status("test-feature")
        assert status["requirements"] is True
        assert status["design"] is False
        assert status["tasks"] is False

        # Add design file
        (spec_dir / "design.md").write_text("# Design")
        status = manager.get_spec_files_status("test-feature")
        assert status["requirements"] is True
        assert status["design"] is True
        assert status["tasks"] is False

        # Add tasks file
        (spec_dir / "tasks.md").write_text("# Tasks")
        status = manager.get_spec_files_status("test-feature")
        assert status["requirements"] is True
        assert status["design"] is True
        assert status["tasks"] is True

    def test_metadata_registry_corruption_handling(self, temp_specs_dir):
        """Test handling of corrupted metadata registry."""
        manager = SpecManager(temp_specs_dir)

        # Create corrupted metadata file
        metadata_file = temp_specs_dir / ".spec-metadata.json"
        metadata_file.write_text("invalid json content")

        # Should handle gracefully and return empty registry
        registry = manager._load_metadata_registry()
        assert registry == {}

        # Should still be able to create specs
        spec = manager.create_spec("test-feature", "Test")
        assert spec.feature_name == "test-feature"

    def test_determine_current_phase(self, temp_specs_dir):
        """Test phase determination logic."""
        manager = SpecManager(temp_specs_dir)
        spec_dir = temp_specs_dir / "test-spec"
        spec_dir.mkdir()

        # No files - should be REQUIREMENTS
        phase = manager._determine_current_phase(spec_dir)
        assert phase == Phase.REQUIREMENTS

        # Only requirements - should be REQUIREMENTS
        (spec_dir / "requirements.md").write_text("# Requirements")
        phase = manager._determine_current_phase(spec_dir)
        assert phase == Phase.REQUIREMENTS

        # Requirements + Design - should be DESIGN
        (spec_dir / "design.md").write_text("# Design")
        phase = manager._determine_current_phase(spec_dir)
        assert phase == Phase.DESIGN

        # All files - should be TASKS
        (spec_dir / "tasks.md").write_text("# Tasks")
        phase = manager._determine_current_phase(spec_dir)
        assert phase == Phase.TASKS

    def test_calculate_task_progress(self, temp_specs_dir):
        """Test task progress calculation."""
        manager = SpecManager(temp_specs_dir)
        spec_dir = temp_specs_dir / "test-spec"
        spec_dir.mkdir()

        # No tasks file
        progress = manager._calculate_task_progress(spec_dir)
        assert progress is None

        # Empty tasks file
        (spec_dir / "tasks.md").write_text("")
        progress = manager._calculate_task_progress(spec_dir)
        assert progress is None

        # Tasks with no checkboxes
        (spec_dir / "tasks.md").write_text("# Tasks\n\nSome text without tasks")
        progress = manager._calculate_task_progress(spec_dir)
        assert progress is None

        # Tasks with checkboxes
        tasks_content = """
# Tasks

- [x] Completed task 1
- [ ] Incomplete task 1
- [x] Completed task 2
- [ ] Incomplete task 2
- [ ] Incomplete task 3
"""
        (spec_dir / "tasks.md").write_text(tasks_content)
        progress = manager._calculate_task_progress(spec_dir)
        assert progress == "2/5 completed"


class TestSpecError:
    """Test SpecError exception class."""

    def test_spec_error_basic(self):
        """Test basic SpecError creation."""
        error = SpecError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.details == {}

    def test_spec_error_with_code_and_details(self):
        """Test SpecError with custom code and details."""
        details = {"feature_name": "test", "path": "/tmp/test"}
        error = SpecError(
            "Custom error message", error_code="CUSTOM_ERROR", details=details
        )

        assert error.message == "Custom error message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details
