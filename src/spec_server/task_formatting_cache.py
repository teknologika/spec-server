"""Caching system for task formatting operations."""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional

from .task_formatting_config import get_config


@dataclass
class CacheEntry:
    """Represents a cached entry with metadata."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a cache entry."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def size(self) -> int:
        """Get the number of cache entries."""
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """Get all cache keys."""
        pass


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction."""

    def __init__(self, max_size: int = 1000):
        """Initialize in-memory cache."""
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry by key."""
        with self.lock:
            entry = self.cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self.cache[key]
                return None

            entry.touch()
            return entry

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a cache entry."""
        with self.lock:
            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            current_time = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                last_accessed=current_time,
                ttl=ttl,
            )

            self.cache[key] = entry

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """Get the number of cache entries."""
        with self.lock:
            return len(self.cache)

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self.lock:
            return list(self.cache.keys())

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find LRU entry
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)

        del self.cache[lru_key]
        self.logger.debug(f"Evicted LRU cache entry: {lru_key}")


class TaskFormattingCache:
    """High-level cache for task formatting operations."""

    def __init__(self, backend: Optional[CacheBackend] = None):
        """Initialize task formatting cache."""
        self.backend = backend or InMemoryCacheBackend()
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "evictions": 0}

    def _generate_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from arguments."""
        # Create a string representation of all arguments
        key_parts = [prefix]

        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # For complex objects, use their string representation
                key_parts.append(str(hash(str(arg))))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        key_string = "|".join(key_parts)

        # Hash the key to ensure consistent length
        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()

    def get_parsed_tasks(self, content: str) -> Optional[List[Any]]:
        """Get cached parsed tasks."""
        if not self.config.enable_caching:
            return None

        key = self._generate_key("parsed_tasks", content)
        entry = self.backend.get(key)

        if entry is not None:
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for parsed tasks: {key}")
            return entry.value  # type: ignore

        self.stats["misses"] += 1
        return None

    def set_parsed_tasks(self, content: str, tasks: List) -> None:
        """Cache parsed tasks."""
        if not self.config.enable_caching:
            return

        key = self._generate_key("parsed_tasks", content)
        ttl = self.config.cache_ttl_seconds

        self.backend.set(key, tasks, ttl)
        self.stats["sets"] += 1
        self.logger.debug(f"Cached parsed tasks: {key}")

    def get_classified_content(self, content: str) -> Optional[List[Any]]:
        """Get cached content classification."""
        if not self.config.enable_caching:
            return None

        key = self._generate_key("classified_content", content)
        entry = self.backend.get(key)

        if entry is not None:
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for classified content: {key}")
            return entry.value  # type: ignore

        self.stats["misses"] += 1
        return None

    def set_classified_content(self, content: str, blocks: List) -> None:
        """Cache content classification."""
        if not self.config.enable_caching:
            return

        key = self._generate_key("classified_content", content)
        ttl = self.config.cache_ttl_seconds

        self.backend.set(key, blocks, ttl)
        self.stats["sets"] += 1
        self.logger.debug(f"Cached classified content: {key}")

    def get_requirements_linking(self, tasks_hash: str, requirements_hash: str) -> Optional[List[Any]]:
        """Get cached requirements linking."""
        if not self.config.enable_caching:
            return None

        key = self._generate_key("requirements_linking", tasks_hash, requirements_hash)
        entry = self.backend.get(key)

        if entry is not None:
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for requirements linking: {key}")
            return entry.value  # type: ignore

        self.stats["misses"] += 1
        return None

    def set_requirements_linking(self, tasks_hash: str, requirements_hash: str, linked_tasks: List) -> None:
        """Cache requirements linking."""
        if not self.config.enable_caching:
            return

        key = self._generate_key("requirements_linking", tasks_hash, requirements_hash)
        ttl = self.config.cache_ttl_seconds

        self.backend.set(key, linked_tasks, ttl)
        self.stats["sets"] += 1
        self.logger.debug(f"Cached requirements linking: {key}")

    def get_parsed_requirements(self, requirements_content: str) -> Optional[Dict[Any, Any]]:
        """Get cached parsed requirements."""
        if not self.config.enable_caching:
            return None

        key = self._generate_key("parsed_requirements", requirements_content)
        entry = self.backend.get(key)

        if entry is not None:
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for parsed requirements: {key}")
            return entry.value  # type: ignore

        self.stats["misses"] += 1
        return None

    def set_parsed_requirements(self, requirements_content: str, parsed_requirements: Dict) -> None:
        """Cache parsed requirements."""
        if not self.config.enable_caching:
            return

        key = self._generate_key("parsed_requirements", requirements_content)
        ttl = self.config.cache_ttl_seconds * 2  # Requirements change less frequently

        self.backend.set(key, parsed_requirements, ttl)
        self.stats["sets"] += 1
        self.logger.debug(f"Cached parsed requirements: {key}")

    def get_llm_validation(self, task_id: str, context_hash: str) -> Optional[Dict[Any, Any]]:
        """Get cached LLM validation result."""
        if not self.config.enable_caching:
            return None

        key = self._generate_key("llm_validation", task_id, context_hash)
        entry = self.backend.get(key)

        if entry is not None:
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for LLM validation: {key}")
            return entry.value  # type: ignore

        self.stats["misses"] += 1
        return None

    def set_llm_validation(self, task_id: str, context_hash: str, validation_result: Dict) -> None:
        """Cache LLM validation result."""
        if not self.config.enable_caching:
            return

        key = self._generate_key("llm_validation", task_id, context_hash)
        ttl = self.config.cache_ttl_seconds // 2  # LLM results are more volatile

        self.backend.set(key, validation_result, ttl)
        self.stats["sets"] += 1
        self.logger.debug(f"Cached LLM validation: {key}")

    def invalidate_spec_cache(self, spec_name: str) -> None:
        """Invalidate all cache entries for a specific spec."""
        keys_to_delete = []

        for key in self.backend.keys():
            if spec_name in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            self.backend.delete(key)
            self.stats["deletes"] += 1

        self.logger.info(f"Invalidated {len(keys_to_delete)} cache entries for spec: {spec_name}")

    def clear_expired_entries(self) -> int:
        """Clear expired cache entries."""
        expired_keys = []

        for key in self.backend.keys():
            entry = self.backend.get(key)
            if entry and entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self.backend.delete(key)

        self.logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "evictions": self.stats["evictions"],
            "cache_size": self.backend.size(),
            "total_requests": total_requests,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "evictions": 0}

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self.backend.clear()
        self.logger.info("Cleared all cache entries")


class BatchProcessor:
    """Batch processor for task formatting operations."""

    def __init__(self, max_batch_size: Optional[int] = None):
        """Initialize batch processor."""
        self.config = get_config()
        self.max_batch_size = max_batch_size or self.config.max_batch_size
        self.logger = logging.getLogger(__name__)

    def process_tasks_batch(self, tasks_list: List[List], processor_func: Any, **kwargs: Any) -> List:
        """Process multiple task lists in batches."""
        if not self.config.batch_processing_enabled:
            # Process individually
            return [processor_func(tasks, **kwargs) for tasks in tasks_list]

        results = []

        for i in range(0, len(tasks_list), self.max_batch_size):
            batch = tasks_list[i : i + self.max_batch_size]

            self.logger.debug(f"Processing batch {i//self.max_batch_size + 1} with {len(batch)} items")

            batch_results = []
            for tasks in batch:
                try:
                    result = processor_func(tasks, **kwargs)
                    batch_results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing batch item: {e}")
                    batch_results.append(None)

            results.extend(batch_results)

        return results

    def process_content_batch(self, content_list: List[str], processor_func: Any, **kwargs: Any) -> List:
        """Process multiple content strings in batches."""
        if not self.config.batch_processing_enabled:
            return [processor_func(content, **kwargs) for content in content_list]

        results = []

        for i in range(0, len(content_list), self.max_batch_size):
            batch = content_list[i : i + self.max_batch_size]

            self.logger.debug(f"Processing content batch {i//self.max_batch_size + 1} with {len(batch)} items")

            batch_results = []
            for content in batch:
                try:
                    result = processor_func(content, **kwargs)
                    batch_results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing batch content: {e}")
                    batch_results.append(None)

            results.extend(batch_results)

        return results


# Global cache instance
_cache: Optional[TaskFormattingCache] = None


def get_cache() -> TaskFormattingCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = TaskFormattingCache()
    return _cache


def clear_cache() -> None:
    """Clear the global cache."""
    get_cache().clear_cache()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    return get_cache().get_cache_stats()


# Utility functions for hashing
def hash_content(content: str) -> str:
    """Generate a hash for content."""
    return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()


def hash_tasks(tasks: List) -> str:
    """Generate a hash for a list of tasks."""
    tasks_str = str([str(task) for task in tasks])
    return hashlib.md5(tasks_str.encode(), usedforsecurity=False).hexdigest()
