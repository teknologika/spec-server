"""Tests for TaskRenderer component."""


from src.spec_server.models import ContentBlock, TaskItem, TaskStatus
from src.spec_server.task_renderer import TaskRenderer


class TestTaskRenderer:
    """Test cases for TaskRenderer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = TaskRenderer()

        # Sample tasks for testing
        self.sample_tasks = [
            TaskItem(
                identifier="1",
                description="Implement user authentication",
                status="completed",
                requirements_refs=["1.1", "1.2"],
            ),
            TaskItem(
                identifier="1.1",
                description="Create login form",
                status="completed",
                requirements_refs=["1.1"],
            ),
            TaskItem(
                identifier="1.2",
                description="Add logout functionality",
                status="in_progress",
                requirements_refs=["1.2"],
            ),
            TaskItem(
                identifier="2",
                description="Database setup",
                status="not_started",
                requirements_refs=["2.1"],
            ),
        ]

    def test_render_tasks_basic(self):
        """Test basic task rendering."""
        rendered = self.renderer.render_tasks(self.sample_tasks)

        # Should include header
        assert "# Implementation Plan" in rendered

        # Should include all tasks
        assert "1. Implement user authentication" in rendered
        assert "1.1. Create login form" in rendered
        assert "1.2. Add logout functionality" in rendered
        assert "2. Database setup" in rendered

        # Should include status indicators
        assert "[x]" in rendered  # Completed tasks
        assert "[-]" in rendered  # In progress tasks
        assert "[ ]" in rendered  # Not started tasks

    def test_render_empty_tasks(self):
        """Test rendering empty task list."""
        rendered = self.renderer.render_tasks([])

        assert "# Implementation Plan" in rendered
        assert "No tasks defined" in rendered

    def test_status_symbols(self):
        """Test that status symbols are rendered correctly."""
        tasks = [
            TaskItem(identifier="1", description="Not started", status="not_started"),
            TaskItem(identifier="2", description="In progress", status="in_progress"),
            TaskItem(identifier="3", description="Completed", status="completed"),
        ]

        rendered = self.renderer.render_tasks(tasks)

        # Check status symbols
        lines = rendered.split("\n")
        not_started_line = next(line for line in lines if "Not started" in line)
        in_progress_line = next(line for line in lines if "In progress" in line)
        completed_line = next(line for line in lines if "Completed" in line)

        assert "[ ]" in not_started_line
        assert "[-]" in in_progress_line
        assert "[x]" in completed_line

    def test_hierarchical_rendering(self):
        """Test hierarchical task rendering with proper indentation."""
        rendered = self.renderer.render_tasks(self.sample_tasks)
        lines = rendered.split("\n")

        # Find task lines
        task_1_line = next(line for line in lines if "1. Implement user authentication" in line)
        task_1_1_line = next(line for line in lines if "1.1. Create login form" in line)
        task_1_2_line = next(line for line in lines if "1.2. Add logout functionality" in line)
        task_2_line = next(line for line in lines if "2. Database setup" in line)

        # Check indentation (subtasks should be indented)
        assert not task_1_line.startswith("  ")  # Top level, no indent
        assert task_1_1_line.startswith("  ")  # Subtask, indented
        assert task_1_2_line.startswith("  ")  # Subtask, indented
        assert not task_2_line.startswith("  ")  # Top level, no indent

    def test_requirements_references(self):
        """Test that requirements references are included."""
        rendered = self.renderer.render_tasks(self.sample_tasks)

        # Should include requirements references
        assert "Requirements: 1.1, 1.2" in rendered
        assert "Requirements: 1.1" in rendered
        assert "Requirements: 1.2" in rendered
        assert "Requirements: 2.1" in rendered

    def test_requirements_references_formatting(self):
        """Test requirements references formatting."""
        task_with_tbd = TaskItem(
            identifier="1",
            description="Task with TBD requirements",
            status="not_started",
            requirements_refs=["[TBD]"],
        )

        task_without_reqs = TaskItem(
            identifier="2",
            description="Task without requirements",
            status="not_started",
            requirements_refs=[],
        )

        rendered = self.renderer.render_tasks([task_with_tbd, task_without_reqs])

        # TBD requirements should not be shown
        assert "Requirements: [TBD]" not in rendered

        # Tasks without requirements should not show requirements line
        lines = rendered.split("\n")
        task_2_area = []
        in_task_2 = False
        for line in lines:
            if "2. Task without requirements" in line:
                in_task_2 = True
            elif in_task_2 and line.strip().startswith("- ["):
                break  # Next task started
            if in_task_2:
                task_2_area.append(line)

        task_2_text = "\n".join(task_2_area)
        assert "Requirements:" not in task_2_text

    def test_sort_tasks_hierarchically(self):
        """Test hierarchical task sorting."""
        unsorted_tasks = [
            TaskItem(identifier="2", description="Second", status="not_started"),
            TaskItem(identifier="1.1", description="First sub", status="not_started"),
            TaskItem(identifier="1", description="First", status="not_started"),
            TaskItem(identifier="1.2", description="Second sub", status="not_started"),
            TaskItem(identifier="10", description="Tenth", status="not_started"),
        ]

        sorted_tasks = self.renderer._sort_tasks_hierarchically(unsorted_tasks)

        # Check order
        identifiers = [task.identifier for task in sorted_tasks]
        assert identifiers == ["1", "1.1", "1.2", "2", "10"]

    def test_extract_sort_key(self):
        """Test sort key extraction for proper ordering."""
        # Test numeric identifiers
        assert self.renderer._extract_sort_key("1") == (1,)
        assert self.renderer._extract_sort_key("1.1") == (1, 1)
        assert self.renderer._extract_sort_key("1.2") == (1, 2)
        assert self.renderer._extract_sort_key("2") == (2,)
        assert self.renderer._extract_sort_key("10") == (10,)
        assert self.renderer._extract_sort_key("1.10") == (1, 10)

        # Test non-numeric identifiers (should fallback)
        non_numeric_key = self.renderer._extract_sort_key("abc")
        assert non_numeric_key[0] == float("inf")
        assert non_numeric_key[1] == "abc"

    def test_calculate_hierarchy_level(self):
        """Test hierarchy level calculation."""
        assert self.renderer._calculate_hierarchy_level("1") == 1
        assert self.renderer._calculate_hierarchy_level("1.1") == 2
        assert self.renderer._calculate_hierarchy_level("1.1.1") == 3
        assert self.renderer._calculate_hierarchy_level("2.3.4.5") == 4

    def test_render_single_task(self):
        """Test rendering of individual tasks."""
        task = TaskItem(
            identifier="1.1",
            description="Test task",
            status="completed",
            requirements_refs=["1.1", "1.2"],
        )

        rendered = self.renderer._render_single_task(task)

        # Should include proper formatting
        assert "  - [x] 1.1. Test task" in rendered
        assert "    - _Requirements: 1.1, 1.2_" in rendered

    def test_render_task_summary(self):
        """Test task summary generation."""
        summary = self.renderer.render_task_summary(self.sample_tasks)

        # Should include counts
        assert "Total tasks: 4" in summary
        assert "Completed: 2 (50.0%)" in summary
        assert "In progress: 1" in summary
        assert "Not started: 1" in summary

    def test_render_task_summary_empty(self):
        """Test task summary with empty task list."""
        summary = self.renderer.render_task_summary([])
        assert "No tasks defined" in summary

    def test_render_task_by_status(self):
        """Test rendering tasks filtered by status."""
        completed_tasks = self.renderer.render_task_by_status(self.sample_tasks, TaskStatus.COMPLETED)

        # Should include header
        assert "# Completed Tasks" in completed_tasks

        # Should only include completed tasks
        assert "1. Implement user authentication" in completed_tasks
        assert "1.1. Create login form" in completed_tasks

        # Should not include other status tasks
        assert "1.2. Add logout functionality" not in completed_tasks
        assert "2. Database setup" not in completed_tasks

    def test_render_task_by_status_empty(self):
        """Test rendering tasks by status when none match."""
        # No tasks have 'blocked' status
        blocked_tasks = self.renderer.render_task_by_status(self.sample_tasks, "blocked")

        assert "No tasks with status: blocked" in blocked_tasks

    def test_validate_rendered_output(self):
        """Test output validation."""
        rendered = self.renderer.render_tasks(self.sample_tasks)
        errors = self.renderer.validate_rendered_output(rendered)

        # Should have no validation errors for properly rendered output
        assert len(errors) == 0

    def test_preserve_content_blocks(self):
        """Test that additional content blocks are preserved."""
        content_blocks = [
            ContentBlock(
                content="This is additional task content.",
                content_type="task",
                confidence=0.8,
                suggested_location="tasks",
                line_number=1,
            ),
            ContentBlock(
                content="This should not be included.",
                content_type="design",
                confidence=0.9,
                suggested_location="design",
                line_number=2,
            ),
        ]

        rendered = self.renderer.render_tasks(self.sample_tasks, content_blocks)

        # Should include task content
        assert "This is additional task content" in rendered
        assert "## Additional Content" in rendered

        # Should not include non-task content
        assert "This should not be included" not in rendered
