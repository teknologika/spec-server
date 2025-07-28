"""
Requirements linking functionality for automatically linking tasks to requirements.
"""

import re
from typing import Dict, List

from .models import TaskItem
from .task_formatting_cache import get_cache, hash_content, hash_tasks


class RequirementsLinker:
    """
    Automatically links tasks to relevant requirements based on content analysis.

    Uses keyword matching and semantic similarity to identify which requirements
    are relevant to each task and generates appropriate requirement references.
    """

    def __init__(self) -> None:
        """Initialize the RequirementsLinker."""
        # Pattern to match requirement numbers like "1.1", "2.3", etc.
        self.requirement_pattern = re.compile(r"(\d+\.\d+)\s*[:-]?\s*(.+?)(?=\n\d+\.\d+|\n#|$)", re.DOTALL)

        # Keywords that indicate strong relationships
        self.strong_keywords = [
            "implement",
            "create",
            "build",
            "develop",
            "add",
            "modify",
            "update",
            "fix",
            "test",
            "validate",
            "ensure",
            "support",
        ]

    def link_tasks_to_requirements(self, tasks: List[TaskItem], requirements_content: str) -> List[TaskItem]:
        """
        Automatically link tasks to relevant requirements.

        Args:
            tasks: List of TaskItem objects to link
            requirements_content: Content of requirements document

        Returns:
            List of TaskItem objects with requirements references added
        """
        # Check cache first
        cache = get_cache()
        tasks_hash = hash_tasks(tasks)
        requirements_hash = hash_content(requirements_content)

        cached_result = cache.get_requirements_linking(tasks_hash, requirements_hash)
        if cached_result is not None:
            return cached_result

        # Parse requirements from content
        requirements = self._parse_requirements(requirements_content)

        # Link each task to relevant requirements
        for task in tasks:
            if not task.requirements_refs:  # Only add if no existing references
                linked_reqs = self._find_relevant_requirements(task, requirements)
                task.requirements_refs = linked_reqs

        # Cache the result
        cache.set_requirements_linking(tasks_hash, requirements_hash, tasks)

        return tasks

    def _parse_requirements(self, content: str) -> Dict[str, str]:
        """
        Parse requirements from content into a dictionary.

        Args:
            content: Requirements document content

        Returns:
            Dictionary mapping requirement IDs to their content
        """
        # Check cache first
        cache = get_cache()
        cached_requirements = cache.get_parsed_requirements(content)
        if cached_requirements is not None:
            return cached_requirements

        requirements = {}

        # Find all requirement patterns
        matches = self.requirement_pattern.findall(content)

        for req_id, req_content in matches:
            # Clean up the content
            cleaned_content = req_content.strip()
            requirements[req_id] = cleaned_content

        # Also try to find requirements in different formats
        lines = content.split("\n")
        current_req_id = None
        current_content: List[str] = []

        for line in lines:
            line = line.strip()

            # Check for requirement headers like "### Requirement 1.1"
            req_header_match = re.match(r"#{1,4}\s*Requirement\s+(\d+\.\d+)", line, re.IGNORECASE)
            if req_header_match:
                # Save previous requirement if any
                if current_req_id and current_content:
                    requirements[current_req_id] = "\n".join(current_content).strip()

                current_req_id = req_header_match.group(1)
                current_content = []
                continue

            # Accumulate content for current requirement
            if current_req_id and line:
                current_content.append(line)

        # Save final requirement
        if current_req_id and current_content:
            requirements[current_req_id] = "\n".join(current_content).strip()

        # Cache the result
        cache.set_parsed_requirements(content, requirements)

        return requirements

    def _find_relevant_requirements(self, task: TaskItem, requirements: Dict[str, str]) -> List[str]:
        """
        Find requirements relevant to a specific task.

        Args:
            task: TaskItem to find requirements for
            requirements: Dictionary of requirement ID to content

        Returns:
            List of requirement IDs relevant to the task
        """
        if not requirements:
            return ["[TBD]"]

        task_text = task.description.lower()
        relevant_reqs = []

        # Score each requirement based on keyword overlap
        req_scores = []

        for req_id, req_content in requirements.items():
            score = self._calculate_relevance_score(task_text, req_content.lower())
            if score > 0.1:  # Minimum threshold
                req_scores.append((req_id, score))

        # Sort by score and take top matches
        req_scores.sort(key=lambda x: x[1], reverse=True)

        # Take top 3 most relevant requirements
        for req_id, score in req_scores[:3]:
            if score > 0.2:  # Higher threshold for inclusion
                relevant_reqs.append(req_id)

        # If no requirements found, add placeholder
        if not relevant_reqs:
            relevant_reqs = ["[TBD]"]

        return relevant_reqs

    def _calculate_relevance_score(self, task_text: str, req_content: str) -> float:
        """
        Calculate relevance score between task and requirement.

        Args:
            task_text: Task description (lowercase)
            req_content: Requirement content (lowercase)

        Returns:
            Relevance score from 0.0 to 1.0
        """
        score = 0.0

        # Extract meaningful words from task (excluding common words)
        task_words = self._extract_meaningful_words(task_text)
        req_words = self._extract_meaningful_words(req_content)

        if not task_words or not req_words:
            return 0.0

        # Calculate word overlap
        common_words = set(task_words) & set(req_words)
        if common_words:
            overlap_ratio = len(common_words) / len(set(task_words) | set(req_words))
            score += overlap_ratio * 0.6

        # Boost score for strong keyword matches
        for keyword in self.strong_keywords:
            if keyword in task_text and keyword in req_content:
                score += 0.2

        # Boost score for exact phrase matches
        task_phrases = self._extract_phrases(task_text)
        for phrase in task_phrases:
            if len(phrase) > 3 and phrase in req_content:
                score += 0.3

        return min(score, 1.0)

    def _extract_meaningful_words(self, text: str) -> List[str]:
        """
        Extract meaningful words from text, excluding common stop words.

        Args:
            text: Input text

        Returns:
            List of meaningful words
        """
        # Simple stop words list
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
            "shall",
            "this",
            "that",
            "these",
            "those",
        }

        # Extract words (alphanumeric only)
        words = re.findall(r"\b[a-zA-Z]\w*\b", text.lower())

        # Filter out stop words and short words
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]

        return meaningful_words

    def _extract_phrases(self, text: str) -> List[str]:
        """
        Extract meaningful phrases from text.

        Args:
            text: Input text

        Returns:
            List of phrases
        """
        # Simple phrase extraction - sequences of 2-4 words
        words = text.split()
        phrases = []

        for i in range(len(words) - 1):
            # 2-word phrases
            if i < len(words) - 1:
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) > 5:  # Minimum phrase length
                    phrases.append(phrase)

            # 3-word phrases
            if i < len(words) - 2:
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                if len(phrase) > 8:
                    phrases.append(phrase)

        return phrases
