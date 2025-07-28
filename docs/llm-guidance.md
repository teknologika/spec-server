# LLM Guidance for spec-server

This document provides guidance for LLMs on how to effectively use the spec-server tool to facilitate a structured conversation with users about requirements and design before proceeding to implementation tasks.

## Overview of the Workflow Process

The spec-server implements a three-phase workflow:

1. **Requirements Phase**: Define what needs to be built
2. **Design Phase**: Determine how it will be built
3. **Tasks Phase**: Break down the implementation into actionable steps

LLMs should guide users through each phase with a conversational approach, ensuring thorough exploration before advancing to the next phase.

## Conversational Approach

### Initial Engagement

When a user expresses interest in building a feature, the LLM should:

1. **Introduce the spec-server workflow**:
   ```
   I see you want to build [feature]. Let's use a structured approach to define requirements, design the solution, and break it down into implementation tasks. This will help ensure we build exactly what you need.
   ```

2. **Explain the benefits**:
   ```
   This approach will help us:
   - Clearly define what success looks like
   - Make thoughtful design decisions
   - Create a clear implementation plan
   - Avoid rework and scope creep
   ```

### Requirements Phase Guidance

Before creating the requirements document, the LLM should have a conversation to:

1. **Understand user needs**:
   ```
   Before we document requirements, let's discuss:
   - Who will use this feature?
   - What problem does it solve?
   - What are the must-have vs. nice-to-have aspects?
   - How will we know if it's successful?
   ```

2. **Explore constraints**:
   ```
   Are there any constraints we should consider?
   - Technical limitations
   - Timeline considerations
   - Integration requirements
   - Performance expectations
   ```

3. **Discuss acceptance criteria**:
   ```
   Let's define some acceptance criteria using the EARS format. These are specific conditions that must be met for the feature to be considered complete:
   - WHEN [condition] THEN the system SHALL [response]
   - WHEN [condition] THEN the system SHALL [response]
   - IF [condition] THEN the system SHALL [response]
   ```

4. **Structure requirements properly**:
   ```
   I'll organize these into numbered requirements with numbered acceptance criteria. This creates a clear reference system where:
   - Requirement 1 has acceptance criteria 1.1, 1.2, 1.3, etc.
   - Requirement 2 has acceptance criteria 2.1, 2.2, 2.3, etc.
   - Tasks can then reference specific criteria like "1.1, 2.3, 3.1"
   ```

5. **Summarize understanding**:
   ```
   Based on our discussion, here's my understanding of what you need... [summary]
   Is this accurate? Would you like to add or modify anything?
   ```

### Design Phase Guidance

After requirements are approved, but before creating the design document:

1. **Discuss design considerations**:
   ```
   Now that we have clear requirements, let's discuss how to implement this feature:
   - What architecture approach makes sense?
   - Are there existing components we can leverage?
   - What data structures will we need?
   - Are there any performance considerations?
   ```

2. **Explore alternatives**:
   ```
   I see a few possible approaches to implementing this:
   1. [Approach A] which offers [benefits] but has [drawbacks]
   2. [Approach B] which offers [benefits] but has [drawbacks]

   What are your thoughts on these approaches?
   ```

3. **Discuss technical details**:
   ```
   Let's talk about some technical details:
   - How will this integrate with the existing system?
   - What APIs or interfaces will be needed?
   - How will we handle error cases?
   - What about security considerations?
   ```

4. **Validate design direction**:
   ```
   Based on our discussion, I recommend [design approach] because [rationale].
   Does this align with your thinking?
   ```

### Tasks Phase Guidance

After design is approved, but before creating the tasks document:

1. **Discuss implementation strategy**:
   ```
   Now let's talk about how to break down the implementation:
   - Should we use a particular development methodology?
   - Are there dependencies between components?
   - What's the logical sequence for implementation?
   - How should we approach testing?
   ```

2. **Identify potential challenges**:
   ```
   I see a few areas that might be challenging:
   - [Challenge 1] which we could address by...
   - [Challenge 2] which we could address by...

   Are there other challenges you anticipate?
   ```

3. **Discuss testing approach**:
   ```
   Let's consider how we'll test this feature:
   - What unit tests will be needed?
   - How about integration tests?
   - Are there specific edge cases to test?
   ```

## Using spec-server Tools Effectively

### Creating a Spec

Only after sufficient discussion about user needs:

```
I'll create a specification for this feature now based on our discussion.

<function_calls>
<invoke name="create_spec">
<parameter name="feature_name">feature-name<paramet
er name="feature_name">feature-name</parameter>
<parameter name="initial_idea">Comprehensive description based on discussion</parameter>
</invoke>
</function_calls>
```

### Updating Requirements

After thorough requirements discussion:

```
Based on our conversation, I'll document the requirements for this feature using the proper numbering system.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">requirements</parameter>
<parameter name="content">
# Requirements Document

## Introduction
[Brief description of the feature and its purpose based on discussion]

## Requirements

### Requirement 1

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]
3. WHEN [condition] THEN the system SHALL [response]

### Requirement 2

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]

### Requirement 3

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]
3. WHEN [condition] THEN the system SHALL [response]
</parameter>
<parameter name="phase_approval">false</parameter>
</invoke>
</function_calls>
```

### Reviewing Requirements

After presenting requirements:

```
These are the documented requirements based on our discussion. Please review them carefully:

[Requirements content]

Is there anything you'd like to add, remove, or modify before we approve these requirements and move to the design phase?
```

### Approving Requirements

Only after user confirmation:

```
Great! I'll mark the requirements as approved so we can move to the design phase.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">requirements</parameter>
<parameter name="content">[Updated content based on feedback]</parameter>
<parameter name="phase_approval">true</parameter>
</invoke>
</function_calls>
```

### Updating Design

After thorough design discussion:

```
Based on our design discussion, I'll document the technical approach for this feature using the enhanced Intent/Goals/Logic format.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">design</parameter>
<parameter name="content">
# Design for [Feature Name]

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
[Approach to testing the implementation]
</parameter>
<parameter name="phase_approval">false</parameter>
</invoke>
</function_calls>
```

### Reviewing Design

After presenting design:

```
This is the technical design based on our discussion. Please review it carefully:

[Design content]

Is there anything you'd like to add, remove, or modify before we approve this design and move to defining implementation tasks?
```

### Approving Design

Only after user confirmation:

```
Great! I'll mark the design as approved so we can move to defining implementation tasks.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">design</parameter>
<parameter name="content">[Updated content based on feedback]</parameter>
<parameter name="phase_approval">true</parameter>
</invoke>
</function_calls>
```

### Creating Tasks

After implementation strategy discussion:

```
Based on our implementation discussion, I'll break down the work into specific tasks. The system will automatically format these and link them to requirements.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">tasks</parameter>
<parameter name="content">
# Implementation Plan

- [ ] 1. [Primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]

- [ ] 2. [Second primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]

- [ ] 3. [Third primary task description]
  - [Detailed sub-task or implementation note]
  - [Another implementation detail]
  - [Additional context or requirements]
</parameter>
<parameter name="phase_approval">false</parameter>
</invoke>
</function_calls>
```

Note: The system will automatically:
- Format tasks into the correct structure
- Add requirements references based on content analysis
- Move any non-task content to appropriate documents
- Validate task completion against requirements and design

### Reviewing Tasks

After presenting tasks:

```
These are the implementation tasks I've defined based on our discussion. Please review them:

[Tasks content]

Is there anything you'd like to add, remove, or modify before we finalize these tasks?
```

### Approving Tasks

Only after user confirmation:

```
Great! I'll mark the tasks as approved so we can begin implementation.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">tasks</parameter>
<parameter name="content">[Updated content based on feedback]</parameter>
<parameter name="phase_approval">true</parameter>
</invoke>
</function_calls>
```

## Enhanced Features

### Enhanced Design Format

The spec-server now uses an enhanced design format that structures all technical elements with Intent/Goals/Logic sections:

- **Intent**: Brief description of what the element does and why it exists
- **Goals**: Specific, measurable objectives the element achieves (bullet points)
- **Logic**: Detailed explanation of how the element works and its implementation approach

This format applies to:
- Components and services
- Interfaces and APIs
- Data models and structures
- Architectural elements

When creating design documents, always use this structure for technical elements. The system will automatically detect and enhance existing designs that lack this format.

### Auto-Format Task Lists

The spec-server automatically formats task lists to ensure consistency:

- **Automatic formatting**: Tasks are reformatted into the correct structure during read/create/update operations
- **Requirements linking**: Tasks are automatically linked to relevant requirements using the numbering system
- **Content redistribution**: Non-task content is moved to appropriate documents (requirements or design)
- **Completion validation**: Task completion is validated against requirements and design

**Requirement Numbering System:**
- Requirements are numbered sequentially (1, 2, 3, etc.)
- Acceptance criteria are numbered within each requirement (1, 2, 3, etc.)
- Tasks reference specific criteria using "requirement.criteria" format (e.g., 1.1, 2.3, 3.1)
- This creates clear traceability from implementation back to specific acceptance criteria

When creating tasks:
- Use a flat numbered list format (no nested numbering like 1.1, 1.2)
- Include detailed sub-tasks as bullet points under main tasks
- Focus only on coding and implementation tasks
- Let the system handle formatting and requirements linking automatically

## Best Practices for LLMs

### Encourage Iteration

```
Remember that we can iterate on these [requirements/design/tasks] as needed. It's better to get feedback early rather than proceeding with incorrect assumptions.
```

### Provide Rationale

```
I'm suggesting this [requirement/design approach/task breakdown] because [rationale]. This helps address [specific need or concern you mentioned].
```

### Highlight Trade-offs

```
There's a trade-off to consider here:
- Option A offers [benefit] but has [drawback]
- Option B offers [benefit] but has [drawback]

What's more important for your specific needs?
```

### Connect Back to Requirements

```
This design decision directly supports the requirement you mentioned about [specific requirement]. It ensures that [benefit].
```

### Use Enhanced Design Format

```
For this component, let me structure it using the Intent/Goals/Logic format:

**Intent**: This component serves as the main data processor for user requests.

**Goals**:
- Validate incoming data according to business rules
- Transform data into the required internal format
- Handle errors gracefully with meaningful messages
- Maintain high performance under load

**Logic**: The component will implement a pipeline pattern where data flows through validation, transformation, and error handling stages. It will use dependency injection for testability and include comprehensive logging for debugging.

Does this structure clearly communicate the component's purpose and implementation approach?
```

### Acknowledge Uncertainty

```
I'm not entirely certain about [aspect]. Could you provide more information about [specific question] so we can make a more informed decision?
```

### Leverage Automatic Features

```
I'll create the tasks now, and the system will automatically format them and link them to the relevant requirements we discussed. If any content doesn't belong in tasks, it will be moved to the appropriate document.
```

```
The system will automatically enhance this design with the Intent/Goals/Logic format for any technical elements that need it. This ensures consistent documentation structure across all your specs.
```

## Document Templates

### Requirements Document Template

```markdown
# Requirements Document

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
3. WHEN [condition] THEN the system SHALL [response]

### Requirement 3

**User Story:** As a [user type], I want to [action], so that [benefit]

#### Acceptance Criteria

1. WHEN [condition] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [response]
```

**Important Numbering System:**
- **Requirements**: Numbered sequentially (1, 2, 3, etc.)
- **Acceptance Criteria**: Numbered within each requirement (1, 2, 3, etc.)
- **Reference Format**: Tasks reference specific criteria as "1.1, 1.2, 2.1, 3.2" (requirement.criteria)
- **EARS Format**: Use "WHEN [condition] THEN system SHALL [response]" for acceptance criteria

### Design Document Template

```markdown
# Design for [Feature Name]

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
[Approach to testing the implementation]
```

### Tasks Document Template

```markdown
# Implementation Plan

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
```

**Important Notes:**
- **Requirements References**: Use format "requirement.criteria" (e.g., 1.1 = Requirement 1, Acceptance Criteria 1)
- **Automatic Formatting**: Tasks are automatically formatted with proper structure
- **Automatic Linking**: Requirements references are automatically added based on content analysis
- **Content Organization**: Non-task content is automatically moved to appropriate documents
- **Validation**: Task completion is validated against requirements and design

## Conclusion

By following this conversational approach and leveraging the enhanced features, LLMs can help users thoroughly explore requirements and design considerations before proceeding to implementation. The spec-server's automatic formatting and enhancement features ensure consistency while the conversational approach ensures that the resulting specifications are well-thought-out and aligned with user needs.

Key benefits of the enhanced workflow:
- **Enhanced Design Format**: Provides clear Intent/Goals/Logic structure for all technical elements
- **Auto-Format Task Lists**: Ensures consistent task formatting and automatic requirements linking
- **Content Organization**: Automatically moves content to appropriate documents
- **Validation**: Task completion is validated against requirements and design

Remember that the goal is not just to create documents, but to facilitate a thoughtful process that results in clear understanding and direction for implementation, while leveraging automation to ensure consistency and quality.
