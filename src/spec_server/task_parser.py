"""
Task parsing functionality for converting markdown to TaskItem objects.
"""

import re
from typing import List, Optional

from .models import TaskItem, TaskStatus
from .task_formatting_cache import get_cache


class TaskParser:
    """
    Parses various markdown task formats into standardized TaskItem objects.

    Handles numbered lists, bulleted lists, mixed formats, and extracts
    task hierarchy, status, and existing requirements references.
    """

    def __init__(self):
        """Initialize the TaskParser."""
        # Regex patterns for different task formats
        self.checkbox_pattern = re.compile(r"^(\s*)-\s*\[([x\s-])\]\s*(.+)", re.MULTILINE)
        self.numbered_pattern = re.compile(r"^(\s*)(\d+(?:\.\d+)*)\.\s*(.+)", re.MULTILINE)
        self.requirements_pattern = re.compile(r"Requirements:\s*([\d\.,\s]+)", re.IGNORECASE)

    def parse_tasks(self, content: str) -> List[TaskItem]:
        """
        Parse task content into TaskItem objects.

        Args:
            content: Raw markdown content containing tasks

        Returns:
            List of TaskItem objects parsed from content
        """
        # Check cache first
        cache = get_cache()
        cached_tasks = cache.get_parsed_tasks(content)
        if cached_tasks is not None:
            return cached_tasks

        tasks = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            task_item = self._parse_line(line, line_num)
            if task_item:
                tasks.append(task_item)

        # Build hierarchy relationships
        self._build_hierarchy(tasks)

        # Cache the result
        cache.set_parsed_tasks(content, tasks)

        return tasks

    def _parse_line(self, line: str, line_num: int) -> Optional[TaskItem]:
        """Parse a single line to extract task information."""
        # Try checkbox format first (- [ ] or - [x])
        checkbox_match = self.checkbox_pattern.match(line)
        if checkbox_match:
            indent, status_char, description = checkbox_match.groups()
            status = self._parse_status(status_char)
            identifier = self._extract_identifier(description)
            requirements_refs = self._extract_requirements(description)

            return TaskItem(
                identifier=identifier or f"line_{line_num}",
                description=self._clean_description(description),
                status=status,
                requirements_refs=requirements_refs,
                original_line=line_num,
            )

        # Try numbered format (1. or 1.1.)
        numbered_match = self.numbered_pattern.match(line)
        if numbered_match:
            indent, identifier, description = numbered_match.groups()
            requirements_refs = self._extract_requirements(description)

            return TaskItem(
                identifier=identifier,
                description=self._clean_description(description),
                status=TaskStatus.NOT_STARTED,
                requirements_refs=requirements_refs,
                original_line=line_num,
            )

        return None

    def _parse_status(self, status_char: str) -> TaskStatus:
        """Parse status character to TaskStatus enum."""
        status_char = status_char.lower().strip()
        if status_char == "x":
            return TaskStatus.COMPLETED
        elif status_char == "-":
            return TaskStatus.IN_PROGRESS
        else:
            return TaskStatus.NOT_STARTED

    def _extract_identifier(self, description: str) -> Optional[str]:
        """Extract task identifier from description if present."""
        # Try to match identifier with dot (1.2.)
        match = re.match(r"^(\d+(?:\.\d+)*)\.\s*", description)
        if match:
            return match.group(1)

        # Try to match identifier without dot (just number at start)
        match = re.match(r"^(\d+(?:\.\d+)*)\s+", description)
        if match:
            return match.group(1)

        return None

    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements references from description."""
        match = self.requirements_pattern.search(description)
        if match:
            refs_text = match.group(1)
            refs = [ref.strip() for ref in refs_text.split(",") if ref.strip()]
            return refs
        return []

    def _clean_description(self, description: str) -> str:
        """Clean task description by removing identifier and requirements."""
        # Remove leading identifier with dot (1., 1.1., etc.)
        description = re.sub(r"^\d+(?:\.\d+)*\.\s*", "", description)
        # Remove leading identifier without dot (1 , 2 , etc.)
        description = re.sub(r"^\d+(?:\.\d+)*\s+", "", description)
        # Remove requirements reference
        description = self.requirements_pattern.sub("", description)
        return description.strip()

    def _build_hierarchy(self, tasks: List[TaskItem]) -> None:
        """Build parent-child relationships between tasks."""
        task_map = {task.identifier: task for task in tasks}

        for task in tasks:
            parent_id = self._get_parent_identifier(task.identifier)
            if parent_id and parent_id in task_map:
                task.parent_task = parent_id
                task_map[parent_id].sub_tasks.append(task.identifier)

    def _get_parent_identifier(self, identifier: str) -> Optional[str]:
        """Get parent identifier from hierarchical identifier."""
        parts = identifier.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None
