# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with spec-server.

## Installation Issues

### Python Version Compatibility

**Problem**: `spec-server` fails to install or run
**Symptoms**: 
- Import errors
- Syntax errors
- Package installation failures

**Solution**:
```bash
# Check Python version
python3 --version

# spec-server requires Python 3.12+
# Install Python 3.12+ if needed
```

### Missing Dependencies

**Problem**: Import errors when running spec-server
**Symptoms**:
- `ModuleNotFoundError`
- `ImportError`

**Solution**:
```bash
# Reinstall with all dependencies
pip install --upgrade spec-server

# Or install from source
pip install -e ".[dev]"
```

## Runtime Issues

### Command Not Found

**Problem**: `spec-server: command not found`
**Symptoms**: Shell cannot find the spec-server command

**Solutions**:
1. **Check installation**:
   ```bash
   pip list | grep spec-server
   ```

2. **Reinstall with entry points**:
   ```bash
   pip install --force-reinstall spec-server
   ```

3. **Use module execution**:
   ```bash
   python -m spec_server
   ```

4. **Check PATH**:
   ```bash
   # Find where pip installs scripts
   python -m site --user-base
   # Add to PATH if needed
   export PATH="$PATH:$(python -m site --user-base)/bin"
   ```

### Permission Errors

**Problem**: Permission denied when creating specs
**Symptoms**:
- `PermissionError`
- Cannot create directories or files

**Solutions**:
1. **Check directory permissions**:
   ```bash
   ls -la specs/
   chmod 755 specs/
   ```

2. **Use different specs directory**:
   ```bash
   export SPEC_SERVER_SPECS_DIR=~/my-specs
   spec-server
   ```

3. **Run with appropriate user**:
   ```bash
   # Don't run as root unless necessary
   whoami
   ```

### Port Already in Use (SSE Transport)

**Problem**: Cannot start SSE server
**Symptoms**: `Address already in use` error

**Solutions**:
1. **Use different port**:
   ```bash
   spec-server sse --port 8001
   ```

2. **Find and kill process using port**:
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

3. **Check for other services**:
   ```bash
   netstat -tulpn | grep :8000
   ```

## MCP Client Issues

### Connection Failures

**Problem**: MCP client cannot connect to spec-server
**Symptoms**:
- Timeout errors
- Connection refused
- Protocol errors

**Solutions**:
1. **Verify server is running**:
   ```bash
   # For stdio transport
   echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1}' | spec-server
   
   # For SSE transport
   curl http://localhost:8000/sse
   ```

2. **Check transport configuration**:
   ```json
   {
     "mcpServers": {
       "spec-server": {
         "command": "spec-server",
         "args": ["stdio"]
       }
     }
   }
   ```

3. **Enable debug logging**:
   ```json
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

### Tool Execution Errors

**Problem**: MCP tools return errors
**Symptoms**:
- Validation errors
- Tool execution failures
- Unexpected responses

**Solutions**:
1. **Check parameter format**:
   ```python
   # Correct format
   await session.call_tool("create_spec", {
       "feature_name": "user-auth",  # kebab-case
       "initial_idea": "User authentication system"
   })
   ```

2. **Validate input data**:
   - Feature names must be kebab-case
   - Document types: "requirements", "design", "tasks"
   - Content cannot be empty

3. **Check error responses**:
   ```python
   result = await session.call_tool("create_spec", {...})
   if not result.get("success", True):
       print("Error:", result.get("message"))
       print("Suggestions:", result.get("suggestions", []))
   ```

## Validation Issues

### Invalid Feature Names

**Problem**: Feature name validation fails
**Symptoms**: `SPEC_INVALID_NAME` error

**Solutions**:
- Use kebab-case: `user-auth`, `data-export`
- Avoid uppercase: `User-Auth` → `user-auth`
- Avoid underscores: `user_auth` → `user-auth`
- Avoid spaces: `user auth` → `user-auth`

### Document Type Errors

**Problem**: Invalid document type
**Symptoms**: `VALIDATION_ERROR` for document_type

**Solutions**:
- Use valid types: `requirements`, `design`, `tasks`
- Check spelling and case sensitivity
- Avoid custom document types

### Content Validation

**Problem**: Document content rejected
**Symptoms**: Content validation errors

**Solutions**:
1. **Check content length**:
   - Maximum: 1MB (1,000,000 bytes)
   - Minimum for ideas: 10 characters

2. **Avoid dangerous content**:
   - No script tags
   - No JavaScript URLs
   - No executable content

## File System Issues

### Specs Directory Problems

**Problem**: Cannot access specs directory
**Symptoms**:
- Directory not found
- Permission errors
- Cannot create specs

**Solutions**:
1. **Create directory**:
   ```bash
   mkdir -p specs
   chmod 755 specs
   ```

2. **Use custom directory**:
   ```bash
   export SPEC_SERVER_SPECS_DIR=/path/to/specs
   spec-server
   ```

3. **Check disk space**:
   ```bash
   df -h .
   ```

### Backup Issues

**Problem**: Backup creation fails
**Symptoms**: Backup errors in logs

**Solutions**:
1. **Check backup directory**:
   ```bash
   mkdir -p backups
   chmod 755 backups
   ```

2. **Disable auto-backup**:
   ```bash
   export SPEC_SERVER_AUTO_BACKUP=false
   spec-server
   ```

## Performance Issues

### Slow Response Times

**Problem**: Tools take too long to respond
**Symptoms**: Timeouts, slow operations

**Solutions**:
1. **Enable caching**:
   ```bash
   export SPEC_SERVER_CACHE_ENABLED=true
   export SPEC_SERVER_CACHE_SIZE=200
   ```

2. **Reduce validation strictness**:
   ```bash
   export SPEC_SERVER_STRICT_VALIDATION=false
   ```

3. **Check system resources**:
   ```bash
   top
   df -h
   ```

### Memory Usage

**Problem**: High memory consumption
**Symptoms**: System slowdown, out of memory errors

**Solutions**:
1. **Reduce cache size**:
   ```bash
   export SPEC_SERVER_CACHE_SIZE=50
   ```

2. **Limit max specs**:
   ```bash
   export SPEC_SERVER_MAX_SPECS=100
   ```

3. **Monitor memory usage**:
   ```bash
   ps aux | grep spec-server
   ```

## Debugging

### Enable Debug Logging

```bash
# Environment variable
export SPEC_SERVER_LOG_LEVEL=DEBUG
export SPEC_SERVER_LOG_FILE=debug.log
spec-server

# Check logs
tail -f debug.log
```

### Test Individual Components

```bash
# Test server startup
spec-server --help

# Test with simple command
echo '{"jsonrpc": "2.0", "method": "ping", "id": 1}' | spec-server

# Run unit tests
python -m pytest tests/ -v

# Test specific functionality
python -c "from spec_server.config import get_config; print(get_config())"
```

### Collect System Information

```bash
# System info
uname -a
python3 --version
pip --version

# Package versions
pip list | grep -E "(spec-server|fastmcp|pydantic)"

# Environment
env | grep SPEC_SERVER

# File permissions
ls -la specs/ backups/
```

## Getting Help

### Before Reporting Issues

1. **Check logs** with debug level enabled
2. **Verify configuration** is correct
3. **Test with minimal setup**
4. **Check system requirements**

### Information to Include

When reporting issues, include:

1. **System information**:
   - Operating system and version
   - Python version
   - spec-server version

2. **Configuration**:
   - Environment variables
   - Configuration file (if used)
   - MCP client configuration

3. **Error details**:
   - Full error messages
   - Debug logs
   - Steps to reproduce

4. **Expected vs actual behavior**

### Support Channels

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/teknologika/spec-server/issues)
- **Documentation**: Check README.md and docs/
- **Debug logs**: Enable debug logging for detailed information

## Common Error Codes

| Error Code | Description | Common Causes |
|------------|-------------|---------------|
| `SPEC_NOT_FOUND` | Specification not found | Typo in feature name, spec not created |
| `SPEC_ALREADY_EXISTS` | Specification already exists | Duplicate creation attempt |
| `SPEC_INVALID_NAME` | Invalid feature name format | Not kebab-case, special characters |
| `DOCUMENT_NOT_FOUND` | Document not found | Invalid document type, spec not created |
| `VALIDATION_ERROR` | Input validation failed | Invalid parameters, format issues |
| `WORKFLOW_APPROVAL_REQUIRED` | Phase approval needed | Missing phase_approval=true |
| `TASK_NOT_FOUND` | Task not found | Invalid task identifier |
| `FILE_NOT_FOUND` | File reference not found | Broken file reference |
| `INTERNAL_ERROR` | Unexpected server error | System issue, check logs |