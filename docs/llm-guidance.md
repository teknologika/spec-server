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
   Let's define some acceptance criteria. These are specific conditions that must be met for the feature to be considered complete. For example:
   - Users should be able to...
   - The system should respond within...
   - When an error occurs...
   ```

4. **Summarize understanding**:
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
Based on our conversation, I'll document the requirements for this feature.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">requirements</parameter>
<parameter name="content">
# Requirements for [Feature Name]

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
- [Feature or aspect explicitly not included]
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
Based on our design discussion, I'll document the technical approach for this feature.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">design</parameter>
<parameter name="content">
# Design for [Feature Name]

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
Based on our implementation discussion, I'll break down the work into specific tasks.

<function_calls>
<invoke name="update_spec_document">
<parameter name="feature_name">feature-name</parameter>
<parameter name="document_type">tasks</parameter>
<parameter name="content">
# Implementation Tasks for [Feature Name]

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
- [ ] 7. [Documentation task]
</parameter>
<parameter name="phase_approval">false</parameter>
</invoke>
</function_calls>
```

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

### Use Visualizations When Helpful

```
Here's a simple diagram to illustrate the proposed architecture:

```
[ASCII diagram or description of a diagram]
```

Would this approach meet your needs?
```

### Acknowledge Uncertainty

```
I'm not entirely certain about [aspect]. Could you provide more information about [specific question] so we can make a more informed decision?
```

## Document Templates

### Requirements Document Template

```markdown
# Requirements for [Feature Name]

## Overview
[Brief description of the feature]

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
- [Feature or aspect explicitly not included]
```

### Design Document Template

```markdown
# Design for [Feature Name]

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
[Approach to testing the implementation]
```

### Tasks Document Template

```markdown
# Implementation Tasks for [Feature Name]

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
- [ ] 7. [Documentation task]
```

## Conclusion

By following this conversational approach, LLMs can help users thoroughly explore requirements and design considerations before proceeding to implementation. This ensures that the resulting specifications are well-thought-out and aligned with user needs, leading to more successful implementations.

Remember that the goal is not just to create documents, but to facilitate a thoughtful process that results in clear understanding and direction for implementation.
