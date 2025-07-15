"""
FastMCP server implementation for spec-server.
"""

from fastmcp import FastMCP


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    server = FastMCP("spec-server")

    # TODO: Register MCP tools here
    # This will be implemented in later tasks

    return server
