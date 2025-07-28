"""
LLM guidance functionality for spec-server.

This module provides guidance resources and tools to help LLMs use the spec-server
effectively through a conversational approach with users.
"""

from pathlib import Path
from typing import Any, Dict

from .errors import ErrorCode, SpecError

# Path to guidance documents
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"


def get_llm_guidance_content() -> str:
    """
    Get the content of the LLM guidance document.

    Returns:
        String containing the LLM guidance content

    Raises:
        SpecError: When the guidance document is not found or cannot be read
    """
    guidance_path = DOCS_DIR / "llm-guidance.md"

    if not guidance_path.exists():
        raise SpecError(
            message=f"LLM guidance document not found at path: {guidance_path}",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            details={
                "expected_path": str(guidance_path),
                "error_type": "FileNotFoundError",
            },
        )

    try:
        return guidance_path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise SpecError(
            message=f"Permission denied reading LLM guidance document: {guidance_path}",
            error_code=ErrorCode.FILE_ACCESS_DENIED,
            details={"path": str(guidance_path), "error_type": "PermissionError"},
            cause=e,
        )
    except UnicodeDecodeError as e:
        raise SpecError(
            message=f"Encoding error reading LLM guidance document: {guidance_path}",
            error_code=ErrorCode.INTERNAL_ERROR,
            details={
                "path": str(guidance_path),
                "error_type": "UnicodeDecodeError",
                "encoding": "utf-8",
            },
            cause=e,
        )
    except Exception as e:
        raise SpecError(
            message=f"Unexpected error reading LLM guidance document: {guidance_path}",
            error_code=ErrorCode.INTERNAL_ERROR,
            details={"path": str(guidance_path), "error_type": type(e).__name__},
            cause=e,
        )


def get_phase_guidance_content(phase: str = "general") -> Dict[str, Any]:
    """
    Get guidance for a specific phase of the spec-server workflow.

    Args:
        phase: The phase to get guidance for ("requirements", "design", "tasks", or "general")

    Returns:
        Dictionary containing guidance for the specified phase
    """
    # Requirements phase guidance
    requirements_guidance: Dict[str, Any] = {
        "questions_to_ask": [
            "Who will use this feature?",
            "What problem does it solve?",
            "What are the must-have vs. nice-to-have aspects?",
            "How will we know if it's successful?",
            "Are there any constraints we should consider?",
            "What are the specific acceptance criteria for each requirement?",
            "How should we structure the requirements for clear task referencing?",
        ],
        "template": """# Requirements Document

## Introduction
[Brief description of the feature and its purpose]

## Requirements

### Requirement 1

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]
3. WHEN [condition] THEN the system SHALL [response]
4. WHEN [condition] THEN the system SHALL [response]

### Requirement 2

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]
3. WHEN [condition] THEN the system SHALL [response]""",
        "best_practices": [
            "Focus on the 'what', not the 'how'",
            "Use clear, testable acceptance criteria in EARS format",
            "Number requirements sequentially (1, 2, 3, etc.)",
            "Number acceptance criteria within each requirement (1, 2, 3, etc.)",
            "Use WHEN/THEN/SHALL format for acceptance criteria",
            "Make criteria specific and measurable",
            "Connect requirements to user needs",
        ],
        "conversation_starters": [
            "Before we document requirements, let's discuss who will use this feature and what problem it solves.",
            "What are the most important aspects of this feature that must be included?",
            "How will we know if this feature is successful once implemented?",
            "Are there any technical or business constraints we should consider?",
        ],
    }

    # Design phase guidance
    design_guidance: Dict[str, Any] = {
        "questions_to_ask": [
            "What architecture approach makes sense?",
            "Are there existing components we can leverage?",
            "What data structures will we need?",
            "Are there any performance considerations?",
            "How will this integrate with the existing system?",
            "What APIs or interfaces will be needed?",
            "How will we handle error cases?",
            "What about security considerations?",
            "What is the intent behind each major component?",
            "What are the specific goals each component should achieve?",
            "How should each component be implemented (the logic)?",
        ],
        "template": """# Design for [Feature Name]

## Overview
[High-level description of the solution architecture and design decisions]

## Architecture
[Overall system architecture and integration points]

## Components and Interfaces

### [Component Name]

**Intent**: [Brief description of what this component does and why it exists]

**Goals**:
- [Specific objective this component achieves]
- [Another objective this component achieves]
- [Additional objectives as needed]

**Logic**: [Detailed explanation of how this component works, its implementation approach, and technical details]

### [Interface Name]

**Intent**: [Brief description of what this interface provides and its purpose]

**Goals**:
- [Specific capability this interface enables]
- [Another capability this interface enables]
- [Additional capabilities as needed]

**Logic**: [Detailed explanation of the interface design, methods, parameters, and usage patterns]

## Data Models

### [Data Model Name]

**Intent**: [Brief description of what this data model represents and its role]

**Goals**:
- [Specific data requirement this model addresses]
- [Another data requirement this model addresses]
- [Additional requirements as needed]

**Logic**: [Detailed explanation of the data structure, relationships, validation rules, and usage patterns]

## Error Handling
[Approach to error handling and recovery]

## Testing Strategy
[Approach to testing the implementation]""",
        "best_practices": [
            "Consider multiple design alternatives",
            "Explain trade-offs between approaches",
            "Connect design decisions back to requirements",
            "Consider security from the beginning",
            "Document interfaces clearly",
            "Include error handling strategy",
            "Use Intent/Goals/Logic structure for all technical elements",
            "Clearly state the intent (purpose) of each component",
            "List specific, measurable goals for each element",
            "Provide detailed implementation logic and approach",
        ],
        "conversation_starters": [
            "Now that we have clear requirements, let's discuss how to implement this feature.",
            "I see a few possible approaches to implementing this. Let's discuss the trade-offs.",
            "How should this feature integrate with the existing system?",
            "Let's talk about how we'll handle error cases and edge conditions.",
        ],
    }

    # Tasks phase guidance
    tasks_guidance: Dict[str, Any] = {
        "questions_to_ask": [
            "Should we use a particular development methodology?",
            "Are there dependencies between components?",
            "What's the logical sequence for implementation?",
            "How should we approach testing?",
            "What potential challenges do you anticipate?",
            "What unit tests will be needed?",
            "How about integration tests?",
            "Are there specific edge cases to test?",
        ],
        "template": """# Implementation Plan

- [ ] 1. [Primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]
  - _Requirements: 1.1, 1.2, 2.1_

- [ ] 2. [Second primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]
  - _Requirements: 1.3, 2.2, 3.1_

- [ ] 3. [Third primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]
  - _Requirements: 2.1, 2.3, 3.2_

**Note:** Requirements references use the format "requirement.criteria" (e.g., 1.1 = Requirement 1, Acceptance Criteria 1)""",
        "best_practices": [
            "Break down tasks into manageable chunks",
            "Include testing tasks explicitly",
            "Consider dependencies between tasks",
            "Prioritize tasks appropriately",
            "Include documentation tasks",
            "Reference requirements in task descriptions",
            "Use the flat numbered list format (no nested numbering)",
            "Include detailed sub-tasks as bullet points under main tasks",
            "Add requirements references at the end of each task",
            "Focus only on coding and implementation tasks",
            "Let the system automatically format and link requirements",
        ],
        "conversation_starters": [
            "Let's talk about how to break down the implementation into specific tasks.",
            "What do you think should be the first steps in implementing this feature?",
            "Are there any dependencies between components that will affect the task order?",
            "What testing approach should we use for this feature?",
            "The system will automatically format tasks and link them to requirements - let's focus on the implementation steps.",
            "Remember that tasks will be automatically validated against requirements when marked complete.",
        ],
    }

    # General guidance
    general_guidance: Dict[str, Any] = {
        "workflow_overview": [
            "Requirements Phase: Define what needs to be built",
            "Design Phase: Determine how it will be built",
            "Tasks Phase: Break down the implementation into actionable steps",
        ],
        "conversation_approach": [
            "Have thorough discussions before creating documents",
            "Explore alternatives and trade-offs",
            "Connect design decisions back to requirements",
            "Encourage iteration and feedback",
            "Acknowledge uncertainty and ask for clarification",
        ],
        "best_practices": [
            "Provide rationale for suggestions",
            "Highlight trade-offs between approaches",
            "Use visualizations when helpful",
            "Encourage iteration on documents",
            "Focus on user needs throughout the process",
        ],
        "conversation_starters": [
            "I'd like to help you develop this feature using a structured approach. Let's start by discussing what you're trying to achieve.",
            "To make sure we build exactly what you need, let's talk through your requirements before documenting anything.",
            "I find it helpful to use a three-phase approach: requirements, design, and implementation tasks. Does that work for you?",
        ],
    }

    # Map phases to guidance
    guidance_map: Dict[str, Dict[str, Any]] = {
        "requirements": requirements_guidance,
        "design": design_guidance,
        "tasks": tasks_guidance,
        "general": general_guidance,
    }

    # Return the requested guidance or general guidance if not found
    phase_key = phase.lower()
    if phase_key in guidance_map:
        return guidance_map[phase_key]
    return general_guidance


def get_introduction_prompt() -> str:
    """
    Get the introduction prompt for spec-server.

    Returns:
        String containing the introduction prompt
    """
    return """
I'm here to help you develop features using a structured approach:

1. REQUIREMENTS: We'll discuss what needs to be built
2. DESIGN: We'll determine how it will be built
3. TASKS: We'll break down the implementation

For best results, let's have a thorough conversation about your needs before creating any documentation.

What feature would you like to develop?
"""
