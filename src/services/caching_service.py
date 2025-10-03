"""Caching service for performance optimization."""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from cachetools import LRUCache, TTLCache
from diskcache import Cache
from loguru import logger

from src.core.base_service import BaseService, timer


class CachingService(BaseService):
    """Service for caching data and results.

    Provides multi-layer caching with memory and disk storage
    for improved performance.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the caching service.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)

        # Configuration
        self.enabled = self.get_config("cache_enabled", True)
        self.ttl = self.get_config("cache_ttl", 3600)  # 1 hour default
        self.max_memory_size = self.get_config("max_memory_cache_size", 1000)
        self.cache_dir = Path(self.get_config("cache_directory", ".cache"))

        # Memory caches
        self.memory_cache = TTLCache(maxsize=self.max_memory_size, ttl=self.ttl)
        self.permanent_cache = LRUCache(maxsize=100)  # For frequently accessed data

        # Disk cache
        self.disk_cache = None
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            self.disk_cache = Cache(str(self.cache_dir / "diskcache"))

        # Statistics
        self.hits = 0
        self.misses = 0
        self.writes = 0

    def initialize(self) -> None:
        """Initialize the caching service."""
        logger.info("Initializing Caching Service")

        if not self.enabled:
            logger.info("Caching is disabled")
        else:
            logger.info(f"Cache initialized: TTL={self.ttl}s, Memory size={self.max_memory_size}")

        self._initialized = True

    def validate(self) -> bool:
        """Validate the service configuration.

        Returns:
            True if configuration is valid.
        """
        if self.enabled and not self.cache_dir.exists():
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create cache directory: {e}")
                return False

        return True

    def cleanup(self) -> None:
        """Clean up caching resources."""
        if self.disk_cache:
            try:
                self.disk_cache.close()
            except:
                pass

        self.memory_cache.clear()
        self.permanent_cache.clear()

        super().cleanup()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments.

        Args:
            prefix: Key prefix.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Cache key string.
        """
        # Create a string representation of arguments
        key_data = {"prefix": prefix, "args": args, "kwargs": kwargs}

        # Convert to JSON for consistent ordering
        key_str = json.dumps(key_data, sort_keys=True, default=str)

        # Generate hash for long keys
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:{key_hash}"

        return key_str

    @timer
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key.
            default: Default value if not found.

        Returns:
            Cached value or default.
        """
        if not self.enabled:
            return default

        # Check memory cache first
        if key in self.memory_cache:
            self.hits += 1
            logger.debug(f"Cache hit (memory): {key}")
            return self.memory_cache[key]

        # Check permanent cache
        if key in self.permanent_cache:
            self.hits += 1
            logger.debug(f"Cache hit (permanent): {key}")
            return self.permanent_cache[key]

        # Check disk cache
        if self.disk_cache:
            try:
                value = self.disk_cache.get(key)
                if value is not None:
                    self.hits += 1
                    logger.debug(f"Cache hit (disk): {key}")
                    # Promote to memory cache
                    self.memory_cache[key] = value
                    return value
            except Exception as e:
                logger.error(f"Disk cache read error: {e}")

        self.misses += 1
        logger.debug(f"Cache miss: {key}")
        return default

    @timer
    def set(self, key: str, value: Any, ttl: Optional[int] = None, permanent: bool = False) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (overrides default).
            permanent: Store in permanent cache.

        Returns:
            True if stored successfully.
        """
        if not self.enabled:
            return False

        try:
            self.writes += 1

            if permanent:
                # Store in permanent cache
                self.permanent_cache[key] = value
                logger.debug(f"Cached (permanent): {key}")
            else:
                # Store in memory cache
                self.memory_cache[key] = value

                # Also store in disk cache
                if self.disk_cache:
                    cache_ttl = ttl or self.ttl
                    self.disk_cache.set(key, value, expire=cache_ttl)

                logger.debug(f"Cached: {key} (TTL: {ttl or self.ttl}s)")

            return True

        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted.
        """
        deleted = False

        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True

        # Remove from permanent cache
        if key in self.permanent_cache:
            del self.permanent_cache[key]
            deleted = True

        # Remove from disk cache
        if self.disk_cache:
            try:
                if key in self.disk_cache:
                    del self.disk_cache[key]
                    deleted = True
            except Exception as e:
                logger.error(f"Disk cache delete error: {e}")

        if deleted:
            logger.debug(f"Cache deleted: {key}")

        return deleted

    def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (prefix).

        Returns:
            Number of entries cleared.
        """
        count = 0

        if pattern:
            # Clear matching entries
            # Memory cache
            keys_to_delete = [k for k in self.memory_cache if k.startswith(pattern)]
            for key in keys_to_delete:
                del self.memory_cache[key]
                count += 1

            # Permanent cache
            keys_to_delete = [k for k in self.permanent_cache if k.startswith(pattern)]
            for key in keys_to_delete:
                del self.permanent_cache[key]
                count += 1

            # Disk cache
            if self.disk_cache:
                for key in list(self.disk_cache):
                    if key.startswith(pattern):
                        del self.disk_cache[key]
                        count += 1
        else:
            # Clear all
            count = len(self.memory_cache) + len(self.permanent_cache)
            self.memory_cache.clear()
            self.permanent_cache.clear()

            if self.disk_cache:
                count += len(self.disk_cache)
                self.disk_cache.clear()

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics dictionary.
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "hit_rate": f"{hit_rate:.1f}%",
            "memory_cache_size": len(self.memory_cache),
            "permanent_cache_size": len(self.permanent_cache),
            "disk_cache_size": len(self.disk_cache) if self.disk_cache else 0,
            "ttl": self.ttl,
            "max_memory_size": self.max_memory_size,
        }

        return stats

    def reset_statistics(self):
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        self.writes = 0
        logger.info("Cache statistics reset")

    def cache_decorator(self, prefix: str, ttl: Optional[int] = None, permanent: bool = False):
        """Decorator for caching function results.

        Args:
            prefix: Cache key prefix.
            ttl: Time to live.
            permanent: Use permanent cache.

        Returns:
            Decorator function.
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(f"{prefix}:{func.__name__}", *args, **kwargs)

                # Check cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Call function
                result = func(*args, **kwargs)

                # Cache result
                self.set(cache_key, result, ttl=ttl, permanent=permanent)

                return result

            return wrapper

        return decorator

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match.

        Returns:
            Number of entries invalidated.
        """
        return self.clear(pattern)

    def warm_cache(self, data: dict[str, Any]):
        """Warm cache with pre-computed data.

        Args:
            data: Dictionary of key-value pairs to cache.
        """
        count = 0
        for key, value in data.items():
            if self.set(key, value):
                count += 1

        logger.info(f"Warmed cache with {count} entries")
