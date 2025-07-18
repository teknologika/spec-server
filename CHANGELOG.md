# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- TBD

### Changed
- TBD

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.4.1] - 2025-07-18

### Added
- Version consistency check script and pre-commit hook
- Automatic validation of version consistency across project files

### Changed
- Updated file formatting and whitespace

### Fixed
- Fixed version consistency across project files

### Security
- None

## [0.4.0] - 2025-07-18

### Added
- Comprehensive LLM guidance functionality with conversational approach
- New `get_guidance` tool to provide phase-specific guidance
- New `get_full_guidance` tool to access complete guidance document
- Enhanced tool descriptions with conversation prompts
- System message with introduction prompt
- Documentation on effective LLM usage of spec-server

### Changed
- Updated server version to match package version
- Enhanced MCP client configuration documentation
- Improved troubleshooting guide for read-only file system errors

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.3.0] - 2025-07-17

### Added
- New test suite for phase approval functionality

### Changed
- Updated workflow engine to require explicit approval for phase advancement

### Deprecated
- None

### Removed
- None

### Fixed
- Fixed issue where specs could be auto-approved without explicit user confirmation
- Enhanced phase approval logic to ensure explicit approval is required

### Security
- Improved workflow security by requiring explicit approval for phase transitions

## [0.2.0] - 2025-07-16

### Added
- Initial implementation of spec-server MCP server
- Complete workflow engine for Requirements → Design → Tasks
- Comprehensive test suite with fixtures and utilities
- Integration tests for transport protocols
- Configuration management with environment variables and files
- Error handling with structured error responses
- Input validation and sanitization
- File reference system for including external content
- Task execution and progress tracking
- Backup and recovery functionality
- Documentation and deployment guides

### Changed
- Code quality improvements

### Deprecated
- None

### Removed
- None

### Fixed
- Fixed flake8 errors by removing unused imports and variables
- Improved code quality and maintainability

### Security
- Input validation to prevent injection attacks
- File path sanitization for security
- Rate limiting for API endpoints

## [0.1.0] - 2025-01-15

### Added
- Initial release of spec-server
- MCP server implementation with FastMCP
- Support for stdio and SSE transport protocols
- Structured specification management
- Phase-based workflow (Requirements → Design → Tasks)
- Task execution and tracking
- File reference resolution
- Comprehensive error handling
- Configuration management
- Full test suite with 95%+ coverage
- Documentation and examples
- Deployment scripts and guides

### Features
- **Specification Management**: Create, read, update, and delete specifications
- **Workflow Engine**: Guided workflow through requirements, design, and tasks phases
- **Task Execution**: Execute and track implementation tasks
- **File References**: Include external files in specifications with `#[[file:path]]` syntax
- **Transport Support**: Both stdio and SSE transport protocols
- **Configuration**: Flexible configuration via environment variables and files
- **Error Handling**: Structured error responses with suggestions
- **Validation**: Comprehensive input validation and sanitization
- **Testing**: Extensive test suite with fixtures and utilities
- **Documentation**: Complete API documentation and usage guides

### Technical Details
- **Python**: Requires Python 3.12+
- **Dependencies**: FastMCP, Pydantic, pathlib-mate
- **Architecture**: Modular design with clear separation of concerns
- **Testing**: pytest with asyncio support and coverage reporting
- **Code Quality**: Black formatting, isort imports, flake8 linting, mypy type checking
- **Packaging**: Modern Python packaging with hatchling build backend
