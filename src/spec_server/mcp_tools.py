"""
MCP tools implementation for spec-server.

This module provides all the MCP tools that expose the spec-server functionality
through the Model Context Protocol interface.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .document_generator import DocumentGenerationError, DocumentGenerator
from .errors import ErrorCode, ErrorFactory, SpecError
from .models import Phase, TaskStatus
from .spec_manager import SpecManager
from .task_executor import TaskExecutor
from .validation import (
    validate_create_spec_params,
    validate_read_spec_params,
    validate_task_params,
    validate_update_spec_params,
)
from .workflow_engine import WorkflowEngine, WorkflowError


# Keep the old MCPToolsError for backward compatibility
class MCPToolsError(SpecError):
    """Legacy MCP tools error class - use SpecError instead."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        # Convert old format to new SpecError format
        from .errors import ErrorCode

        try:
            if isinstance(error_code, ErrorCode):
                code = error_code
            elif error_code:
                code = ErrorCode(error_code)
            else:
                code = ErrorCode.INTERNAL_ERROR
        except ValueError:
            code = ErrorCode.INTERNAL_ERROR

        super().__init__(message=message, error_code=code, details=details or {})


class MCPTools:
    """
    MCP tools implementation for spec-server.

    Provides all the MCP tools that expose spec-server functionality through
    the Model Context Protocol interface.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize MCP tools with core components.

        Args:
            base_path: Base directory for storing specs (None for auto-detection)
        """
        self.spec_manager = SpecManager(base_path)
        self.document_generator = DocumentGenerator()
        self.workflow_engine = WorkflowEngine(self.spec_manager)
        self.task_executor = TaskExecutor()

    def create_spec(self, feature_name: str, initial_idea: str) -> Dict[str, Any]:
        """
        Create a new feature specification.

        Args:
            feature_name: Kebab-case feature identifier
            initial_idea: User's rough feature description

        Returns:
            Dictionary containing created spec metadata and initial requirements

        Raises:
            SpecError: If spec creation fails
        """
        try:
            # Validate and sanitize inputs
            validated_params = validate_create_spec_params(feature_name, initial_idea)
            feature_name = validated_params["feature_name"]
            initial_idea = validated_params["initial_idea"]
            # Create the spec
            spec = self.spec_manager.create_spec(
                feature_name.strip(), initial_idea.strip()
            )

            # Generate initial requirements document
            requirements_content = self.document_generator.generate_requirements(
                initial_idea.strip()
            )

            # Write requirements to file
            requirements_path = spec.get_requirements_path()
            requirements_path.write_text(requirements_content, encoding="utf-8")

            # Update spec metadata
            self.spec_manager.update_spec_metadata(
                feature_name.strip(),
                current_phase=Phase.REQUIREMENTS.value,
                has_requirements=True,
            )

            return {
                "success": True,
                "spec": {
                    "feature_name": spec.feature_name,
                    "current_phase": spec.current_phase,
                    "created_at": spec.created_at,
                    "base_path": str(spec.base_path),
                },
                "requirements_content": requirements_content,
                "message": f"Successfully created spec '{feature_name}' with initial requirements",
            }

        except SpecError as e:
            raise MCPToolsError(
                message=e.message,
                error_code=(
                    e.error_code.value
                    if hasattr(e.error_code, "value")
                    else str(e.error_code)
                ),
                details=e.details,
            )
        except DocumentGenerationError as e:
            raise MCPToolsError(
                message=f"Failed to generate requirements document: {e.message}",
                error_code="INTERNAL_ERROR",
                details=e.details,
            )
        except Exception as e:
            raise MCPToolsError(
                message=f"Unexpected error creating spec: {str(e)}",
                error_code="INTERNAL_ERROR",
                details={"feature_name": feature_name},
            )

    def update_spec_document(
        self,
        feature_name: str,
        document_type: str,
        content: str,
        phase_approval: bool = False,  # Must be explicitly set to True to approve and advance phases
    ) -> Dict[str, Any]:
        """
        Update a spec document and manage workflow transitions.

        Args:
            feature_name: Target spec identifier
            document_type: "requirements", "design", or "tasks"
            content: Updated document content
            phase_approval: Whether user approves current phase

        Returns:
            Dictionary containing updated document and workflow status

        Raises:
            MCPToolsError: If update fails
        """
        # Validate and sanitize inputs
        validated_params = validate_update_spec_params(
            feature_name, document_type, content, phase_approval
        )
        feature_name = validated_params["feature_name"]
        document_type = validated_params["document_type"]
        content = validated_params["content"]
        phase_approval = validated_params["phase_approval"]

        try:
            # Get the spec
            spec = self.spec_manager.get_spec(feature_name)

            # Validate document format (skip for now since validate_document_format doesn't exist)
            # if not self.document_generator.validate_document_format(document_type, content):
            #     raise SpecError(
            #         message=f"Invalid {document_type} document format",
            #         error_code=ErrorCode.VALIDATION_ERROR,
            #         details={"document_type": document_type}
            #     )

            # Get current workflow state
            current_phase = self.workflow_engine.get_current_phase(spec)

            # Write the document
            if document_type == "requirements":
                file_path = spec.get_requirements_path()
            elif document_type == "design":
                file_path = spec.get_design_path()
            else:  # tasks
                file_path = spec.get_tasks_path()

            file_path.write_text(content.strip(), encoding="utf-8")

            # Handle workflow transitions
            next_phase = current_phase
            workflow_message = f"Updated {document_type} document"

            # Only advance phase if explicit approval is provided by the user
            # This ensures specs are never auto-approved without user confirmation
            if phase_approval and self.workflow_engine.can_advance_phase(
                spec, phase_approval
            ):
                try:
                    # Pass explicit approval to advance_phase
                    next_phase = self.workflow_engine.advance_phase(spec, approval=True)
                    workflow_message += f" and advanced to {next_phase.value} phase"

                    # Generate next phase document if needed
                    if (
                        next_phase == Phase.DESIGN
                        and not spec.get_design_path().exists()
                    ):
                        requirements_content = spec.get_requirements_path().read_text(
                            encoding="utf-8"
                        )
                        design_content = self.document_generator.generate_design(
                            requirements_content
                        )
                        spec.get_design_path().write_text(
                            design_content, encoding="utf-8"
                        )
                        workflow_message += " and generated initial design document"

                    elif (
                        next_phase == Phase.TASKS and not spec.get_tasks_path().exists()
                    ):
                        requirements_content = spec.get_requirements_path().read_text(
                            encoding="utf-8"
                        )
                        design_content = spec.get_design_path().read_text(
                            encoding="utf-8"
                        )
                        tasks_content = self.document_generator.generate_tasks(
                            requirements_content, design_content
                        )
                        spec.get_tasks_path().write_text(
                            tasks_content, encoding="utf-8"
                        )
                        workflow_message += " and generated initial tasks document"

                except WorkflowError as e:
                    # Phase advancement failed, but document update succeeded
                    workflow_message += f" (phase advancement failed: {e.message})"

            # Update metadata
            self.spec_manager.update_spec_metadata(
                feature_name,
                current_phase=next_phase.value,
                has_requirements=spec.get_requirements_path().exists(),
                has_design=spec.get_design_path().exists(),
                has_tasks=spec.get_tasks_path().exists(),
            )

            return {
                "success": True,
                "document_type": document_type,
                "current_phase": next_phase.value,
                "content": content.strip(),
                "message": workflow_message,
                "can_advance": (
                    self.workflow_engine.can_advance_phase(spec, False)
                    if not phase_approval
                    else False
                ),
                "requires_approval": self.workflow_engine.require_approval(spec),
            }

        except SpecError as e:
            raise e
        except DocumentGenerationError as e:
            raise SpecError(
                message=f"Failed to generate document: {e.message}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details=e.details,
            )
        except Exception as e:
            raise SpecError(
                message=f"Unexpected error updating document: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={"feature_name": feature_name, "document_type": document_type},
            )

    def list_specs(self) -> Dict[str, Any]:
        """
        List all existing specifications with metadata.

        Returns:
            Dictionary containing list of spec metadata

        Raises:
            MCPToolsError: If listing fails
        """
        try:
            specs_metadata = self.spec_manager.list_specs()

            specs_list = []
            for metadata in specs_metadata:
                specs_list.append(
                    {
                        "feature_name": metadata.feature_name,
                        "current_phase": metadata.current_phase,
                        "has_requirements": metadata.has_requirements,
                        "has_design": metadata.has_design,
                        "has_tasks": metadata.has_tasks,
                        "task_progress": metadata.task_progress,
                        "created_at": metadata.created_at,
                        "updated_at": metadata.updated_at,
                    }
                )

            return {
                "success": True,
                "specs": specs_list,
                "total_count": len(specs_list),
                "message": f"Found {len(specs_list)} specifications",
            }

        except Exception as e:
            raise MCPToolsError(
                f"Failed to list specs: {str(e)}", error_code="LIST_SPECS_ERROR"
            )

    def read_spec_document(
        self, feature_name: str, document_type: str, resolve_references: bool = True
    ) -> Dict[str, Any]:
        """
        Read a spec document with optional file reference resolution.

        Args:
            feature_name: Target spec identifier
            document_type: "requirements", "design", or "tasks"
            resolve_references: Whether to resolve file references

        Returns:
            Dictionary containing document content and metadata

        Raises:
            MCPToolsError: If reading fails
        """
        # Validate and sanitize inputs
        validated_params = validate_read_spec_params(
            feature_name, document_type, resolve_references
        )
        feature_name = validated_params["feature_name"]
        document_type = validated_params["document_type"]
        resolve_references = validated_params["resolve_references"]

        try:
            # Get the spec
            spec = self.spec_manager.get_spec(feature_name)
        except SpecError as e:
            raise e

        # Get the document path
        if document_type == "requirements":
            file_path = spec.get_requirements_path()
        elif document_type == "design":
            file_path = spec.get_design_path()
        else:  # tasks
            file_path = spec.get_tasks_path()

        if not file_path.exists():
            raise ErrorFactory.document_not_found(feature_name, document_type)

        try:
            # Read the content
            content = file_path.read_text(encoding="utf-8")

            # Resolve file references if requested
            if resolve_references:
                from .models import FileReferenceResolver

                resolver = FileReferenceResolver(spec.base_path)

                # Get validation errors for references before substitution
                reference_errors = resolver.validate_references(content)

                # Substitute references with content
                content = resolver.substitute_references(content, resolve_content=True)
            else:
                reference_errors = []

            # Get file metadata
            stat = file_path.stat()

            return {
                "success": True,
                "feature_name": feature_name,
                "document_type": document_type,
                "content": content,
                "file_size": stat.st_size,
                "last_modified": stat.st_mtime,
                "resolve_references": resolve_references,
                "reference_errors": reference_errors,
                "message": f"Successfully read {document_type} document",
            }

        except SpecError as e:
            raise e
        except Exception as e:
            raise MCPToolsError(
                f"Failed to read document: {str(e)}",
                error_code="READ_DOCUMENT_ERROR",
                details={"feature_name": feature_name, "document_type": document_type},
            )

    def execute_task(
        self, feature_name: str, task_identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific implementation task or get the next task.

        Args:
            feature_name: Target spec identifier
            task_identifier: Task number/identifier (optional)

        Returns:
            Dictionary containing task execution context and results

        Raises:
            SpecError: If task execution fails
        """
        # Validate and sanitize inputs
        validated_params = validate_task_params(feature_name, task_identifier)
        feature_name = validated_params["feature_name"]
        task_identifier = validated_params["task_identifier"]

        try:
            # Get the spec
            spec = self.spec_manager.get_spec(feature_name)
        except SpecError as e:
            raise e

        # Ensure tasks document exists
        tasks_path = spec.get_tasks_path()
        if not tasks_path.exists():
            raise MCPToolsError(
                f"Tasks document does not exist for spec '{feature_name}'",
                error_code="TASKS_NOT_FOUND",
                details={"feature_name": feature_name},
            )

        # Parse tasks
        tasks_content = tasks_path.read_text(encoding="utf-8")
        tasks = self.task_executor.parse_tasks(tasks_content)

        if not tasks:
            raise MCPToolsError(
                f"No tasks found in spec '{feature_name}'",
                error_code="NO_TASKS_FOUND",
                details={"feature_name": feature_name},
            )

        # Get the target task
        if task_identifier:
            task = self.task_executor.get_task_by_identifier(tasks, task_identifier)
            if not task:
                raise MCPToolsError(
                    f"Task '{task_identifier}' not found in spec '{feature_name}'",
                    error_code="TASK_NOT_FOUND",
                    details={
                        "feature_name": feature_name,
                        "task_identifier": task_identifier,
                    },
                )
        else:
            # Get next task to execute
            task = self.task_executor.get_next_task(tasks)
            if not task:
                raise MCPToolsError(
                    f"No tasks available for execution in spec '{feature_name}'",
                    error_code="NO_TASKS_AVAILABLE",
                    details={"feature_name": feature_name},
                )

        try:
            # Check if task can be executed
            if not self.task_executor.can_execute_task(task, tasks):
                dependencies = self.task_executor.get_task_dependencies(task, tasks)
                incomplete_deps = [
                    dep.identifier
                    for dep in dependencies
                    if dep.status != TaskStatus.COMPLETED.value
                ]

                raise MCPToolsError(
                    f"Task '{task.identifier}' cannot be executed. Dependencies not complete: {incomplete_deps}",
                    error_code="TASK_DEPENDENCIES_NOT_COMPLETE",
                    details={
                        "feature_name": feature_name,
                        "task_identifier": task.identifier,
                        "incomplete_dependencies": incomplete_deps,
                    },
                )

            # Create execution context
            context = self.task_executor.execute_task_context(spec, task)

            # Update task status to in progress
            updated_tasks_content = self.task_executor.update_task_status(
                tasks_content, task.identifier, TaskStatus.IN_PROGRESS
            )
            tasks_path.write_text(updated_tasks_content, encoding="utf-8")

            # Get task progress
            completed, total = self.task_executor.get_task_progress(tasks)

            return {
                "success": True,
                "feature_name": feature_name,
                "task": {
                    "identifier": task.identifier,
                    "description": task.description,
                    "status": TaskStatus.IN_PROGRESS.value,
                    "requirements_refs": task.requirements_refs,
                    "parent_task": task.parent_task,
                    "sub_tasks": task.sub_tasks,
                },
                "execution_context": {
                    "has_requirements": context.requirements_content is not None,
                    "has_design": context.design_content is not None,
                    "has_tasks": context.tasks_content is not None,
                    "requirements_content": context.requirements_content,
                    "design_content": context.design_content,
                    "referenced_requirements": context.get_referenced_requirements(),
                },
                "progress": {
                    "completed": completed,
                    "total": total,
                    "percentage": (
                        round((completed / total) * 100, 1) if total > 0 else 0
                    ),
                },
                "message": f"Started execution of task '{task.identifier}': {task.description}",
            }

        except SpecError as e:
            raise MCPToolsError(
                message=e.message,
                error_code=(
                    e.error_code.value
                    if hasattr(e.error_code, "value")
                    else str(e.error_code)
                ),
                details=e.details,
            )
        except Exception as e:
            raise MCPToolsError(
                f"Failed to execute task: {str(e)}",
                error_code="TASK_EXECUTION_ERROR",
                details={
                    "feature_name": feature_name,
                    "task_identifier": task_identifier,
                },
            )

    def complete_task(self, feature_name: str, task_identifier: str) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            feature_name: Target spec identifier
            task_identifier: Task number/identifier

        Returns:
            Dictionary containing updated task status

        Raises:
            SpecError: If task completion fails
        """
        # Validate and sanitize inputs
        validated_params = validate_task_params(feature_name, task_identifier)
        feature_name = validated_params["feature_name"]
        task_identifier = validated_params["task_identifier"]

        # task_identifier is required for completion
        if task_identifier is None:
            raise ErrorFactory.validation_error(
                "task_identifier", None, "Task identifier is required for completion"
            )

        try:
            # Get the spec
            spec = self.spec_manager.get_spec(feature_name)
        except SpecError as e:
            raise e

        # Ensure tasks document exists
        tasks_path = spec.get_tasks_path()
        if not tasks_path.exists():
            raise MCPToolsError(
                f"Tasks document does not exist for spec '{feature_name}'",
                error_code="TASKS_NOT_FOUND",
                details={"feature_name": feature_name},
            )

        # Parse tasks and find the target task
        tasks_content = tasks_path.read_text(encoding="utf-8")
        tasks = self.task_executor.parse_tasks(tasks_content)

        task = self.task_executor.get_task_by_identifier(tasks, task_identifier)
        if not task:
            raise MCPToolsError(
                f"Task '{task_identifier}' not found in spec '{feature_name}'",
                error_code="TASK_NOT_FOUND",
                details={
                    "feature_name": feature_name,
                    "task_identifier": task_identifier,
                },
            )

        try:
            # Update task status to completed
            updated_tasks_content = self.task_executor.update_task_status(
                tasks_content, task_identifier, TaskStatus.COMPLETED
            )
            tasks_path.write_text(updated_tasks_content, encoding="utf-8")

            # Get updated progress
            updated_tasks = self.task_executor.parse_tasks(updated_tasks_content)
            completed, total = self.task_executor.get_task_progress(updated_tasks)

            # Get next task suggestion
            next_task = self.task_executor.get_next_task(updated_tasks)

            return {
                "success": True,
                "feature_name": feature_name,
                "completed_task": {
                    "identifier": task_identifier,
                    "description": task.description,
                    "status": TaskStatus.COMPLETED.value,
                },
                "progress": {
                    "completed": completed,
                    "total": total,
                    "percentage": (
                        round((completed / total) * 100, 1) if total > 0 else 0
                    ),
                },
                "next_task": (
                    {
                        "identifier": next_task.identifier,
                        "description": next_task.description,
                    }
                    if next_task
                    else None
                ),
                "message": f"Completed task '{task_identifier}': {task.description}",
            }

        except SpecError as e:
            raise MCPToolsError(
                message=e.message,
                error_code=(
                    e.error_code.value
                    if hasattr(e.error_code, "value")
                    else str(e.error_code)
                ),
                details=e.details,
            )
        except Exception as e:
            raise MCPToolsError(
                f"Failed to complete task: {str(e)}",
                error_code="TASK_COMPLETION_ERROR",
                details={
                    "feature_name": feature_name,
                    "task_identifier": task_identifier,
                },
            )

    def delete_spec(self, feature_name: str) -> Dict[str, Any]:
        """
        Delete a specification entirely.

        Args:
            feature_name: Target spec identifier

        Returns:
            Dictionary containing deletion confirmation

        Raises:
            SpecError: If deletion fails
        """
        # Validate and sanitize inputs
        from .validation import InputValidator

        name_result = InputValidator.validate_feature_name(feature_name)
        if not name_result.is_valid:
            raise ErrorFactory.invalid_spec_name(
                feature_name, "; ".join(name_result.errors)
            )

        feature_name = name_result.sanitized_value

        try:
            # Get spec info before deletion for confirmation
            spec = self.spec_manager.get_spec(feature_name)
            spec_info = {
                "feature_name": spec.feature_name,
                "current_phase": spec.current_phase,
                "created_at": spec.created_at,
                "base_path": str(spec.base_path),
            }

            # Check what files exist
            files_to_delete = []
            if spec.get_requirements_path().exists():
                files_to_delete.append("requirements.md")
            if spec.get_design_path().exists():
                files_to_delete.append("design.md")
            if spec.get_tasks_path().exists():
                files_to_delete.append("tasks.md")

            # Delete the spec
            success = self.spec_manager.delete_spec(feature_name)

            if not success:
                raise MCPToolsError(
                    f"Failed to delete spec '{feature_name}'",
                    error_code="DELETION_FAILED",
                    details={"feature_name": feature_name},
                )

            return {
                "success": True,
                "deleted_spec": spec_info,
                "deleted_files": files_to_delete,
                "message": f"Successfully deleted spec '{feature_name}' and all associated files",
            }

        except SpecError as e:
            raise MCPToolsError(
                message=e.message,
                error_code=(
                    e.error_code.value
                    if hasattr(e.error_code, "value")
                    else str(e.error_code)
                ),
                details=e.details,
            )
        except Exception as e:
            raise MCPToolsError(
                f"Failed to delete spec: {str(e)}",
                error_code="DELETE_SPEC_ERROR",
                details={"feature_name": feature_name},
            )
