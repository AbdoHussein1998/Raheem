"""FastAPI lifecycle and ownership of application-scoped resources."""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
import loguru

from .api_settings import ApplicationBasicSettings, get_basic_settings
from .api_application_services import (
    MongoManager,
    PostgresManager,
    RedisManager,
    LLMManager,
)


class ApplicationServices:
    
    """Own the lifecycle of reusable, application-scoped resources."""

    def __init__(
        self,
        settings: ApplicationBasicSettings,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> None:
        self.logger = logger or loguru.logger
        self.settings = settings
        self.mongo = MongoManager(logger=self.logger)
        self.postgres = PostgresManager(logger=self.logger)
        self.redis = RedisManager(logger=self.logger)
        self.llm = LLMManager(logger=self.logger)
        # Qdrant remains unregistered until QdrantManager is implemented.

    async def startup(self) -> None:
        """Initialize shared resources; clean up on partial startup failure."""
        try:
            await self.mongo.connect(self.settings)
            await self.redis.connect(self.settings)
            await self.postgres.connect(self.settings)
        except BaseException:
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Attempt all cleanups in reverse initialization order."""
        for name, manager in (
            ("llm", self.llm),
            ("postgres", self.postgres),
            ("redis", self.redis),
            ("mongo", self.mongo),
        ):
            try:
                await manager.disconnect()
            except Exception:
                self.logger.exception("Failed to disconnect {} manager", name)


def create_lifespan(logger: Optional[loguru._logger.Logger] = None):
    logger = logger or loguru.logger

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("API Backend is starting up...")
        app.state.basic_settings = get_basic_settings()
        app.state.services = ApplicationServices(
            settings=app.state.basic_settings,
            logger=logger,
        )
        await app.state.services.startup()
        try:
            yield
        finally:
            logger.info("API Backend is shutting down...")
            await app.state.services.shutdown()

    return lifespan
