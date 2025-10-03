"""Base service class for all services in the system."""

import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Optional

from loguru import logger


def timer(func):
    """Decorator to measure function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


def error_handler(func):
    """Decorator to handle errors in service methods."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper


class BaseService(ABC):
    """Abstract base class for all services.

    Provides common functionality like logging, error handling,
    and configuration management.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the base service.

        Args:
            config: Configuration dictionary for the service.
        """
        self.config = config or {}
        self._initialized = False
        self._cache = {}
        logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service.

        This method should be implemented by subclasses to perform
        any necessary initialization tasks.
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the service configuration and state.

        Returns:
            True if the service is valid and ready to use.
        """
        pass

    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        logger.info(f"Cleaning up {self.__class__.__name__}")
        self._cache.clear()
        self._initialized = False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: The configuration key.
            default: Default value if key not found.

        Returns:
            The configuration value or default.
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: The configuration key.
            value: The configuration value.
        """
        self.config[key] = value
        logger.debug(f"Configuration updated: {key} = {value}")

    def is_initialized(self) -> bool:
        """Check if the service is initialized.

        Returns:
            True if the service is initialized.
        """
        return self._initialized

    def cache_get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value or None.
        """
        return self._cache.get(key)

    def cache_set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        self._cache[key] = value

    def cache_clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        logger.debug(f"Cache cleared for {self.__class__.__name__}")

    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False

    def __repr__(self) -> str:
        """String representation of the service."""
        return f"{self.__class__.__name__}(initialized={self._initialized})"
