"""
Main entry point for the spec-server MCP application.
"""

import sys

from spec_server.server import create_server


def main() -> None:
    """Main entry point for the spec-server application."""
    # Handle help
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("spec-server - MCP server for structured feature development")
        print()
        print("Usage:")
        print("  spec-server                    # Run with stdio transport (default)")
        print("  spec-server stdio              # Run with stdio transport")
        print("  spec-server sse [port]         # Run with SSE transport (default port: 8000)")
        print()
        print("Examples:")
        print("  spec-server                    # Default stdio transport")
        print("  spec-server sse                # SSE transport on port 8000")
        print("  spec-server sse 3000           # SSE transport on port 3000")
        print()
        print("For MCP client configuration, add to your mcp.json:")
        print('  "spec-server": {')
        print('    "command": "spec-server",')
        print('    "args": ["stdio"]')
        print("  }")
        return

    # Default to stdio transport
    transport = "stdio"
    port = 8000

    # Parse command line arguments
    if len(sys.argv) > 1:
        transport = sys.argv[1]
        if transport == "sse" and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print(f"Invalid port number: {sys.argv[2]}")
                sys.exit(1)

    # Create and run the server
    server = create_server()

    if transport == "stdio":
        # Run with stdio transport (default MCP transport)
        server.run()
    elif transport == "sse":
        # Run with SSE transport
        # Note: SSE support may vary by FastMCP version
        if hasattr(server, "run_sse"):
            server.run_sse(port=port)  # type: ignore
        else:
            print("SSE transport not supported in this FastMCP version")
            sys.exit(1)
    else:
        print(f"Unknown transport: {transport}")
        print("Usage: spec-server [stdio|sse] [port]")
        print("Use 'spec-server --help' for more information")
        sys.exit(1)


if __name__ == "__main__":
    main()
