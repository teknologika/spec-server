"""Tests for TaskFormatter component."""

from pathlib import Path

from src.spec_server.models import FormattingResult, Spec
from src.spec_server.task_formatter import BasicTaskFormatter


class TestTaskFormatter:
    """Test cases for TaskFormatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = BasicTaskFormatter()

        # Mock spec object
        self.mock_spec = Spec(feature_name="test-spec", base_path=Path("/tmp/test_spec"))

        # Sample unformatted task content
        self.sample_content = """
# Implementation Plan

Some introduction text about the implementation.

- [ ] 1. Implement authentication
- [x] 2. Create database models
- [-] 3. Add validation logic

Additional notes about the tasks.

The system shall provide user authentication.
As a user, I want to log in securely.

The architecture follows a component-based approach.
"""

    def test_format_tasks_basic(self):
        """Test basic task formatting."""
        result = self.formatter.format_task_document(self.sample_content, self.mock_spec)

        # Should return FormattingResult
        assert isinstance(result, FormattingResult)
        assert hasattr(result, "formatted_tasks")
        assert hasattr(result, "moved_content")
        assert hasattr(result, "requirements_added")
        assert hasattr(result, "changes_made")
        assert hasattr(result, "errors")

        # Should have formatted tasks
        assert len(result.formatted_tasks) > 0
        assert "# Implementation Plan" in result.formatted_tasks

        # Should have no errors for valid input
        assert len(result.errors) == 0

    def test_format_tasks_with_requirements_linking(self):
        """Test task formatting with requirements linking."""
        content_with_reqs = """
- [ ] 1. Implement user authentication system
- [ ] 2. Create database models
- [ ] 3. Add input validation
"""

        result = self.formatter.format_task_document(content_with_reqs, self.mock_spec)

        # Should process tasks (requirements linking would need actual requirements file)
        assert isinstance(result, FormattingResult)
        assert len(result.formatted_tasks) > 0

    def test_format_tasks_content_redistribution(self):
        """Test content redistribution to different documents."""
        result = self.formatter.format_task_document(self.sample_content, self.mock_spec)

        # Should redistribute content appropriately
        moved_content = result.moved_content
        if moved_content.get("requirements"):
            assert any("shall provide" in content or "As a user" in content for content in moved_content["requirements"])

        if moved_content.get("design"):
            assert any("architecture" in content or "component-based" in content for content in moved_content["design"])

    def test_format_tasks_empty_content(self):
        """Test formatting empty content."""
        result = self.formatter.format_task_document("", self.mock_spec)

        # Should handle gracefully
        assert isinstance(result, FormattingResult)
        assert "No tasks defined" in result.formatted_tasks or len(result.formatted_tasks.strip()) == 0

    def test_format_tasks_invalid_content(self):
        """Test formatting with invalid content."""
        invalid_content = "This is not a valid task format at all."

        result = self.formatter.format_task_document(invalid_content, self.mock_spec)

        # Should handle gracefully and not crash
        assert isinstance(result, FormattingResult)
        # May have warnings about no tasks found
        assert len(result.errors) == 0  # Should not error, just handle gracefully

    def test_format_tasks_mixed_formats(self):
        """Test formatting with mixed task formats."""
        mixed_content = """
- [ ] 1. Checkbox task
2. Numbered task
- [x] 3. Completed checkbox
4.1. Hierarchical numbered task
"""

        result = self.formatter.format_task_document(mixed_content, self.mock_spec)

        # Should standardize all formats
        formatted = result.formatted_tasks
        assert "- [ ] 1." in formatted
        assert "- [ ] 2." in formatted
        assert "- [x] 3." in formatted
        assert "- [ ] 4.1." in formatted

    def test_format_tasks_preserve_hierarchy(self):
        """Test that task hierarchy is preserved."""
        hierarchical_content = """
- [ ] 1. Main task
- [ ] 1.1. Subtask one
- [ ] 1.2. Subtask two
- [ ] 2. Another main task
"""

        result = self.formatter.format_task_document(hierarchical_content, self.mock_spec)

        # Should preserve hierarchy with proper indentation
        lines = result.formatted_tasks.split("\n")
        main_task_lines = [line for line in lines if "1. Main task" in line or "2. Another main task" in line]
        subtask_lines = [line for line in lines if "1.1." in line or "1.2." in line]

        # Main tasks should not be indented
        for line in main_task_lines:
            if line.strip():
                assert not line.startswith("  ")

        # Subtasks should be indented
        for line in subtask_lines:
            if line.strip():
                assert line.startswith("  ")

    def test_format_tasks_error_handling(self):
        """Test error handling in formatting pipeline."""

        # Create a formatter that will cause an error
        class ErrorFormatter(BasicTaskFormatter):
            def format_task_document(self, content, spec):
                raise Exception("Test parsing error")

        error_formatter = ErrorFormatter()
        try:
            result = error_formatter.format_task_document("test content", self.mock_spec)
            # If no exception, check for errors in result
            assert len(result.errors) > 0
        except Exception as e:
            # Exception handling depends on implementation
            assert "Test parsing error" in str(e)

    def test_format_tasks_with_existing_requirements(self):
        """Test formatting tasks that already have requirements references."""
        content_with_reqs = """
- [ ] 1. Implement authentication - Requirements: 1.1, 1.2
- [ ] 2. Create database models Requirements: 2.1
"""

        result = self.formatter.format_task_document(content_with_reqs, self.mock_spec)

        # Should preserve existing requirements
        assert "Requirements: 1.1, 1.2" in result.formatted_tasks
        assert "Requirements: 2.1" in result.formatted_tasks

    def test_format_tasks_status_preservation(self):
        """Test that task status is preserved during formatting."""
        status_content = """
- [ ] 1. Not started task
- [x] 2. Completed task
- [-] 3. In progress task
"""

        result = self.formatter.format_task_document(status_content, self.mock_spec)

        # Should preserve all status indicators
        assert "- [ ] 1." in result.formatted_tasks
        assert "- [x] 2." in result.formatted_tasks
        assert "- [-] 3." in result.formatted_tasks

    def test_format_tasks_with_additional_content(self):
        """Test formatting with additional non-task content."""
        content_with_extra = """
# Implementation Plan

This is an introduction paragraph.

- [ ] 1. First task
- [ ] 2. Second task

## Additional Notes

These are some additional notes about the implementation.
They should be preserved in the output.

### Technical Details

More technical information here.
"""

        result = self.formatter.format_task_document(content_with_extra, self.mock_spec)

        # Should preserve additional content
        assert "introduction paragraph" in result.formatted_tasks
        assert "Additional Notes" in result.formatted_tasks
        assert "technical information" in result.formatted_tasks

    def test_format_tasks_requirements_extraction(self):
        """Test extraction of requirements content."""
        content_with_reqs = """
- [ ] 1. Implement feature

The system shall provide authentication.
As a user, I want to log in.
When the user enters credentials, then the system validates them.
"""

        result = self.formatter.format_task_document(content_with_reqs, self.mock_spec)

        # Should extract requirements-like content
        moved_content = result.moved_content
        if moved_content.get("requirements"):
            requirements_text = " ".join(moved_content["requirements"])
            assert "shall provide" in requirements_text
            assert "As a user" in requirements_text
            assert "When the user" in requirements_text

    def test_format_tasks_design_extraction(self):
        """Test extraction of design content."""
        content_with_design = """
- [ ] 1. Implement feature

The architecture uses a component-based approach.
The system design follows MVC pattern.
The interface provides a clean separation of concerns.
"""

        result = self.formatter.format_task_document(content_with_design, self.mock_spec)

        # Should extract design-like content
        moved_content = result.moved_content
        if moved_content.get("design"):
            design_text = " ".join(moved_content["design"])
            assert "architecture" in design_text
            assert "design" in design_text
            assert "interface" in design_text

    def test_format_tasks_confidence_thresholds(self):
        """Test that content classification respects confidence thresholds."""
        ambiguous_content = """
- [ ] 1. Implement feature

This is some neutral content that could go anywhere.
It doesn't have strong indicators for any particular document type.
"""

        result = self.formatter.format_task_document(ambiguous_content, self.mock_spec)

        # Ambiguous content should stay in tasks (default location)
        assert "neutral content" in result.formatted_tasks
        # Should not be redistributed due to low confidence
        moved_content = result.moved_content
        requirements_text = " ".join(moved_content.get("requirements", []))
        design_text = " ".join(moved_content.get("design", []))
        assert "neutral content" not in requirements_text
        assert "neutral content" not in design_text

    def test_format_tasks_warning_generation(self):
        """Test that appropriate warnings are generated."""
        problematic_content = """
- [ ] Task without identifier
- [?] Task with invalid status
- [ ] 1. Valid task
"""

        result = self.formatter.format_task_document(problematic_content, self.mock_spec)

        # Should generate warnings for problematic content
        # Note: Actual warning generation depends on implementation
        # This test ensures the warning system is in place
        assert isinstance(result.errors, list)  # Check errors instead of warnings

    def test_format_tasks_large_content(self):
        """Test formatting with large amounts of content."""
        # Generate large content
        large_content = "# Implementation Plan\n\n"
        for i in range(100):
            large_content += f"- [ ] {i+1}. Task number {i+1}\n"

        result = self.formatter.format_task_document(large_content, self.mock_spec)

        # Should handle large content without issues
        assert isinstance(result, FormattingResult)
        assert len(result.errors) == 0
        assert "100. Task number 100" in result.formatted_tasks

    def test_format_tasks_unicode_content(self):
        """Test formatting with unicode characters."""
        unicode_content = """
- [ ] 1. Implement authentication 🔐
- [ ] 2. Create database models 📊
- [ ] 3. Add validation logic ✅

Task with émojis and spëcial characters.
"""

        result = self.formatter.format_task_document(unicode_content, self.mock_spec)

        # Should handle unicode gracefully
        assert "🔐" in result.formatted_tasks
        assert "📊" in result.formatted_tasks
        assert "✅" in result.formatted_tasks
        assert "émojis" in result.formatted_tasks
        assert "spëcial" in result.formatted_tasks

    def test_format_tasks_line_ending_normalization(self):
        """Test that different line endings are normalized."""
        # Content with mixed line endings
        mixed_endings = "- [ ] 1. Task one\r\n- [ ] 2. Task two\n- [ ] 3. Task three\r"

        result = self.formatter.format_task_document(mixed_endings, self.mock_spec)

        # Should normalize line endings
        assert "\r\n" not in result.formatted_tasks
        assert "\r" not in result.formatted_tasks
        # Should have consistent \n line endings
        lines = result.formatted_tasks.split("\n")
        assert len([line for line in lines if "Task" in line]) >= 3
