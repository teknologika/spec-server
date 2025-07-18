"""
LLM guidance functionality for spec-server.

This module provides guidance resources and tools to help LLMs use the spec-server
effectively through a conversational approach with users.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Path to guidance documents
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"


def get_llm_guidance_content() -> str:
    """
    Get the content of the LLM guidance document.
    
    Returns:
        String containing the LLM guidance content
    """
    guidance_path = DOCS_DIR / "llm-guidance.md"
    if guidance_path.exists():
        return guidance_path.read_text(encoding="utf-8")
    else:
        return "LLM guidance document not found."


def get_phase_guidance_content(phase: str = "general") -> Dict[str, Any]:
    """
    Get guidance for a specific phase of the spec-server workflow.
    
    Args:
        phase: The phase to get guidance for ("requirements", "design", "tasks", or "general")
        
    Returns:
        Dictionary containing guidance for the specified phase
    """
    # Requirements phase guidance
    requirements_guidance = {
        "questions_to_ask": [
            "Who will use this feature?",
            "What problem does it solve?",
            "What are the must-have vs. nice-to-have aspects?",
            "How will we know if it's successful?",
            "Are there any constraints we should consider?",
            "What are the acceptance criteria?"
        ],
        "template": """# Requirements for [Feature Name]

## Overview
[Brief description of the feature based on discussion]

## User Stories
- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [Specific, testable condition]
- [Specific, testable condition]

## Constraints
- [Technical constraint]
- [Business constraint]

## Out of Scope
- [Feature or aspect explicitly not included]""",
        "best_practices": [
            "Focus on the 'what', not the 'how'",
            "Use clear, testable acceptance criteria",
            "Identify constraints early",
            "Define what's out of scope explicitly",
            "Connect requirements to user needs"
        ],
        "conversation_starters": [
            "Before we document requirements, let's discuss who will use this feature and what problem it solves.",
            "What are the most important aspects of this feature that must be included?",
            "How will we know if this feature is successful once implemented?",
            "Are there any technical or business constraints we should consider?"
        ]
    }
    
    # Design phase guidance
    design_guidance = {
        "questions_to_ask": [
            "What architecture approach makes sense?",
            "Are there existing components we can leverage?",
            "What data structures will we need?",
            "Are there any performance considerations?",
            "How will this integrate with the existing system?",
            "What APIs or interfaces will be needed?",
            "How will we handle error cases?",
            "What about security considerations?"
        ],
        "template": """# Design for [Feature Name]

## Architecture Overview
[High-level description of the solution architecture]

## Components
- [Component 1]: [Description]
- [Component 2]: [Description]

## Data Models
[Description of data structures and relationships]

## Interfaces
[API definitions, function signatures, etc.]

## Error Handling
[Approach to error handling and recovery]

## Security Considerations
[Security measures and considerations]

## Performance Considerations
[Performance requirements and optimizations]

## Testing Strategy
[Approach to testing the implementation]""",
        "best_practices": [
            "Consider multiple design alternatives",
            "Explain trade-offs between approaches",
            "Connect design decisions back to requirements",
            "Consider security from the beginning",
            "Document interfaces clearly",
            "Include error handling strategy"
        ],
        "conversation_starters": [
            "Now that we have clear requirements, let's discuss how to implement this feature.",
            "I see a few possible approaches to implementing this. Let's discuss the trade-offs.",
            "How should this feature integrate with the existing system?",
            "Let's talk about how we'll handle error cases and edge conditions."
        ]
    }
    
    # Tasks phase guidance
    tasks_guidance = {
        "questions_to_ask": [
            "Should we use a particular development methodology?",
            "Are there dependencies between components?",
            "What's the logical sequence for implementation?",
            "How should we approach testing?",
            "What potential challenges do you anticipate?",
            "What unit tests will be needed?",
            "How about integration tests?",
            "Are there specific edge cases to test?"
        ],
        "template": """# Implementation Tasks for [Feature Name]

## Setup and Infrastructure
- [ ] 1. [Setup task]
- [ ] 2. [Infrastructure task]

## Core Functionality
- [ ] 3. [Core feature task]
  - [ ] 3.1. [Sub-task]
  - [ ] 3.2. [Sub-task]
- [ ] 4. [Core feature task]

## Testing
- [ ] 5. [Unit test task]
- [ ] 6. [Integration test task]

## Documentation
- [ ] 7. [Documentation task]""",
        "best_practices": [
            "Break down tasks into manageable chunks",
            "Include testing tasks explicitly",
            "Consider dependencies between tasks",
            "Prioritize tasks appropriately",
            "Include documentation tasks",
            "Reference requirements in task descriptions"
        ],
        "conversation_starters": [
            "Let's talk about how to break down the implementation into specific tasks.",
            "What do you think should be the first steps in implementing this feature?",
            "Are there any dependencies between components that will affect the task order?",
            "What testing approach should we use for this feature?"
        ]
    }
    
    # General guidance
    general_guidance = {
        "workflow_overview": [
            "Requirements Phase: Define what needs to be built",
            "Design Phase: Determine how it will be built",
            "Tasks Phase: Break down the implementation into actionable steps"
        ],
        "conversation_approach": [
            "Have thorough discussions before creating documents",
            "Explore alternatives and trade-offs",
            "Connect design decisions back to requirements",
            "Encourage iteration and feedback",
            "Acknowledge uncertainty and ask for clarification"
        ],
        "best_practices": [
            "Provide rationale for suggestions",
            "Highlight trade-offs between approaches",
            "Use visualizations when helpful",
            "Encourage iteration on documents",
            "Focus on user needs throughout the process"
        ],
        "conversation_starters": [
            "I'd like to help you develop this feature using a structured approach. Let's start by discussing what you're trying to achieve.",
            "To make sure we build exactly what you need, let's talk through your requirements before documenting anything.",
            "I find it helpful to use a three-phase approach: requirements, design, and implementation tasks. Does that work for you?"
        ]
    }
    
    # Map phases to guidance
    guidance_map = {
        "requirements": requirements_guidance,
        "design": design_guidance,
        "tasks": tasks_guidance,
        "general": general_guidance
    }
    
    # Return the requested guidance or general guidance if not found
    return guidance_map.get(phase.lower(), general_guidance)


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