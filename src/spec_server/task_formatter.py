"""
Task formatting functionality for spec-server.

This module provides automatic task list formatting, content classification,
requirements linking, and LLM-based task completion validation.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .content_classifier import ContentClassifier
from .models import ContentBlock, FormattingResult, Spec, TaskItem, TaskValidationResult
from .requirements_linker import RequirementsLinker
from .task_formatting_config import TaskFormattingConfig, get_config
from .task_formatting_errors import TaskFormattingErrorCode, TaskFormattingException, get_error_handler, record_operation
from .task_parser import TaskParser
from .task_renderer import TaskRenderer


class TaskFormatter(ABC):
    """Abstract base class for task document formatting operations."""

    @abstractmethod
    def format_task_document(self, content: str, spec: Spec) -> FormattingResult:
        """Format a task document into the standard format."""
        pass

    @abstractmethod
    def classify_content_blocks(self, content: str) -> List[ContentBlock]:
        """Classify content blocks to determine appropriate document placement."""
        pass

    @abstractmethod
    def link_tasks_to_requirements(self, tasks: List[TaskItem], requirements_content: str) -> List[TaskItem]:
        """Automatically link tasks to relevant requirements."""
        pass

    @abstractmethod
    def redistribute_content(self, spec: Spec, moved_content: Dict[str, List[str]]) -> None:
        """Move content to appropriate documents (requirements or design)."""
        pass


class TaskCompletionValidator(ABC):
    """Abstract base class for LLM-based task completion validation."""

    @abstractmethod
    def validate_task_completion(self, task: TaskItem, spec: Spec, implementation_context: str) -> TaskValidationResult:
        """Validate that a task is actually complete using LLM analysis."""
        pass

    @abstractmethod
    def generate_validation_prompt(self, task: TaskItem, requirements: str, design: str, context: str) -> str:
        """Generate a prompt for LLM validation of task completion."""
        pass

    @abstractmethod
    def parse_llm_validation_response(self, response: str) -> TaskValidationResult:
        """Parse LLM response to extract validation result."""
        pass

    @abstractmethod
    def should_allow_manual_override(self, validation_result: TaskValidationResult) -> bool:
        """Determine if manual override should be allowed for validation result."""
        pass


class BasicTaskFormatter(TaskFormatter):
    """Complete implementation of TaskFormatter with all components integrated."""

    def __init__(self, config: Optional[TaskFormattingConfig] = None):
        """Initialize the BasicTaskFormatter with all components."""
        self.config = config or get_config()
        self.error_handler = get_error_handler()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.parser = TaskParser()
        self.classifier = ContentClassifier()
        self.requirements_linker = RequirementsLinker()
        self.renderer = TaskRenderer()

    def format_task_document(self, content: str, spec: Spec) -> FormattingResult:
        """Format a task document into the standard format with configuration and error handling."""
        start_time = time.time()
        changes_made = []
        errors = []

        try:
            # Check if auto-formatting is enabled
            if not self.config.auto_format_enabled:
                self.logger.info("Auto-formatting is disabled, returning original content")
                return FormattingResult(
                    formatted_tasks=content,
                    moved_content={},
                    requirements_added=[],
                    changes_made=["Auto-formatting disabled"],
                    errors=[],
                )

            # Parse existing tasks with error handling
            tasks = []
            try:
                tasks = self.parser.parse_tasks(content)
                changes_made.append(f"Parsed {len(tasks)} tasks from document")

                if self.config.log_formatting_changes:
                    self.logger.info(f"Successfully parsed {len(tasks)} tasks")

            except Exception as e:
                error = self.error_handler.handle_parsing_error(
                    f"Failed to parse tasks from content: {str(e)}",
                    content,
                    exception=e,
                )
                errors.append(str(error))

                if self.config.fail_on_formatting_errors:
                    raise TaskFormattingException(error, e)

                if self.config.fallback_to_original_on_error:
                    return FormattingResult(
                        formatted_tasks=self.error_handler.create_fallback_result(content, error),
                        moved_content={},
                        requirements_added=[],
                        changes_made=changes_made,
                        errors=errors,
                    )

            # Link tasks to requirements if enabled and available
            requirements_added = []
            if self.config.auto_requirements_linking and tasks:
                try:
                    requirements_path = spec.base_path / "requirements.md"
                    if requirements_path.exists():
                        requirements_content = requirements_path.read_text(encoding="utf-8")
                        original_refs = {task.identifier: task.requirements_refs[:] for task in tasks}

                        tasks = self.requirements_linker.link_tasks_to_requirements(tasks, requirements_content)

                        # Track which tasks got new requirements
                        for task in tasks:
                            if task.requirements_refs != original_refs.get(task.identifier, []):
                                requirements_added.append(task.identifier)

                        if requirements_added:
                            changes_made.append(f"Added requirements links to {len(requirements_added)} tasks")

                            if self.config.log_formatting_changes:
                                self.logger.info(f"Linked {len(requirements_added)} tasks to requirements")

                except Exception as e:
                    error = self.error_handler.handle_requirements_linking_error(
                        f"Failed to link requirements: {str(e)}",
                        f"{len(tasks)} tasks",
                        exception=e,
                    )
                    errors.append(str(error))

                    if self.config.fail_on_formatting_errors:
                        raise TaskFormattingException(error, e)

            # Classify content blocks if content redistribution is enabled
            moved_content = {"requirements": [], "design": []}
            task_blocks = []

            if self.config.content_redistribution_enabled:
                try:
                    blocks = self.classifier.classify_content_blocks(content)

                    # Separate content that should be moved
                    for block in blocks:
                        if block.suggested_location != "tasks" and block.confidence > self.config.classification_confidence_threshold:
                            moved_content[block.suggested_location].append(block.content)
                        else:
                            task_blocks.append(block)

                    if moved_content["requirements"] or moved_content["design"]:
                        changes_made.append("Identified content for redistribution")

                        if self.config.log_formatting_changes:
                            self.logger.info(f"Identified content for redistribution: " f"{len(moved_content['requirements'])} requirements, " f"{len(moved_content['design'])} design")

                except Exception as e:
                    error = self.error_handler.handle_classification_error(f"Failed to classify content: {str(e)}", content, exception=e)
                    errors.append(str(error))

                    if self.config.fail_on_formatting_errors:
                        raise TaskFormattingException(error, e)

            # Generate formatted tasks
            formatted_tasks = ""
            try:
                formatted_tasks = self._render_tasks(tasks, task_blocks)
                changes_made.append("Applied standard task formatting")

                if self.config.log_formatting_changes:
                    self.logger.info("Successfully applied standard task formatting")

            except Exception as e:
                error = self.error_handler.handle_error(
                    TaskFormattingErrorCode.TASK_RENDERING_FAILED,
                    f"Failed to render tasks: {str(e)}",
                    exception=e,
                    context={"task_count": len(tasks)},
                )
                errors.append(str(error))

                if self.config.fail_on_formatting_errors:
                    raise TaskFormattingException(error, e)

                if self.config.fallback_to_original_on_error:
                    formatted_tasks = self.error_handler.create_fallback_result(content, error)

            # Record successful operation
            processing_time = time.time() - start_time
            record_operation("format_task_document", len(errors) == 0, processing_time)

            return FormattingResult(
                formatted_tasks=formatted_tasks,
                moved_content=moved_content,
                requirements_added=requirements_added,
                changes_made=changes_made,
                errors=errors,
            )

        except TaskFormattingException:
            # Re-raise TaskFormattingException
            processing_time = time.time() - start_time
            record_operation("format_task_document", False, processing_time)
            raise

        except Exception as e:
            # Handle unexpected errors
            error = self.error_handler.handle_error(
                TaskFormattingErrorCode.UNKNOWN_ERROR,
                f"Unexpected error during task formatting: {str(e)}",
                exception=e,
                recoverable=False,
            )

            processing_time = time.time() - start_time
            record_operation("format_task_document", False, processing_time, error.error_code)

            if self.config.fail_on_formatting_errors:
                raise TaskFormattingException(error, e)

            # Return fallback result
            return FormattingResult(
                formatted_tasks=self.error_handler.create_fallback_result(content, error),
                moved_content={},
                requirements_added=[],
                changes_made=changes_made,
                errors=[str(error)],
            )

    def classify_content_blocks(self, content: str) -> List[ContentBlock]:
        """Classify content blocks using the ContentClassifier."""
        return self.classifier.classify_content_blocks(content)

    def link_tasks_to_requirements(self, tasks: List[TaskItem], requirements_content: str) -> List[TaskItem]:
        """Link tasks to requirements using the RequirementsLinker."""
        return self.requirements_linker.link_tasks_to_requirements(tasks, requirements_content)

    def redistribute_content(self, spec: Spec, moved_content: Dict[str, List[str]]) -> None:
        """Move content to appropriate documents."""
        try:
            # Update requirements document if content should be moved there
            if moved_content.get("requirements"):
                requirements_path = spec.base_path / "requirements.md"
                if requirements_path.exists():
                    existing_content = requirements_path.read_text(encoding="utf-8")
                    new_content = existing_content + "\n\n## Additional Content\n\n"
                    new_content += "\n\n".join(moved_content["requirements"])
                    requirements_path.write_text(new_content, encoding="utf-8")

            # Update design document if content should be moved there
            if moved_content.get("design"):
                design_path = spec.base_path / "design.md"
                if design_path.exists():
                    existing_content = design_path.read_text(encoding="utf-8")
                    new_content = existing_content + "\n\n## Additional Content\n\n"
                    new_content += "\n\n".join(moved_content["design"])
                    design_path.write_text(new_content, encoding="utf-8")

        except Exception as e:
            # Log error but don't fail the entire operation
            self.logger.error(f"Error during content redistribution: {e}")

    def _render_tasks(self, tasks: List[TaskItem], blocks: List[ContentBlock]) -> str:
        """Render tasks in standard format using TaskRenderer."""
        # Filter blocks that should stay in tasks
        task_content_blocks = [block for block in blocks if block.suggested_location == "tasks"]

        # Use the TaskRenderer for consistent formatting
        return self.renderer.render_tasks(tasks, task_content_blocks)


# The LLMTaskCompletionValidator implementation is now in llm_task_validator.py
# This import makes it available for use in other modules
