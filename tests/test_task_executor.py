"""
Unit tests for TaskExecutor class.
"""

import pytest
from pathlib import Path

from spec_server.models import Spec, Task, TaskStatus, Phase
from spec_server.task_executor import TaskExecutor, TaskExecutionContext


class TestTaskExecutor:
    """Test TaskExecutor class."""

    def test_task_executor_initialization(self):
        """Test TaskExecutor initialization."""
        executor = TaskExecutor()
        assert executor is not None

    def test_parse_tasks_empty_content(self):
        """Test parsing tasks from empty content."""
        executor = TaskExecutor()
        tasks = executor.parse_tasks("")
        assert len(tasks) == 0

    def test_parse_tasks_no_tasks(self):
        """Test parsing content with no tasks."""
        executor = TaskExecutor()
        content = """
        # Implementation Plan
        
        This is just regular text with no tasks.
        """
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 0

    def test_parse_tasks_single_task(self):
        """Test parsing a single task."""
        executor = TaskExecutor()
        content = """
        # Implementation Plan
        
        - [ ] 1 Create basic structure
          - Set up project files
          - _Requirements: 1.1, 1.2_
        """
        
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task.identifier == "1"
        assert task.description == "Create basic structure"
        assert task.status == TaskStatus.NOT_STARTED.value
        assert task.requirements_refs == ["1.1", "1.2"]
        assert task.parent_task is None
        assert task.sub_tasks == []

    def test_parse_tasks_multiple_tasks(self):
        """Test parsing multiple tasks."""
        executor = TaskExecutor()
        content = """
        # Implementation Plan
        
        - [ ] 1 First task
          - _Requirements: 1.1_
        - [x] 2 Second task (completed)
          - _Requirements: 2.1, 2.2_
        - [-] 3 Third task (in progress)
          - _Requirements: 3.1_
        """
        
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 3
        
        assert tasks[0].identifier == "1"
        assert tasks[0].status == TaskStatus.NOT_STARTED.value
        assert tasks[0].requirements_refs == ["1.1"]
        
        assert tasks[1].identifier == "2"
        assert tasks[1].status == TaskStatus.COMPLETED.value
        assert tasks[1].requirements_refs == ["2.1", "2.2"]
        
        assert tasks[2].identifier == "3"
        assert tasks[2].status == TaskStatus.IN_PROGRESS.value
        assert tasks[2].requirements_refs == ["3.1"]

    def test_parse_tasks_with_hierarchy(self):
        """Test parsing tasks with parent-child hierarchy."""
        executor = TaskExecutor()
        content = """
        # Implementation Plan
        
        - [ ] 1 Parent task
          - _Requirements: 1.1_
        - [ ] 1.1 First sub-task
          - _Requirements: 1.1.1_
        - [ ] 1.2 Second sub-task
          - _Requirements: 1.1.2_
        - [ ] 2 Another parent task
          - _Requirements: 2.1_
        - [ ] 2.1 Sub-task of second parent
          - _Requirements: 2.1.1_
        """
        
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 5
        
        # Check parent task
        parent1 = next(t for t in tasks if t.identifier == "1")
        assert parent1.parent_task is None
        assert set(parent1.sub_tasks) == {"1.1", "1.2"}
        
        # Check sub-tasks
        sub1_1 = next(t for t in tasks if t.identifier == "1.1")
        assert sub1_1.parent_task == "1"
        assert sub1_1.sub_tasks == []
        
        sub1_2 = next(t for t in tasks if t.identifier == "1.2")
        assert sub1_2.parent_task == "1"
        assert sub1_2.sub_tasks == []
        
        # Check second parent
        parent2 = next(t for t in tasks if t.identifier == "2")
        assert parent2.parent_task is None
        assert parent2.sub_tasks == ["2.1"]
        
        sub2_1 = next(t for t in tasks if t.identifier == "2.1")
        assert sub2_1.parent_task == "2"

    def test_parse_tasks_deep_hierarchy(self):
        """Test parsing tasks with deeper hierarchy."""
        executor = TaskExecutor()
        content = """
        - [ ] 1 Level 1
        - [ ] 1.1 Level 2
        - [ ] 1.1.1 Level 3
        - [ ] 1.1.1.1 Level 4
        """
        
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 4
        
        level1 = next(t for t in tasks if t.identifier == "1")
        level2 = next(t for t in tasks if t.identifier == "1.1")
        level3 = next(t for t in tasks if t.identifier == "1.1.1")
        level4 = next(t for t in tasks if t.identifier == "1.1.1.1")
        
        assert level1.parent_task is None
        assert level2.parent_task == "1"
        assert level3.parent_task == "1.1"
        assert level4.parent_task == "1.1.1"
        
        assert level1.sub_tasks == ["1.1"]
        assert level2.sub_tasks == ["1.1.1"]
        assert level3.sub_tasks == ["1.1.1.1"]
        assert level4.sub_tasks == []

    def test_parse_tasks_complex_requirements_refs(self):
        """Test parsing tasks with complex requirements references."""
        executor = TaskExecutor()
        content = """
        - [ ] 1 Task with multiple refs
          - Some description
          - _Requirements: 1.1, 2.3, 4.5.6_
        - [ ] 2 Task with single ref
          - _Requirements: 3.2_
        - [ ] 3 Task with no refs
          - Just a description
        """
        
        tasks = executor.parse_tasks(content)
        assert len(tasks) == 3
        
        assert tasks[0].requirements_refs == ["1.1", "2.3", "4.5.6"]
        assert tasks[1].requirements_refs == ["3.2"]
        assert tasks[2].requirements_refs == []

    def test_get_next_task_simple(self):
        """Test getting next task from simple list."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First", status=TaskStatus.COMPLETED),
            Task(identifier="2", description="Second", status=TaskStatus.NOT_STARTED),
            Task(identifier="3", description="Third", status=TaskStatus.NOT_STARTED),
        ]
        
        next_task = executor.get_next_task(tasks)
        assert next_task is not None
        assert next_task.identifier == "2"

    def test_get_next_task_with_hierarchy(self):
        """Test getting next task respecting hierarchy."""
        executor = TaskExecutor()
        
        tasks = [
            Task(
                identifier="1",
                description="Parent",
                status=TaskStatus.NOT_STARTED,
                sub_tasks=["1.1", "1.2"],
            ),
            Task(
                identifier="1.1",
                description="Sub 1",
                status=TaskStatus.NOT_STARTED,
                parent_task="1",
            ),
            Task(
                identifier="1.2",
                description="Sub 2",
                status=TaskStatus.NOT_STARTED,
                parent_task="1",
            ),
        ]
        
        # Should return first sub-task, not parent
        next_task = executor.get_next_task(tasks)
        assert next_task is not None
        assert next_task.identifier == "1.1"

    def test_get_next_task_parent_ready(self):
        """Test getting parent task when sub-tasks are complete."""
        executor = TaskExecutor()
        
        tasks = [
            Task(
                identifier="1",
                description="Parent",
                status=TaskStatus.NOT_STARTED,
                sub_tasks=["1.1", "1.2"],
            ),
            Task(
                identifier="1.1",
                description="Sub 1",
                status=TaskStatus.COMPLETED,
                parent_task="1",
            ),
            Task(
                identifier="1.2",
                description="Sub 2",
                status=TaskStatus.COMPLETED,
                parent_task="1",
            ),
        ]
        
        # Should return parent task since sub-tasks are complete
        next_task = executor.get_next_task(tasks)
        assert next_task is not None
        assert next_task.identifier == "1"

    def test_get_next_task_in_progress(self):
        """Test getting in-progress task when no not-started tasks."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First", status=TaskStatus.COMPLETED),
            Task(identifier="2", description="Second", status=TaskStatus.IN_PROGRESS),
            Task(identifier="3", description="Third", status=TaskStatus.COMPLETED),
        ]
        
        next_task = executor.get_next_task(tasks)
        assert next_task is not None
        assert next_task.identifier == "2"

    def test_get_next_task_all_complete(self):
        """Test getting next task when all are complete."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First", status=TaskStatus.COMPLETED),
            Task(identifier="2", description="Second", status=TaskStatus.COMPLETED),
        ]
        
        next_task = executor.get_next_task(tasks)
        assert next_task is None

    def test_update_task_status_not_started_to_in_progress(self):
        """Test updating task status from not started to in progress."""
        executor = TaskExecutor()
        
        content = """
        # Implementation Plan
        
        - [ ] 1 First task
        - [ ] 2 Second task
        """
        
        updated_content = executor.update_task_status(content, "1", TaskStatus.IN_PROGRESS)
        
        assert "- [-] 1 First task" in updated_content
        assert "- [ ] 2 Second task" in updated_content

    def test_update_task_status_in_progress_to_completed(self):
        """Test updating task status from in progress to completed."""
        executor = TaskExecutor()
        
        content = """
        # Implementation Plan
        
        - [-] 1 First task
        - [ ] 2 Second task
        """
        
        updated_content = executor.update_task_status(content, "1", TaskStatus.COMPLETED)
        
        assert "- [x] 1 First task" in updated_content
        assert "- [ ] 2 Second task" in updated_content

    def test_update_task_status_completed_to_not_started(self):
        """Test updating task status from completed back to not started."""
        executor = TaskExecutor()
        
        content = """
        - [x] 1 Completed task
        - [ ] 2 Not started task
        """
        
        updated_content = executor.update_task_status(content, "1", TaskStatus.NOT_STARTED)
        
        assert "- [ ] 1 Completed task" in updated_content
        assert "- [ ] 2 Not started task" in updated_content

    def test_update_task_status_task_not_found(self):
        """Test updating status of non-existent task."""
        executor = TaskExecutor()
        
        content = """
        - [ ] 1 First task
        - [ ] 2 Second task
        """
        
        with pytest.raises(ValueError) as exc_info:
            executor.update_task_status(content, "999", TaskStatus.COMPLETED)
        
        assert "Task identifier '999' not found" in str(exc_info.value)

    def test_update_task_status_with_indentation(self):
        """Test updating task status preserves indentation."""
        executor = TaskExecutor()
        
        content = """
        # Implementation Plan
        
        - [ ] 1 Parent task
        - [ ] 1.1 Sub task with indentation
          - Some details
        """
        
        updated_content = executor.update_task_status(content, "1.1", TaskStatus.COMPLETED)
        
        # Should preserve the original indentation
        assert "- [x] 1.1 Sub task with indentation" in updated_content

    def test_execute_task_context_all_files_exist(self, temp_specs_dir):
        """Test creating execution context when all files exist."""
        executor = TaskExecutor()
        
        # Create spec directory and files
        spec_dir = temp_specs_dir / "test-feature"
        spec_dir.mkdir()
        
        requirements_content = "# Requirements\nTest requirements"
        design_content = "# Design\nTest design"
        tasks_content = "# Tasks\n- [ ] 1 Test task"
        
        (spec_dir / "requirements.md").write_text(requirements_content)
        (spec_dir / "design.md").write_text(design_content)
        (spec_dir / "tasks.md").write_text(tasks_content)
        
        spec = Spec(feature_name="test-feature", base_path=spec_dir)
        task = Task(identifier="1", description="Test task")
        
        context = executor.execute_task_context(spec, task)
        
        assert context.spec == spec
        assert context.task == task
        assert context.requirements_content == requirements_content
        assert context.design_content == design_content
        assert context.tasks_content == tasks_content

    def test_execute_task_context_missing_files(self, temp_specs_dir):
        """Test creating execution context when files are missing."""
        executor = TaskExecutor()
        
        spec_dir = temp_specs_dir / "test-feature"
        spec_dir.mkdir()
        
        spec = Spec(feature_name="test-feature", base_path=spec_dir)
        task = Task(identifier="1", description="Test task")
        
        context = executor.execute_task_context(spec, task)
        
        assert context.spec == spec
        assert context.task == task
        assert context.requirements_content is None
        assert context.design_content is None
        assert context.tasks_content is None

    def test_get_task_by_identifier_found(self):
        """Test finding task by identifier."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First"),
            Task(identifier="2.1", description="Second"),
            Task(identifier="3", description="Third"),
        ]
        
        task = executor.get_task_by_identifier(tasks, "2.1")
        assert task is not None
        assert task.identifier == "2.1"
        assert task.description == "Second"

    def test_get_task_by_identifier_not_found(self):
        """Test finding non-existent task by identifier."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First"),
            Task(identifier="2", description="Second"),
        ]
        
        task = executor.get_task_by_identifier(tasks, "999")
        assert task is None

    def test_get_task_progress_empty(self):
        """Test getting progress from empty task list."""
        executor = TaskExecutor()
        
        completed, total = executor.get_task_progress([])
        assert completed == 0
        assert total == 0

    def test_get_task_progress_mixed_status(self):
        """Test getting progress from mixed status tasks."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="First", status=TaskStatus.COMPLETED),
            Task(identifier="2", description="Second", status=TaskStatus.NOT_STARTED),
            Task(identifier="3", description="Third", status=TaskStatus.COMPLETED),
            Task(identifier="4", description="Fourth", status=TaskStatus.IN_PROGRESS),
        ]
        
        completed, total = executor.get_task_progress(tasks)
        assert completed == 2
        assert total == 4

    def test_validate_task_hierarchy_valid(self):
        """Test validating valid task hierarchy."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="Parent", sub_tasks=["1.1", "1.2"]),
            Task(identifier="1.1", description="Sub 1", parent_task="1"),
            Task(identifier="1.2", description="Sub 2", parent_task="1"),
            Task(identifier="2", description="Independent"),
        ]
        
        errors = executor.validate_task_hierarchy(tasks)
        assert len(errors) == 0

    def test_validate_task_hierarchy_missing_parent(self):
        """Test validating hierarchy with missing parent."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1.1", description="Sub task", parent_task="1"),
            Task(identifier="2", description="Independent"),
        ]
        
        errors = executor.validate_task_hierarchy(tasks)
        assert len(errors) == 1
        assert "non-existent parent 1" in errors[0]

    def test_validate_task_hierarchy_missing_subtask(self):
        """Test validating hierarchy with missing sub-task."""
        executor = TaskExecutor()
        
        tasks = [
            Task(identifier="1", description="Parent", sub_tasks=["1.1", "1.2"]),
            Task(identifier="1.1", description="Sub 1", parent_task="1"),
            # Missing 1.2
        ]
        
        errors = executor.validate_task_hierarchy(tasks)
        assert len(errors) == 1
        assert "non-existent sub-task 1.2" in errors[0]

    def test_get_task_dependencies_no_subtasks(self):
        """Test getting dependencies for task with no sub-tasks."""
        executor = TaskExecutor()
        
        task = Task(identifier="1", description="Independent task")
        all_tasks = [task]
        
        dependencies = executor.get_task_dependencies(task, all_tasks)
        assert len(dependencies) == 0

    def test_get_task_dependencies_with_subtasks(self):
        """Test getting dependencies for task with sub-tasks."""
        executor = TaskExecutor()
        
        parent = Task(identifier="1", description="Parent", sub_tasks=["1.1", "1.2"])
        sub1 = Task(identifier="1.1", description="Sub 1", parent_task="1")
        sub2 = Task(identifier="1.2", description="Sub 2", parent_task="1")
        
        all_tasks = [parent, sub1, sub2]
        
        dependencies = executor.get_task_dependencies(parent, all_tasks)
        assert len(dependencies) == 2
        assert sub1 in dependencies
        assert sub2 in dependencies

    def test_can_execute_task_no_dependencies(self):
        """Test checking if task with no dependencies can be executed."""
        executor = TaskExecutor()
        
        task = Task(identifier="1", description="Independent", status=TaskStatus.NOT_STARTED)
        all_tasks = [task]
        
        can_execute = executor.can_execute_task(task, all_tasks)
        assert can_execute is True

    def test_can_execute_task_completed(self):
        """Test checking if completed task can be executed."""
        executor = TaskExecutor()
        
        task = Task(identifier="1", description="Completed", status=TaskStatus.COMPLETED)
        all_tasks = [task]
        
        can_execute = executor.can_execute_task(task, all_tasks)
        assert can_execute is False

    def test_can_execute_task_dependencies_complete(self):
        """Test checking if task can be executed when dependencies are complete."""
        executor = TaskExecutor()
        
        parent = Task(
            identifier="1",
            description="Parent",
            status=TaskStatus.NOT_STARTED,
            sub_tasks=["1.1", "1.2"],
        )
        sub1 = Task(
            identifier="1.1",
            description="Sub 1",
            status=TaskStatus.COMPLETED,
            parent_task="1",
        )
        sub2 = Task(
            identifier="1.2",
            description="Sub 2",
            status=TaskStatus.COMPLETED,
            parent_task="1",
        )
        
        all_tasks = [parent, sub1, sub2]
        
        can_execute = executor.can_execute_task(parent, all_tasks)
        assert can_execute is True

    def test_can_execute_task_dependencies_incomplete(self):
        """Test checking if task can be executed when dependencies are incomplete."""
        executor = TaskExecutor()
        
        parent = Task(
            identifier="1",
            description="Parent",
            status=TaskStatus.NOT_STARTED,
            sub_tasks=["1.1", "1.2"],
        )
        sub1 = Task(
            identifier="1.1",
            description="Sub 1",
            status=TaskStatus.COMPLETED,
            parent_task="1",
        )
        sub2 = Task(
            identifier="1.2",
            description="Sub 2",
            status=TaskStatus.NOT_STARTED,  # Not complete
            parent_task="1",
        )
        
        all_tasks = [parent, sub1, sub2]
        
        can_execute = executor.can_execute_task(parent, all_tasks)
        assert can_execute is False


class TestTaskExecutionContext:
    """Test TaskExecutionContext class."""

    def test_task_execution_context_creation(self):
        """Test creating TaskExecutionContext."""
        spec = Spec(feature_name="test", base_path=Path("/tmp/test"))
        task = Task(identifier="1", description="Test task")
        
        context = TaskExecutionContext(spec, task)
        
        assert context.spec == spec
        assert context.task == task
        assert context.requirements_content is None
        assert context.design_content is None
        assert context.tasks_content is None

    def test_task_execution_context_with_content(self):
        """Test creating TaskExecutionContext with content."""
        spec = Spec(feature_name="test", base_path=Path("/tmp/test"))
        task = Task(identifier="1", description="Test task")
        
        req_content = "Requirements content"
        design_content = "Design content"
        tasks_content = "Tasks content"
        
        context = TaskExecutionContext(
            spec, task, req_content, design_content, tasks_content
        )
        
        assert context.requirements_content == req_content
        assert context.design_content == design_content
        assert context.tasks_content == tasks_content

    def test_get_referenced_requirements_no_refs(self):
        """Test getting referenced requirements when task has no refs."""
        spec = Spec(feature_name="test", base_path=Path("/tmp/test"))
        task = Task(identifier="1", description="Test task")
        
        context = TaskExecutionContext(spec, task, "Requirements content")
        
        refs = context.get_referenced_requirements()
        assert len(refs) == 0

    def test_get_referenced_requirements_no_content(self):
        """Test getting referenced requirements when no requirements content."""
        spec = Spec(feature_name="test", base_path=Path("/tmp/test"))
        task = Task(
            identifier="1", description="Test task", requirements_refs=["1.1", "1.2"]
        )
        
        context = TaskExecutionContext(spec, task)
        
        refs = context.get_referenced_requirements()
        assert len(refs) == 0

    def test_get_referenced_requirements_with_refs(self):
        """Test getting referenced requirements when task has refs."""
        spec = Spec(feature_name="test", base_path=Path("/tmp/test"))
        task = Task(
            identifier="1", description="Test task", requirements_refs=["1.1", "2.3"]
        )
        
        context = TaskExecutionContext(spec, task, "Requirements content")
        
        refs = context.get_referenced_requirements()
        assert len(refs) == 2
        assert "Requirement 1.1" in refs
        assert "Requirement 2.3" in refs


# Integration test with real markdown content
class TestTaskExecutorIntegration:
    """Integration tests for TaskExecutor with realistic content."""

    def test_parse_real_tasks_markdown(self):
        """Test parsing realistic tasks.md content."""
        executor = TaskExecutor()
        
        content = """
# Implementation Plan

- [ ] 1. Set up project structure and dependencies
  - Create Python project with pyproject.toml configuration
  - Install FastMCP, Pydantic, and other core dependencies
  - Set up development environment with testing framework
  - _Requirements: 8.4, 8.5_

- [ ] 2. Implement core data models
- [x] 2.1 Create Pydantic models for spec entities
  - Implement Phase, TaskStatus, Spec, SpecMetadata, Task, and DocumentTemplate models
  - Add validation rules and helper methods to models
  - Write unit tests for model validation and serialization
  - _Requirements: 6.1, 6.2_

- [-] 2.2 Implement file reference system models
  - Create FileReference and FileReferenceResolver classes
  - Implement reference parsing with regex patterns for `#[[file:path]]` syntax
  - Write unit tests for file reference extraction and resolution
  - _Requirements: 7.1, 7.2, 7.3, 7.4_
        """
        
        tasks = executor.parse_tasks(content)
        
        # Should find 4 tasks
        assert len(tasks) == 4
        
        # Check first task
        task1 = next(t for t in tasks if t.identifier == "1")
        assert task1.description == "Set up project structure and dependencies"
        assert task1.status == TaskStatus.NOT_STARTED.value
        assert task1.requirements_refs == ["8.4", "8.5"]
        assert task1.parent_task is None
        assert task1.sub_tasks == []
        
        # Check parent task
        task2 = next(t for t in tasks if t.identifier == "2")
        assert task2.description == "Implement core data models"
        assert task2.status == TaskStatus.NOT_STARTED.value
        assert task2.sub_tasks == ["2.1", "2.2"]
        
        # Check completed sub-task
        task2_1 = next(t for t in tasks if t.identifier == "2.1")
        assert task2_1.status == TaskStatus.COMPLETED.value
        assert task2_1.parent_task == "2"
        assert task2_1.requirements_refs == ["6.1", "6.2"]
        
        # Check in-progress sub-task
        task2_2 = next(t for t in tasks if t.identifier == "2.2")
        assert task2_2.status == TaskStatus.IN_PROGRESS.value
        assert task2_2.parent_task == "2"
        assert task2_2.requirements_refs == ["7.1", "7.2", "7.3", "7.4"]

    def test_workflow_next_task_selection(self):
        """Test realistic workflow for next task selection."""
        executor = TaskExecutor()
        
        # Simulate a project with some completed tasks
        tasks = [
            Task(
                identifier="1",
                description="Setup",
                status=TaskStatus.COMPLETED,
            ),
            Task(
                identifier="2",
                description="Core models",
                status=TaskStatus.NOT_STARTED,
                sub_tasks=["2.1", "2.2"],
            ),
            Task(
                identifier="2.1",
                description="Basic models",
                status=TaskStatus.COMPLETED,
                parent_task="2",
            ),
            Task(
                identifier="2.2",
                description="Advanced models",
                status=TaskStatus.NOT_STARTED,
                parent_task="2",
            ),
            Task(
                identifier="3",
                description="API implementation",
                status=TaskStatus.NOT_STARTED,
            ),
        ]
        
        # Should return 2.2 (remaining sub-task)
        next_task = executor.get_next_task(tasks)
        assert next_task.identifier == "2.2"
        
        # Complete 2.2
        tasks[3].status = TaskStatus.COMPLETED.value
        
        # Should now return 2 (parent task, since sub-tasks are complete)
        next_task = executor.get_next_task(tasks)
        assert next_task.identifier == "2"
        
        # Complete 2
        tasks[1].status = TaskStatus.COMPLETED.value
        
        # Should now return 3 (next independent task)
        next_task = executor.get_next_task(tasks)
        assert next_task.identifier == "3"