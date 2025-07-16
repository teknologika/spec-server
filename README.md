# spec-server

An MCP (Model Context Protocol) server that provides structured feature development capabilities through a systematic three-phase workflow: **Requirements → Design → Implementation Tasks**.

## Overview

spec-server helps AI assistants and developers transform rough feature ideas into executable implementation plans through a structured approach:

1. **Requirements Phase**: Define user stories and acceptance criteria in EARS format
2. **Design Phase**: Create comprehensive technical design documents  
3. **Tasks Phase**: Generate actionable implementation tasks with test-driven development focus

## Features

- **Systematic Workflow**: Enforced progression through Requirements → Design → Tasks phases
- **MCP Integration**: Works with any MCP-compatible AI assistant
- **File References**: Support for `#[[file:path]]` syntax to include external specifications
- **Task Management**: Hierarchical task tracking with status updates
- **Multiple Transports**: Support for both stdio and SSE (Server-Sent Events) transport methods
- **Validation**: Built-in validation for document formats and workflow transitions

## Installation

### From PyPI

```bash
pip install spec-server
```

### From Source

```bash
git clone https://github.com/teknologika/spec-server.git
cd spec-server
pip install -e .
```

## Usage

### As MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "spec-server": {
      "command": "spec-server",
      "args": ["stdio"],
      "disabled": false
    }
  }
}
```

### Command Line

```bash
# Run with stdio transport (default)
spec-server

# Run with SSE transport on port 8000
spec-server sse 8000

# Run with SSE transport on custom port
spec-server sse 3000
```

## MCP Tools

The server exposes the following MCP tools:

### `create_spec`
Create a new feature specification with initial requirements document.

**Parameters:**
- `feature_name` (string): Kebab-case feature identifier
- `initial_idea` (string): User's rough feature description

### `update_spec_document`
Update requirements, design, or tasks documents with workflow validation.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `document_type` (enum): "requirements" | "design" | "tasks"
- `content` (string): Updated document content
- `phase_approval` (boolean): Whether user approves current phase

### `list_specs`
List all existing specifications with their current status and progress.

### `read_spec_document`
Retrieve content of spec documents with file reference resolution.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `document_type` (enum): "requirements" | "design" | "tasks"

### `execute_task`
Execute a specific implementation task from the tasks document.

**Parameters:**
- `feature_name` (string): Target spec identifier
- `task_identifier` (string): Task number/identifier

### `delete_spec`
Remove a specification entirely including all documents.

**Parameters:**
- `feature_name` (string): Target spec identifier

## Workflow

### 1. Requirements Phase
- Create user stories in "As a [role], I want [feature], so that [benefit]" format
- Define acceptance criteria using EARS (Easy Approach to Requirements Syntax)
- Must receive explicit approval before advancing to design phase

### 2. Design Phase
- Generate comprehensive technical design based on approved requirements
- Include sections: Overview, Architecture, Components, Data Models, Error Handling, Testing
- Conduct research and incorporate findings into design decisions
- Must receive explicit approval before advancing to tasks phase

### 3. Tasks Phase
- Create actionable implementation tasks focused on code development
- Format as numbered checkboxes with hierarchical structure
- Reference specific requirements and ensure test-driven development
- Tasks ready for execution by coding agents

## File Structure

```
specs/
├── feature-name-1/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── feature-name-2/
│   ├── requirements.md
│   └── design.md
└── .spec-metadata.json
```

## File References

Spec documents support file references using the syntax `#[[file:relative/path/to/file.md]]`. These references are automatically resolved and their content is included when documents are read.

Example:
```markdown
# API Design

The API follows the OpenAPI specification defined in:
#[[file:api/openapi.yaml]]
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/teknologika/spec-server.git
cd spec-server
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests

# Type checking
mypy src
```

## Configuration

### Workspace Integration

spec-server features intelligent workspace detection that automatically organizes your specifications with your project files when running in an IDE or project directory.

**How It Works:**
- **Automatic Detection**: Scans upward from current directory looking for workspace indicators
- **Smart Placement**: Creates `.specs/` directory at the detected workspace root
- **Fallback Behavior**: Uses `specs/` directory in current location if no workspace detected
- **IDE Friendly**: Works seamlessly with VS Code, IntelliJ, Sublime Text, and other editors

**Workspace Indicators:**
- `.git` (Git repository)
- `package.json` (Node.js project)
- `pyproject.toml` (Python project)
- `Cargo.toml` (Rust project)
- `go.mod` (Go project)
- `pom.xml` (Maven project)
- `.vscode`, `.idea` (IDE configurations)
- `README.md`, `LICENSE`, `Makefile` (common project files)

**Example Structure:**
```
my-project/                 ← Detected workspace root
├── .git/
├── src/
├── package.json
├── README.md
└── .specs/                 ← Specs automatically placed here
    ├── user-auth/
    │   ├── requirements.md
    │   ├── design.md
    │   └── tasks.md
    ├── data-export/
    │   └── requirements.md
    └── .spec-metadata.json
```

**Benefits:**
- **Version Control**: Specs can be committed alongside your code
- **Team Collaboration**: Shared specifications across team members
- **Context Awareness**: Specs are logically grouped with related projects
- **IDE Integration**: Specifications appear in your project file tree
- **Automatic Organization**: No manual directory management required

**Configuration:**
```bash
# Enable/disable workspace detection (default: true)
export SPEC_SERVER_AUTO_DETECT_WORKSPACE=true

# Customize specs directory name in workspace (default: ".specs")
export SPEC_SERVER_WORKSPACE_SPECS_DIR=".my-specs"

# Customize fallback directory name (default: "specs")
export SPEC_SERVER_SPECS_DIR="my-specs"
```

### Environment Variables

- `SPEC_SERVER_SPECS_DIR`: Base directory for specs (default: "specs")
- `SPEC_SERVER_AUTO_DETECT_WORKSPACE`: Enable workspace detection (default: "true")
- `SPEC_SERVER_WORKSPACE_SPECS_DIR`: Specs directory name in workspace (default: ".specs")
- `SPEC_SERVER_PORT`: Default SSE server port (default: 8000)
- `SPEC_SERVER_LOG_LEVEL`: Logging level (default: "INFO")

### Configuration File

Optional `spec-server.json`:

```json
{
  "specs_dir": "specs",
  "auto_detect_workspace": true,
  "workspace_specs_dir": ".specs",
  "host": "127.0.0.1",
  "port": 8000,
  "transport": "stdio",
  "log_level": "INFO",
  "auto_backup": true,
  "cache_enabled": true
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- GitHub Issues: [https://github.com/teknologika/spec-server/issues](https://github.com/teknologika/spec-server/issues)
- Documentation: [Coming Soon]

## Roadmap
