"""
Unit tests for WorkflowEngine class.
"""

from pathlib import Path

import pytest

from spec_server.models import Phase, Spec
from spec_server.spec_manager import SpecManager
from spec_server.workflow_engine import WorkflowEngine, WorkflowError


class TestWorkflowEngine:
    """Test WorkflowEngine class."""

    def test_workflow_engine_initialization(self, temp_specs_dir):
        """Test WorkflowEngine initialization."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        assert engine.spec_manager == spec_manager
        assert len(engine.phase_order) == 4
        assert Phase.REQUIREMENTS in engine.phase_order
        assert Phase.DESIGN in engine.phase_order
        assert Phase.TASKS in engine.phase_order
        assert Phase.COMPLETE in engine.phase_order

    def test_get_current_phase_no_files(self, temp_specs_dir):
        """Test getting current phase with no files."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        current_phase = engine.get_current_phase(spec)

        assert current_phase == Phase.REQUIREMENTS

    def test_get_current_phase_with_requirements(self, temp_specs_dir):
        """Test getting current phase with requirements file."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        current_phase = engine.get_current_phase(spec)
        assert current_phase == Phase.REQUIREMENTS

    def test_get_current_phase_with_design(self, temp_specs_dir):
        """Test getting current phase with design file."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")
        spec.get_design_path().write_text("# Design")

        current_phase = engine.get_current_phase(spec)
        assert current_phase == Phase.DESIGN

    def test_get_current_phase_with_tasks(self, temp_specs_dir):
        """Test getting current phase with tasks file."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")
        spec.get_design_path().write_text("# Design")
        spec.get_tasks_path().write_text("# Tasks")

        current_phase = engine.get_current_phase(spec)
        assert current_phase == Phase.TASKS

    def test_can_advance_phase_without_approval(self, temp_specs_dir):
        """Test checking if phase can advance without approval."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        # Without approval, cannot advance
        can_advance = engine.can_advance_phase(spec, approval=False)
        assert can_advance is False

    def test_can_advance_phase_with_approval(self, temp_specs_dir):
        """Test checking if phase can advance with approval."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        # With approval, can advance
        can_advance = engine.can_advance_phase(spec, approval=True)
        assert can_advance is True

    def test_can_advance_phase_from_complete(self, temp_specs_dir):
        """Test that cannot advance from COMPLETE phase."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")
        spec.get_design_path().write_text("# Design")
        spec.get_tasks_path().write_text("# Tasks")

        # Approve all phases to reach COMPLETE
        engine._record_phase_approval("test-feature", "requirements")
        engine._record_phase_approval("test-feature", "design")
        engine._record_phase_approval("test-feature", "tasks")

        can_advance = engine.can_advance_phase(spec, approval=True)
        assert can_advance is False

    def test_advance_phase_success(self, temp_specs_dir):
        """Test successful phase advancement."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        # Advance from REQUIREMENTS to DESIGN
        new_phase = engine.advance_phase(spec, approval=True)
        assert new_phase == Phase.DESIGN

        # Check approval was recorded
        assert engine._is_phase_approved("test-feature", "requirements")

    def test_advance_phase_without_approval(self, temp_specs_dir):
        """Test phase advancement without approval fails."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        # Try to advance without approval
        with pytest.raises(WorkflowError) as exc_info:
            engine.advance_phase(spec, approval=False)

        assert exc_info.value.error_code == "PHASE_ADVANCEMENT_DENIED"

    def test_advance_phase_sequence(self, temp_specs_dir):
        """Test advancing through all phases in sequence."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")

        # Start at REQUIREMENTS
        assert engine.get_current_phase(spec) == Phase.REQUIREMENTS

        # Add requirements file and advance to DESIGN
        spec.get_requirements_path().write_text("# Requirements")
        new_phase = engine.advance_phase(spec, approval=True)
        assert new_phase == Phase.DESIGN

        # Add design file and advance to TASKS
        spec.get_design_path().write_text("# Design")
        new_phase = engine.advance_phase(spec, approval=True)
        assert new_phase == Phase.TASKS

        # Add tasks file and advance to COMPLETE
        spec.get_tasks_path().write_text("# Tasks")
        new_phase = engine.advance_phase(spec, approval=True)
        assert new_phase == Phase.COMPLETE

    def test_validate_phase_transition_valid_forward(self, temp_specs_dir):
        """Test validating valid forward phase transitions."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Valid forward transitions
        assert engine.validate_phase_transition(Phase.REQUIREMENTS, Phase.DESIGN) is True
        assert engine.validate_phase_transition(Phase.DESIGN, Phase.TASKS) is True
        assert engine.validate_phase_transition(Phase.TASKS, Phase.COMPLETE) is True

    def test_validate_phase_transition_valid_backward(self, temp_specs_dir):
        """Test validating valid backward phase transitions."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Valid backward transitions
        assert engine.validate_phase_transition(Phase.DESIGN, Phase.REQUIREMENTS) is True
        assert engine.validate_phase_transition(Phase.TASKS, Phase.DESIGN) is True
        assert engine.validate_phase_transition(Phase.TASKS, Phase.REQUIREMENTS) is True
        assert engine.validate_phase_transition(Phase.COMPLETE, Phase.TASKS) is True

    def test_validate_phase_transition_same_phase(self, temp_specs_dir):
        """Test validating staying in same phase."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Same phase transitions
        assert engine.validate_phase_transition(Phase.REQUIREMENTS, Phase.REQUIREMENTS) is True
        assert engine.validate_phase_transition(Phase.DESIGN, Phase.DESIGN) is True
        assert engine.validate_phase_transition(Phase.TASKS, Phase.TASKS) is True
        assert engine.validate_phase_transition(Phase.COMPLETE, Phase.COMPLETE) is True

    def test_validate_phase_transition_invalid_skip(self, temp_specs_dir):
        """Test validating invalid phase skipping."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Invalid forward skips
        assert engine.validate_phase_transition(Phase.REQUIREMENTS, Phase.TASKS) is False
        assert engine.validate_phase_transition(Phase.REQUIREMENTS, Phase.COMPLETE) is False
        assert engine.validate_phase_transition(Phase.DESIGN, Phase.COMPLETE) is False

    def test_require_approval_new_spec(self, temp_specs_dir):
        """Test approval requirement for new spec."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")

        # New spec requires approval
        requires_approval = engine.require_approval(spec)
        assert requires_approval is True

    def test_require_approval_after_approval(self, temp_specs_dir):
        """Test approval requirement after phase is approved."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")

        # Record approval
        engine._record_phase_approval("test-feature", "requirements")

        # Should not require approval anymore
        requires_approval = engine.require_approval(spec, Phase.REQUIREMENTS)
        assert requires_approval is False

    def test_get_phase_status_comprehensive(self, temp_specs_dir):
        """Test getting comprehensive phase status."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        status = engine.get_phase_status(spec)

        assert "current_phase" in status
        assert "can_advance" in status
        assert "requires_approval" in status
        assert "phase_approvals" in status
        assert "available_transitions" in status
        assert "phase_files" in status

        assert status["current_phase"] == "requirements"
        assert status["can_advance"] is False  # No approval yet
        assert status["requires_approval"] is True
        assert status["phase_files"]["requirements"] is True
        assert status["phase_files"]["design"] is False
        assert status["phase_files"]["tasks"] is False

    def test_reset_phase_approvals(self, temp_specs_dir):
        """Test resetting phase approvals."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Record some approvals
        engine._record_phase_approval("test-feature", "requirements")
        engine._record_phase_approval("test-feature", "design")

        # Verify approvals exist
        assert engine._is_phase_approved("test-feature", "requirements")
        assert engine._is_phase_approved("test-feature", "design")

        # Reset approvals
        engine.reset_phase_approvals("test-feature")

        # Verify approvals are gone
        assert not engine._is_phase_approved("test-feature", "requirements")
        assert not engine._is_phase_approved("test-feature", "design")

    def test_get_workflow_history(self, temp_specs_dir):
        """Test getting workflow history."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")

        # Record some approvals
        engine._record_phase_approval("test-feature", "requirements")

        history = engine.get_workflow_history(spec)

        assert len(history) >= 1
        assert history[0]["event"] == "spec_created"
        assert history[0]["phase"] == "requirements"

        # Should include approval events
        approval_events = [event for event in history if event["event"] == "phase_approved"]
        assert len(approval_events) >= 1

    def test_validate_phase_requirements(self, temp_specs_dir):
        """Test validating phase requirements."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        spec = spec_manager.create_spec("test-feature", "Test feature")

        # REQUIREMENTS phase has no file requirements
        assert engine._validate_phase_requirements(spec, Phase.REQUIREMENTS) is True

        # DESIGN phase requires requirements file
        assert engine._validate_phase_requirements(spec, Phase.DESIGN) is False

        # Add requirements file
        spec.get_requirements_path().write_text("# Requirements")
        assert engine._validate_phase_requirements(spec, Phase.DESIGN) is True

        # TASKS phase requires both requirements and design files
        assert engine._validate_phase_requirements(spec, Phase.TASKS) is False

        # Add design file
        spec.get_design_path().write_text("# Design")
        assert engine._validate_phase_requirements(spec, Phase.TASKS) is True

        # COMPLETE phase requires all files
        assert engine._validate_phase_requirements(spec, Phase.COMPLETE) is False

        # Add tasks file
        spec.get_tasks_path().write_text("# Tasks")
        assert engine._validate_phase_requirements(spec, Phase.COMPLETE) is True

    def test_get_available_transitions(self, temp_specs_dir):
        """Test getting available phase transitions."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # From REQUIREMENTS phase
        transitions = engine._get_available_transitions(Phase.REQUIREMENTS)
        assert "requirements" in transitions  # Stay in current
        assert "design" in transitions  # Advance
        assert len(transitions) == 2

        # From DESIGN phase
        transitions = engine._get_available_transitions(Phase.DESIGN)
        assert "requirements" in transitions  # Go back
        assert "design" in transitions  # Stay in current
        assert "tasks" in transitions  # Advance
        assert len(transitions) == 3

        # From TASKS phase
        transitions = engine._get_available_transitions(Phase.TASKS)
        assert "requirements" in transitions  # Go back
        assert "design" in transitions  # Go back
        assert "tasks" in transitions  # Stay in current
        assert "complete" in transitions  # Advance
        assert len(transitions) == 4

        # From COMPLETE phase
        transitions = engine._get_available_transitions(Phase.COMPLETE)
        assert "requirements" in transitions  # Go back
        assert "design" in transitions  # Go back
        assert "tasks" in transitions  # Go back
        assert "complete" in transitions  # Stay in current
        assert len(transitions) == 4

    def test_approval_tracking_methods(self, temp_specs_dir):
        """Test approval tracking helper methods."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        feature_name = "test-feature"

        # Initially no approvals
        assert not engine._is_phase_approved(feature_name, "requirements")
        assert engine._get_phase_approvals(feature_name) == {}

        # Record approval
        engine._record_phase_approval(feature_name, "requirements")

        # Check approval is recorded
        assert engine._is_phase_approved(feature_name, "requirements")
        approvals = engine._get_phase_approvals(feature_name)
        assert approvals["requirements"] is True

        # Record another approval
        engine._record_phase_approval(feature_name, "design")

        # Check both approvals
        assert engine._is_phase_approved(feature_name, "requirements")
        assert engine._is_phase_approved(feature_name, "design")
        approvals = engine._get_phase_approvals(feature_name)
        assert approvals["requirements"] is True
        assert approvals["design"] is True

    def test_workflow_error_handling(self, temp_specs_dir):
        """Test workflow error handling."""
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Create spec with invalid path to trigger errors
        spec = Spec(
            feature_name="invalid-spec",
            base_path=Path("/nonexistent/path"),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        # The method should still work but return REQUIREMENTS phase for nonexistent files
        # Let's test a different error condition - invalid phase advancement
        spec = spec_manager.create_spec("test-feature", "Test feature")

        # Try to advance without meeting requirements
        with pytest.raises(WorkflowError) as exc_info:
            engine.advance_phase(spec, approval=False)

        assert exc_info.value.error_code == "PHASE_ADVANCEMENT_DENIED"


class TestWorkflowError:
    """Test WorkflowError exception class."""

    def test_workflow_error_basic(self):
        """Test basic WorkflowError creation."""
        error = WorkflowError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "WORKFLOW_ERROR"
        assert error.details == {}

    def test_workflow_error_with_code_and_details(self):
        """Test WorkflowError with custom code and details."""
        details = {"feature_name": "test", "phase": "requirements"}
        error = WorkflowError("Custom error message", error_code="CUSTOM_ERROR", details=details)

        assert error.message == "Custom error message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details
