"""Helper functions for testing."""

import json
import os
import random
import string
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from spec_server.models import Phase, Spec, SpecMetadata, Task, TaskStatus
from spec_server.spec_manager import SpecManager


def random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def random_feature_name() -> str:
    """Generate a random feature name in kebab-case."""
    words = [random_string(5) for _ in range(2)]
    return f"{words[0]}-{words[1]}"


def create_temp_spec_dir() -> Tuple[Path, Path]:
    """Create a temporary specs directory."""
    temp_dir = Path(tempfile.mkdtemp())
    specs_dir = temp_dir / "specs"
    specs_dir.mkdir(exist_ok=True)
    return temp_dir, specs_dir


def create_test_spec(spec_manager: SpecManager, feature_name: Optional[str] = None) -> Spec:
    """Create a test specification."""
    if feature_name is None:
        feature_name = random_feature_name()
    
    initial_idea = f"Test specification for {feature_name}"
    
    # Create the spec
    spec = spec_manager.create_spec(feature_name, initial_idea)
    return spec


def create_full_test_spec(spec_manager: SpecManager, feature_name: Optional[str] = None) -> Spec:
    """Create a complete test specification with all documents."""
    if feature_name is None:
        feature_name = random_feature_name()
    
    # Create the spec
    spec = create_test_spec(spec_manager, feature_name)
    
    # Add requirements
    requirements = f"""# Requirements for {feature_name}

## Overview
This is a test specification for {feature_name}.

## Requirements

### Requirement 1
**User Story:** As a user, I want to test the system, so that I can verify it works.

#### Acceptance Criteria
1. WHEN the system is tested THEN it SHALL respond correctly
2. WHEN invalid input is provided THEN the system SHALL return an error

### Requirement 2
**User Story:** As a developer, I want to validate the implementation, so that I can ensure quality.

#### Acceptance Criteria
1. WHEN tests are run THEN they SHALL pass
2. WHEN code is reviewed THEN it SHALL meet standards
"""
    
    spec_manager.update_spec_document(feature_name, "requirements", requirements)
    spec_manager.approve_phase(feature_name, Phase.REQUIREMENTS)
    
    # Add design
    design = f"""# Design for {feature_name}

## Overview
This is the design document for {feature_name}.

## Architecture
The system will use a modular architecture with the following components:

## Components
1. **Controller** - Handles HTTP requests
2. **Service** - Business logic
3. **Repository** - Data access

## Data Models
```
TestModel {{
  id: UUID
  name: String
  created_at: DateTime
}}
```

## API Endpoints
- GET /api/test
- POST /api/test
- PUT /api/test/:id
- DELETE /api/test/:id

## Error Handling
All errors will be handled consistently with proper HTTP status codes.

## Testing Strategy
- Unit tests for all components
- Integration tests for API endpoints
- End-to-end tests for user workflows
"""
    
    spec_manager.update_spec_document(feature_name, "design", design)
    spec_manager.approve_phase(feature_name, Phase.DESIGN)
    
    # Add tasks
    tasks = f"""# Tasks for {feature_name}

- [ ] 1. Set up project structure
  - [ ] 1.1 Create directory structure
  - [ ] 1.2 Set up dependencies
  - [ ] 1.3 Configure build system

- [ ] 2. Implement data models
  - [ ] 2.1 Create TestModel
  - [ ] 2.2 Set up database migrations
  - [ ] 2.3 Add model validation

- [ ] 3. Implement business logic
  - [ ] 3.1 Create service layer
  - [ ] 3.2 Implement CRUD operations
  - [ ] 3.3 Add error handling

- [ ] 4. Implement API endpoints
  - [ ] 4.1 Create controller
  - [ ] 4.2 Add request validation
  - [ ] 4.3 Add response formatting

- [ ] 5. Write tests
  - [ ] 5.1 Unit tests
  - [ ] 5.2 Integration tests
  - [ ] 5.3 End-to-end tests
"""
    
    spec_manager.update_spec_document(feature_name, "tasks", tasks)
    
    return spec_manager.get_spec(feature_name)


def assert_spec_structure(spec: Spec, feature_name: str):
    """Assert that a spec has the expected structure."""
    assert spec.metadata.feature_name == feature_name
    assert spec.metadata.created_at is not None
    assert spec.metadata.updated_at is not None
    assert spec.metadata.phase in [Phase.REQUIREMENTS, Phase.DESIGN, Phase.TASKS, Phase.IMPLEMENTATION]
    
    # Check that documents exist
    assert spec.requirements is not None
    assert len(spec.requirements.strip()) > 0


def assert_task_structure(task: Task):
    """Assert that a task has the expected structure."""
    assert task.identifier is not None
    assert len(task.identifier.strip()) > 0
    assert task.title is not None
    assert len(task.title.strip()) > 0
    assert task.status in [TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]


def create_sample_file_references(temp_dir: Path) -> Dict[str, Path]:
    """Create sample files for testing file references."""
    files = {}
    
    # Create markdown file
    md_file = temp_dir / "sample.md"
    md_content = """# Sample Markdown

This is a sample markdown file for testing.

## Features
- Feature 1
- Feature 2
- Feature 3

## Code Example
```python
def hello():
    print("Hello, world!")
```
"""
    md_file.write_text(md_content)
    files["markdown"] = md_file
    
    # Create JSON file
    json_file = temp_dir / "sample.json"
    json_content = {
        "name": "Sample Data",
        "version": "1.0.0",
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
    }
    json_file.write_text(json.dumps(json_content, indent=2))
    files["json"] = json_file
    
    # Create text file
    txt_file = temp_dir / "sample.txt"
    txt_content = """This is a plain text file.
Line 2
Line 3
Final line"""
    txt_file.write_text(txt_content)
    files["text"] = txt_file
    
    return files


def mock_environment_variables(env_vars: Dict[str, str]):
    """Context manager to temporarily set environment variables."""
    class EnvVarContext:
        def __init__(self, env_vars: Dict[str, str]):
            self.env_vars = env_vars
            self.old_values = {}
        
        def __enter__(self):
            for key, value in self.env_vars.items():
                if key in os.environ:
                    self.old_values[key] = os.environ[key]
                os.environ[key] = value
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            for key in self.env_vars:
                if key in self.old_values:
                    os.environ[key] = self.old_values[key]
                else:
                    del os.environ[key]
    
    return EnvVarContext(env_vars)


def create_test_config_file(temp_dir: Path, config_data: Dict[str, Any]) -> Path:
    """Create a test configuration file."""
    config_file = temp_dir / "test-config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
    return config_file


def assert_error_response(response: Dict[str, Any], expected_error_code: Optional[str] = None):
    """Assert that a response is a proper error response."""
    assert response["success"] is False
    assert "error_code" in response
    assert "message" in response
    assert "suggestions" in response
    assert isinstance(response["suggestions"], list)
    
    if expected_error_code:
        assert response["error_code"] == expected_error_code


def assert_success_response(response: Dict[str, Any], expected_keys: Optional[List[str]] = None):
    """Assert that a response is a successful response."""
    assert response["success"] is True
    
    if expected_keys:
        for key in expected_keys:
            assert key in response


def compare_specs(spec1: Spec, spec2: Spec, ignore_timestamps: bool = True):
    """Compare two specs for equality."""
    assert spec1.metadata.feature_name == spec2.metadata.feature_name
    assert spec1.metadata.phase == spec2.metadata.phase
    
    if not ignore_timestamps:
        assert spec1.metadata.created_at == spec2.metadata.created_at
        assert spec1.metadata.updated_at == spec2.metadata.updated_at
    
    assert spec1.requirements == spec2.requirements
    assert spec1.design == spec2.design
    assert spec1.tasks == spec2.tasks


def get_task_by_identifier(tasks: List[Task], identifier: str) -> Optional[Task]:
    """Get a task by its identifier."""
    for task in tasks:
        if task.identifier == identifier:
            return task
    return None


def count_tasks_by_status(tasks: List[Task], status: TaskStatus) -> int:
    """Count tasks with a specific status."""
    return sum(1 for task in tasks if task.status == status)


def create_test_json_rpc_request(method: str, params: Dict[str, Any], request_id: int = 1) -> Dict[str, Any]:
    """Create a test JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }


def assert_json_rpc_response(response: Dict[str, Any], request_id: int = 1, expect_error: bool = False):
    """Assert that a response is a valid JSON-RPC response."""
    assert "jsonrpc" in response
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert response["id"] == request_id
    
    if expect_error:
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
    else:
        assert "result" in response


def cleanup_temp_directory(temp_dir: Path):
    """Clean up a temporary directory."""
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)