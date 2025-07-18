# MCP Client Configuration for spec-server

This document provides guidance on configuring your MCP client to work with spec-server.

## Basic Configuration

Add the following to your MCP configuration file (`mcp.json`):

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Configuration with Full Path

If the `spec-server` command is not in your system PATH (e.g., when installed in a virtual environment), specify the full path:

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "/path/to/your/venv/bin/spec-server",
      "args": ["stdio"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Configuration with Custom Specs Directory

If you need to specify a custom directory for storing specifications (e.g., when the default directory is on a read-only file system):

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "disabled": false,
      "autoApprove": [],
      "env": {
        "SPEC_SERVER_SPECS_DIR": "/path/to/writable/directory/specs"
      }
    }
  }
}
```

## Configuration with Workspace Detection

To enable automatic workspace detection (default behavior):

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "disabled": false,
      "autoApprove": [],
      "env": {
        "SPEC_SERVER_AUTO_DETECT_WORKSPACE": "true",
        "SPEC_SERVER_WORKSPACE_SPECS_DIR": ".specs"
      }
    }
  }
}
```

## Configuration with SSE Transport

To use Server-Sent Events (SSE) transport instead of stdio:

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["sse", "8000"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Configuration Location

The MCP configuration can be placed in one of two locations:

1. **Workspace Level**: `.kiro/settings/mcp.json` in your project directory
2. **User Level**: `~/.kiro/settings/mcp.json` for global configuration

If both exist, they are merged with workspace-level settings taking precedence.

## Troubleshooting

If you encounter issues with the spec-server:

1. **Command not found**: Ensure the `spec-server` command is in your PATH or use the full path in the configuration
2. **Permission errors**: Specify a custom specs directory using the `SPEC_SERVER_SPECS_DIR` environment variable
3. **Connection issues**: Check that the transport method (stdio or SSE) is correctly configured
4. **Version compatibility**: Ensure you're using a compatible version of spec-server with your MCP client

For more detailed troubleshooting, refer to the [troubleshooting guide](troubleshooting.md).
