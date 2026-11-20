
import asyncio
import loguru

from loguru._logger import Logger
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse
from .utility import retry



class AsyncMinioConnectionManger:

    def __init__(self,url: str,logger: Logger | None = None,access_key: str = "minioadmin",secret_key: str = "minioadmin",):
        self.url = url
        self.client: Minio | None = None
        self.logger = logger or loguru.logger

        self.access_key = access_key
        self.secret_key = secret_key

    @classmethod
    async def init_class(
        cls,
        url: str,
        logger: Logger | None = None,
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
    ) -> "AsyncMinioConnectionManger":

        instance = cls(
            url=url,
            logger=logger,
            access_key=access_key,
            secret_key=secret_key,
        )

        await instance.connect()
        return instance

    @retry(max_attempts=3)
    async def connect(self) -> None:
        if self.client is not None:
            self.logger.debug(
                "MinIO client already initialized: {}",
                self.url,
            )
            return

        self.logger.info(
            "Initializing MinIO connection: {}",
            self.url,
        )

        client = None

        try:
            parsed_url = urlparse(self.url)

            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(
                    f"Invalid MinIO URL: {self.url}"
                )

            if parsed_url.scheme not in ("http", "https"):
                raise ValueError(
                    "MinIO URL must use http or https"
                )

            client = Minio(
                endpoint=parsed_url.netloc,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=parsed_url.scheme == "https",
            )

            # Minio constructor does not check connectivity.
            # This is a real, synchronous network operation.
            await asyncio.to_thread(client.list_buckets)

            self.client = client

            self.logger.success(
                "MinIO connection verified successfully: {}",
                self.url,
            )

        except Exception:
            if client is not None:
                await asyncio.to_thread(client._http.clear)

            self.logger.exception("Failed to establish MinIO connection")
            raise

    async def disconnect(self) -> None:
        if self.client is None:
            self.logger.debug(
                "MinIO client is already disconnected"
            )
            return

        self.logger.info(
            "Disconnecting MinIO client: {}",
            self.url,
        )

        client = self.client
        self.client = None

        try:
            await asyncio.to_thread(client._http.clear)

            self.logger.info(
                "MinIO HTTP connection pool cleared"
            )

        except Exception:
            self.logger.exception(
                "Failed to clean up MinIO connection pool"
            )
            raise

    async def ensure_connected(self) -> None:
        if self.client is None:
            self.logger.warning(
                "MinIO client is not initialized. "
                "Attempting connection."
            )
            await self.connect()

    async def reconnect(self) -> None:
        self.logger.warning(
            "Reconnecting to MinIO: {}",
            self.url,
        )

        try:
            await self.disconnect()
            await self.connect()

            self.logger.success(
                "MinIO reconnection successful: {}",
                self.url,
            )

        except Exception:
            self.logger.exception(
                "MinIO reconnection failed: {}",
                self.url,
            )
            raise





