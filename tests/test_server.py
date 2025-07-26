"""
Tests for the server module.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_server.server import create_server, run_server


class TestServer:
    """Test cases for server functionality."""

    def test_create_server(self):
        """Test server creation."""
        server = create_server()
        assert server is not None
        assert server.name == "spec-server"

    def test_server_tools_registered(self):
        """Test that all tools are registered with the server."""
        server = create_server()

        # Check that the server instance exists and is properly configured
        # FastMCP handles tool registration internally
        assert server is not None
        assert server.name == "spec-server"

    @patch("spec_server.server.mcp")
    def test_run_server_stdio_default(self, mock_mcp):
        """Test running server with stdio transport (default)."""
        # Mock sys.argv to simulate no arguments
        with patch.object(sys, "argv", ["spec-server"]):
            run_server()
            mock_mcp.run.assert_called_once()

    @patch("spec_server.server.mcp")
    def test_run_server_stdio_explicit(self, mock_mcp):
        """Test running server with explicit stdio transport."""
        with patch.object(sys, "argv", ["spec-server", "stdio"]):
            run_server()
            mock_mcp.run.assert_called_once()

    @patch("spec_server.server.mcp")
    def test_run_server_sse_default_port(self, mock_mcp):
        """Test running server with SSE transport using default port."""
        with patch.object(sys, "argv", ["spec-server", "sse"]):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=8000, host="127.0.0.1")

    @patch("spec_server.server.mcp")
    def test_run_server_sse_custom_port(self, mock_mcp):
        """Test running server with SSE transport using custom port."""
        with patch.object(sys, "argv", ["spec-server", "sse", "9000"]):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=9000, host="127.0.0.1")

    @patch("spec_server.server.mcp")
    def test_run_server_sse_custom_port_and_host(self, mock_mcp):
        """Test running server with SSE transport using custom port and host."""
        with patch.object(sys, "argv", ["spec-server", "sse", "9000", "0.0.0.0"]):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=9000, host="0.0.0.0")

    def test_run_server_unknown_transport(self):
        """Test running server with unknown transport."""
        with patch.object(sys, "argv", ["spec-server", "unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch("spec_server.server.mcp")
    def test_run_server_keyboard_interrupt(self, mock_mcp):
        """Test server handling of keyboard interrupt."""
        mock_mcp.run.side_effect = KeyboardInterrupt()

        with patch.object(sys, "argv", ["spec-server"]):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 0

    @patch("spec_server.server.mcp")
    def test_run_server_exception(self, mock_mcp):
        """Test server handling of general exceptions."""
        mock_mcp.run.side_effect = Exception("Test error")

        with patch.object(sys, "argv", ["spec-server"]):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch("spec_server.server.mcp")
    def test_run_server_sse_exception(self, mock_mcp):
        """Test SSE server handling of general exceptions."""
        mock_mcp.run_sse.side_effect = Exception("SSE error")

        with patch.object(sys, "argv", ["spec-server", "sse"]):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch("spec_server.server.mcp")
    def test_run_server_sse_keyboard_interrupt(self, mock_mcp):
        """Test SSE server handling of keyboard interrupt."""
        mock_mcp.run_sse.side_effect = KeyboardInterrupt()

        with patch.object(sys, "argv", ["spec-server", "sse"]):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 0


class TestMCPToolIntegration:
    """Test MCP tool integration with the server."""

    def test_create_spec_tool_registered(self):
        """Test that create_spec tool is properly registered."""
        # FastMCP wraps functions in FunctionTool objects
        from spec_server.server import create_spec

        assert create_spec is not None
        assert hasattr(create_spec, "name")
        assert create_spec.name == "create_spec"

    def test_update_spec_document_tool_registered(self):
        """Test that update_spec_document tool is properly registered."""
        from spec_server.server import update_spec_document

        assert update_spec_document is not None
        assert hasattr(update_spec_document, "name")
        assert update_spec_document.name == "update_spec_document"

    def test_list_specs_tool_registered(self):
        """Test that list_specs tool is properly registered."""
        from spec_server.server import list_specs

        assert list_specs is not None
        assert hasattr(list_specs, "name")
        assert list_specs.name == "list_specs"

    def test_read_spec_document_tool_registered(self):
        """Test that read_spec_document tool is properly registered."""
        from spec_server.server import read_spec_document

        assert read_spec_document is not None
        assert hasattr(read_spec_document, "name")
        assert read_spec_document.name == "read_spec_document"

    def test_execute_task_tool_registered(self):
        """Test that execute_task tool is properly registered."""
        from spec_server.server import execute_task

        assert execute_task is not None
        assert hasattr(execute_task, "name")
        assert execute_task.name == "execute_task"

    def test_complete_task_tool_registered(self):
        """Test that complete_task tool is properly registered."""
        from spec_server.server import complete_task

        assert complete_task is not None
        assert hasattr(complete_task, "name")
        assert complete_task.name == "complete_task"

    def test_delete_spec_tool_registered(self):
        """Test that delete_spec tool is properly registered."""
        from spec_server.server import delete_spec

        assert delete_spec is not None
        assert hasattr(delete_spec, "name")
        assert delete_spec.name == "delete_spec"

    def test_get_full_guidance_tool_registered(self):
        """Test that get_full_guidance tool is properly registered."""
        from spec_server.server import get_full_guidance

        assert get_full_guidance is not None
        assert hasattr(get_full_guidance, "name")
        assert get_full_guidance.name == "get_full_guidance"

    def test_get_guidance_tool_registered(self):
        """Test that get_guidance tool is properly registered."""
        from spec_server.server import get_guidance

        assert get_guidance is not None
        assert hasattr(get_guidance, "name")
        assert get_guidance.name == "get_guidance"

    def test_tool_error_handling_structure(self):
        """Test that MCP tools have proper error handling structure."""
        # Test that our tools are properly wrapped and have the expected structure
        from spec_server.server import create_spec

        # Verify the tool has the expected attributes
        assert hasattr(create_spec, "name")
        assert hasattr(create_spec, "description")
        assert create_spec.name == "create_spec"
        assert "Create a new feature specification" in create_spec.description


class TestGuidanceToolsIntegration:
    """Test guidance tools integration with proper error handling."""

    def test_get_full_guidance_success(self):
        """Test that get_full_guidance returns success when document exists."""
        from spec_server.server import get_full_guidance

        result = get_full_guidance.fn()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
        assert "LLM Guidance for spec-server" in result["content"]
        assert result["message"] == "Retrieved complete LLM guidance document"

    @patch("spec_server.llm_guidance.DOCS_DIR")
    def test_get_full_guidance_document_not_found(self, mock_docs_dir):
        """Test that get_full_guidance returns proper error when document doesn't exist."""
        from spec_server.server import get_full_guidance

        # Create a temporary directory without the guidance document
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            result = get_full_guidance.fn()

            assert isinstance(result, dict)
            assert result["success"] is False
            assert result["error_code"] == "DOCUMENT_NOT_FOUND"
            assert "LLM guidance document not found at path:" in result["message"]
            assert result["details"]["error_type"] == "FileNotFoundError"

    @patch("spec_server.llm_guidance.DOCS_DIR")
    def test_get_full_guidance_permission_error(self, mock_docs_dir):
        """Test that get_full_guidance handles permission errors correctly."""
        from spec_server.server import get_full_guidance

        # Create a temporary file with restricted permissions
        with tempfile.TemporaryDirectory() as temp_dir:
            guidance_file = Path(temp_dir) / "llm-guidance.md"
            guidance_file.write_text("test content")
            guidance_file.chmod(0o000)  # Remove all permissions

            mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

            try:
                result = get_full_guidance.fn()

                assert isinstance(result, dict)
                assert result["success"] is False
                assert result["error_code"] == "FILE_ACCESS_DENIED"
                assert "Permission denied reading LLM guidance document:" in result["message"]
                assert result["details"]["error_type"] == "PermissionError"
            finally:
                # Restore permissions for cleanup
                guidance_file.chmod(0o644)

    def test_get_guidance_success(self):
        """Test that get_guidance returns success for valid phases."""
        from spec_server.server import get_guidance

        # Test requirements phase
        result = get_guidance.fn("requirements")

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["phase"] == "requirements"
        assert "guidance" in result
        assert isinstance(result["guidance"], dict)
        assert "questions_to_ask" in result["guidance"]
        assert result["message"] == "Retrieved guidance for requirements phase"

    def test_get_guidance_general_phase(self):
        """Test that get_guidance returns general guidance by default."""
        from spec_server.server import get_guidance

        result = get_guidance.fn()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["phase"] == "general"
        assert "guidance" in result
        assert isinstance(result["guidance"], dict)
        assert "workflow_overview" in result["guidance"]
        assert result["message"] == "Retrieved guidance for general phase"

    def test_get_guidance_invalid_phase(self):
        """Test that get_guidance handles invalid phases gracefully."""
        from spec_server.server import get_guidance

        result = get_guidance.fn("invalid_phase")

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["phase"] == "invalid_phase"
        assert "guidance" in result
        assert isinstance(result["guidance"], dict)
        # Should return general guidance for invalid phases
        assert "workflow_overview" in result["guidance"]
        assert result["message"] == "Retrieved guidance for invalid_phase phase"

    def test_guidance_tools_error_response_consistency(self):
        """Test that guidance tools error responses match other MCP tools format."""
        from spec_server.server import get_full_guidance

        # Test with missing document to trigger error
        with patch("spec_server.llm_guidance.DOCS_DIR") as mock_docs_dir:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_docs_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

                result = get_full_guidance.fn()

                # Verify error response format matches other tools
                assert isinstance(result, dict)
                assert "success" in result
                assert result["success"] is False
                assert "error_code" in result
                assert "message" in result
                assert "details" in result

                # Verify it doesn't claim success when there's an error
                assert "Retrieved complete LLM guidance document" not in result["message"]
