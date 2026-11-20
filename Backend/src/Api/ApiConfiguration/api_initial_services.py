"""Construction of application-owned infrastructure connections.

These managers implement resource ownership by composition: they neither
inherit from a service base class nor create resources on import.
"""
from __future__ import annotations

import inspect
import asyncio
from typing import Any

from Infrastructure.Logging.start import LoggerManager

from Infrastructure.Databases.Mongodb.async_connection import MongoConnectionManager
from Infrastructure.Databases.PostgreSQL.async_connection import PostgresConnectionManager
from Infrastructure.Databases.Redis.async_connection import RedisConnectionManager
from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger
from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from Infrastructure.Temporal.async_connection import TemporalConnectionManager

from .api_settings import ApplicationBasicSettings


class MongoManager:
    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("MongoManager")
        self.omni_mongo_connection: MongoConnectionManager | None = None

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        if self.omni_mongo_connection is not None:
            return
        self.omni_mongo_connection = await MongoConnectionManager.init_class(
            mongo_url=settings.OMNI_MONGO_URL,
            db_name=settings.OMNI_MONGO_DB_NAME,
            logger=self.get_logger("omni_mongo"),
        )

    async def disconnect(self) -> None:
        connection, self.omni_mongo_connection = self.omni_mongo_connection, None
        if connection is not None:
            await connection.disconnect()


class PostgresManager:
    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("PostgresManager")
        self.omni_postgres_conn: PostgresConnectionManager | None = None
        self.omni_postgres_dml: PostgresDML | None = None

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        if self.omni_postgres_conn is not None:
            return
        self.omni_postgres_conn = await PostgresConnectionManager.init_class(
            host=settings.OMNI_POSTGRES_HOST,
            port=settings.OMNI_POSTGRES_PORT,
            username=settings.OMNI_POSTGRES_USER,
            password=settings.OMNI_POSTGRES_PASSWORD,
            database=settings.OMNI_POSTGRES_DB,

            logger=self.get_logger("omni_postgres"),
        )
        self.omni_postgres_dml = await PostgresDML.init_class(
            manager=self.omni_postgres_conn,
            schema="processing_catalog",
            logger=self.get_logger("omni_postgres_dml"),
        )

    async def disconnect(self) -> None:
        dml, self.omni_postgres_dml = self.omni_postgres_dml, None
        if dml is not None:
            await dml.close()
        connection, self.omni_postgres_conn = self.omni_postgres_conn, None
        if connection is not None:
            await connection.disconnect()


class RedisManager:
    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("RedisManager")
        self.omni_redis_conn: RedisConnectionManager | None = None

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        if self.omni_redis_conn is not None:
            return
        self.omni_redis_conn = await RedisConnectionManager.init_class(
            redis_url=settings.OMNI_REDIS_URL,
            logger=self.get_logger("omni_redis"),
        )

    async def disconnect(self) -> None:
        connection, self.omni_redis_conn = self.omni_redis_conn, None
        if connection is not None:
            await connection.disconnect()


class MinioManager:
    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("MinioManager")
        self.omni_minio_conn: AsyncMinioConnectionManger | None = None

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        if self.omni_minio_conn is not None:
            return
        self.omni_minio_conn = await AsyncMinioConnectionManger.init_class(
            url=settings.OMNI_MINIO_ENDPOINT,
            access_key=settings.OMNI_MINIO_ACCESS_KEY,
            secret_key=settings.OMNI_MINIO_SECRET_KEY,
            logger=self.get_logger("omni_minio"),
        )

    async def disconnect(self) -> None:
        connection, self.omni_minio_conn = self.omni_minio_conn, None
        if connection is not None:
            await connection.disconnect()


class LLMManager:
    """Optional models: never imported or started unless ENABLE_LLM is true."""

    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("LLMManager")
        self.omni_llm_gen: Any | None = None
        self.omni_llm_embd: Any | None = None

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        # Lazy imports avoid requiring model SDKs on API startup when disabled.
        from Backend.src.Infrastructure.LLM.Generation.generation_factory import GenerationConfig, GenerationFactory
        from Backend.src.Infrastructure.LLM.Embedding.embedding_factory import EmbeddingConfig, EmbeddingFactory

        if not settings.OMNI_GENERATION_MODEL or not settings.OMNI_EMBEDDING_MODEL:
            raise ValueError("LLM model names are required when ENABLE_LLM is true")

        self.omni_llm_gen = await GenerationFactory.create_llm(
            model_config=GenerationConfig(
                model_name=settings.OMNI_GENERATION_MODEL,
                model_provider=settings.OMNI_GENERATION_PROVIDER,
                api_key=settings.OMNI_GENERATION_MODEL_API_KEY,
                base_url=settings.OMNI_GENERATION_MODEL_CONNECTION_URL,
            ),
            logger=self.get_logger("omni_generation_model"),
        )
        if self.omni_llm_gen is None:
            raise RuntimeError("LLM generation factory returned no model")
        self.omni_llm_embd = await EmbeddingFactory.create_llm(
            embedding_config=EmbeddingConfig(
                model_name=settings.OMNI_EMBEDDING_MODEL,
                embedding_provider=settings.OMNI_EMBEDDING_PROVIDER,
                api_key=settings.OMNI_EMBEDDING_MODEL_API_KEY,
                base_url=settings.OMNI_EMBEDDING_MODEL_CONNECTION_URL,
            ),
            logger=self.get_logger("omni_embedding_model"),
        )
        if self.omni_llm_embd is None:
            raise RuntimeError("LLM embedding factory returned no model")

    async def disconnect(self) -> None:
        for attribute in ("omni_llm_embd", "omni_llm_gen"):
            model = getattr(self, attribute)
            setattr(self, attribute, None)
            if model is None:
                continue
            close = getattr(model, "aclose", None) or getattr(model, "close", None)
            if close is not None:
                try:
                    result = close()
                    if inspect.isawaitable(result):
                        await result
                except Exception:
                    self.logger.exception("Failed to close {} model", attribute)


class TemporalManager:
    """Application-scoped registry of independent named Temporal connections.

    The default `omni` connection mirrors the existing Mongo/Postgres naming.
    Additional connections are created using connect_named(...) with their own
    namespaces and credentials; they are not new worker processes.
    """

    def __init__(self, logger_manager: LoggerManager) -> None:
        self.logger_manager = logger_manager
        self.get_logger = logger_manager.get_logger
        self.logger = self.get_logger("TemporalManager")
        self.omni_temporal_conn: TemporalConnectionManager | None = None
        self.connections: dict[str, TemporalConnectionManager] = {}
        self._lock = asyncio.Lock()

    async def connect(self, settings: ApplicationBasicSettings) -> None:
        connection = await self.connect_named(
            name="omni", address=settings.TEMPORAL_ADDRESS,
            namespace=settings.TEMPORAL_NAMESPACE,
            tls=settings.TEMPORAL_TLS, api_key=settings.TEMPORAL_API_KEY,
        )
        self.omni_temporal_conn = connection

    async def connect_named(
        self, name: str, address: str, namespace: str = "default", *,
        tls: bool = False, api_key: str | None = None,
    ) -> TemporalConnectionManager:
        if not name.strip():
            raise ValueError("Temporal connection name cannot be empty")
        async with self._lock:
            if name in self.connections:
                existing = self.connections[name]
                if (existing.address, existing.namespace, existing.tls, existing.api_key) != (address, namespace, tls, api_key):
                    raise ValueError(f"Temporal connection {name!r} already has different settings")
                await existing.connect()
                return existing
            conn = await TemporalConnectionManager.init_class(
                address=address, namespace=namespace, tls=tls, api_key=api_key,
                logger=self.get_logger(f"temporal_{name}"),
            )
            self.connections[name] = conn
            if name == "omni":
                self.omni_temporal_conn = conn
            return conn

    def get_connection(self, name: str = "omni") -> TemporalConnectionManager:
        connection = self.connections.get(name)
        if connection is None:
            raise RuntimeError(f"Temporal connection {name!r} is unavailable")
        return connection

    async def disconnect(self) -> None:
        async with self._lock:
            connections = list(self.connections.values())
            self.connections.clear()
            self.omni_temporal_conn = None
            for connection in connections:
                await connection.disconnect()
