"""Construction of application-owned infrastructure connections.

These managers implement resource ownership by composition: they neither
inherit from a service base class nor create resources on import.
"""
from __future__ import annotations

import inspect
from typing import Any

from Infrastructure.Logging.start import LoggerManager

from Infrastructure.Databases.Mongodb.async_connection import MongoConnectionManager
from Infrastructure.Databases.PostgreSQL.async_connection import PostgresConnectionManager
from Infrastructure.Databases.Redis.async_connection import RedisConnectionManager
from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger

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

    async def disconnect(self) -> None:
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
