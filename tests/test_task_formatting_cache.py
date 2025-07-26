"""Tests for task formatting cache system."""

import time

from src.spec_server.models import TaskItem
from src.spec_server.task_formatting_cache import BatchProcessor, CacheEntry, InMemoryCacheBackend, TaskFormattingCache, clear_cache, get_cache, get_cache_stats, hash_content, hash_tasks


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=300,
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.access_count == 0
        assert entry.ttl == 300

    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        # Non-expiring entry
        entry = CacheEntry(key="test", value="value", created_at=time.time(), last_accessed=time.time())
        assert not entry.is_expired()

        # Expired entry
        entry_expired = CacheEntry(
            key="test",
            value="value",
            created_at=time.time() - 400,
            last_accessed=time.time() - 400,
            ttl=300,
        )
        assert entry_expired.is_expired()

    def test_cache_entry_touch(self):
        """Test cache entry touch functionality."""
        entry = CacheEntry(key="test", value="value", created_at=time.time(), last_accessed=time.time())

        original_access_time = entry.last_accessed
        original_count = entry.access_count

        time.sleep(0.01)  # Small delay
        entry.touch()

        assert entry.last_accessed > original_access_time
        assert entry.access_count == original_count + 1


class TestInMemoryCacheBackend:
    """Test InMemoryCacheBackend class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = InMemoryCacheBackend(max_size=3)

    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        self.cache.set("key1", "value1", ttl=300)

        entry = self.cache.get("key1")
        assert entry is not None
        assert entry.value == "value1"
        assert entry.access_count == 1

    def test_get_nonexistent(self):
        """Test getting non-existent key."""
        entry = self.cache.get("nonexistent")
        assert entry is None

    def test_get_expired(self):
        """Test getting expired entry."""
        self.cache.set("key1", "value1", ttl=0.01)
        time.sleep(0.02)

        entry = self.cache.get("key1")
        assert entry is None
        assert "key1" not in self.cache.cache

    def test_delete(self):
        """Test deleting cache entries."""
        self.cache.set("key1", "value1")
        assert self.cache.delete("key1") is True
        assert self.cache.get("key1") is None
        assert self.cache.delete("nonexistent") is False

    def test_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        self.cache.clear()
        assert self.cache.size() == 0
        assert self.cache.get("key1") is None

    def test_size_and_keys(self):
        """Test size and keys methods."""
        assert self.cache.size() == 0
        assert self.cache.keys() == []

        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        assert self.cache.size() == 2
        assert set(self.cache.keys()) == {"key1", "key2"}

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        # Access key1 to make it more recently used
        self.cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        self.cache.set("key4", "value4")

        assert self.cache.get("key1") is not None  # Still there
        assert self.cache.get("key2") is None  # Evicted
        assert self.cache.get("key3") is not None  # Still there
        assert self.cache.get("key4") is not None  # New entry


class TestTaskFormattingCache:
    """Test TaskFormattingCache class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = TaskFormattingCache()
        self.cache.backend.clear()  # Start with clean cache
        self.cache.reset_stats()

    def test_parsed_tasks_cache(self):
        """Test caching of parsed tasks."""
        content = "- [ ] 1. Test task"
        tasks = [TaskItem(identifier="1", description="Test task", status="not_started")]

        # Should miss first time
        assert self.cache.get_parsed_tasks(content) is None

        # Set cache
        self.cache.set_parsed_tasks(content, tasks)

        # Should hit second time
        cached_tasks = self.cache.get_parsed_tasks(content)
        assert cached_tasks is not None
        assert len(cached_tasks) == 1
        assert cached_tasks[0].description == "Test task"

    def test_classified_content_cache(self):
        """Test caching of classified content."""
        content = "This is test content"
        blocks = [{"type": "test", "content": content}]

        # Should miss first time
        assert self.cache.get_classified_content(content) is None

        # Set cache
        self.cache.set_classified_content(content, blocks)

        # Should hit second time
        cached_blocks = self.cache.get_classified_content(content)
        assert cached_blocks is not None
        assert len(cached_blocks) == 1

    def test_requirements_linking_cache(self):
        """Test caching of requirements linking."""
        tasks_hash = "task_hash_123"
        requirements_hash = "req_hash_456"
        linked_tasks = [TaskItem(identifier="1", description="Test", status="not_started")]

        # Should miss first time
        assert self.cache.get_requirements_linking(tasks_hash, requirements_hash) is None

        # Set cache
        self.cache.set_requirements_linking(tasks_hash, requirements_hash, linked_tasks)

        # Should hit second time
        cached_tasks = self.cache.get_requirements_linking(tasks_hash, requirements_hash)
        assert cached_tasks is not None
        assert len(cached_tasks) == 1

    def test_parsed_requirements_cache(self):
        """Test caching of parsed requirements."""
        requirements_content = "### Requirement 1.1\nTest requirement"
        parsed_reqs = {"1.1": "Test requirement"}

        # Should miss first time
        assert self.cache.get_parsed_requirements(requirements_content) is None

        # Set cache
        self.cache.set_parsed_requirements(requirements_content, parsed_reqs)

        # Should hit second time
        cached_reqs = self.cache.get_parsed_requirements(requirements_content)
        assert cached_reqs is not None
        assert cached_reqs["1.1"] == "Test requirement"

    def test_llm_validation_cache(self):
        """Test caching of LLM validation results."""
        task_id = "1"
        context_hash = "context_123"
        validation_result = {"is_complete": True, "confidence": 0.9}

        # Should miss first time
        assert self.cache.get_llm_validation(task_id, context_hash) is None

        # Set cache
        self.cache.set_llm_validation(task_id, context_hash, validation_result)

        # Should hit second time
        cached_result = self.cache.get_llm_validation(task_id, context_hash)
        assert cached_result is not None
        assert cached_result["is_complete"] is True
        assert cached_result["confidence"] == 0.9

    def test_cache_stats(self):
        """Test cache statistics."""
        content = "test content"

        # Initial stats
        stats = self.cache.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Miss
        self.cache.get_parsed_tasks(content)
        stats = self.cache.get_cache_stats()
        assert stats["misses"] == 1

        # Set and hit
        self.cache.set_parsed_tasks(content, [])
        self.cache.get_parsed_tasks(content)

        stats = self.cache.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit out of 2 total requests

    def test_invalidate_spec_cache(self):
        """Test invalidating cache for specific spec."""
        self.cache.set_parsed_tasks("spec1_content", [])
        self.cache.set_parsed_tasks("spec2_content", [])

        # Mock the backend keys method to return keys with spec names
        original_keys = self.cache.backend.keys
        self.cache.backend.keys = lambda: ["spec1_task", "spec1_req", "spec2_task"]

        self.cache.invalidate_spec_cache("spec1")

        # Restore original method
        self.cache.backend.keys = original_keys

        # Should have deleted spec1 entries
        assert self.cache.stats["deletes"] >= 2

    def test_clear_expired_entries(self):
        """Test clearing expired entries."""
        # Add entry with short TTL
        self.cache.backend.set("short_ttl", "value", ttl=0.01)
        self.cache.backend.set("long_ttl", "value", ttl=300)

        time.sleep(0.02)  # Wait for expiration

        cleared_count = self.cache.clear_expired_entries()
        assert cleared_count >= 1

    def test_reset_stats(self):
        """Test resetting cache statistics."""
        self.cache.get_parsed_tasks("test")  # Generate some stats

        stats_before = self.cache.get_cache_stats()
        assert stats_before["misses"] > 0

        self.cache.reset_stats()

        stats_after = self.cache.get_cache_stats()
        assert stats_after["misses"] == 0
        assert stats_after["hits"] == 0


class TestBatchProcessor:
    """Test BatchProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = BatchProcessor(max_batch_size=2)

    def test_process_tasks_batch(self):
        """Test batch processing of tasks."""
        tasks_list = [
            [TaskItem(identifier="1", description="Task 1", status="not_started")],
            [TaskItem(identifier="2", description="Task 2", status="not_started")],
            [TaskItem(identifier="3", description="Task 3", status="not_started")],
        ]

        def mock_processor(tasks):
            return f"processed_{len(tasks)}_tasks"

        results = self.processor.process_tasks_batch(tasks_list, mock_processor)

        assert len(results) == 3
        assert all("processed_1_tasks" == result for result in results)

    def test_process_content_batch(self):
        """Test batch processing of content."""
        content_list = ["content1", "content2", "content3"]

        def mock_processor(content):
            return f"processed_{content}"

        results = self.processor.process_content_batch(content_list, mock_processor)

        assert len(results) == 3
        assert results[0] == "processed_content1"
        assert results[1] == "processed_content2"
        assert results[2] == "processed_content3"

    def test_batch_error_handling(self):
        """Test error handling in batch processing."""
        content_list = ["good", "bad", "good"]

        def mock_processor(content):
            if content == "bad":
                raise Exception("Processing error")
            return f"processed_{content}"

        results = self.processor.process_content_batch(content_list, mock_processor)

        assert len(results) == 3
        assert results[0] == "processed_good"
        assert results[1] is None  # Error case
        assert results[2] == "processed_good"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_hash_content(self):
        """Test content hashing."""
        content1 = "test content"
        content2 = "test content"
        content3 = "different content"

        hash1 = hash_content(content1)
        hash2 = hash_content(content2)
        hash3 = hash_content(content3)

        assert hash1 == hash2  # Same content, same hash
        assert hash1 != hash3  # Different content, different hash
        assert len(hash1) == 32  # MD5 hash length

    def test_hash_tasks(self):
        """Test tasks hashing."""
        tasks1 = [TaskItem(identifier="1", description="Task 1", status="not_started")]
        tasks2 = [TaskItem(identifier="1", description="Task 1", status="not_started")]
        tasks3 = [TaskItem(identifier="2", description="Task 2", status="not_started")]

        hash1 = hash_tasks(tasks1)
        hash2 = hash_tasks(tasks2)
        hash3 = hash_tasks(tasks3)

        assert hash1 == hash2  # Same tasks, same hash
        assert hash1 != hash3  # Different tasks, different hash

    def test_global_cache_functions(self):
        """Test global cache functions."""
        # Clear cache
        clear_cache()

        # Get cache instance
        cache = get_cache()
        assert isinstance(cache, TaskFormattingCache)

        # Get stats
        stats = get_cache_stats()
        assert isinstance(stats, dict)
        assert "hits" in stats
        assert "misses" in stats
