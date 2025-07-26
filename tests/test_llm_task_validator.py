"""Tests for LLMTaskCompletionValidator component."""

from pathlib import Path

from src.spec_server.llm_task_validator import LLMTaskCompletionValidator
from src.spec_server.models import TaskItem, TaskValidationResult


class TestLLMTaskCompletionValidator:
    """Test cases for LLMTaskCompletionValidator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = LLMTaskCompletionValidator()

        # Mock spec object
        self.mock_spec = type("MockSpec", (), {"base_path": Path("/tmp/test_spec")})()

        # Sample task
        self.sample_task = TaskItem(
            identifier="1",
            description="Implement user authentication system",
            status="completed",
            requirements_refs=["1.1", "1.2"],
        )

    def test_validate_task_completion_basic(self):
        """Test basic task completion validation."""
        result = self.validator.validate_task_completion(
            self.sample_task,
            self.mock_spec,
            "Implemented login and logout functionality with session management.",
        )

        # Should return a TaskValidationResult
        assert isinstance(result, TaskValidationResult)
        assert hasattr(result, "is_complete")
        assert hasattr(result, "confidence")
        assert hasattr(result, "feedback")
        assert hasattr(result, "missing_items")
        assert hasattr(result, "validation_prompt")
        assert hasattr(result, "llm_response")

        # Confidence should be between 0 and 1
        assert 0.0 <= result.confidence <= 1.0

    def test_generate_validation_prompt(self):
        """Test validation prompt generation."""
        prompt = self.validator.generate_validation_prompt(
            self.sample_task,
            "The system shall provide user authentication.",
            "Use MVC pattern for authentication.",
            "Implemented login form and session handling.",
        )

        # Should include all key information
        assert "Task ID: 1" in prompt
        assert "Implement user authentication system" in prompt
        assert "Requirements References: 1.1, 1.2" in prompt
        assert "The system shall provide user authentication" in prompt
        assert "Use MVC pattern for authentication" in prompt
        assert "Implemented login form and session handling" in prompt

        # Should include validation instructions
        assert "COMPLETION_STATUS" in prompt
        assert "CONFIDENCE" in prompt
        assert "FEEDBACK" in prompt
        assert "MISSING_ITEMS" in prompt

    def test_parse_llm_validation_response_complete(self):
        """Test parsing LLM response for complete task."""
        response = """
COMPLETION_STATUS: COMPLETE
CONFIDENCE: 0.9
FEEDBACK: The task has been fully implemented with all requirements satisfied. The authentication system includes login, logout, and session management as specified.
MISSING_ITEMS: None
"""

        result = self.validator.parse_llm_validation_response(response)

        assert result.is_complete is True
        assert result.confidence == 0.9
        assert "fully implemented" in result.feedback
        assert len(result.missing_items) == 0

    def test_parse_llm_validation_response_incomplete(self):
        """Test parsing LLM response for incomplete task."""
        response = """
COMPLETION_STATUS: INCOMPLETE
CONFIDENCE: 0.7
FEEDBACK: The task is partially implemented but lacks proper error handling and unit tests as specified in the requirements.
MISSING_ITEMS:
- Error handling for invalid credentials
- Unit tests for authentication functions
- Documentation updates
"""

        result = self.validator.parse_llm_validation_response(response)

        assert result.is_complete is False
        assert result.confidence == 0.7
        assert "partially implemented" in result.feedback
        assert len(result.missing_items) == 3
        assert any("Error handling for invalid credentials" in item for item in result.missing_items)
        assert any("Unit tests for authentication functions" in item for item in result.missing_items)
        assert any("Documentation updates" in item for item in result.missing_items)

    def test_should_allow_manual_override_low_confidence(self):
        """Test manual override for low confidence results."""
        low_confidence_result = TaskValidationResult(
            is_complete=False,
            confidence=0.6,  # Below 0.7 threshold
            feedback="Low confidence assessment",
            missing_items=["Some item"],
            validation_prompt="",
            llm_response="",
        )

        assert self.validator.should_allow_manual_override(low_confidence_result) is True

    def test_should_not_allow_manual_override_major_issues(self):
        """Test no manual override for major issues."""
        major_issues_result = TaskValidationResult(
            is_complete=False,
            confidence=0.9,
            feedback="Task has significant problems",
            missing_items=["Core functionality missing", "Security vulnerabilities"],
            validation_prompt="",
            llm_response="",
        )

        assert self.validator.should_allow_manual_override(major_issues_result) is False
