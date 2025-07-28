"""
Content classification functionality for determining document placement.
"""

import re
from typing import List

from .models import ContentBlock
from .task_formatting_cache import get_cache


class ContentClassifier:
    """
    Analyzes content blocks to determine appropriate document placement.
    """

    def __init__(self) -> None:
        """Initialize the ContentClassifier."""
        self.task_keywords = [
            "implement",
            "create",
            "write",
            "build",
            "develop",
            "test",
            "add",
            "modify",
            "update",
            "fix",
            "refactor",
            "deploy",
        ]

        self.requirement_keywords = [
            "shall",
            "must",
            "should",
            "user story",
            "acceptance criteria",
            "as a",
            "i want",
            "so that",
            "when",
            "then",
            "if",
        ]

        self.design_keywords = [
            "architecture",
            "component",
            "interface",
            "model",
            "pattern",
            "approach",
            "strategy",
            "design",
            "structure",
            "framework",
        ]

    def classify_content_blocks(self, content: str) -> List[ContentBlock]:
        """Classify content blocks to determine appropriate document placement."""
        # Check cache first
        cache = get_cache()
        cached_blocks = cache.get_classified_content(content)
        if cached_blocks is not None:
            return cached_blocks

        blocks = []
        lines = content.split("\n")

        current_block: List[str] = []
        current_line_start = 1

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line:
                if current_block:
                    block_content = "\n".join(current_block)
                    block = self._classify_block(block_content, current_line_start)
                    blocks.append(block)
                    current_block = []
                continue

            if self._is_header(line) or self._is_task_line(line):
                if current_block:
                    block_content = "\n".join(current_block)
                    block = self._classify_block(block_content, current_line_start)
                    blocks.append(block)
                    current_block = []

                # Process header/task as its own block
                content_type = "header" if self._is_header(line) else "task"
                block = ContentBlock(
                    content=line,
                    content_type=content_type,
                    confidence=0.9,
                    suggested_location="tasks",
                    line_number=line_num,
                )
                blocks.append(block)
                current_line_start = line_num + 1
                continue

            if not current_block:
                current_line_start = line_num
            current_block.append(line)

        if current_block:
            block_content = "\n".join(current_block)
            block = self._classify_block(block_content, current_line_start)
            blocks.append(block)

        # Cache the result
        cache.set_classified_content(content, blocks)

        return blocks

    def _classify_block(self, content: str, line_number: int) -> ContentBlock:
        """Classify a single content block."""
        content_lower = content.lower()

        task_score = self._calculate_keyword_score(content_lower, self.task_keywords)
        requirement_score = self._calculate_keyword_score(content_lower, self.requirement_keywords)
        design_score = self._calculate_keyword_score(content_lower, self.design_keywords)

        scores = {
            "task": task_score,
            "requirement": requirement_score,
            "design": design_score,
        }

        best_type = max(scores, key=lambda x: scores[x])
        confidence = scores[best_type]

        suggested_location = {
            "requirement": "requirements",
            "design": "design",
            "task": "tasks",
        }.get(best_type, "tasks")

        return ContentBlock(
            content=content,
            content_type=best_type,
            confidence=max(confidence, 0.1),
            suggested_location=suggested_location,
            line_number=line_number,
        )

    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """Calculate keyword match score for content."""
        matches = sum(1 for keyword in keywords if keyword in content)
        if not keywords:
            return 0.0
        return min(matches / len(keywords), 1.0)

    def _is_header(self, line: str) -> bool:
        """Check if line is a markdown header."""
        return line.startswith("#")

    def _is_task_line(self, line: str) -> bool:
        """Check if line represents a task."""
        return bool(re.match(r"^\s*-\s*\[[\sx-]\]\s*", line) or re.match(r"^\s*\d+(?:\.\d+)*\.\s*", line))
