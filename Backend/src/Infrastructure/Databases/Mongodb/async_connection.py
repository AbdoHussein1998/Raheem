"""
Async MongoDB Connection Manager with retry decorator.

Handles connection lifecycle, pooling, health checks, and automatic
reconnection for transient failures.

Version: 3.0.0
"""

import time
import asyncio
from typing import Optional, Any, Callable
from .utility import retry
from pymongo.errors import (ConnectionFailure as PyMongoConnectionError, ServerSelectionTimeoutError, NetworkTimeout, AutoReconnect)
import loguru
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


# Errors we should retry (transient / network issues only)
# DuplicateKeyError, BulkWriteError, and programming errors are NOT retried.



class MongoConnectionManager:
    """
    Production-grade async MongoDB connection manager using Motor.

    Handles connection lifecycle, pooling, health checks, and reconnection.
    Used by DDL and DML classes via composition.

    Attributes:
        url (str): MongoDB connection URL.
        db_name (str): Database name.
        client (Optional[AsyncIOMotorClient]): Motor async client.
        db (Optional[AsyncIOMotorDatabase]): Async database instance.
        logger: Logger instance (loguru by default).
    """

    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        logger: Optional[Any] = None,
        max_pool_size: int = 20,
        min_pool_size: int = 5,
        server_selection_timeout_ms: int = 5000,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 30000,
        health_check_interval: int = 30,
    ) -> None:
        """
        Initialize async MongoDB connection manager.

        Args:
            mongo_url (str): MongoDB connection URL.
            db_name (str): Database name.
            logger: Optional custom logger (defaults to loguru).
            max_pool_size (int): Max concurrent connections. Default 20.
            min_pool_size (int): Min maintained connections. Default 5.
            server_selection_timeout_ms (int): Server discovery timeout. Default 5000.
            connect_timeout_ms (int): TCP connect timeout. Default 10000.
            socket_timeout_ms (int): Per-operation socket timeout. Default 30000.
            health_check_interval (int): Seconds between active pings. Default 30.

        Raises:
            ValueError: If mongo_url is not provided.
        """
        if not mongo_url:
            raise ValueError("Connection_String not provided. Pass as argument")

        self.url: str = mongo_url
        self.db_name: str = db_name
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.connect_timeout_ms = connect_timeout_ms
        self.socket_timeout_ms = socket_timeout_ms
        self.health_check_interval = health_check_interval

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.logger = logger if logger is not None else loguru.logger

        # For throttled health checks
        self._last_health_check: float = 0.0

        self.logger.info(
            f"MongoConnectionManager initialized | db='{self.db_name}' | "
            f"pool={self.min_pool_size}-{self.max_pool_size}"
        )

    @classmethod
    async def init_class(
        cls,
        mongo_url: str,
        db_name: str,
        logger: Optional[Any] = None,
        max_pool_size: int = 20,
        min_pool_size: int = 5,
        server_selection_timeout_ms: int = 5000,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 30000,
        health_check_interval: int = 30,
        **kwargs,
    ) -> "MongoConnectionManager":   # ✅ FIXED: correct class name
        """
        Factory method to initialize and return a MongoConnectionManager instance.

        Extra keyword arguments (max_pool_size, timeouts, etc.) are passed
        to __init__.

        Args:
            mongo_url (str): MongoDB connection URL.
            db_name (str): Database name.
            logger: Optional custom logger.
            **kwargs: Extra connection parameters (max_pool_size, etc.).

        Returns:
            MongoConnectionManager: Connected and verified instance.

        Raises:
            Exception: If initialization fails.
        """
        try:
            instance = cls(mongo_url, db_name, logger,max_pool_size,
                            min_pool_size,
                            server_selection_timeout_ms,
                            connect_timeout_ms,
                            socket_timeout_ms,
                            health_check_interval ,**kwargs)
            if not await instance.connect():
                raise ConnectionError("MongoDB connection initialization failed")
            return instance
        except Exception as e:
            loguru.logger.error(f"Failed to initialize MongoConnectionManager: {e}")
            raise


    async def connect(self) -> bool:
        """
        Establish async connection to MongoDB with configurable pool.

        Returns:
            bool: True on success, False on failure.
        """
        try:
            self.logger.info(
                f"Connecting to MongoDB | db='{self.db_name}' | "
                f"pool={self.min_pool_size}-{self.max_pool_size}"
            )

            if self.client is not None:
                return await self.ensure_connected()

            candidate = AsyncIOMotorClient(
                self.url,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                retryWrites=True,
            )

            try:
                await candidate.admin.command("ping")
            except Exception:
                candidate.close()
                raise
            self.client = candidate
            self.db = candidate[self.db_name]
            self._last_health_check = time.monotonic()

            self.logger.success(f"Connected to MongoDB | db='{self.db_name}'")
            return True

        except PyMongoConnectionError as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected connection error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return False

    async def disconnect(self) -> bool:
        """
        Close MongoDB connection and cleanup resources.

        Returns:
            bool: True on success or if already disconnected.
        """
        try:
            if self.client is not None:
                self.client.close()
                self.client = None
                self.db = None
                self._last_health_check = 0.0
                self.logger.info("Disconnected from MongoDB")
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
        self.logger.info("Reconnecting to MongoDB...")
        await self.disconnect()
        return await self.connect()

    async def ensure_connected(self) -> bool:
        """
        Validate connection with THROTTLED health checks.

        Only pings server every `health_check_interval` seconds instead of
        every operation. Motor's pool handles most connection issues internally.

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
            await self.client.admin.command("ping")
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
            raise ConnectionError("Failed to establish MongoDB connection")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes connection."""
        await self.disconnect()
        return False


# Convenience alias for easy access: `from connection import retry`
