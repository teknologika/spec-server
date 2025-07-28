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
        assert "# Requirements for [Feature Name]" in guidance["template"]

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
