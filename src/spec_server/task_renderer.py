"""
Task rendering functionality for converting TaskItem objects back to markdown.
"""

import re
from typing import List, Optional

from .models import ContentBlock, TaskItem, TaskStatus


class TaskRenderer:
    """
    Renders TaskItem objects back to standardized markdown format.

    Converts TaskItem objects into consistent markdown task lists with proper
    hierarchy, status indicators, and requirements references.
    """

    def __init__(self) -> None:
        """Initialize the TaskRenderer."""
        # Status symbols mapping
        self.status_symbols = {
            "not_started": "[ ]",
            "in_progress": "[-]",
            "completed": "[x]",
        }

    def render_tasks(self, tasks: List[TaskItem], preserve_content: Optional[List[ContentBlock]] = None) -> str:
        """
        Render a list of TaskItem objects to standardized markdown.

        Args:
            tasks: List of TaskItem objects to render
            preserve_content: Additional content blocks to preserve in output

        Returns:
            Formatted markdown string
        """
        if not tasks:
            return "# Implementation Plan\n\nNo tasks defined."

        output = ["# Implementation Plan", ""]

        # Sort tasks hierarchically (parent tasks first, then their children)
        sorted_tasks = self._sort_tasks_hierarchically(tasks)

        # Render each task
        for i, task in enumerate(sorted_tasks):
            rendered_task = self._render_single_task(task)
            output.append(rendered_task)

            # Add spacing between top-level task groups
            if i < len(sorted_tasks) - 1:
                current_hierarchy = self._calculate_hierarchy_level(task.identifier)
                next_task = sorted_tasks[i + 1]
                next_hierarchy = self._calculate_hierarchy_level(next_task.identifier)

                # Add spacing when transitioning from any task to a top-level task
                # (unless we're going from one top-level task directly to another)
                if next_hierarchy == 1 and not (current_hierarchy == 1 and self._get_task_group(task.identifier) == self._get_task_group(next_task.identifier)):
                    # Only add spacing if we're transitioning between different top-level groups
                    if self._get_task_group(task.identifier) != self._get_task_group(next_task.identifier):
                        output.append("")

        # Add any preserved content blocks
        if preserve_content:
            output.append("")
            output.append("## Additional Content")
            output.append("")
            for block in preserve_content:
                if block.suggested_location == "tasks":
                    output.append(block.content)
                    output.append("")

        # Clean up extra newlines at the end
        while output and output[-1] == "":
            output.pop()

        return "\n".join(output)

    def _sort_tasks_hierarchically(self, tasks: List[TaskItem]) -> List[TaskItem]:
        """
        Sort tasks hierarchically so parent tasks come before their children.

        Args:
            tasks: List of TaskItem objects to sort

        Returns:
            Sorted list of tasks
        """
        # Sort by identifier using natural ordering
        return sorted(tasks, key=lambda t: self._extract_sort_key(t.identifier))

    def _extract_sort_key(self, identifier: str) -> tuple:
        """
        Extract sort key from task identifier for proper ordering.

        Args:
            identifier: Task identifier (e.g., "1", "1.1", "2.3")

        Returns:
            Tuple for sorting
        """
        try:
            # Handle numeric identifiers like "1", "1.1", "2.3"
            parts = identifier.split(".")
            return tuple(int(part) for part in parts)
        except ValueError:
            # Fallback for non-numeric identifiers
            return (float("inf"), identifier)

    def _calculate_hierarchy_level(self, identifier: str) -> int:
        """
        Calculate hierarchy level from task identifier.

        Args:
            identifier: Task identifier (e.g., "1", "1.1", "2.3")

        Returns:
            Hierarchy level (1 for "1", 2 for "1.1", etc.)
        """
        return len(identifier.split("."))

    def _get_task_group(self, identifier: str) -> str:
        """
        Get the top-level task group for a given identifier.

        Args:
            identifier: Task identifier (e.g., "1", "1.1", "2.3")

        Returns:
            Top-level group identifier (e.g., "1" for "1.1", "2" for "2.3")
        """
        return identifier.split(".")[0]

    def _render_single_task(self, task: TaskItem) -> str:
        """
        Render a single TaskItem to markdown format.

        Args:
            task: TaskItem to render

        Returns:
            Formatted markdown string for the task
        """
        # Get status symbol
        status_key = task.status.value if hasattr(task.status, "value") else str(task.status)
        status_symbol = self.status_symbols.get(status_key, "[ ]")

        # Calculate hierarchy level and indentation
        hierarchy_level = self._calculate_hierarchy_level(task.identifier)
        indent = "  " * (hierarchy_level - 1) if hierarchy_level > 1 else ""
        task_line = f"{indent}- {status_symbol} {task.identifier}. {task.description}"

        lines = [task_line]

        # Add sub-bullets for additional information
        if task.requirements_refs and task.requirements_refs != ["[TBD]"]:
            req_text = ", ".join(task.requirements_refs)
            lines.append(f"{indent}  - _Requirements: {req_text}_")

        # Add any additional details if present
        if hasattr(task, "details") and task.details:
            for detail in task.details:
                lines.append(f"{indent}  - {detail}")

        return "\n".join(lines)

    def render_task_summary(self, tasks: List[TaskItem]) -> str:
        """
        Render a summary of task completion status.

        Args:
            tasks: List of TaskItem objects

        Returns:
            Summary string
        """
        if not tasks:
            return "No tasks defined."

        total = len(tasks)
        completed = sum(1 for task in tasks if task.status == "completed")
        in_progress = sum(1 for task in tasks if task.status == "in_progress")
        not_started = sum(1 for task in tasks if task.status == "not_started")

        completion_rate = (completed / total) * 100 if total > 0 else 0

        summary = f"""Task Summary:
- Total tasks: {total}
- Completed: {completed} ({completion_rate:.1f}%)
- In progress: {in_progress}
- Not started: {not_started}"""

        return summary

    def render_task_by_status(self, tasks: List[TaskItem], status: TaskStatus) -> str:
        """
        Render tasks filtered by status.

        Args:
            tasks: List of TaskItem objects
            status: Status to filter by

        Returns:
            Formatted markdown string for tasks with the specified status
        """
        filtered_tasks = [task for task in tasks if task.status == status]

        if not filtered_tasks:
            return f"No tasks with status: {status.value}"

        status_name = status.value.replace("_", " ").title()
        output = [f"# {status_name} Tasks", ""]

        for task in filtered_tasks:
            rendered_task = self._render_single_task(task)
            output.append(rendered_task)
            output.append("")

        # Clean up extra newlines
        while output and output[-1] == "":
            output.pop()

        return "\n".join(output)

    def validate_rendered_output(self, rendered_content: str) -> List[str]:
        """
        Validate that rendered output follows the standard format.

        Args:
            rendered_content: Rendered markdown content

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        lines = rendered_content.split("\n")

        # Check for required header
        if not lines or not lines[0].startswith("# Implementation Plan"):
            errors.append("Missing required '# Implementation Plan' header")

        # Check task format
        task_pattern = re.compile(r"^(\s*)-\s*\[([ x-])\]\s*\d+(\.\d+)*\.\s*.+")

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("- ["):
                if not task_pattern.match(line):
                    errors.append(f"Line {i}: Invalid task format: {line}")

        # Check for proper indentation
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("- ["):
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % 2 != 0:
                    errors.append(f"Line {i}: Invalid indentation (should be multiples of 2): {line}")

        return errors
