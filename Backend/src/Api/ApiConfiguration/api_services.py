"""Single application-scoped composition root and resource lifecycle."""
from __future__ import annotations

from typing import Any

from .api_initial_services import (
    MongoManager,
    PostgresManager,
    RedisManager,
    MinioManager,
    LLMManager,
)
from .api_settings import ApplicationBasicSettings


class ApplicationServices:
    def __init__(self, settings: ApplicationBasicSettings, logger_manager: Any) -> None:
        self.settings = settings
        self.logger_manager = logger_manager
        self.logger = logger_manager.get_logger("ApplicationServices")
        self.mongo = MongoManager(logger_manager)
        self.redis = RedisManager(logger_manager)
        self.postgres = PostgresManager(logger_manager)
        self.minio = MinioManager(logger_manager)
        self.llm = LLMManager(logger_manager)
        self._started: list[tuple[str, Any]] = []

    async def startup(self) -> None:
        if self._started:
            return
        managers = [
            ("mongo", self.mongo),
            # ("redis", self.redis),
            ("postgres", self.postgres),
            ("minio", self.minio),
        ]
        # if self.settings.ENABLE_LLM:
        #     managers.append(("llm", self.llm))

        try:
            for name, manager in managers:
                self.logger.info("Starting {}", name)
                # Include an in-progress manager in cleanup (e.g. when LLM
                # generation succeeds but embedding initialization fails).
                self._started.append((name, manager))
                await manager.connect(self.settings)
        except BaseException:
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        # Only managers that were reached during startup, in reverse order.
        while self._started:
            name, manager = self._started.pop()
            try:
                await manager.disconnect()
            except Exception:
                self.logger.exception("Failed to disconnect {}", name)
