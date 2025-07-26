"""Tests for ContentClassifier component."""

from src.spec_server.content_classifier import ContentClassifier


class TestContentClassifier:
    """Test cases for ContentClassifier functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()

    def test_classify_task_content(self):
        """Test classification of task-related content."""
        content = """
- [ ] 1. Implement the authentication system
- [ ] 2. Create login forms and add validation logic
- [ ] 3. Add proper error handling
"""
        blocks = self.classifier.classify_content_blocks(content)

        # Should identify this as task-related content
        task_blocks = [b for b in blocks if b.content_type == "task"]
        assert len(task_blocks) > 0

        # Should suggest tasks location
        for block in task_blocks:
            assert block.suggested_location == "tasks"
            assert block.confidence > 0.0

    def test_classify_requirement_content(self):
        """Test classification of requirements content."""
        content = """
The system shall provide user authentication.
As a user, I want to log in securely.
When the user enters credentials, then the system should validate them.
"""
        blocks = self.classifier.classify_content_blocks(content)

        # Should identify this as requirements content
        req_blocks = [b for b in blocks if b.content_type == "requirement"]
        assert len(req_blocks) > 0

        # Should suggest requirements location
        for block in req_blocks:
            assert block.suggested_location == "requirements"
            assert block.confidence > 0.0

    def test_classify_design_content(self):
        """Test classification of design-related content."""
        content = """
The architecture follows a component-based approach.
We'll use the MVC pattern for the interface design.
The framework provides a structured approach to development.
"""
        blocks = self.classifier.classify_content_blocks(content)

        # Should identify this as design content
        design_blocks = [b for b in blocks if b.content_type == "design"]
        assert len(design_blocks) > 0

        # Should suggest design location
        for block in design_blocks:
            assert block.suggested_location == "design"
            assert block.confidence > 0.0

    def test_classify_mixed_content(self):
        """Test classification of mixed content types."""
        content = """
# Implementation Plan

The system shall provide authentication.

We need to implement the login functionality.
This follows a component-based architecture approach.

- [ ] 1. Create login form
- [ ] 2. Add validation

As a user, I want secure access.
"""
        blocks = self.classifier.classify_content_blocks(content)

        # Should classify different types of content
        content_types = [block.content_type for block in blocks]
        assert "header" in content_types
        assert "task" in content_types

        # Should have different suggested locations
        locations = [block.suggested_location for block in blocks]
        assert "tasks" in locations

    def test_classify_headers(self):
        """Test classification of markdown headers."""
        content = """
# Main Header
## Sub Header
### Another Header
"""
        blocks = self.classifier.classify_content_blocks(content)

        # All should be classified as headers
        header_blocks = [b for b in blocks if b.content_type == "header"]
        assert len(header_blocks) == 3

        # Headers should stay in tasks by default
        for block in header_blocks:
            assert block.suggested_location == "tasks"
            assert block.confidence == 0.9  # High confidence for headers

    def test_classify_task_lines(self):
        """Test classification of task lines."""
        content = """
- [ ] 1. Implement feature
- [x] 2. Complete task
1. Numbered task
2.1. Subtask
"""
        blocks = self.classifier.classify_content_blocks(content)

        # All should be classified as tasks
        task_blocks = [b for b in blocks if b.content_type == "task"]
        assert len(task_blocks) == 4

        # All should stay in tasks
        for block in task_blocks:
            assert block.suggested_location == "tasks"
            assert block.confidence == 0.9  # High confidence for task lines

    def test_keyword_scoring(self):
        """Test keyword-based scoring system."""
        # Content with many task keywords
        task_content = "implement create build develop test add modify update"
        task_score = self.classifier._calculate_keyword_score(task_content, self.classifier.task_keywords)

        # Content with many requirement keywords
        req_content = "shall must should user story as a i want so that"
        req_score = self.classifier._calculate_keyword_score(req_content, self.classifier.requirement_keywords)

        # Content with many design keywords
        design_content = "architecture component interface model pattern design"
        design_score = self.classifier._calculate_keyword_score(design_content, self.classifier.design_keywords)

        # Each should score higher for their respective keywords
        assert task_score > 0.5
        assert req_score > 0.5
        assert design_score > 0.5

    def test_empty_content(self):
        """Test classification of empty content."""
        blocks = self.classifier.classify_content_blocks("")
        assert len(blocks) == 0

        blocks = self.classifier.classify_content_blocks("\n\n\n")
        assert len(blocks) == 0

    def test_confidence_levels(self):
        """Test that confidence levels are reasonable."""
        content = """
# Header
- [ ] Task
Some regular content here.
"""
        blocks = self.classifier.classify_content_blocks(content)

        # All blocks should have confidence > 0
        for block in blocks:
            assert block.confidence > 0.0
            assert block.confidence <= 1.0

        # Headers and explicit task lines should have high confidence
        header_blocks = [b for b in blocks if b.content_type == "header"]
        explicit_task_blocks = [b for b in blocks if b.content_type == "task" and ("- [" in b.content or b.content.strip().startswith(("1.", "2.", "3.")))]

        for block in header_blocks + explicit_task_blocks:
            assert block.confidence >= 0.9

    def test_suggested_location_logic(self):
        """Test the logic for suggesting document locations."""
        # High-confidence requirement content
        req_content = "The system shall provide authentication as a user story."
        blocks = self.classifier.classify_content_blocks(req_content)
        req_block = blocks[0] if blocks else None

        if req_block and req_block.confidence > 0.5:
            assert req_block.suggested_location == "requirements"

        # High-confidence design content
        design_content = "The architecture uses a component-based design pattern."
        blocks = self.classifier.classify_content_blocks(design_content)
        design_block = blocks[0] if blocks else None

        if design_block and design_block.confidence > 0.5:
            assert design_block.suggested_location == "design"

        # Low-confidence content should default to tasks
        neutral_content = "This is just some neutral text."
        blocks = self.classifier.classify_content_blocks(neutral_content)
        neutral_block = blocks[0] if blocks else None

        if neutral_block:
            assert neutral_block.suggested_location == "tasks"
