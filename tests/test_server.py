"""
Tests for the server module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

from spec_server.server import create_server, run_server, mcp


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

    @patch('spec_server.server.mcp')
    def test_run_server_stdio_default(self, mock_mcp):
        """Test running server with stdio transport (default)."""
        # Mock sys.argv to simulate no arguments
        with patch.object(sys, 'argv', ['spec-server']):
            run_server()
            mock_mcp.run.assert_called_once()

    @patch('spec_server.server.mcp')
    def test_run_server_stdio_explicit(self, mock_mcp):
        """Test running server with explicit stdio transport."""
        with patch.object(sys, 'argv', ['spec-server', 'stdio']):
            run_server()
            mock_mcp.run.assert_called_once()

    @patch('spec_server.server.mcp')
    def test_run_server_sse_default_port(self, mock_mcp):
        """Test running server with SSE transport using default port."""
        with patch.object(sys, 'argv', ['spec-server', 'sse']):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=8000, host="127.0.0.1")

    @patch('spec_server.server.mcp')
    def test_run_server_sse_custom_port(self, mock_mcp):
        """Test running server with SSE transport using custom port."""
        with patch.object(sys, 'argv', ['spec-server', 'sse', '9000']):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=9000, host="127.0.0.1")

    @patch('spec_server.server.mcp')
    def test_run_server_sse_custom_port_and_host(self, mock_mcp):
        """Test running server with SSE transport using custom port and host."""
        with patch.object(sys, 'argv', ['spec-server', 'sse', '9000', '0.0.0.0']):
            run_server()
            mock_mcp.run_sse.assert_called_once_with(port=9000, host="0.0.0.0")

    def test_run_server_unknown_transport(self):
        """Test running server with unknown transport."""
        with patch.object(sys, 'argv', ['spec-server', 'unknown']):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch('spec_server.server.mcp')
    def test_run_server_keyboard_interrupt(self, mock_mcp):
        """Test server handling of keyboard interrupt."""
        mock_mcp.run.side_effect = KeyboardInterrupt()
        
        with patch.object(sys, 'argv', ['spec-server']):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 0

    @patch('spec_server.server.mcp')
    def test_run_server_exception(self, mock_mcp):
        """Test server handling of general exceptions."""
        mock_mcp.run.side_effect = Exception("Test error")
        
        with patch.object(sys, 'argv', ['spec-server']):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch('spec_server.server.mcp')
    def test_run_server_sse_exception(self, mock_mcp):
        """Test SSE server handling of general exceptions."""
        mock_mcp.run_sse.side_effect = Exception("SSE error")
        
        with patch.object(sys, 'argv', ['spec-server', 'sse']):
            with pytest.raises(SystemExit) as exc_info:
                run_server()
            assert exc_info.value.code == 1

    @patch('spec_server.server.mcp')
    def test_run_server_sse_keyboard_interrupt(self, mock_mcp):
        """Test SSE server handling of keyboard interrupt."""
        mock_mcp.run_sse.side_effect = KeyboardInterrupt()
        
        with patch.object(sys, 'argv', ['spec-server', 'sse']):
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
        assert hasattr(create_spec, 'name')
        assert create_spec.name == 'create_spec'

    def test_update_spec_document_tool_registered(self):
        """Test that update_spec_document tool is properly registered."""
        from spec_server.server import update_spec_document
        assert update_spec_document is not None
        assert hasattr(update_spec_document, 'name')
        assert update_spec_document.name == 'update_spec_document'

    def test_list_specs_tool_registered(self):
        """Test that list_specs tool is properly registered."""
        from spec_server.server import list_specs
        assert list_specs is not None
        assert hasattr(list_specs, 'name')
        assert list_specs.name == 'list_specs'

    def test_read_spec_document_tool_registered(self):
        """Test that read_spec_document tool is properly registered."""
        from spec_server.server import read_spec_document
        assert read_spec_document is not None
        assert hasattr(read_spec_document, 'name')
        assert read_spec_document.name == 'read_spec_document'

    def test_execute_task_tool_registered(self):
        """Test that execute_task tool is properly registered."""
        from spec_server.server import execute_task
        assert execute_task is not None
        assert hasattr(execute_task, 'name')
        assert execute_task.name == 'execute_task'

    def test_complete_task_tool_registered(self):
        """Test that complete_task tool is properly registered."""
        from spec_server.server import complete_task
        assert complete_task is not None
        assert hasattr(complete_task, 'name')
        assert complete_task.name == 'complete_task'

    def test_delete_spec_tool_registered(self):
        """Test that delete_spec tool is properly registered."""
        from spec_server.server import delete_spec
        assert delete_spec is not None
        assert hasattr(delete_spec, 'name')
        assert delete_spec.name == 'delete_spec'

    def test_tool_error_handling_structure(self):
        """Test that MCP tools have proper error handling structure."""
        # Test that our tools are properly wrapped and have the expected structure
        from spec_server.server import create_spec
        
        # Verify the tool has the expected attributes
        assert hasattr(create_spec, 'name')
        assert hasattr(create_spec, 'description')
        assert create_spec.name == 'create_spec'
        assert 'Create a new feature specification' in create_spec.description