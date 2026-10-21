"""Qdrant constants and conservative read-only retry decorator."""
import asyncio
from functools import wraps
from httpx import TransportError
from qdrant_client.models import Distance

class QdrantUtility:
    DISTANCE_MAP = {
        'cosine': Distance.COSINE,
        'euclid': Distance.EUCLID,
        'dot': Distance.DOT,
        'manhattan': Distance.MANHATTAN,
    }
    DEFAULT_MAX_ATTEMPTS = 1
    BASE_RETRY_DELAY = 0.2
    MAX_RETRY_DELAY = 2.0
    BACKOFF_FACTOR = 2.0
    RETRYABLE_ERRORS = (ConnectionError, TimeoutError, OSError, TransportError)

    @staticmethod
    def retry(max_attempts: int = 1, base_delay: float = 0.2,
              max_delay: float = 2.0, backoff_factor: float = 2.0,
              exceptions: tuple[type[Exception], ...] = RETRYABLE_ERRORS):
        """Retry reads/transient transport failures; avoid replaying writes."""
        if max_attempts < 1 or base_delay < 0 or max_delay < 0 or backoff_factor < 1:
            raise ValueError('Invalid Qdrant retry configuration')
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
                            logger.warning('{}: transient Qdrant error ({}/{}); retrying', func.__name__, attempt, max_attempts)
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
            return wrapped
        return decorator

retry = QdrantUtility.retry
