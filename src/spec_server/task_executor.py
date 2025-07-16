"""
TaskExecutor implementation for handling task parsing and execution.

This module provides the TaskExecutor class which manages the execution of
individual implementation tasks from the tasks.md file. It parses task hierarchies,
tracks completion status, and provides execution context.
"""

import re
from typing import Dict, List, Optional, Tuple

from .models import Spec, Task, TaskStatus


class TaskExecutionContext:
    """Context information for task execution."""

    def __init__(
        self,
        spec: Spec,
        task: Task,
        requirements_content: Optional[str] = None,
        design_content: Optional[str] = None,
        tasks_content: Optional[str] = None,
    ):
        """
        Initialize task execution context.

        Args:
            spec: The specification containing the task
            task: The task to execute
            requirements_content: Content of requirements.md
            design_content: Content of design.md
            tasks_content: Content of tasks.md
        """
        self.spec = spec
        self.task = task
        self.requirements_content = requirements_content
        self.design_content = design_content
        self.tasks_content = tasks_content

    def get_referenced_requirements(self) -> List[str]:
        """Get the content of requirements referenced by this task."""
        if not self.requirements_content or not self.task.requirements_refs:
            return []

        referenced_content = []
        for ref in self.task.requirements_refs:
            # Extract requirement content based on reference
            # This is a simplified implementation - could be enhanced
            # to parse specific requirement sections
            referenced_content.append(f"Requirement {ref}")

        return referenced_content


class TaskExecutor:
    """
    Manages the execution of individual implementation tasks.

    Parses task hierarchies, tracks completion status, and provides execution
    context by combining information from all three spec documents.
    """

    # Regex patterns for parsing markdown checkbox tasks
    TASK_PATTERN = re.compile(
        r"^(\s*)-\s*\[([x\s-])\]\s*(\d+(?:\.\d+)*\.?)\s+(.+)$", re.MULTILINE
    )
    REQUIREMENTS_REF_PATTERN = re.compile(r"_Requirements:\s*([^_]+)_")
    SUB_BULLET_PATTERN = re.compile(r"^(\s+)-\s+(.+)$", re.MULTILINE)

    def __init__(self):
        """Initialize the TaskExecutor."""
        pass

    def parse_tasks(self, tasks_content: str) -> List[Task]:
        """
        Parse tasks from tasks.md content.

        Args:
            tasks_content: Content of the tasks.md file

        Returns:
            List of parsed Task objects with hierarchy relationships
        """
        tasks = []
        task_hierarchy = {}  # Maps task identifier to Task object

        # Find all task matches
        matches = list(self.TASK_PATTERN.finditer(tasks_content))

        for match in matches:
            # indent = match.group(1)  # Indentation (not used currently)
            status_char = match.group(2)  # x, space, or -
            identifier = match.group(3)  # Task number like "1.2"
            description = match.group(4).strip()  # Task description

            # Determine task status from checkbox
            if status_char == "x":
                status = TaskStatus.COMPLETED
            elif status_char == "-":
                status = TaskStatus.IN_PROGRESS
            else:
                status = TaskStatus.NOT_STARTED

            # Extract requirements references
            requirements_refs = self._extract_requirements_refs(
                tasks_content, match.end()
            )

            # Determine parent task based on identifier
            parent_task = self._determine_parent_task(identifier)

            # Clean up identifier (remove trailing dot)
            clean_identifier = identifier.rstrip(".")

            # Create task object
            task = Task(
                identifier=clean_identifier,
                description=description,
                requirements_refs=requirements_refs,
                status=status,
                parent_task=parent_task,
                sub_tasks=[],  # Will be populated later
            )

            tasks.append(task)
            task_hierarchy[clean_identifier] = task

        # Build parent-child relationships
        self._build_task_hierarchy(tasks, task_hierarchy)

        return tasks

    def _extract_requirements_refs(self, content: str, start_pos: int) -> List[str]:
        """
        Extract requirements references from the task details.

        Args:
            content: Full tasks.md content
            start_pos: Position after the task line

        Returns:
            List of requirement references
        """
        # Look for requirements reference in the next few lines after the task
        lines_to_check = content[start_pos:].split("\n")[:5]  # Check next 5 lines

        for line in lines_to_check:
            match = self.REQUIREMENTS_REF_PATTERN.search(line)
            if match:
                refs_text = match.group(1).strip()
                # Split by comma and clean up
                refs = [ref.strip() for ref in refs_text.split(",")]
                return [ref for ref in refs if ref]

        return []

    def _determine_parent_task(self, identifier: str) -> Optional[str]:
        """
        Determine parent task identifier based on task identifier.

        Args:
            identifier: Task identifier like "1.2.3"

        Returns:
            Parent task identifier or None if top-level task
        """
        # Remove trailing dot if present
        clean_id = identifier.rstrip(".")
        parts = clean_id.split(".")
        if len(parts) <= 1:
            return None

        # Parent is the identifier with the last part removed
        return ".".join(parts[:-1])

    def _build_task_hierarchy(
        self, tasks: List[Task], task_hierarchy: Dict[str, Task]
    ) -> None:
        """
        Build parent-child relationships between tasks.

        Args:
            tasks: List of all tasks
            task_hierarchy: Dictionary mapping identifiers to tasks
        """
        for task in tasks:
            if task.parent_task and task.parent_task in task_hierarchy:
                parent = task_hierarchy[task.parent_task]
                parent.sub_tasks.append(task.identifier)

    def get_next_task(self, tasks: List[Task]) -> Optional[Task]:
        """
        Get the next task that should be executed.

        Args:
            tasks: List of all tasks

        Returns:
            Next task to execute or None if all tasks are complete
        """
        # First, find tasks that are not started and have no incomplete sub-tasks
        for task in tasks:
            if task.status == TaskStatus.NOT_STARTED.value:
                # Check if this task has sub-tasks
                if task.sub_tasks:
                    # Check if all sub-tasks are completed
                    sub_tasks = [t for t in tasks if t.identifier in task.sub_tasks]
                    if all(st.status == TaskStatus.COMPLETED.value for st in sub_tasks):
                        return task
                    # If sub-tasks are not all complete, skip this parent task
                    continue
                else:
                    # No sub-tasks, this task can be executed
                    return task

        # If no not-started tasks, look for in-progress tasks
        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS.value:
                return task

        return None

    def update_task_status(
        self, tasks_content: str, task_identifier: str, status: TaskStatus
    ) -> str:
        """
        Update task status in the tasks.md content.

        Args:
            tasks_content: Current content of tasks.md
            task_identifier: Identifier of task to update
            status: New status for the task

        Returns:
            Updated tasks.md content

        Raises:
            ValueError: If task identifier is not found
        """
        # Map status to checkbox character
        status_chars = {
            TaskStatus.NOT_STARTED: " ",
            TaskStatus.IN_PROGRESS: "-",
            TaskStatus.COMPLETED: "x",
        }

        status_char = status_chars[status]

        # Find the task line and update it
        lines = tasks_content.split("\n")
        updated = False

        for i, line in enumerate(lines):
            # Check if this line contains our task
            match = self.TASK_PATTERN.match(line)
            if match and match.group(3).rstrip(".") == task_identifier:
                # Replace the status character
                indent = match.group(1)
                identifier = match.group(3)
                description = match.group(4)

                lines[i] = f"{indent}- [{status_char}] {identifier} {description}"
                updated = True
                break

        if not updated:
            raise ValueError(f"Task identifier '{task_identifier}' not found")

        return "\n".join(lines)

    def execute_task_context(self, spec: Spec, task: Task) -> TaskExecutionContext:
        """
        Create execution context for a task by loading all spec documents.

        Args:
            spec: The specification containing the task
            task: The task to execute

        Returns:
            TaskExecutionContext with all relevant information
        """
        # Load document contents
        requirements_content = None
        design_content = None
        tasks_content = None

        try:
            if spec.get_requirements_path().exists():
                requirements_content = spec.get_requirements_path().read_text(
                    encoding="utf-8"
                )
        except IOError:
            pass

        try:
            if spec.get_design_path().exists():
                design_content = spec.get_design_path().read_text(encoding="utf-8")
        except IOError:
            pass

        try:
            if spec.get_tasks_path().exists():
                tasks_content = spec.get_tasks_path().read_text(encoding="utf-8")
        except IOError:
            pass

        return TaskExecutionContext(
            spec=spec,
            task=task,
            requirements_content=requirements_content,
            design_content=design_content,
            tasks_content=tasks_content,
        )

    def get_task_by_identifier(
        self, tasks: List[Task], identifier: str
    ) -> Optional[Task]:
        """
        Find a task by its identifier.

        Args:
            tasks: List of tasks to search
            identifier: Task identifier to find

        Returns:
            Task with matching identifier or None if not found
        """
        for task in tasks:
            if task.identifier == identifier:
                return task
        return None

    def get_task_progress(self, tasks: List[Task]) -> Tuple[int, int]:
        """
        Calculate task progress statistics.

        Args:
            tasks: List of tasks

        Returns:
            Tuple of (completed_count, total_count)
        """
        completed = sum(
            1 for task in tasks if task.status == TaskStatus.COMPLETED.value
        )
        total = len(tasks)
        return completed, total

    def validate_task_hierarchy(self, tasks: List[Task]) -> List[str]:
        """
        Validate task hierarchy for consistency.

        Args:
            tasks: List of tasks to validate

        Returns:
            List of validation error messages
        """
        errors = []
        task_ids = {task.identifier for task in tasks}

        for task in tasks:
            # Check if parent task exists
            if task.parent_task and task.parent_task not in task_ids:
                errors.append(
                    f"Task {task.identifier} references non-existent parent {task.parent_task}"
                )

            # Check if sub-tasks exist
            for sub_task_id in task.sub_tasks:
                if sub_task_id not in task_ids:
                    errors.append(
                        f"Task {task.identifier} references non-existent sub-task {sub_task_id}"
                    )

        return errors

    def get_task_dependencies(self, task: Task, all_tasks: List[Task]) -> List[Task]:
        """
        Get all tasks that must be completed before this task can be executed.

        Args:
            task: The task to check dependencies for
            all_tasks: List of all tasks

        Returns:
            List of tasks that are dependencies
        """
        dependencies = []

        # If this task has sub-tasks, they are dependencies
        for sub_task_id in task.sub_tasks:
            sub_task = self.get_task_by_identifier(all_tasks, sub_task_id)
            if sub_task:
                dependencies.append(sub_task)

        return dependencies

    def can_execute_task(self, task: Task, all_tasks: List[Task]) -> bool:
        """
        Check if a task can be executed (all dependencies are complete).

        Args:
            task: The task to check
            all_tasks: List of all tasks

        Returns:
            True if task can be executed, False otherwise
        """
        if task.status == TaskStatus.COMPLETED.value:
            return False

        dependencies = self.get_task_dependencies(task, all_tasks)
        return all(dep.status == TaskStatus.COMPLETED.value for dep in dependencies)
