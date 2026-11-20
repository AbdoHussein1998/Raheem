"""Mongodb shared constants and async retry decorator (no instances)."""
from __future__ import annotations
from enum import Enum
import asyncio
from functools import wraps
from pymongo.errors import (ConnectionFailure as PyMongoConnectionError,
    ServerSelectionTimeoutError, NetworkTimeout, AutoReconnect)

RETRYABLE_ERRORS = (
    PyMongoConnectionError,
    ServerSelectionTimeoutError,
    NetworkTimeout,
    AutoReconnect,
    ConnectionError,
)

# Functional Enum construction keeps the pre-existing UpdateOperation API,
# without introducing a subclass in infrastructure code.
UpdateOperation = Enum('UpdateOperation', {
    'SET': 'set',
    'PUSH': 'push',
    'PUSH_BOUNDED': 'push_bounded',
    'CURRENT_DATE': 'current_date',
    'SET_ON_INSERT': 'set_on_insert',
    'UNSET': 'unset',
    'INC': 'inc',
})

class MongoUtility:
    DEFAULT_MAX_ATTEMPTS = 1  # Avoid silent replay of non-idempotent writes.
    BASE_RETRY_DELAY = 0.1
    MAX_RETRY_DELAY = 5.0
    BACKOFF_FACTOR = 2.0
    RETRYABLE_ERRORS = RETRYABLE_ERRORS
    UPDATE_OPERATION = UpdateOperation

    @staticmethod
    def retry(max_attempts: int = 1, base_delay: float = 0.1,
              max_delay: float = 5.0, backoff_factor: float = 2.0,
              exceptions: tuple[type[Exception], ...] = RETRYABLE_ERRORS):
        """Retry transient async failures only when callers explicitly opt in.

        Attempt count defaults to one; set max_attempts > 1 only for reads
        or provably idempotent operations. Retrying an ambiguous acknowledged
        write can duplicate side effects.
        """
        if max_attempts < 1 or base_delay < 0 or max_delay < 0 or backoff_factor < 1:
            raise ValueError("Invalid Mongodb retry configuration")
        def decorator(func):
            @wraps(func)
            async def wrapped(self, *args, **kwargs):
                delay = base_delay
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(self, *args, **kwargs)
                    except exceptions:
                        if attempt >= max_attempts:
                            raise
                        logger = getattr(self, 'logger', None)
                        if logger is not None:
                            logger.warning("{} transient failure (attempt {}/{}); retrying", func.__name__, attempt, max_attempts)
                        manager = getattr(self, 'conn', None) or getattr(self, 'connection_manager', None) or self
                        if hasattr(manager, 'reconnect'):
                            await manager.reconnect()
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
            return wrapped
        return decorator

retry = MongoUtility.retry
