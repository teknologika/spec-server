"""
FastMCP server implementation for spec-server.

This module sets up the FastMCP server and registers all the MCP tools.
It supports both stdio and SSE transports with proper error handling and logging.
"""

import logging
import sys
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .errors import format_error_response
from .llm_guidance import get_llm_guidance_content, get_phase_guidance_content
from .mcp_tools import MCPTools

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the FastMCP server with proper configuration
mcp: FastMCP = FastMCP(name="spec-server", version="v0.3.0")

# Initialize MCP tools
mcp_tools = MCPTools()

# Note: The introduction prompt is available through the get_introduction_prompt() function
# and can be accessed by the LLM through the get_guidance tool


@mcp.tool()
def get_full_guidance() -> Dict[str, Any]:
    """
    Get the complete LLM guidance document.

    IMPORTANT: Use this tool to access the full guidance on how to effectively use spec-server
    through a conversational approach with users.

    Returns:
        Dictionary containing the complete LLM guidance document
    """
    try:
        content = get_llm_guidance_content()
        return {
            "success": True,
            "content": content,
            "message": "Retrieved complete LLM guidance document",
        }
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def get_guidance(phase: str = "general") -> Dict[str, Any]:
    """
    Get guidance for a specific phase of the spec-server workflow.

    IMPORTANT: Use this tool to get guidance on how to have effective conversations with users
    during different phases of the specification process.

    Args:
        phase: The phase to get guidance for ("requirements", "design", "tasks", or "general")

    Returns:
        Dictionary containing guidance for the specified phase including:
        - Questions to ask users
        - Document templates
        - Best practices
        - Conversation starters
    """
    try:
        guidance = get_phase_guidance_content(phase)
        return {
            "success": True,
            "phase": phase,
            "guidance": guidance,
            "message": f"Retrieved guidance for {phase} phase",
        }
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def create_spec(feature_name: str, initial_idea: str) -> Dict[str, Any]:
    """
    Create a new feature specification.

    IMPORTANT: Before calling this tool, have a thorough conversation with the user about:
    - Who will use this feature
    - What problem it solves
    - Key requirements and constraints
    - Success criteria

    Use the get_guidance tool with phase="requirements" for conversation starters.

    Args:
        feature_name: Kebab-case feature identifier (e.g., "user-authentication")
        initial_idea: User's rough feature description based on your discussion

    Returns:
        Dictionary containing created spec metadata and initial requirements
    """
    try:
        return mcp_tools.create_spec(feature_name, initial_idea)
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def update_spec_document(feature_name: str, document_type: str, content: str, phase_approval: bool = False) -> Dict[str, Any]:
    """
    Update a spec document and manage workflow transitions.

    IMPORTANT: Before calling this tool:
    - For requirements: Have a thorough discussion about user needs and acceptance criteria
    - For design: Discuss architecture approaches, trade-offs, and technical details
    - For tasks: Talk about implementation strategy and potential challenges
    - For phase_approval=True: Ensure the user has explicitly approved the document

    Use the get_guidance tool with phase="requirements", "design", or "tasks" for conversation starters.

    Args:
        feature_name: Target spec identifier
        document_type: "requirements", "design", or "tasks"
        content: Updated document content
        phase_approval: Whether user approves current phase for advancement

    Returns:
        Dictionary containing updated document and workflow status
    """
    try:
        return mcp_tools.update_spec_document(feature_name, document_type, content, phase_approval)
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def list_specs() -> Dict[str, Any]:
    """
    List all existing specifications with metadata.

    Returns:
        Dictionary containing list of spec metadata
    """
    try:
        return mcp_tools.list_specs()
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def read_spec_document(feature_name: str, document_type: str, resolve_references: bool = True) -> Dict[str, Any]:
    """
    Read a spec document with optional file reference resolution.

    IMPORTANT: After reading a document, review it with the user and discuss:
    - Whether it accurately captures their needs
    - If anything is missing or needs clarification
    - What questions they have about the content

    This helps ensure shared understanding before proceeding.

    Args:
        feature_name: Target spec identifier
        document_type: "requirements", "design", or "tasks"
        resolve_references: Whether to resolve #[[file:path]] references

    Returns:
        Dictionary containing document content and metadata
    """
    try:
        return mcp_tools.read_spec_document(feature_name, document_type, resolve_references)
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def execute_task(feature_name: str, task_identifier: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a specific implementation task or get the next task.

    IMPORTANT: Before executing tasks, discuss with the user:
    - The implementation approach for this specific task
    - Any dependencies or prerequisites
    - How this task relates to the overall requirements
    - Testing strategy for this functionality

    This ensures alignment on implementation details before coding begins.

    Args:
        feature_name: Target spec identifier
        task_identifier: Task number/identifier (optional - if not provided, returns next task)

    Returns:
        Dictionary containing task execution context and results
    """
    try:
        return mcp_tools.execute_task(feature_name, task_identifier)
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def complete_task(feature_name: str, task_identifier: str) -> Dict[str, Any]:
    """
    Mark a task as completed.

    IMPORTANT: Before marking a task as complete, discuss with the user:
    - Whether the implementation meets all requirements
    - If testing has been performed
    - Whether there are any outstanding issues or edge cases
    - What was learned during implementation

    This ensures quality and knowledge sharing before moving on.

    Args:
        feature_name: Target spec identifier
        task_identifier: Task number/identifier

    Returns:
        Dictionary containing updated task status and progress
    """
    try:
        return mcp_tools.complete_task(feature_name, task_identifier)
    except Exception as e:
        return format_error_response(e)


@mcp.tool()
def delete_spec(feature_name: str) -> Dict[str, Any]:
    """
    Delete a specification entirely.

    IMPORTANT: Before deleting a specification, discuss with the user:
    - Why they want to delete it
    - Whether any valuable information should be preserved
    - If they're sure they want to permanently delete it

    This prevents accidental loss of important work.

    Args:
        feature_name: Target spec identifier

    Returns:
        Dictionary containing deletion confirmation
    """
    try:
        return mcp_tools.delete_spec(feature_name)
    except Exception as e:
        return format_error_response(e)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    return mcp


def run_server() -> None:
    """Run the MCP server with appropriate transport."""
    try:
        if len(sys.argv) == 1 or sys.argv[1] == "stdio":
            # Run with stdio transport (default MCP transport)
            logger.info("Starting spec-server with stdio transport")
            logger.debug("Server configuration: stdio transport, 7 tools registered")
            mcp.run()
        elif sys.argv[1] == "sse":
            # Run with SSE transport on specified port
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
            host = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
            logger.info(f"Starting spec-server with SSE transport on {host}:{port}")
            logger.debug(f"Server configuration: SSE transport, {host}:{port}, 7 tools registered")
            logger.info("SSE transport includes CORS support for web client compatibility")

            # Run SSE server with configuration
            mcp.run_sse(port=port, host=host)  # type: ignore
        else:
            logger.error(f"Unknown transport: {sys.argv[1]}")
            logger.error("Usage: python -m spec_server [stdio|sse] [port] [host]")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
