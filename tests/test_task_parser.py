"""Tests for TaskParser component."""

from src.spec_server.task_parser import TaskParser


class TestTaskParser:
    """Test cases for TaskParser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TaskParser()

    def test_parse_checkbox_tasks(self):
        """Test parsing checkbox format tasks."""
        content = """
- [ ] 1. Implement authentication
- [x] 2. Create database models
- [-] 3. Add validation logic
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 3
        assert tasks[0].identifier == "1"
        assert tasks[0].description == "Implement authentication"
        assert tasks[0].status == "not_started"

        assert tasks[1].identifier == "2"
        assert tasks[1].description == "Create database models"
        assert tasks[1].status == "completed"

        assert tasks[2].identifier == "3"
        assert tasks[2].description == "Add validation logic"
        assert tasks[2].status == "in_progress"

    def test_parse_numbered_tasks(self):
        """Test parsing numbered format tasks."""
        content = """
1. Implement user authentication
2.1. Create login form
2.2. Add logout functionality
3. Database setup
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 4
        assert tasks[0].identifier == "1"
        assert tasks[0].description == "Implement user authentication"
        assert tasks[0].status == "not_started"

        assert tasks[1].identifier == "2.1"
        assert tasks[1].description == "Create login form"

        assert tasks[2].identifier == "2.2"
        assert tasks[2].description == "Add logout functionality"

        assert tasks[3].identifier == "3"
        assert tasks[3].description == "Database setup"

    def test_parse_mixed_formats(self):
        """Test parsing mixed task formats."""
        content = """
- [ ] 1. Implement authentication
2. Create database models
- [x] 3. Add validation
4.1. Write unit tests
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 4
        assert tasks[0].identifier == "1"
        assert tasks[0].status == "not_started"

        assert tasks[1].identifier == "2"
        assert tasks[1].status == "not_started"

        assert tasks[2].identifier == "3"
        assert tasks[2].status == "completed"

        assert tasks[3].identifier == "4.1"
        assert tasks[3].status == "not_started"

    def test_parse_tasks_with_requirements(self):
        """Test parsing tasks with requirements references."""
        content = """
- [ ] 1. Implement authentication - Requirements: 1.1, 1.2
- [x] 2. Create database models Requirements: 2.1
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 2
        assert tasks[0].requirements_refs == ["1.1", "1.2"]
        assert tasks[1].requirements_refs == ["2.1"]

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        tasks = self.parser.parse_tasks("")
        assert len(tasks) == 0

        tasks = self.parser.parse_tasks("\n\n\n")
        assert len(tasks) == 0

    def test_parse_content_without_tasks(self):
        """Test parsing content that doesn't contain tasks."""
        content = """
# Some Header

This is just regular text content.
No tasks here.

Another paragraph.
"""
        tasks = self.parser.parse_tasks(content)
        assert len(tasks) == 0

    def test_clean_description(self):
        """Test description cleaning functionality."""
        content = """
- [ ] 1. Implement authentication - Requirements: 1.1
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 1
        # Description should be cleaned of identifier and requirements
        assert tasks[0].description == "Implement authentication"
        assert "Requirements:" not in tasks[0].description
        assert "1." not in tasks[0].description

    def test_status_parsing(self):
        """Test status character parsing."""
        content = """
- [ ] 1. Not started
- [x] 2. Completed
- [X] 3. Also completed
- [-] 4. In progress
- [~] 5. Unknown status (should default to not started)
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 5
        assert tasks[0].status == "not_started"
        assert tasks[1].status == "completed"
        assert tasks[2].status == "completed"  # X should work too
        assert tasks[3].status == "in_progress"
        assert tasks[4].status == "not_started"  # Unknown defaults to not started

    def test_extract_identifier_edge_cases(self):
        """Test identifier extraction edge cases."""
        content = """
- [ ] 1.1.1. Deep nesting
- [ ] 10. Double digit
- [ ] 1.10. Mixed digits
- [ ] Task without number
"""
        tasks = self.parser.parse_tasks(content)

        # Should handle various identifier formats
        identifiers = [task.identifier for task in tasks if task.identifier]
        assert "1.1.1" in identifiers
        assert "10" in identifiers
        assert "1.10" in identifiers

    def test_requirements_extraction_formats(self):
        """Test various requirements reference formats."""
        content = """
- [ ] 1. Task with Requirements: 1.1, 1.2
- [ ] 2. Task with requirements: 2.1
- [ ] 3. Task with REQUIREMENTS: 3.1, 3.2, 3.3
- [ ] 4. Task without requirements
"""
        tasks = self.parser.parse_tasks(content)

        assert len(tasks) == 4
        assert tasks[0].requirements_refs == ["1.1", "1.2"]
        assert tasks[1].requirements_refs == ["2.1"]
        assert tasks[2].requirements_refs == ["3.1", "3.2", "3.3"]
        assert tasks[3].requirements_refs == []
