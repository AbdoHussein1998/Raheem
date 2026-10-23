"""Small welcome service reused by API and Celery tasks."""

from typing import Optional

import loguru
from loguru._logger import Logger

from Services.service_interface import ServiceInterface


class WelcomeService(ServiceInterface):
    def __init__(self, logger: Optional[Logger] = None) -> None:
        super().__init__(logger=logger)

    @classmethod
    async def init_service(cls, logger: Optional[Logger] = None) -> "WelcomeService":
        log = logger or loguru.logger
        log.info("Initializing Welcome service...")
        instance = cls(logger=log)
        log.success("Welcome service initialized successfully")
        return instance

    async def run(self) -> str:
        self.logger.info("Welcome service is running")
        return "Welcome to the Base RAG application"
