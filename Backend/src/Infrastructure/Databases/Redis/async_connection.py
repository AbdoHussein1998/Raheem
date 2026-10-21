import asyncio
import time
from typing import Any, Callable, Optional
from .utility import retry
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
import redis.asyncio as redis
import loguru


# Retryable errors for the @retry decorator



class RedisConnectionManager:
    """
    Production-grade async Redis connection manager using redis-py async.

    Handles connection lifecycle, pooling, health checks, and reconnection.
    Used by DDL and DML classes via composition.

    Attributes:
        redis_url (str): Redis connection URL.
        client (Optional[redis.Redis]): Async Redis client.
        logger: Logger instance (loguru by default).
    """

    def __init__(
        self,
        redis_url: str,
        logger: Optional[Any] = None,
        max_pool_size: int = 20,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 30000,
        health_check_interval: int = 30,
    ) -> None:
        """
        Initialize async Redis connection manager.

        Args:
            redis_url (str): Redis connection URL.
            logger: Optional custom logger (defaults to loguru).
            max_pool_size (int): Max concurrent connections. Default 20.
            connect_timeout_ms (int): TCP connect timeout. Default 10000.
            socket_timeout_ms (int): Per-operation socket timeout. Default 30000.
            health_check_interval (int): Seconds between active pings. Default 30.

        Raises:
            ValueError: If redis_url is not provided.
        """
        if not redis_url:
            raise ValueError("Connection_String not provided. Pass as argument")

        self.redis_url: str = redis_url
        self.max_pool_size = max_pool_size
        self.connect_timeout_ms = connect_timeout_ms
        self.socket_timeout_ms = socket_timeout_ms
        self.health_check_interval = health_check_interval

        self.client: Optional[redis.Redis] = None
        self.logger = logger if logger is not None else loguru.logger

        # For throttled health checks
        self._last_health_check: float = 0.0

        self.logger.info(
            f"RedisConnectionManager initialized | "
            f"pool max={self.max_pool_size} | "
            f"connect_timeout={self.connect_timeout_ms}ms | "
            f"socket_timeout={self.socket_timeout_ms}ms"
        )

    @classmethod
    async def init_class(
        cls,
        redis_url: str,
        logger: Optional[Any] = None,
        max_pool_size: int = 20,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 30000,
        health_check_interval: int = 30,
        **kwargs,
    ) -> "RedisConnectionManager":
        """
        Factory method to initialize and return a RedisConnectionManager instance.

        Extra keyword arguments are passed to __init__.

        Args:
            redis_url (str): Redis connection URL.
            logger: Optional custom logger.
            **kwargs: Extra connection parameters.

        Returns:
            RedisConnectionManager: Initialized and connectivity-verified instance.

        Raises:
            Exception: If initialization fails.
        """
        try:
            instance = cls(
                redis_url=redis_url,
                logger=logger,
                max_pool_size=max_pool_size,
                connect_timeout_ms=connect_timeout_ms,
                socket_timeout_ms=socket_timeout_ms,
                health_check_interval=health_check_interval,
                **kwargs,
            )
            
            if not await instance.connect():
                raise ConnectionError("Redis connection initialization failed")
            return instance
        except Exception as e:
            loguru.logger.error(f"Failed to initialize RedisConnectionManager: {e}")
            raise

    async def connect(self) -> bool:
        """
        Establish async connection to Redis with configurable pool.

        Returns:
            bool: True on success, False on failure.
        """
        try:
            self.logger.info(
                f"Connecting to Redis | "
                f"pool max={self.max_pool_size} | "
                f"connect_timeout={self.connect_timeout_ms}ms"
            )

            if self.client is not None:
                return await self.ensure_connected()

            candidate = redis.Redis.from_url(
                self.redis_url,
                max_connections=self.max_pool_size,
                socket_connect_timeout=self.connect_timeout_ms / 1000,
                socket_timeout=self.socket_timeout_ms / 1000,
                health_check_interval=self.health_check_interval,
                decode_responses=True,
                socket_keepalive=True,
            )

            try:
                await candidate.ping()
            except Exception:
                await candidate.aclose()
                raise
            self.client = candidate
            self._last_health_check = time.monotonic()

            self.logger.success("Connected to Redis")
            return True

        except RedisConnectionError as e:
            self.logger.error(f"Redis connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected connection error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return False

    async def disconnect(self) -> bool:
        """
        Close Redis connection and cleanup resources.

        Returns:
            bool: True on success or if already disconnected.
        """
        try:
            if self.client is not None:
                await self.client.aclose()
                self.client = None
                self._last_health_check = 0.0
                self.logger.info("Disconnected from Redis")
            return True
        except Exception as e:
            self.logger.error(
                f"Disconnect error: {type(e).__name__}: {e}", exc_info=True
            )
            return False

    async def reconnect(self) -> bool:
        """
        Force reconnection — used by @retry decorator between attempts.

        Returns:
            bool: True if reconnection successful.
        """
        self.logger.info("Reconnecting to Redis...")
        await self.disconnect()
        return await self.connect()

    async def ensure_connected(self) -> bool:
        """
        Validate connection with THROTTLED health checks.

        Only pings server every `health_check_interval` seconds instead of
        every operation. Redis connection pool handles most issues internally.

        Returns:
            bool: True if connected and healthy.
        """
        if self.client is None:
            self.logger.warning("No active connection, attempting to connect...")
            return await self.connect()

        # Throttle: skip ping if we recently verified connection
        now = time.monotonic()
        if now - self._last_health_check < self.health_check_interval:
            return True

        try:
            await self.client.ping()
            self._last_health_check = now
            return True
        except Exception as e:
            self.logger.warning(
                f"Health check failed ({type(e).__name__}), reconnecting..."
            )
            return await self.reconnect()

    async def __aenter__(self):
        """Async context manager entry - establishes connection."""
        if not await self.connect():
            raise ConnectionError("Failed to establish Redis connection")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes connection."""
        await self.disconnect()
        return False

    

