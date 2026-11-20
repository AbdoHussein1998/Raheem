"""An independent Temporal client connection, following infrastructure managers.

One instance per configured address / namespace / credentials. Clients are
bound to the event loop on which they were created and must not be forked or
passed between FastAPI and worker processes.
"""
from __future__ import annotations

import asyncio
from typing import Any
from loguru import logger as default_logger
from temporalio.client import Client


class TemporalConnectionManager:
    def __init__(
        self, address: str, namespace: str = "default", *,
        tls: bool = False, api_key: str | None = None,
        logger: Any = None,
    ) -> None:
        self.address = address
        self.namespace = namespace
        self.tls = tls
        self.api_key = api_key
        self.logger = logger or default_logger
        self.client: Client | None = None
        self._connection_lock = asyncio.Lock()

    @classmethod
    async def init_class(
        cls, address: str, namespace: str = "default", *,
        tls: bool = False, api_key: str | None = None,
        logger: Any = None,
    ) -> "TemporalConnectionManager":
        manager = cls(address=address, namespace=namespace, tls=tls,
                      api_key=api_key, logger=logger)
        await manager.connect()
        return manager

    async def connect(self) -> None:
        if self.client is not None:
            return
        async with self._connection_lock:
            if self.client is not None:
                return
            kwargs: dict[str, Any] = {"namespace": self.namespace, "tls": self.tls}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self.client = await Client.connect(self.address, **kwargs)
            self.logger.info("Temporal connected namespace={} address={}",
                             self.namespace, self.address)

    async def ensure_connected(self) -> Client:
        await self.connect()
        return self.get_client()

    def get_client(self) -> Client:
        if self.client is None:
            raise RuntimeError("Temporal client is not connected")
        return self.client

    async def reconnect(self) -> None:
        async with self._connection_lock:
            # Python SDK Client has no public close(); discard and reconnect.
            self.client = None
        await self.connect()

    async def disconnect(self) -> None:
        async with self._connection_lock:
            self.client = None
            self.logger.info("Temporal client reference released for {}", self.namespace)

    async def __aenter__(self) -> "TemporalConnectionManager":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.disconnect()
