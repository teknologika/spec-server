"""Sample data for testing."""

from typing import Dict, List


def get_sample_specs() -> List[Dict]:
    """Get sample specifications for testing."""
    return [
        {
            "feature_name": "user-authentication",
            "initial_idea": "Implement user authentication with login and registration",
            "requirements": """# User Authentication Requirements

## Overview
Implement a secure user authentication system with registration, login, and password reset.

## Functional Requirements
1. Users should be able to register with email and password
2. Users should be able to login with email and password
3. Users should be able to reset their password
4. Users should be able to logout

## Security Requirements
1. Passwords must be hashed using bcrypt
2. Failed login attempts should be rate-limited
3. Password reset links should expire after 24 hours
4. Sessions should timeout after 30 minutes of inactivity
""",
            "design": """# User Authentication Design

## Architecture
The authentication system will use a stateless JWT-based approach with refresh tokens.

## Components
1. AuthController - Handles HTTP requests
2. AuthService - Business logic for authentication
3. UserRepository - Data access for user information
4. TokenService - JWT token generation and validation

## Data Models
```
User {
  id: UUID
  email: String
  password_hash: String
  created_at: DateTime
  updated_at: DateTime
}

Session {
  id: UUID
  user_id: UUID
  refresh_token: String
  expires_at: DateTime
}
```

## API Endpoints
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh-token
- POST /auth/forgot-password
- POST /auth/reset-password
""",
            "tasks": """# User Authentication Tasks

- [ ] 1. Set up project structure
  - [ ] 1.1 Create directory structure
  - [ ] 1.2 Set up dependencies
  - [ ] 1.3 Configure build system

- [ ] 2. Implement data models
  - [ ] 2.1 Create User model
  - [ ] 2.2 Create Session model
  - [ ] 2.3 Set up database migrations

- [ ] 3. Implement authentication service
  - [ ] 3.1 Implement password hashing
  - [ ] 3.2 Implement JWT token generation
  - [ ] 3.3 Implement token validation

- [ ] 4. Implement API endpoints
  - [ ] 4.1 Implement registration endpoint
  - [ ] 4.2 Implement login endpoint
  - [ ] 4.3 Implement logout endpoint
  - [ ] 4.4 Implement token refresh endpoint
  - [ ] 4.5 Implement password reset endpoints

- [ ] 5. Implement security features
  - [ ] 5.1 Add rate limiting
  - [ ] 5.2 Add session timeout
  - [ ] 5.3 Add CSRF protection

- [ ] 6. Write tests
  - [ ] 6.1 Unit tests
  - [ ] 6.2 Integration tests
  - [ ] 6.3 End-to-end tests
""",
        },
        {
            "feature_name": "data-export",
            "initial_idea": "Create a data export system that supports multiple formats",
            "requirements": """# Data Export Requirements

## Overview
Implement a flexible data export system that supports multiple formats and delivery methods.

## Functional Requirements
1. Support CSV, JSON, and Excel export formats
2. Allow users to select which fields to export
3. Support filtering data before export
4. Support scheduled exports
5. Support email delivery of exports

## Performance Requirements
1. Handle exports of up to 1 million records
2. Process exports asynchronously for large datasets
3. Provide progress updates for long-running exports
""",
            "design": """# Data Export Design

## Architecture
The export system will use a modular architecture with format-specific exporters and delivery methods.

## Components
1. ExportController - Handles HTTP requests
2. ExportService - Orchestrates the export process
3. ExportFormatters - Format-specific exporters (CSV, JSON, Excel)
4. DeliveryService - Handles delivery of exports (download, email)
5. SchedulerService - Manages scheduled exports

## Data Models
```
ExportJob {
  id: UUID
  user_id: UUID
  format: String
  filters: JSON
  fields: String[]
  status: String
  created_at: DateTime
  completed_at: DateTime
}

ScheduledExport {
  id: UUID
  export_job_id: UUID
  schedule: String
  delivery_method: String
  delivery_params: JSON
}
```

## Process Flow
1. User creates export request
2. System validates request
3. System creates export job
4. Worker processes job asynchronously
5. System delivers export when complete
""",
            "tasks": """# Data Export Tasks

- [ ] 1. Set up project structure
  - [ ] 1.1 Create directory structure
  - [ ] 1.2 Set up dependencies
  - [ ] 1.3 Configure build system

- [ ] 2. Implement data models
  - [ ] 2.1 Create ExportJob model
  - [ ] 2.2 Create ScheduledExport model
  - [ ] 2.3 Set up database migrations

- [ ] 3. Implement export formatters
  - [ ] 3.1 Implement CSV formatter
  - [ ] 3.2 Implement JSON formatter
  - [ ] 3.3 Implement Excel formatter

- [ ] 4. Implement export service
  - [ ] 4.1 Implement job creation
  - [ ] 4.2 Implement filtering logic
  - [ ] 4.3 Implement field selection
  - [ ] 4.4 Implement progress tracking

- [ ] 5. Implement delivery methods
  - [ ] 5.1 Implement download delivery
  - [ ] 5.2 Implement email delivery

- [ ] 6. Implement scheduler
  - [ ] 6.1 Implement cron-based scheduling
  - [ ] 6.2 Implement scheduler worker

- [ ] 7. Implement API endpoints
  - [ ] 7.1 Implement export creation endpoint
  - [ ] 7.2 Implement export status endpoint
  - [ ] 7.3 Implement scheduled export endpoints

- [ ] 8. Write tests
  - [ ] 8.1 Unit tests
  - [ ] 8.2 Integration tests
  - [ ] 8.3 Performance tests
""",
        },
    ]


def get_sample_file_references() -> Dict[str, str]:
    """Get sample file references for testing."""
    return {
        "markdown": """# Sample Markdown File

## Introduction
This is a sample markdown file for testing file references.

## Features
- Feature 1
- Feature 2
- Feature 3

## Code Example
```python
def hello_world():
    print("Hello, world!")
```
""",
        "code": """// Sample JavaScript code
function calculateTotal(items) {
  return items.reduce((total, item) => {
    return total + (item.price * item.quantity);
  }, 0);
}

const items = [
  { name: 'Product 1', price: 10, quantity: 2 },
  { name: 'Product 2', price: 15, quantity: 1 },
  { name: 'Product 3', price: 5, quantity: 4 }
];

const total = calculateTotal(items);
console.log(`Total: $${total}`);
""",
        "data": """id,name,email,role
1,John Doe,john@example.com,admin
2,Jane Smith,jane@example.com,user
3,Bob Johnson,bob@example.com,user
4,Alice Brown,alice@example.com,manager
5,Charlie Davis,charlie@example.com,user
""",
        "config": """{
  "server": {
    "port": 8080,
    "host": "127.0.0.1",
    "debug": true
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "appdb",
    "user": "dbuser",
    "password": "dbpass"
  },
  "logging": {
    "level": "info",
    "file": "app.log"
  }
}
""",
    }


def get_sample_tasks() -> Dict[str, List[Dict]]:
    """Get sample tasks for testing."""
    return {
        "user-authentication": [
            {
                "identifier": "1",
                "title": "Set up project structure",
                "status": "completed",
            },
            {
                "identifier": "1.1",
                "title": "Create directory structure",
                "status": "completed",
            },
            {
                "identifier": "1.2",
                "title": "Set up dependencies",
                "status": "completed",
            },
            {
                "identifier": "1.3",
                "title": "Configure build system",
                "status": "completed",
            },
            {
                "identifier": "2",
                "title": "Implement data models",
                "status": "in_progress",
            },
            {"identifier": "2.1", "title": "Create User model", "status": "completed"},
            {
                "identifier": "2.2",
                "title": "Create Session model",
                "status": "in_progress",
            },
            {
                "identifier": "2.3",
                "title": "Set up database migrations",
                "status": "not_started",
            },
            {
                "identifier": "3",
                "title": "Implement authentication service",
                "status": "not_started",
            },
            {
                "identifier": "3.1",
                "title": "Implement password hashing",
                "status": "not_started",
            },
            {
                "identifier": "3.2",
                "title": "Implement JWT token generation",
                "status": "not_started",
            },
            {
                "identifier": "3.3",
                "title": "Implement token validation",
                "status": "not_started",
            },
        ],
        "data-export": [
            {
                "identifier": "1",
                "title": "Set up project structure",
                "status": "completed",
            },
            {
                "identifier": "1.1",
                "title": "Create directory structure",
                "status": "completed",
            },
            {
                "identifier": "1.2",
                "title": "Set up dependencies",
                "status": "completed",
            },
            {
                "identifier": "1.3",
                "title": "Configure build system",
                "status": "completed",
            },
            {
                "identifier": "2",
                "title": "Implement data models",
                "status": "completed",
            },
            {
                "identifier": "2.1",
                "title": "Create ExportJob model",
                "status": "completed",
            },
            {
                "identifier": "2.2",
                "title": "Create ScheduledExport model",
                "status": "completed",
            },
            {
                "identifier": "2.3",
                "title": "Set up database migrations",
                "status": "completed",
            },
            {
                "identifier": "3",
                "title": "Implement export formatters",
                "status": "in_progress",
            },
            {
                "identifier": "3.1",
                "title": "Implement CSV formatter",
                "status": "completed",
            },
            {
                "identifier": "3.2",
                "title": "Implement JSON formatter",
                "status": "in_progress",
            },
            {
                "identifier": "3.3",
                "title": "Implement Excel formatter",
                "status": "not_started",
            },
        ],
    }
