
import asyncio

from collections.abc import AsyncIterator
from itertools import islice
from typing import BinaryIO

from loguru import logger as default_logger
from minio import Minio
from minio.commonconfig import CopySource
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
from .async_conncetion import AsyncMinioConnectionManger
from .utility import retry



class AsyncMinioController:

    def __init__(
        self,
        connection_manager:AsyncMinioConnectionManger,
        logger=None,
        timeout: float = 45.0,
    ):
        if connection_manager.client is None:
            raise RuntimeError(
                "MinIO connection manager must be initialized "
                "before creating MinioController"
            )

        self.conn = connection_manager
        self.logger = logger or default_logger
        self.timeout = timeout

        self.logger.info(
            "Creating MinIO controller with timeout={}s",
            self.timeout,
        )
        self.logger.success(
            "MinIO controller created successfully"
        )

    @property
    def client(self) -> Minio:
        client = self.conn.client
        if client is None:
            raise RuntimeError("MinIO connection manager is disconnected")
        return client

    @classmethod
    async def init_class(
        cls,
        connection_manager,
        logger=None,
        timeout: float = 45.0,
    ) -> "AsyncMinioController":

        log = logger or default_logger
        log.info("Initializing MinIO controller")

        instance = cls(
            connection_manager=connection_manager,
            logger=log,
            timeout=timeout,
        )

        log.success(
            "MinIO controller initialization completed"
        )
        return instance

    # ==========================================
    # Execution
    # ==========================================

    async def _execute(
        self,
        operation: str,
        func,
        *args,
        timeout: float | None = None,
        **kwargs,
    ):
        if timeout is None:
            timeout = self.timeout
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            self.logger.error(
                "MinIO operation '{}' timed out after {} seconds",
                operation,
                timeout,
            )
            raise

        except Exception:
            self.logger.exception(
                "MinIO operation '{}' failed",
                operation,
            )
            raise

    # ==========================================
    # Bucket Operations
    # ==========================================

    async def create_bucket(
        self,
        bucket_name: str,
    ) -> None:
        self.logger.info(
            "Creating MinIO bucket '{}'",
            bucket_name,
        )

        await self._execute(
            "create_bucket",
            self.client.make_bucket,
            bucket_name,
        )

        self.logger.success(
            "MinIO bucket '{}' created successfully",
            bucket_name,
        )

    async def delete_bucket(
        self,
        bucket_name: str,
    ) -> None:
        self.logger.info(
            "Deleting MinIO bucket '{}'",
            bucket_name,
        )

        await self._execute(
            "delete_bucket",
            self.client.remove_bucket,
            bucket_name,
        )

        self.logger.success(
            "MinIO bucket '{}' deleted successfully",
            bucket_name,
        )

    @retry(max_attempts=3)
    async def bucket_exists(
        self,
        bucket_name: str,
    ) -> bool:
        self.logger.info(
            "Checking existence of MinIO bucket '{}'",
            bucket_name,
        )

        exists = await self._execute(
            "bucket_exists",
            self.client.bucket_exists,
            bucket_name,
        )

        if exists:
            self.logger.success(
                "MinIO bucket '{}' exists",
                bucket_name,
            )
        else:
            self.logger.warning(
                "MinIO bucket '{}' does not exist",
                bucket_name,
            )

        return exists

    @retry(max_attempts=3)
    async def list_buckets(self) -> list[str]:
        self.logger.info(
            "Retrieving accessible MinIO buckets"
        )

        buckets = await self._execute(
            "list_buckets",
            self.client.list_buckets,
        )

        names = [bucket.name for bucket in buckets]

        self.logger.success(
            "Retrieved {} MinIO buckets successfully",
            len(names),
        )

        return names

    # ==========================================
    # Object Operations
    # ==========================================

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> None:
        self.logger.info(
            "Uploading local file '{}' to MinIO object '{}/{}'",
            file_path,
            bucket_name,
            object_name,
        )

        await self._execute(
            "upload_file",
            self.client.fupload_object,
            bucket_name,
            object_name,
            file_path,
        )

        self.logger.success(
            "Uploaded file '{}' to '{}/{}' successfully",
            file_path,
            bucket_name,
            object_name,
        )

    async def download_file(
        self,
        bucket_name: str,
        object_name: str,
        destination_path: str,
    ) -> None:
        self.logger.info(
            "Downloading MinIO object '{}/{}' to '{}'",
            bucket_name,
            object_name,
            destination_path,
        )

        await self._execute(
            "download_file",
            self.client.fdownload_object,
            bucket_name,
            object_name,
            destination_path,
        )

        self.logger.success(
            "Downloaded object '{}/{}' to '{}' successfully",
            bucket_name,
            object_name,
            destination_path,
        )

    async def upload_object(self,bucket_name: str,object_name: str,data: BinaryIO,length: int,
    ) -> None:
        self.logger.info(
            "Uploading stream to MinIO object '{}/{}' ({} bytes)",
            bucket_name,
            object_name,
            length,
        )

        await self._execute(
            "upload_object",
            self.client.put_object,bucket_name,object_name,
            data,length,
        )

        self.logger.success(
            "Uploaded {} bytes to '{}/{}' successfully",
            length,
            bucket_name,
            object_name,
        )

    @retry(max_attempts=3)
    async def download_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bytes:
        self.logger.info(
            "Retrieving MinIO object '{}/{}'",
            bucket_name,
            object_name,
        )

        def read_object() -> bytes:
            response = self.client.get_object(
                bucket_name,
                object_name,
            )

            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        data = await self._execute(
            "download_object",
            read_object,
        )

        self.logger.success(
            "Retrieved object '{}/{}' successfully ({} bytes)",
            bucket_name,
            object_name,
            len(data),
        )

        return data

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        self.logger.info(
            "Deleting MinIO object '{}/{}'",
            bucket_name,
            object_name,
        )

        await self._execute(
            "delete_object",
            self.client.remove_object,
            bucket_name,
            object_name,
        )

        self.logger.success(
            "MinIO object '{}/{}' deleted successfully",
            bucket_name,
            object_name,
        )

    @retry(max_attempts=3)
    async def object_exists(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        self.logger.info(
            "Checking existence of MinIO object '{}/{}'",
            bucket_name,
            object_name,
        )

        try:
            await self._execute(
                "object_exists",
                self.client.stat_object,
                bucket_name,
                object_name,
            )

        except S3Error as exc:
            if exc.code in (
                "NoSuchKey",
                "NoSuchObject",
                "NotFound",
            ):
                self.logger.warning(
                    "MinIO object '{}/{}' does not exist",
                    bucket_name,
                    object_name,
                )
                return False

            raise

        self.logger.success(
            "MinIO object '{}/{}' exists",
            bucket_name,
            object_name,
        )
        return True

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = True,
    ) -> AsyncIterator[str]:
        self.logger.info(
            "Listing MinIO objects in bucket '{}' "
            "with prefix='{}', recursive={}",
            bucket_name,
            prefix,
            recursive,
        )

        objects = self.client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=recursive,
        )

        count = 0

        while True:
            batch = await self._execute(
                "list_objects",
                lambda: list(islice(objects, 100)),
            )

            if not batch:
                break

            for obj in batch:
                count += 1
                yield obj.object_name

        self.logger.success(
            "Listed {} objects in MinIO bucket '{}' successfully",
            count,
            bucket_name,
        )

    # ==========================================
    # Metadata
    # ==========================================

    @retry(max_attempts=3)
    async def download_object_metadata(
        self,
        bucket_name: str,
        object_name: str,
    ) -> dict:
        self.logger.info(
            "Retrieving metadata for MinIO object '{}/{}'",
            bucket_name,
            object_name,
        )

        result = await self._execute(
            "download_object_metadata",
            self.client.stat_object,
            bucket_name,
            object_name,
        )

        metadata = {
            "object_name": result.object_name,
            "size": result.size,
            "etag": result.etag,
            "content_type": result.content_type,
            "last_modified": result.last_modified,
            "metadata": result.metadata,
        }

        self.logger.success(
            "Retrieved metadata for MinIO object '{}/{}' "
            "(size={} bytes, content_type={})",
            bucket_name,
            object_name,
            result.size,
            result.content_type,
        )

        return metadata

    # ==========================================
    # Copy / Move
    # ==========================================

    async def copy_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str,
    ) -> None:
        self.logger.info(
            "Copying MinIO object '{}/{}' to '{}/{}'",
            source_bucket,
            source_object,
            destination_bucket,
            destination_object,
        )

        await self._execute(
            "copy_object",
            self.client.copy_object,
            destination_bucket,
            destination_object,
            CopySource(
                source_bucket,
                source_object,
            ),
        )

        self.logger.success(
            "Copied MinIO object '{}/{}' to '{}/{}' successfully",
            source_bucket,
            source_object,
            destination_bucket,
            destination_object,
        )

    async def move_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str,
    ) -> None:
        self.logger.info(
            "Moving MinIO object '{}/{}' to '{}/{}'",
            source_bucket,
            source_object,
            destination_bucket,
            destination_object,
        )

        if (
            source_bucket == destination_bucket
            and source_object == destination_object
        ):
            self.logger.warning(
                "Skipping move: source and destination are identical"
            )
            return

        await self.copy_object(
            source_bucket,
            source_object,
            destination_bucket,
            destination_object,
        )

        await self.delete_object(
            source_bucket,
            source_object,
        )

        self.logger.success(
            "Moved MinIO object '{}/{}' to '{}/{}' successfully",
            source_bucket,
            source_object,
            destination_bucket,
            destination_object,
        )

    # ==========================================
    # Bulk Operations
    # ==========================================

    async def delete_objects(
        self,
        bucket_name: str,
        object_names: list[str],
    ) -> None:
        self.logger.info(
            "Deleting {} objects from MinIO bucket '{}'",
            len(object_names),
            bucket_name,
        )

        if not object_names:
            self.logger.warning(
                "Skipping bulk deletion: no objects supplied "
                "for bucket '{}'",
                bucket_name,
            )
            return

        def delete_many() -> None:
            errors = list(
                self.client.remove_objects(
                    bucket_name,
                    [
                        DeleteObject(name)
                        for name in object_names
                    ],
                )
            )

            if errors:
                raise RuntimeError(
                    f"Failed to delete objects: "
                    f"{[(e.object_name, e.message) for e in errors]}"
                )

        await self._execute(
            "delete_objects",
            delete_many,
        )

        self.logger.success(
            "Deleted {} objects from MinIO bucket '{}' successfully",
            len(object_names),
            bucket_name,
        )

    # ==========================================
    # Lifecycle
    # ==========================================

    async def close(self) -> None:
        # Borrowed connection: application-scoped manager owns the HTTP pool.
        # Do not disconnect shared MinIO clients from request-level controllers.
        self.logger.debug("MinIO controller closed; shared connection remains owned by manager")
