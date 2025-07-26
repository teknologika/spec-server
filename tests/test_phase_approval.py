"""
Tests for phase approval functionality to ensure specs are never auto-approved.
"""

from spec_server.mcp_tools import MCPTools
from spec_server.spec_manager import SpecManager
from spec_server.workflow_engine import WorkflowEngine


class TestPhaseApproval:
    """Test phase approval functionality."""

    def test_explicit_approval_required(self, temp_specs_dir):
        """Test that explicit approval is required for phase advancement."""
        # Initialize components
        spec_manager = SpecManager(temp_specs_dir)
        engine = WorkflowEngine(spec_manager)

        # Create a spec
        spec = spec_manager.create_spec("test-feature", "Test feature")
        spec.get_requirements_path().write_text("# Requirements")

        # Without explicit approval, cannot advance
        assert not engine.can_advance_phase(spec, approval=False)

        # With explicit approval, can advance
        assert engine.can_advance_phase(spec, approval=True)

    def test_update_document_without_approval(self, temp_specs_dir):
        """Test that updating a document without approval doesn't advance phase."""
        # Initialize components
        mcp_tools = MCPTools(temp_specs_dir)

        # Create a spec
        mcp_tools.create_spec("test-feature", "Test feature")

        # Update document without approval
        result = mcp_tools.update_spec_document(
            "test-feature",
            "requirements",
            "# Updated Requirements",
            phase_approval=False,
        )

        # Verify phase hasn't changed
        assert result["current_phase"] == "requirements"
        assert result["requires_approval"] is True

    def test_update_document_with_approval(self, temp_specs_dir):
        """Test that updating a document with approval advances phase."""
        # Initialize components
        mcp_tools = MCPTools(temp_specs_dir)

        # Create a spec
        mcp_tools.create_spec("test-feature", "Test feature")

        # Update document with approval
        result = mcp_tools.update_spec_document(
            "test-feature",
            "requirements",
            "# Updated Requirements",
            phase_approval=True,
        )

        # Verify phase has advanced
        assert result["current_phase"] == "design"

    def test_multiple_phase_transitions(self, temp_specs_dir):
        """Test multiple phase transitions with explicit approval."""
        # Initialize components
        mcp_tools = MCPTools(temp_specs_dir)

        # Create a spec
        mcp_tools.create_spec("test-feature", "Test feature")

        # Update requirements with approval to advance to design
        result1 = mcp_tools.update_spec_document(
            "test-feature",
            "requirements",
            "# Updated Requirements",
            phase_approval=True,
        )
        assert result1["current_phase"] == "design"

        # Update design with approval to advance to tasks
        result2 = mcp_tools.update_spec_document("test-feature", "design", "# Design Document", phase_approval=True)
        assert result2["current_phase"] == "tasks"

        # Update tasks with approval to advance to complete
        result3 = mcp_tools.update_spec_document("test-feature", "tasks", "# Tasks Document", phase_approval=True)
        assert result3["current_phase"] == "complete"
