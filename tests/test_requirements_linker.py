"""Tests for RequirementsLinker component."""

from src.spec_server.models import TaskItem, TaskStatus
from src.spec_server.requirements_linker import RequirementsLinker


class TestRequirementsLinker:
    """Test cases for RequirementsLinker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.linker = RequirementsLinker()

        # Sample requirements content
        self.requirements_content = """
### Requirement 1.1
The system shall provide user authentication functionality.
Users must be able to log in securely with username and password.

### Requirement 1.2
The system shall implement session management.
User sessions should timeout after 30 minutes of inactivity.

### Requirement 2.1
The system shall validate all user inputs.
Input validation must prevent SQL injection and XSS attacks.

### Requirement 2.2
The system shall provide error handling.
All errors should be logged and user-friendly messages displayed.
"""

        # Sample tasks
        self.tasks = [
            TaskItem(
                identifier="1",
                description="Implement user authentication system",
                status=TaskStatus.NOT_STARTED,
                requirements_refs=[],
            ),
            TaskItem(
                identifier="2",
                description="Add input validation logic",
                status=TaskStatus.NOT_STARTED,
                requirements_refs=[],
            ),
            TaskItem(
                identifier="3",
                description="Create session management",
                status=TaskStatus.NOT_STARTED,
                requirements_refs=[],
            ),
            TaskItem(
                identifier="4",
                description="Implement error handling",
                status=TaskStatus.NOT_STARTED,
                requirements_refs=[],
            ),
        ]

    def test_link_tasks_to_requirements(self):
        """Test basic task-to-requirements linking."""
        linked_tasks = self.linker.link_tasks_to_requirements(self.tasks, self.requirements_content)

        assert len(linked_tasks) == 4

        # Check that tasks got linked to relevant requirements
        auth_task = next(t for t in linked_tasks if "authentication" in t.description)
        assert len(auth_task.requirements_refs) > 0
        assert "1.1" in auth_task.requirements_refs or "1.2" in auth_task.requirements_refs

        validation_task = next(t for t in linked_tasks if "validation" in t.description)
        assert len(validation_task.requirements_refs) > 0
        assert "2.1" in validation_task.requirements_refs

        session_task = next(t for t in linked_tasks if "session" in t.description)
        assert len(session_task.requirements_refs) > 0
        assert "1.2" in session_task.requirements_refs

    def test_parse_requirements_standard_format(self):
        """Test parsing requirements in standard format."""
        requirements = self.linker._parse_requirements(self.requirements_content)

        assert "1.1" in requirements
        assert "1.2" in requirements
        assert "2.1" in requirements
        assert "2.2" in requirements

        # Check content is parsed correctly
        assert "authentication" in requirements["1.1"].lower()
        assert "session" in requirements["1.2"].lower()
        assert "validate" in requirements["2.1"].lower()
        assert "error" in requirements["2.2"].lower()

    def test_find_relevant_requirements(self):
        """Test finding relevant requirements for specific tasks."""
        requirements = self.linker._parse_requirements(self.requirements_content)

        # Test authentication task
        auth_task = TaskItem(
            identifier="1",
            description="Implement user authentication and login",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=[],
        )

        relevant_reqs = self.linker._find_relevant_requirements(auth_task, requirements)
        assert len(relevant_reqs) > 0
        assert "1.1" in relevant_reqs  # Should match authentication requirement

        # Test validation task
        validation_task = TaskItem(
            identifier="2",
            description="Add input validation and security",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=[],
        )

        relevant_reqs = self.linker._find_relevant_requirements(validation_task, requirements)
        assert len(relevant_reqs) > 0
        assert "2.1" in relevant_reqs  # Should match validation requirement

    def test_calculate_relevance_score(self):
        """Test relevance score calculation."""
        req_content = "The system shall provide user authentication functionality"

        # High relevance task
        high_task = "Implement user authentication system"
        high_score = self.linker._calculate_relevance_score(high_task.lower(), req_content.lower())

        # Low relevance task
        low_task = "Create database backup procedure"
        low_score = self.linker._calculate_relevance_score(low_task.lower(), req_content.lower())

        # High relevance should score higher
        assert high_score > low_score
        assert high_score > 0.2  # Should meet threshold
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= low_score <= 1.0

    def test_extract_meaningful_words(self):
        """Test meaningful word extraction."""
        text = "The system shall implement user authentication functionality"
        words = self.linker._extract_meaningful_words(text)

        # Should extract meaningful words
        assert "system" in words
        assert "implement" in words
        assert "user" in words
        assert "authentication" in words
        assert "functionality" in words

        # Should exclude stop words
        assert "the" not in words
        assert "shall" not in words  # This is in stop words

        # Should exclude short words
        short_words = [w for w in words if len(w) <= 2]
        assert len(short_words) == 0

    def test_no_requirements_document(self):
        """Test behavior when no requirements are provided."""
        linked_tasks = self.linker.link_tasks_to_requirements(self.tasks, "")

        # Should add TBD placeholders
        for task in linked_tasks:
            assert task.requirements_refs == ["[TBD]"]

    def test_preserve_existing_requirements(self):
        """Test that existing requirements references are preserved."""
        # Task with existing requirements
        task_with_reqs = TaskItem(
            identifier="1",
            description="Implement authentication",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=["1.1", "1.2"],
        )

        linked_tasks = self.linker.link_tasks_to_requirements([task_with_reqs], self.requirements_content)

        # Should preserve existing requirements
        assert linked_tasks[0].requirements_refs == ["1.1", "1.2"]

    def test_empty_task_description(self):
        """Test handling of empty task descriptions."""
        empty_task = TaskItem(
            identifier="1",
            description="",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=[],
        )

        linked_tasks = self.linker.link_tasks_to_requirements([empty_task], self.requirements_content)

        # Should handle gracefully and add TBD
        assert linked_tasks[0].requirements_refs == ["[TBD]"]

    def test_relevance_threshold(self):
        """Test that relevance threshold filtering works."""
        requirements = {"1.1": "completely unrelated content about databases"}

        auth_task = TaskItem(
            identifier="1",
            description="implement user authentication",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=[],
        )

        relevant_reqs = self.linker._find_relevant_requirements(auth_task, requirements)

        # Should fall back to TBD if no requirements meet threshold
        assert relevant_reqs == ["[TBD]"]

    def test_max_requirements_limit(self):
        """Test that maximum number of linked requirements is limited."""
        # Create many requirements that could match
        many_reqs = {}
        for i in range(10):
            many_reqs[f"{i}.1"] = "implement user authentication system"

        auth_task = TaskItem(
            identifier="1",
            description="implement user authentication",
            status=TaskStatus.NOT_STARTED,
            requirements_refs=[],
        )

        relevant_reqs = self.linker._find_relevant_requirements(auth_task, many_reqs)

        # Should limit to top 3 requirements
        assert len(relevant_reqs) <= 3
