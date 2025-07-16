# MCP Client Configuration

This document provides examples of how to configure various MCP clients to work with spec-server.

## Overview

Spec-server supports two transport protocols:
- **stdio**: Standard input/output (default, recommended for most MCP clients)
- **sse**: Server-Sent Events (for web-based clients)

## Configuration Examples

### Claude Desktop

Add the following to your Claude Desktop MCP configuration file:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "env": {
        "SPEC_SERVER_SPECS_DIR": "~/Documents/specs",
        "SPEC_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Continue.dev

Add to your Continue configuration:

```json
{
  "mcp": {
    "servers": {
      "spec-server": {
        "command": "spec-server",
        "args": ["stdio"],
        "cwd": "~/projects"
      }
    }
  }
}
```

### Custom MCP Client (stdio)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="spec-server",
        args=["stdio"],
        env={
            "SPEC_SERVER_SPECS_DIR": "./specs",
            "SPEC_SERVER_LOG_LEVEL": "DEBUG"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])
            
            # Create a new spec
            result = await session.call_tool(
                "create_spec",
                arguments={
                    "feature_name": "user-authentication",
                    "initial_idea": "Implement user login and registration system"
                }
            )
            print("Created spec:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom MCP Client (SSE)

```python
import asyncio
import aiohttp
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    # Start spec-server with SSE transport
    # spec-server sse --port 8000
    
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use the session
            result = await session.call_tool(
                "list_specs",
                arguments={}
            )
            print("Available specs:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Variables

You can configure spec-server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SPEC_SERVER_HOST` | Host to bind to (SSE only) | `127.0.0.1` |
| `SPEC_SERVER_PORT` | Port to listen on (SSE only) | `8000` |
| `SPEC_SERVER_TRANSPORT` | Transport protocol | `stdio` |
| `SPEC_SERVER_SPECS_DIR` | Specifications directory | `specs` |
| `SPEC_SERVER_MAX_SPECS` | Maximum number of specs | `1000` |
| `SPEC_SERVER_MAX_DOCUMENT_SIZE` | Max document size (bytes) | `1000000` |
| `SPEC_SERVER_AUTO_BACKUP` | Enable auto-backup | `true` |
| `SPEC_SERVER_BACKUP_DIR` | Backup directory | `backups` |
| `SPEC_SERVER_STRICT_VALIDATION` | Enable strict validation | `true` |
| `SPEC_SERVER_LOG_LEVEL` | Logging level | `INFO` |
| `SPEC_SERVER_LOG_FILE` | Log file path | `null` |
| `SPEC_SERVER_CACHE_ENABLED` | Enable caching | `true` |
| `SPEC_SERVER_CACHE_SIZE` | Cache size | `100` |

## Configuration File

You can also use a JSON configuration file. Place it in one of these locations:
- `./spec-server.json` (current directory)
- `./config/spec-server.json`
- `~/.spec-server.json` (home directory)
- `/etc/spec-server.json` (system-wide)

Example configuration file:

```json
{
  "host": "127.0.0.1",
  "port": 8000,
  "transport": "stdio",
  "specs_dir": "specs",
  "max_specs": 1000,
  "max_document_size": 1000000,
  "auto_backup": true,
  "backup_dir": "backups",
  "strict_validation": true,
  "allow_dangerous_paths": false,
  "log_level": "INFO",
  "log_file": null,
  "cache_enabled": true,
  "cache_size": 100
}
```

## Available Tools

Spec-server provides the following MCP tools:

### create_spec
Create a new feature specification.

**Parameters:**
- `feature_name` (string): Kebab-case feature identifier
- `initial_idea` (string): User's rough feature description

### update_spec_document
Update a spec document and manage workflow transitions.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `document_type` (string): "requirements", "design", or "tasks"
- `content` (string): Updated document content
- `phase_approval` (boolean): Whether user approves current phase for advancement

### list_specs
List all existing specifications with metadata.

**Parameters:** None

### read_spec_document
Read a spec document with optional file reference resolution.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `document_type` (string): "requirements", "design", or "tasks"
- `resolve_references` (boolean): Whether to resolve #[[file:path]] references

### execute_task
Execute a specific implementation task or get the next task.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `task_identifier` (string, optional): Task number/identifier

### complete_task
Mark a task as completed.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `task_identifier` (string): Task number/identifier

### delete_spec
Delete a specification entirely.

**Parameters:**
- `feature_name` (string): Target spec identifier

## Troubleshooting

### Common Issues

1. **"Command not found: spec-server"**
   - Make sure spec-server is installed: `pip install spec-server`
   - Or install from source: `pip install -e .`

2. **"Permission denied"**
   - Check that the specs directory is writable
   - Ensure the user has permissions to create files

3. **"Transport error"**
   - For stdio: Check that the command and args are correct
   - For SSE: Ensure the server is running and the port is accessible

4. **"Validation errors"**
   - Check that feature names are in kebab-case format
   - Ensure document types are valid: "requirements", "design", "tasks"
   - Verify that content is not empty

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Environment variable
export SPEC_SERVER_LOG_LEVEL=DEBUG
spec-server

# Or in MCP client config
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "env": {
        "SPEC_SERVER_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Log Files

To save logs to a file:

```bash
export SPEC_SERVER_LOG_FILE=spec-server.log
spec-server
```

## Support

For issues and questions:
- Check the [GitHub Issues](https://github.com/teknologika/spec-server/issues)
- Review the [README.md](../README.md) for additional documentation
- Enable debug logging to get more detailed error information