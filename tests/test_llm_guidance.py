"""
Tests for the LLM guidance functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_server.errors import ErrorCode, SpecError
from spec_server.llm_guidance import get_introduction_prompt, get_llm_guidance_content, get_phase_guidance_content


class TestGetLlmGuidanceContent:
    """Test cases for get_llm_guidance_content function."""

    def test_get_guidance_content_success(self):
        """Test successful retrieval when document exists."""
        # This test uses the actual guidance document
        content = get_llm_guidance_content()

        assert isinstance(content, str)
        assert len(content) > 0
        assert "LLM Guidance for spec-server" in content
        assert "Overview of the Workflow Process" in content

    @patch("spec_server.llm_guidance.DOCS_DIR")
    def test_get_guidance_content_document_not_found(self, mock_docs_dir):
        """Test error handling when document doesn't exist."""
        # Create a temporary directory without the guidance document
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            with pytest.raises(SpecError) as exc_info:
                get_llm_guidance_content()

            error = exc_info.value
            assert error.error_code == ErrorCode.DOCUMENT_NOT_FOUND
            assert "LLM guidance document not found at path:" in error.message
            assert error.details["error_type"] == "FileNotFoundError"

    @patch("spec_server.llm_guidance.DOCS_DIR")
    def test_get_guidance_content_permission_error(self, mock_docs_dir):
        """Test error handling for permission issues."""
        # Create a temporary file with restricted permissions
        with tempfile.TemporaryDirectory() as temp_dir:
            guidance_file = Path(temp_dir) / "llm-guidance.md"
            guidance_file.write_text("test content")
            guidance_file.chmod(0o000)  # Remove all permissions

            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            try:
                with pytest.raises(SpecError) as exc_info:
                    get_llm_guidance_content()

                error = exc_info.value
                assert error.error_code == ErrorCode.FILE_ACCESS_DENIED
                assert "Permission denied reading LLM guidance document:" in error.message
                assert error.details["error_type"] == "PermissionError"
            finally:
                # Restore permissions for cleanup
                guidance_file.chmod(0o644)

    @patch("spec_server.llm_guidance.DOCS_DIR")
    def test_get_guidance_content_encoding_error(self, mock_docs_dir):
        """Test error handling for encoding issues."""
        # Create a temporary file with invalid UTF-8 content
        with tempfile.TemporaryDirectory() as temp_dir:
            guidance_file = Path(temp_dir) / "llm-guidance.md"
            # Write invalid UTF-8 bytes
            guidance_file.write_bytes(b"\xff\xfe\x00\x00invalid utf-8")

            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            with pytest.raises(SpecError) as exc_info:
                get_llm_guidance_content()

            error = exc_info.value
            assert error.error_code == ErrorCode.INTERNAL_ERROR
            assert "Encoding error reading LLM guidance document:" in error.message
            assert error.details["error_type"] == "UnicodeDecodeError"
            assert error.details["encoding"] == "utf-8"

    @patch("spec_server.llm_guidance.DOCS_DIR")
    @patch("pathlib.Path.read_text")
    def test_get_guidance_content_unexpected_error(self, mock_read_text, mock_docs_dir):
        """Test error handling for unexpected errors."""
        # Create a temporary directory with the guidance file
        with tempfile.TemporaryDirectory() as temp_dir:
            guidance_file = Path(temp_dir) / "llm-guidance.md"
            guidance_file.write_text("test content")

            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            # Mock read_text to raise an unexpected error
            mock_read_text.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(SpecError) as exc_info:
                get_llm_guidance_content()

            error = exc_info.value
            assert error.error_code == ErrorCode.INTERNAL_ERROR
            assert "Unexpected error reading LLM guidance document:" in error.message
            assert error.details["error_type"] == "RuntimeError"


class TestGetPhaseGuidanceContent:
    """Test cases for get_phase_guidance_content function."""

    def test_get_requirements_guidance(self):
        """Test getting requirements phase guidance."""
        guidance = get_phase_guidance_content("requirements")

        assert isinstance(guidance, dict)
        assert "questions_to_ask" in guidance
        assert "template" in guidance
        assert "best_practices" in guidance
        assert "conversation_starters" in guidance

        # Check specific content
        assert "Who will use this feature?" in guidance["questions_to_ask"]
        assert "# Requirements Document" in guidance["template"]

    def test_requirements_numbering_system(self):
        """Test that requirements guidance includes proper numbering system."""
        guidance = get_phase_guidance_content("requirements")
        template = guidance["template"]

        # Check for proper requirement numbering
        assert "### Requirement 1" in template
        assert "### Requirement 2" in template

        # Check for proper acceptance criteria numbering
        assert "#### Acceptance Criteria" in template
        assert "1. WHEN" in template
        assert "2. WHEN" in template
        assert "3. WHEN" in template

        # Check for EARS format
        assert "THEN the system SHALL" in template

        # Check best practices include numbering guidance
        best_practices = guidance["best_practices"]
        numbering_practices = [practice for practice in best_practices if "number" in practice.lower()]
        assert len(numbering_practices) >= 2, "Should have practices about numbering requirements and criteria"

    def test_get_design_guidance(self):
        """Test getting design phase guidance."""
        guidance = get_phase_guidance_content("design")

        assert isinstance(guidance, dict)
        assert "questions_to_ask" in guidance
        assert "template" in guidance
        assert "best_practices" in guidance
        assert "conversation_starters" in guidance

        # Check specific content
        assert "What architecture approach makes sense?" in guidance["questions_to_ask"]
        assert "# Design for [Feature Name]" in guidance["template"]

    def test_get_tasks_guidance(self):
        """Test getting tasks phase guidance."""
        guidance = get_phase_guidance_content("tasks")

        assert isinstance(guidance, dict)
        assert "questions_to_ask" in guidance
        assert "template" in guidance
        assert "best_practices" in guidance
        assert "conversation_starters" in guidance

        # Check specific content
        assert "Should we use a particular development methodology?" in guidance["questions_to_ask"]
        assert "# Implementation Plan" in guidance["template"]

    def test_tasks_requirement_references(self):
        """Test that tasks guidance includes proper requirement reference format."""
        guidance = get_phase_guidance_content("tasks")
        template = guidance["template"]

        # Check for requirement reference format
        assert "_Requirements:" in template
        assert "1.1, 1.2, 2.1" in template
        assert "1.3, 2.2, 3.1" in template
        assert "2.1, 2.3, 3.2" in template

        # Check for explanation of numbering system
        assert "requirement.criteria" in template

        # Check that template explains the reference format
        assert "Requirement 1, Acceptance Criteria 1" in template or "requirement.criteria" in template

    def test_get_general_guidance(self):
        """Test getting general guidance."""
        guidance = get_phase_guidance_content("general")

        assert isinstance(guidance, dict)
        assert "workflow_overview" in guidance
        assert "conversation_approach" in guidance
        assert "best_practices" in guidance
        assert "conversation_starters" in guidance

        # Check specific content
        assert "Requirements Phase: Define what needs to be built" in guidance["workflow_overview"]

    def test_get_guidance_default_general(self):
        """Test that default phase returns general guidance."""
        guidance_default = get_phase_guidance_content()
        guidance_general = get_phase_guidance_content("general")

        assert guidance_default == guidance_general

    def test_get_guidance_invalid_phase(self):
        """Test that invalid phase returns general guidance."""
        guidance_invalid = get_phase_guidance_content("invalid_phase")
        guidance_general = get_phase_guidance_content("general")

        assert guidance_invalid == guidance_general

    def test_get_guidance_case_insensitive(self):
        """Test that phase names are case insensitive."""
        guidance_upper = get_phase_guidance_content("REQUIREMENTS")
        guidance_lower = get_phase_guidance_content("requirements")

        assert guidance_upper == guidance_lower


class TestRequirementNumberingSystem:
    """Test cases for requirement numbering system documentation."""

    def test_numbering_system_consistency(self):
        """Test that numbering system is consistently documented across guidance."""
        requirements_guidance = get_phase_guidance_content("requirements")
        tasks_guidance = get_phase_guidance_content("tasks")

        # Requirements should show proper numbering structure
        req_template = requirements_guidance["template"]
        assert "### Requirement 1" in req_template
        assert "### Requirement 2" in req_template
        assert "1. WHEN" in req_template
        assert "2. WHEN" in req_template

        # Tasks should show proper reference format
        task_template = tasks_guidance["template"]
        assert "_Requirements: 1.1, 1.2, 2.1_" in task_template
        assert "_Requirements: 1.3, 2.2, 3.1_" in task_template

        # Both should be consistent in their numbering approach
        assert "requirement.criteria" in task_template

    def test_ears_format_documentation(self):
        """Test that EARS format is properly documented."""
        guidance = get_phase_guidance_content("requirements")
        template = guidance["template"]

        # Check for EARS format elements
        assert "WHEN [condition] THEN the system SHALL [response]" in template

        # Check that best practices mention EARS
        best_practices = guidance["best_practices"]
        ears_practices = [practice for practice in best_practices if "EARS" in practice or "WHEN/THEN/SHALL" in practice]
        assert len(ears_practices) >= 1, "Should have practices about EARS format"

    def test_traceability_documentation(self):
        """Test that traceability from tasks to requirements is documented."""
        tasks_guidance = get_phase_guidance_content("tasks")

        # Check that the template explains the reference system
        template = tasks_guidance["template"]
        assert "requirement.criteria" in template

        # Check that best practices mention traceability
        best_practices = tasks_guidance["best_practices"]
        reference_practices = [practice for practice in best_practices if "reference" in practice.lower() or "requirements" in practice.lower()]
        assert len(reference_practices) >= 1, "Should have practices about referencing requirements"


class TestGetIntroductionPrompt:
    """Test cases for get_introduction_prompt function."""

    def test_get_introduction_prompt(self):
        """Test getting the introduction prompt."""
        prompt = get_introduction_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "REQUIREMENTS" in prompt
        assert "DESIGN" in prompt
        assert "TASKS" in prompt
        assert "What feature would you like to develop?" in prompt
