# Project Planning

This document outlines the high-level strategic objectives for the project. Assistants should refer to this file to understand the overall goals and priorities.

## How to Use

1.  Define major features or epics as Level 2 Headings (`##`).
2.  Add a `Status` and `Depends On` field for each objective.
3.  Before starting work, review this plan to select the next high-priority objective.
4.  Update the status of objectives as they are completed.

---

### Development Tools
- **uv**: use uv for Python dependency management, not poetry.
- **pytest + pytest-cov**: Testing framework with coverage
- **black**: Code formatting (100-character lines)
- **flake8**: Linting with zero tolerance for F-level errors
- **GitHub Actions**: CI/CD with automated testing and code review

## Development Workflow

### 1. Feature Development Process
```
Design → Plan Mode → Feature Documentation → Create github issue → Implementation → Testing → Documentation → Commit → Push → Close issue as complete → Ask user to publish to PyPi or not.

use ./ISSUE_TEMPLATE/feature_request.md as the template.

```

1. **Always design a feature first** and request plan-only mode
2. **Save design to `./docs/Features/feature_name.md`**
3. **Add TODO section at bottom of design for implementation tracking**
4. **Implement with comprehensive testing**
5. **Update TASK.md with completion status**

### 2. Code Quality Standards

**CRITICAL: Always run before committing:**
```bash
# Format code with black (REQUIRED)
black --line-length 100 src/

# Check all flake8 violations (REQUIRED)
flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503,E501

# Run tests to ensure no regressions (REQUIRED)
pytest tests/
```

**F-Level Error Policy:**
- **F401**: Remove ALL unused imports immediately
- **F841**: Remove ALL unused variables (or use `_` for intentional)
- **F811**: Never duplicate imports
- **F541**: Fix f-strings without placeholders

### 3. Task Management
- **Check TASK.md before starting new tasks**
- **Add new tasks with brief description and today's date**
- **Mark completed tasks immediately after finishing**
- **Add discovered sub-tasks to "Discovered During Work" section**

---

## Current Objectives
