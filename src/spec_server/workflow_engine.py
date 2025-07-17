"""
WorkflowEngine implementation for managing spec workflow state and phase transitions.

This module provides the WorkflowEngine class which enforces the three-phase workflow
progression (Requirements → Design → Tasks). It tracks the current phase of each spec,
validates phase transitions, and ensures users cannot skip phases without proper approval.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import Phase, Spec
from .spec_manager import SpecManager


class WorkflowError(Exception):
    """Exception raised when workflow operations fail."""

    def __init__(
        self,
        message: str,
        error_code: str = "WORKFLOW_ERROR",
        details: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class WorkflowEngine:
    """
    Enforces the three-phase workflow progression (Requirements → Design → Tasks).

    Tracks the current phase of each spec, validates phase transitions, and ensures
    users cannot skip phases without proper approval. The engine maintains workflow
    state and provides safeguards against invalid transitions.
    """

    def __init__(self, spec_manager: SpecManager):
        """
        Initialize the WorkflowEngine.

        Args:
            spec_manager: SpecManager instance for spec operations
        """
        self.spec_manager = spec_manager
        self.phase_order = [
            Phase.REQUIREMENTS,
            Phase.DESIGN,
            Phase.TASKS,
            Phase.COMPLETE,
        ]
        self.approval_tracking: Dict[str, Dict[str, bool]] = {}

    def get_current_phase(self, spec: Spec) -> Phase:
        """
        Get the current phase of a specification.

        Args:
            spec: Spec instance

        Returns:
            Current phase of the spec

        Raises:
            WorkflowError: If phase cannot be determined
        """
        try:
            # Check which files exist to determine phase
            requirements_exists = spec.get_requirements_path().exists()
            design_exists = spec.get_design_path().exists()
            tasks_exists = spec.get_tasks_path().exists()

            # Determine phase based on file existence and explicit approval status
            # Phase advancement requires explicit approval
            if tasks_exists and self._is_phase_approved(spec.feature_name, "tasks"):
                return Phase.COMPLETE
            elif tasks_exists:
                return Phase.TASKS
            elif design_exists and self._is_phase_approved(spec.feature_name, "design"):
                return Phase.TASKS
            elif design_exists:
                return Phase.DESIGN
            elif requirements_exists and self._is_phase_approved(
                spec.feature_name, "requirements"
            ):
                return Phase.DESIGN
            elif requirements_exists:
                return Phase.REQUIREMENTS
            else:
                return Phase.REQUIREMENTS

        except Exception as e:
            raise WorkflowError(
                f"Failed to determine current phase for spec '{spec.feature_name}': {str(e)}",
                error_code="PHASE_DETERMINATION_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def can_advance_phase(self, spec: Spec, approval: bool = False) -> bool:
        """
        Check if a spec can advance to the next phase.

        Args:
            spec: Spec instance
            approval: Whether user has provided explicit approval for this operation.
                     Must be True for phase advancement unless already approved.

        Returns:
            True if spec can advance to next phase

        Raises:
            WorkflowError: If validation fails
        """
        try:
            current_phase = self.get_current_phase(spec)

            # Cannot advance from COMPLETE phase
            if current_phase == Phase.COMPLETE:
                return False

            # Explicit approval is required for phase advancement
            # Either the phase must already be approved or explicit approval must be provided now
            if not approval and not self._is_phase_approved(
                spec.feature_name, current_phase.value
            ):
                return False

            # Check if required files exist for current phase
            if not self._validate_phase_requirements(spec, current_phase):
                return False

            return True

        except Exception as e:
            raise WorkflowError(
                f"Failed to validate phase advancement for spec '{spec.feature_name}': {str(e)}",
                error_code="PHASE_VALIDATION_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def advance_phase(self, spec: Spec, approval: bool = True) -> Phase:
        """
        Advance a spec to the next phase.

        Args:
            spec: Spec instance
            approval: Whether user has provided explicit approval for this operation
                     This parameter should be True for explicit user approval

        Returns:
            New phase after advancement

        Raises:
            WorkflowError: If advancement is not allowed
        """
        if not self.can_advance_phase(spec, approval):
            current_phase = self.get_current_phase(spec)
            raise WorkflowError(
                f"Cannot advance spec '{spec.feature_name}' from phase '{current_phase.value}' without explicit approval",
                error_code="PHASE_ADVANCEMENT_DENIED",
                details={
                    "feature_name": spec.feature_name,
                    "current_phase": current_phase.value,
                    "approval_provided": approval,
                },
            )

        try:
            current_phase = self.get_current_phase(spec)

            # Record approval for current phase
            if approval:
                self._record_phase_approval(spec.feature_name, current_phase.value)

            # Determine next phase
            current_index = self.phase_order.index(current_phase)
            if current_index < len(self.phase_order) - 1:
                next_phase = self.phase_order[current_index + 1]
            else:
                next_phase = Phase.COMPLETE

            # Update spec metadata
            self.spec_manager.update_spec_metadata(
                spec.feature_name,
                current_phase=next_phase.value,
                last_phase_advancement=datetime.now().isoformat(),
            )

            return next_phase

        except Exception as e:
            raise WorkflowError(
                f"Failed to advance phase for spec '{spec.feature_name}': {str(e)}",
                error_code="PHASE_ADVANCEMENT_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def validate_phase_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """
        Validate if a phase transition is allowed.

        Args:
            from_phase: Current phase
            to_phase: Target phase

        Returns:
            True if transition is valid

        Raises:
            WorkflowError: If validation fails
        """
        try:
            # Allow staying in same phase
            if from_phase == to_phase:
                return True

            # Get phase indices
            try:
                from_index = self.phase_order.index(from_phase)
                to_index = self.phase_order.index(to_phase)
            except ValueError as e:
                raise WorkflowError(
                    f"Invalid phase in transition: {str(e)}",
                    error_code="INVALID_PHASE",
                    details={
                        "from_phase": from_phase.value,
                        "to_phase": to_phase.value,
                    },
                )

            # Allow forward progression (one step at a time)
            if to_index == from_index + 1:
                return True

            # Allow backward progression (for revisions)
            if to_index < from_index:
                return True

            # Disallow skipping phases forward
            return False

        except Exception as e:
            raise WorkflowError(
                f"Failed to validate phase transition: {str(e)}",
                error_code="PHASE_TRANSITION_VALIDATION_ERROR",
                details={
                    "from_phase": from_phase.value,
                    "to_phase": to_phase.value,
                    "error": str(e),
                },
            )

    def require_approval(self, spec: Spec, phase: Optional[Phase] = None) -> bool:
        """
        Check if a phase requires user approval before advancement.
        
        All phases require explicit approval before advancement.

        Args:
            spec: Spec instance
            phase: Phase to check (defaults to current phase)

        Returns:
            True if approval is required (which is always the case unless already approved)

        Raises:
            WorkflowError: If validation fails
        """
        try:
            if phase is None:
                phase = self.get_current_phase(spec)

            # All phases require explicit approval before advancement
            # Only return False if the phase has already been approved
            return not self._is_phase_approved(spec.feature_name, phase.value)

        except Exception as e:
            raise WorkflowError(
                f"Failed to check approval requirement: {str(e)}",
                error_code="APPROVAL_CHECK_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def get_phase_status(self, spec: Spec) -> Dict[str, Any]:
        """
        Get comprehensive phase status information.

        Args:
            spec: Spec instance

        Returns:
            Dictionary with phase status information

        Raises:
            WorkflowError: If status cannot be determined
        """
        try:
            current_phase = self.get_current_phase(spec)

            status = {
                "current_phase": current_phase.value,
                "can_advance": self.can_advance_phase(spec),
                "requires_approval": self.require_approval(spec),
                "phase_approvals": self._get_phase_approvals(spec.feature_name),
                "available_transitions": self._get_available_transitions(current_phase),
                "phase_files": {
                    "requirements": spec.get_requirements_path().exists(),
                    "design": spec.get_design_path().exists(),
                    "tasks": spec.get_tasks_path().exists(),
                },
            }

            return status

        except Exception as e:
            raise WorkflowError(
                f"Failed to get phase status: {str(e)}",
                error_code="PHASE_STATUS_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def reset_phase_approvals(self, feature_name: str) -> None:
        """
        Reset all phase approvals for a spec.

        Args:
            feature_name: Feature name to reset approvals for
        """
        if feature_name in self.approval_tracking:
            del self.approval_tracking[feature_name]

    def get_workflow_history(self, spec: Spec) -> List[Dict[str, str]]:
        """
        Get workflow history for a spec.

        Args:
            spec: Spec instance

        Returns:
            List of workflow events

        Raises:
            WorkflowError: If history cannot be retrieved
        """
        try:
            # This would typically come from a persistent store
            # For now, return basic information based on current state
            history = []

            # Add creation event
            history.append(
                {
                    "event": "spec_created",
                    "phase": Phase.REQUIREMENTS.value,
                    "timestamp": spec.created_at,
                    "description": "Specification created",
                }
            )

            # Add phase progression events based on file existence and approvals
            # current_phase = self.get_current_phase(spec)  # Not used currently
            approvals = self._get_phase_approvals(spec.feature_name)

            for phase in [Phase.REQUIREMENTS, Phase.DESIGN, Phase.TASKS]:
                if phase.value in approvals and approvals[phase.value]:
                    history.append(
                        {
                            "event": "phase_approved",
                            "phase": phase.value,
                            "timestamp": spec.updated_at,  # Would be more specific in real implementation
                            "description": f"{phase.value.title()} phase approved",
                        }
                    )

            return history

        except Exception as e:
            raise WorkflowError(
                f"Failed to get workflow history: {str(e)}",
                error_code="WORKFLOW_HISTORY_ERROR",
                details={"feature_name": spec.feature_name, "error": str(e)},
            )

    def _is_phase_approved(self, feature_name: str, phase: str) -> bool:
        """
        Check if a phase has been approved.
        
        A phase is considered approved only if it has been explicitly approved
        by recording it in the approval_tracking dictionary.
        """
        return (
            feature_name in self.approval_tracking
            and phase in self.approval_tracking[feature_name]
            and self.approval_tracking[feature_name][phase]
        )

    def _record_phase_approval(self, feature_name: str, phase: str) -> None:
        """Record approval for a phase."""
        if feature_name not in self.approval_tracking:
            self.approval_tracking[feature_name] = {}
        self.approval_tracking[feature_name][phase] = True

    def _get_phase_approvals(self, feature_name: str) -> Dict[str, bool]:
        """Get all phase approvals for a feature."""
        return self.approval_tracking.get(feature_name, {})

    def _validate_phase_requirements(self, spec: Spec, phase: Phase) -> bool:
        """Validate that required files exist for a phase."""
        if phase == Phase.REQUIREMENTS:
            return True  # No file required to start requirements
        elif phase == Phase.DESIGN:
            return spec.get_requirements_path().exists()
        elif phase == Phase.TASKS:
            return (
                spec.get_requirements_path().exists()
                and spec.get_design_path().exists()
            )
        elif phase == Phase.COMPLETE:
            return (
                spec.get_requirements_path().exists()
                and spec.get_design_path().exists()
                and spec.get_tasks_path().exists()
            )
        return False

    def _get_available_transitions(self, current_phase: Phase) -> List[str]:
        """Get list of available phase transitions."""
        transitions = []

        # Can always stay in current phase
        transitions.append(current_phase.value)

        # Can go back to previous phases
        current_index = self.phase_order.index(current_phase)
        for i in range(current_index):
            transitions.append(self.phase_order[i].value)

        # Can advance to next phase if not at end
        if current_index < len(self.phase_order) - 1:
            transitions.append(self.phase_order[current_index + 1].value)

        return transitions
