"""MinIO constants and a conservative, async retry decorator."""
import asyncio
from functools import wraps
from urllib3.exceptions import (ConnectTimeoutError, ReadTimeoutError, ProtocolError, MaxRetryError, NewConnectionError)

class MinioUtility:
    DEFAULT_MAX_ATTEMPTS = 1
    BASE_RETRY_DELAY = 0.2
    MAX_RETRY_DELAY = 2.0
    BACKOFF_FACTOR = 2.0
    RETRYABLE_ERRORS = (ConnectionError, TimeoutError, OSError, ConnectTimeoutError, ReadTimeoutError, ProtocolError, MaxRetryError, NewConnectionError)
    # S3Error is deliberately excluded; most 4xx are not transient.

    @staticmethod
    def retry(max_attempts: int = 1, base_delay: float = 0.2,
              max_delay: float = 2.0, backoff_factor: float = 2.0,
              exceptions: tuple[type[Exception], ...] = RETRYABLE_ERRORS):
        """Retry safe MinIO operations; do not replay writes after ambiguous timeout.

        asyncio.to_thread timeouts do not cancel running synchronous work.
        A caller must opt in to >1 attempt only if replay is safe.
        """
        if max_attempts < 1 or base_delay < 0 or max_delay < 0 or backoff_factor < 1:
            raise ValueError('Invalid MinIO retry configuration')
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
                            logger.warning('{} failed transiently ({}/{}); retrying', func.__name__, attempt, max_attempts)
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
            return wrapped
        return decorator

retry = MinioUtility.retry
