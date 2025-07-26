"""
LLM-based task completion validation functionality.
"""

import re

from .models import Spec, TaskItem, TaskValidationResult


class LLMTaskCompletionValidator:
    """
    LLM-based task completion validator.

    Uses LLM analysis to validate that tasks are actually complete
    by comparing implementation against requirements and design.
    """

    def __init__(self):
        """Initialize the LLM task completion validator."""
        pass

    def validate_task_completion(self, task: TaskItem, spec: Spec, implementation_context: str) -> TaskValidationResult:
        """
        Validate that a task is actually complete using LLM analysis.

        Args:
            task: TaskItem to validate
            spec: Specification containing requirements and design
            implementation_context: Context about what was implemented

        Returns:
            TaskValidationResult with completion assessment
        """
        try:
            # Gather relevant requirements and design content
            requirements_content = self._get_relevant_requirements(task, spec)
            design_content = self._get_relevant_design(task, spec)

            # Generate validation prompt
            prompt = self.generate_validation_prompt(task, requirements_content, design_content, implementation_context)

            # Get LLM response (placeholder for actual LLM integration)
            llm_response = self._call_llm(prompt)

            # Parse the response
            result = self.parse_llm_validation_response(llm_response)
            result.validation_prompt = prompt
            result.llm_response = llm_response

            return result

        except Exception as e:
            # Return error result
            return TaskValidationResult(
                is_complete=False,
                confidence=0.0,
                feedback=f"Validation failed: {str(e)}",
                missing_items=["Unable to validate due to error"],
                validation_prompt="",
                llm_response="",
            )

    def generate_validation_prompt(self, task: TaskItem, requirements: str, design: str, context: str) -> str:
        """
        Generate a prompt for LLM validation of task completion.

        Args:
            task: TaskItem being validated
            requirements: Relevant requirements content
            design: Relevant design content
            context: Implementation context

        Returns:
            Formatted prompt string for LLM
        """
        prompt = f"""You are a technical reviewer validating task completion. Please analyze \
whether the following task has been properly completed based on the requirements and design.

**TASK TO VALIDATE:**
Task ID: {task.identifier}
Description: {task.description}
Requirements References: {', '.join(task.requirements_refs) if task.requirements_refs else 'None'}

**RELEVANT REQUIREMENTS:**
{requirements if requirements else 'No specific requirements provided'}

**RELEVANT DESIGN:**
{design if design else 'No specific design provided'}

**IMPLEMENTATION CONTEXT:**
{context if context else 'No implementation context provided'}

**VALIDATION INSTRUCTIONS:**
Please evaluate whether this task is truly complete by checking:
1. Does the implementation fulfill the task description?
2. Are all referenced requirements satisfied?
3. Does the implementation follow the design specifications?
4. Are there any missing components or incomplete aspects?

Respond in the following format:

COMPLETION_STATUS: [COMPLETE/INCOMPLETE]
CONFIDENCE: [0.0-1.0]
FEEDBACK: [Detailed explanation of your assessment]
MISSING_ITEMS: [List any specific items that are missing or need attention, one per line, or 'None' if complete]

Be thorough and specific in your analysis."""

        return prompt

    def parse_llm_validation_response(self, response: str) -> TaskValidationResult:
        """
        Parse LLM response to extract validation result.

        Args:
            response: Raw LLM response text

        Returns:
            TaskValidationResult parsed from response
        """
        try:
            # Extract completion status
            is_complete = False
            completion_match = re.search(r"COMPLETION_STATUS:\s*(COMPLETE|INCOMPLETE)", response, re.IGNORECASE)
            if completion_match:
                is_complete = completion_match.group(1).upper() == "COMPLETE"

            # Extract confidence
            confidence = 0.5  # Default
            confidence_match = re.search(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", response)
            if confidence_match:
                confidence = float(confidence_match.group(1))
                confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range

            # Extract feedback
            feedback = "No feedback provided"
            feedback_match = re.search(
                r"FEEDBACK:\s*(.+?)(?=\nMISSING_ITEMS:|$)",
                response,
                re.DOTALL | re.IGNORECASE,
            )
            if feedback_match:
                feedback = feedback_match.group(1).strip()

            # Extract missing items
            missing_items = []
            missing_match = re.search(r"MISSING_ITEMS:\s*(.+?)$", response, re.DOTALL | re.IGNORECASE)
            if missing_match:
                missing_text = missing_match.group(1).strip()
                if missing_text.lower() != "none":
                    # Split by lines and clean up
                    items = [item.strip() for item in missing_text.split("\n") if item.strip()]
                    missing_items = [item for item in items if item and item.lower() != "none"]

            return TaskValidationResult(
                is_complete=is_complete,
                confidence=confidence,
                feedback=feedback,
                missing_items=missing_items,
                validation_prompt="",  # Will be set by caller
                llm_response=response,
            )

        except Exception as e:
            # Return default result on parsing error
            return TaskValidationResult(
                is_complete=False,
                confidence=0.0,
                feedback=f"Failed to parse LLM response: {str(e)}",
                missing_items=["Response parsing failed"],
                validation_prompt="",
                llm_response=response,
            )

    def should_allow_manual_override(self, validation_result: TaskValidationResult) -> bool:
        """
        Determine if manual override should be allowed for validation result.

        Args:
            validation_result: Result from LLM validation

        Returns:
            True if manual override should be allowed
        """
        # Allow override if:
        # 1. Confidence is low (< 0.7)
        # 2. Task is marked incomplete but only minor issues
        # 3. Validation failed due to technical issues

        if validation_result.confidence < 0.7:
            return True

        if not validation_result.is_complete:
            # Check if missing items are minor
            minor_keywords = ["documentation", "comment", "test", "minor", "small"]
            if validation_result.missing_items:
                all_minor = all(any(keyword in item.lower() for keyword in minor_keywords) for item in validation_result.missing_items)
                if all_minor:
                    return True

        # Allow override if validation failed due to technical issues
        if "failed" in validation_result.feedback.lower() or "error" in validation_result.feedback.lower():
            return True

        return False

    def _get_relevant_requirements(self, task: TaskItem, spec: Spec) -> str:
        """
        Get requirements content relevant to the task.

        Args:
            task: TaskItem to get requirements for
            spec: Specification containing requirements

        Returns:
            Relevant requirements content
        """
        try:
            requirements_path = spec.base_path / "requirements.md"
            if not requirements_path.exists():
                return "No requirements document found"

            content = requirements_path.read_text(encoding="utf-8")

            # If task has specific requirement references, try to extract those sections
            if task.requirements_refs and task.requirements_refs != ["[TBD]"]:
                relevant_sections = []
                for req_ref in task.requirements_refs:
                    # Look for sections containing this requirement reference
                    pattern = rf"#{1, 4}.*{re.escape(req_ref)}.*?(?=\n#{1, 4}|$)"
                    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                    relevant_sections.extend(matches)

                if relevant_sections:
                    return "\n\n".join(relevant_sections)

            # Return full requirements if no specific references
            return content

        except Exception:
            return "Unable to read requirements document"

    def _get_relevant_design(self, task: TaskItem, spec: Spec) -> str:
        """
        Get design content relevant to the task.

        Args:
            task: TaskItem to get design for
            spec: Specification containing design

        Returns:
            Relevant design content
        """
        try:
            design_path = spec.base_path / "design.md"
            if not design_path.exists():
                return "No design document found"

            content = design_path.read_text(encoding="utf-8")

            # For now, return full design content
            # Could be enhanced to extract relevant sections based on task content
            return content

        except Exception:
            return "Unable to read design document"

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with the validation prompt.

        Args:
            prompt: Validation prompt

        Returns:
            LLM response
        """
        # Placeholder for actual LLM integration
        # In a real implementation, this would call an LLM service
        # For now, return a mock response for demonstration

        return """COMPLETION_STATUS: INCOMPLETE
CONFIDENCE: 0.8
FEEDBACK: The task appears to be partially implemented but lacks proper error handling and \
unit tests as specified in the requirements. The core functionality is present but needs \
additional validation and edge case handling.
MISSING_ITEMS:
- Error handling for edge cases
- Unit tests for the implemented functionality
- Documentation updates"""
