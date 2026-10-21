"""Authentication settings constants and opt-in transient retry helper."""
import asyncio
from functools import wraps

class AuthenticationUtility:
    DEFAULT_MAX_ATTEMPTS = 1
    BASE_RETRY_DELAY = 0.2
    MAX_RETRY_DELAY = 1.5
    BACKOFF_FACTOR = 2.0
    RETRYABLE_ERRORS = (ConnectionError, TimeoutError, OSError)
    GOOGLE_METADATA_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    GOOGLE_SCOPE = 'openid email profile'
    JWT_AUDIENCE = 'SIGNING_IN'
    ACCESS_COOKIE = 'access_token'
    REFRESH_COOKIE = 'refresh_token'
    REFRESH_COOKIE_PATH = '/api/v1/auth/refresh'

    @staticmethod
    def retry(max_attempts: int = 1, base_delay: float = 0.2,
              max_delay: float = 1.5, backoff_factor: float = 2.0,
              exceptions: tuple[type[Exception], ...] = RETRYABLE_ERRORS):
        """Opt-in for repeatable network lookups only, NOT OAuth code exchange.

        Access-token exchange uses a single-use authorization code and must
        never be replayed automatically. JWT validation is deterministic and
        likewise has no reason to be retried.
        """
        if max_attempts < 1 or base_delay < 0 or max_delay < 0 or backoff_factor < 1:
            raise ValueError('Invalid authentication retry configuration')
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
                            logger.warning('{}: transient failure ({}/{}); retrying', func.__name__, attempt, max_attempts)
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
            return wrapped
        return decorator

retry = AuthenticationUtility.retry
