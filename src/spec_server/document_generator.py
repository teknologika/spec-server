"""
DocumentGenerator implementation for creating properly formatted specification documents.

This module provides the DocumentGenerator class which creates properly formatted
specification documents based on templates and user input. It enforces document
structure standards and handles document validation.
"""

import re
from typing import Any, Dict, List, Optional

from .models import (
    DEFAULT_DESIGN_TEMPLATE,
    DEFAULT_REQUIREMENTS_TEMPLATE,
    DEFAULT_TASKS_TEMPLATE,
    DocumentTemplate,
)


class DocumentGenerationError(Exception):
    """Exception raised when document generation fails."""

    def __init__(
        self,
        message: str,
        error_code: str = "DOCUMENT_GENERATION_ERROR",
        details: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DocumentGenerator:
    """
    Creates properly formatted specification documents based on templates and user input.

    Enforces document structure standards, including EARS format for requirements,
    specific section layouts for design documents, and checkbox formatting for tasks.
    """

    def __init__(self) -> None:
        """Initialize the DocumentGenerator with default templates."""
        self.templates = {
            "requirements": DEFAULT_REQUIREMENTS_TEMPLATE,
            "design": DEFAULT_DESIGN_TEMPLATE,
            "tasks": DEFAULT_TASKS_TEMPLATE,
        }

    def generate_requirements(self, initial_idea: str, feature_name: str = "") -> str:
        """
        Generate a requirements document based on the initial idea.

        Args:
            initial_idea: User's rough feature description
            feature_name: Optional feature name for context

        Returns:
            Formatted requirements document in markdown

        Raises:
            DocumentGenerationError: If generation fails
        """
        if not initial_idea.strip():
            raise DocumentGenerationError(
                "Initial idea cannot be empty",
                error_code="EMPTY_INITIAL_IDEA",
                details={"initial_idea": initial_idea},
            )

        try:
            # Extract key concepts from the initial idea
            concepts = self._extract_concepts_from_idea(initial_idea)

            # Generate introduction
            introduction = self._generate_requirements_introduction(
                initial_idea, feature_name, concepts
            )

            # Generate requirements based on concepts
            requirements_sections = self._generate_requirements_sections(
                concepts, initial_idea
            )

            # Combine into full document
            document = f"""# Requirements Document

## Introduction

{introduction}

## Requirements

{requirements_sections}"""

            return document

        except Exception as e:
            raise DocumentGenerationError(
                f"Failed to generate requirements document: {str(e)}",
                error_code="REQUIREMENTS_GENERATION_FAILED",
                details={"initial_idea": initial_idea, "error": str(e)},
            )

    def generate_design(self, requirements: str, feature_name: str = "") -> str:
        """
        Generate a design document based on approved requirements.

        Args:
            requirements: Content of the requirements document
            feature_name: Optional feature name for context

        Returns:
            Formatted design document in markdown

        Raises:
            DocumentGenerationError: If generation fails
        """
        if not requirements.strip():
            raise DocumentGenerationError(
                "Requirements content cannot be empty",
                error_code="EMPTY_REQUIREMENTS",
                details={"requirements": requirements},
            )

        try:
            # Parse requirements to extract key information
            parsed_requirements = self._parse_requirements(requirements)

            # Generate design sections
            overview = self._generate_design_overview(parsed_requirements, feature_name)
            architecture = self._generate_design_architecture(parsed_requirements)
            components = self._generate_design_components(parsed_requirements)
            data_models = self._generate_design_data_models(parsed_requirements)
            error_handling = self._generate_design_error_handling(parsed_requirements)
            testing_strategy = self._generate_design_testing_strategy(
                parsed_requirements
            )

            # Combine into full document
            document = f"""# Design Document

## Overview

{overview}

## Architecture

{architecture}

## Components and Interfaces

{components}

## Data Models

{data_models}

## Error Handling

{error_handling}

## Testing Strategy

{testing_strategy}"""

            return document

        except Exception as e:
            raise DocumentGenerationError(
                f"Failed to generate design document: {str(e)}",
                error_code="DESIGN_GENERATION_FAILED",
                details={"requirements": requirements[:200], "error": str(e)},
            )

    def generate_tasks(
        self, requirements: str, design: str, feature_name: str = ""
    ) -> str:
        """
        Generate implementation tasks based on requirements and design.

        Args:
            requirements: Content of the requirements document
            design: Content of the design document
            feature_name: Optional feature name for context

        Returns:
            Formatted tasks document in markdown

        Raises:
            DocumentGenerationError: If generation fails
        """
        if not requirements.strip():
            raise DocumentGenerationError(
                "Requirements content cannot be empty",
                error_code="EMPTY_REQUIREMENTS",
                details={"requirements": requirements},
            )

        if not design.strip():
            raise DocumentGenerationError(
                "Design content cannot be empty",
                error_code="EMPTY_DESIGN",
                details={"design": design},
            )

        try:
            # Parse requirements and design
            parsed_requirements = self._parse_requirements(requirements)
            parsed_design = self._parse_design(design)

            # Generate implementation tasks
            tasks = self._generate_implementation_tasks(
                parsed_requirements, parsed_design, feature_name
            )

            # Format tasks as numbered checkboxes
            formatted_tasks = self._format_tasks_as_checkboxes(tasks)

            # Combine into full document
            document = f"""# Implementation Plan

{formatted_tasks}"""

            return document

        except Exception as e:
            raise DocumentGenerationError(
                f"Failed to generate tasks document: {str(e)}",
                error_code="TASKS_GENERATION_FAILED",
                details={
                    "requirements": requirements[:100],
                    "design": design[:100],
                    "error": str(e),
                },
            )

    def validate_document_format(self, doc_type: str, content: str) -> bool:
        """
        Validate that a document follows the expected format.

        Args:
            doc_type: Type of document ("requirements", "design", "tasks")
            content: Document content to validate

        Returns:
            True if document is valid

        Raises:
            DocumentGenerationError: If validation fails
        """
        if doc_type not in self.templates:
            raise DocumentGenerationError(
                f"Unknown document type: {doc_type}",
                error_code="UNKNOWN_DOCUMENT_TYPE",
                details={"doc_type": doc_type},
            )

        template = self.templates[doc_type]

        try:
            if doc_type == "requirements":
                return self._validate_requirements_format(content, template)
            elif doc_type == "design":
                return self._validate_design_format(content, template)
            elif doc_type == "tasks":
                return self._validate_tasks_format(content, template)
            else:
                return False

        except Exception as e:
            raise DocumentGenerationError(
                f"Document validation failed: {str(e)}",
                error_code="VALIDATION_FAILED",
                details={"doc_type": doc_type, "error": str(e)},
            )

    def _extract_concepts_from_idea(self, initial_idea: str) -> Dict[str, List[str]]:
        """Extract key concepts from the initial idea."""
        concepts: Dict[str, List[str]] = {
            "actors": [],
            "actions": [],
            "objects": [],
            "goals": [],
            "constraints": [],
        }

        # Simple keyword extraction (could be enhanced with NLP)
        text = initial_idea.lower()

        # Extract actors (users, systems, etc.)
        actor_patterns = [
            r"\b(user|admin|developer|system|client|customer|manager)\b",
            r"\b(as a|for)\s+(\w+)",
        ]
        for pattern in actor_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    concepts["actors"].extend(
                        [m for m in match if m not in ["as a", "for"]]
                    )
                else:
                    concepts["actors"].append(match)

        # Extract actions (verbs)
        action_patterns = [
            r"\b(create|manage|track|monitor|generate|implement|provide|enable|support)\b",
            r"\b(want to|need to|should|can|will)\s+(\w+)",
        ]
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    concepts["actions"].extend(
                        [
                            m
                            for m in match
                            if m not in ["want to", "need to", "should", "can", "will"]
                        ]
                    )
                else:
                    concepts["actions"].append(match)

        # Extract objects (nouns)
        object_patterns = [
            r"\b(feature|specification|document|task|requirement|design|workflow|process)\b",
            r"\b(server|client|api|interface|component|module|system)\b",
        ]
        for pattern in object_patterns:
            matches = re.findall(pattern, text)
            concepts["objects"].extend(matches)

        # Remove duplicates and clean up
        for key in concepts:
            concepts[key] = list(
                set([item.strip() for item in concepts[key] if item.strip()])
            )

        return concepts

    def _generate_requirements_introduction(
        self, initial_idea: str, feature_name: str, concepts: Dict[str, List[str]]
    ) -> str:
        """Generate the introduction section for requirements."""
        feature_desc = feature_name if feature_name else "this feature"

        intro = f"This feature implements {initial_idea.strip()}"

        if concepts["actors"]:
            actors_text = ", ".join(concepts["actors"][:3])
            intro += f" The system will serve {actors_text}"

        if concepts["actions"]:
            actions_text = ", ".join(concepts["actions"][:3])
            intro += f" by enabling them to {actions_text}"

        if concepts["objects"]:
            objects_text = ", ".join(concepts["objects"][:3])
            intro += f" with {objects_text}"

        intro += "."

        return intro

    def _generate_requirements_sections(
        self, concepts: Dict[str, List[str]], initial_idea: str
    ) -> str:
        """Generate requirements sections with user stories and acceptance criteria."""
        requirements = []

        # Generate primary requirement based on main concept
        primary_actors = concepts["actors"][:2] if concepts["actors"] else ["user"]
        primary_actions = concepts["actions"][:2] if concepts["actions"] else ["use"]
        primary_objects = concepts["objects"][:2] if concepts["objects"] else ["system"]

        req_num = 1
        for actor in primary_actors:
            for action in primary_actions:
                for obj in primary_objects:
                    user_story = f"As a {actor}, I want to {action} {obj}, so that I can achieve my goals efficiently"

                    # Generate EARS format acceptance criteria
                    criteria = [
                        f"WHEN {actor} requests to {action} {obj} THEN the system SHALL provide appropriate functionality",
                        f"WHEN {actor} interacts with {obj} THEN the system SHALL respond within acceptable time limits",
                        f"IF {actor} provides invalid input THEN the system SHALL provide clear error messages",
                    ]

                    criteria_text = "\n".join(
                        [f"{i+1}. {criterion}" for i, criterion in enumerate(criteria)]
                    )

                    requirement = f"""### Requirement {req_num}

**User Story:** {user_story}

#### Acceptance Criteria

{criteria_text}"""

                    requirements.append(requirement)
                    req_num += 1

                    # Limit to avoid too many requirements
                    if req_num > 3:
                        break
                if req_num > 3:
                    break
            if req_num > 3:
                break

        return "\n\n".join(requirements)

    def _parse_requirements(self, requirements: str) -> Dict[str, List]:
        """Parse requirements document to extract key information."""
        parsed: Dict[str, List] = {
            "user_stories": [],
            "acceptance_criteria": [],
            "actors": [],
            "features": [],
        }

        # Extract user stories
        user_story_pattern = r"As a ([^,]+), I want ([^,]+), so that ([^.]+)"
        matches = re.findall(user_story_pattern, requirements, re.IGNORECASE)
        for match in matches:
            actor, want, benefit = match
            parsed["user_stories"].append(
                {
                    "actor": actor.strip(),
                    "want": want.strip(),
                    "benefit": benefit.strip(),
                }
            )
            parsed["actors"].append(actor.strip())

        # Extract acceptance criteria
        criteria_pattern = r"(WHEN|IF|GIVEN)([^.]+)(THEN|SHALL)([^.]+)"
        matches = re.findall(criteria_pattern, requirements, re.IGNORECASE)
        for match in matches:
            condition_type, condition, action_type, action = match
            parsed["acceptance_criteria"].append(
                {
                    "condition_type": condition_type.strip(),
                    "condition": condition.strip(),
                    "action_type": action_type.strip(),
                    "action": action.strip(),
                }
            )

        # Clean up duplicates
        parsed["actors"] = list(set(parsed["actors"]))

        return parsed

    def _generate_design_overview(
        self, parsed_requirements: Dict[str, Any], feature_name: str
    ) -> str:
        """Generate design overview section."""
        actors = parsed_requirements.get("actors", [])
        user_stories = parsed_requirements.get("user_stories", [])

        overview = f"The {feature_name or 'system'} is designed to provide"

        if user_stories:
            main_features = [story["want"] for story in user_stories[:2]]
            overview += f" {' and '.join(main_features)}"

        if actors:
            overview += f" for {', '.join(actors[:2])}"

        overview += ". The system follows a modular architecture with clear separation of concerns."

        return overview

    def _generate_design_architecture(
        self, parsed_requirements: Dict[str, List[str]]
    ) -> str:
        """Generate architecture section."""
        return """The system follows a layered architecture pattern:

- **Presentation Layer**: User interface and API endpoints
- **Business Logic Layer**: Core functionality and business rules
- **Data Access Layer**: Data persistence and retrieval
- **Integration Layer**: External system integrations

The architecture supports scalability, maintainability, and testability."""

    def _generate_design_components(
        self, parsed_requirements: Dict[str, List[str]]
    ) -> str:
        """Generate components and interfaces section."""
        return """### Core Components

1. **Main Controller**: Orchestrates business logic and handles user requests
2. **Service Layer**: Implements business rules and processes
3. **Repository Layer**: Handles data access and persistence
4. **Validation Layer**: Input validation and business rule enforcement

### Interfaces

- **REST API**: HTTP-based interface for external clients
- **Internal APIs**: Component-to-component communication
- **Data Interfaces**: Database and external service connections"""

    def _generate_design_data_models(
        self, parsed_requirements: Dict[str, List[str]]
    ) -> str:
        """Generate data models section."""
        return """### Primary Entities

The system will include the following core data models:

- **User**: Represents system users with roles and permissions
- **Configuration**: System settings and parameters
- **Audit Log**: Track system activities and changes

### Relationships

- Users have roles that determine permissions
- All entities include audit fields for tracking
- Configuration supports hierarchical organization"""

    def _generate_design_error_handling(
        self, parsed_requirements: Dict[str, List[str]]
    ) -> str:
        """Generate error handling section."""
        return """### Error Categories

1. **Validation Errors**: Invalid input data or business rule violations
2. **System Errors**: Infrastructure failures and technical issues
3. **Business Errors**: Domain-specific error conditions
4. **Integration Errors**: External service communication failures

### Error Response Format

All errors include:
- Error code for programmatic handling
- Human-readable message
- Additional context and suggestions
- Timestamp and correlation ID"""

    def _generate_design_testing_strategy(
        self, parsed_requirements: Dict[str, List[str]]
    ) -> str:
        """Generate testing strategy section."""
        return """### Testing Approach

1. **Unit Testing**: Individual component testing with high coverage
2. **Integration Testing**: Component interaction and API testing
3. **End-to-End Testing**: Complete user workflow validation
4. **Performance Testing**: Load and stress testing

### Test Data Management

- Use test fixtures for consistent data
- Implement test data builders for complex scenarios
- Maintain separate test databases
- Include both positive and negative test cases"""

    def _parse_design(self, design: str) -> Dict[str, List[str]]:
        """Parse design document to extract key information."""
        parsed: Dict[str, List[str]] = {
            "components": [],
            "interfaces": [],
            "data_models": [],
            "sections": [],
        }

        # Extract section headers
        section_pattern = r"^\s*##\s+(.+)$"
        matches = re.findall(section_pattern, design, re.MULTILINE)
        parsed["sections"] = [match.strip() for match in matches]

        # Extract components mentioned
        component_pattern = r"\*\*([^*]+)\*\*:"
        matches = re.findall(component_pattern, design)
        parsed["components"] = [match.strip() for match in matches]

        return parsed

    def _generate_implementation_tasks(
        self,
        parsed_requirements: Dict[str, Any],
        parsed_design: Dict[str, List[str]],
        feature_name: str,
    ) -> List[Dict[str, Any]]:
        """Generate implementation tasks based on requirements and design."""
        tasks = []

        # Setup and infrastructure tasks
        tasks.append(
            {
                "id": "1",
                "description": "Set up project structure and dependencies",
                "details": [
                    "Create project directory structure",
                    "Configure build system and dependencies",
                    "Set up development environment",
                    "Initialize version control",
                ],
                "requirements_refs": ["1.1"],
            }
        )

        # Core implementation tasks
        components = parsed_design.get(
            "components", ["Core Module", "Service Layer", "Data Layer"]
        )
        task_id = 2

        for i, component in enumerate(components[:3]):  # Limit to 3 main components
            tasks.append(
                {
                    "id": str(task_id),
                    "description": f"Implement {component}",
                    "details": [
                        f"Create {component} interface and implementation",
                        f"Add input validation for {component}",
                        f"Write unit tests for {component}",
                        f"Add error handling for {component}",
                    ],
                    "requirements_refs": [f"{task_id}.1", f"{task_id}.2"],
                }
            )
            task_id += 1

        # Integration and testing tasks
        tasks.append(
            {
                "id": str(task_id),
                "description": "Integration and testing",
                "details": [
                    "Write integration tests",
                    "Perform end-to-end testing",
                    "Add performance tests",
                    "Validate against requirements",
                ],
                "requirements_refs": ["1.1", "2.1"],
            }
        )

        return tasks

    def _format_tasks_as_checkboxes(self, tasks: List[Dict[str, List]]) -> str:
        """Format tasks as numbered checkboxes."""
        formatted_tasks = []

        for task in tasks:
            task_line = f"- [ ] {task['id']}. {task['description']}"

            # Add details as sub-bullets
            details = []
            for detail in task.get("details", []):
                details.append(f"  - {detail}")

            # Add requirements references
            req_refs: List[str] = task.get("requirements_refs", [])
            if req_refs:
                req_text = ", ".join(req_refs)
                details.append(f"  - _Requirements: {req_text}_")

            if details:
                task_line += "\n" + "\n".join(details)

            formatted_tasks.append(task_line)

        return "\n\n".join(formatted_tasks)

    def _validate_requirements_format(
        self, content: str, template: DocumentTemplate
    ) -> bool:
        """Validate requirements document format."""
        # Check for required sections
        required_sections = template.sections
        for section in required_sections:
            if f"## {section}" not in content:
                return False

        # Check for user stories format
        user_story_pattern = r"As a [^,]+, I want [^,]+, so that"
        if not re.search(user_story_pattern, content, re.IGNORECASE):
            return False

        # Check for acceptance criteria
        ears_pattern = r"(WHEN|IF|GIVEN).+(THEN|SHALL)"
        if not re.search(ears_pattern, content, re.IGNORECASE):
            return False

        return True

    def _validate_design_format(self, content: str, template: DocumentTemplate) -> bool:
        """Validate design document format."""
        # Check for required sections
        required_sections = template.sections
        for section in required_sections:
            if f"## {section}" not in content:
                return False

        return True

    def _validate_tasks_format(self, content: str, template: DocumentTemplate) -> bool:
        """Validate tasks document format."""
        # Check for required sections
        if "# Implementation Plan" not in content:
            return False

        # Check for checkbox format
        checkbox_pattern = r"- \[ \] \d+\."
        if not re.search(checkbox_pattern, content):
            return False

        return True
