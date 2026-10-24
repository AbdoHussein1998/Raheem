"""HTTP-side PDF validation and upload using the injected API-owned MinIO manager.

This service intentionally does not import Docling or create a MinIO connection.
Connection lifecycle belongs to FastAPI ApplicationServices.
"""
from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile
from loguru import logger as default_logger
from pathlib import PurePosixPath

from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController


class InvalidPDFError(ValueError):
    """Invalid file name, empty file, or missing PDF header."""


class PDFTooLargeError(ValueError):
    """Upload exceeds the permitted byte limit."""


class ParsePDFBooks:
    """Validate and stage an uploaded PDF; return its MinIO object key."""

    def __init__(
        self,
        lake_connection: AsyncMinioConnectionManger,
        max_upload_bytes: int = 25 * 1024 * 1024,
        logger=None,
    ) -> None:
        if lake_connection.client is None:
            raise RuntimeError("The injected MinIO manager must already be connected")
        if max_upload_bytes <= 0:
            raise ValueError("max_upload_bytes must be positive")

        self.logger = logger or default_logger
        self.max_upload_bytes = max_upload_bytes
        self.lake_connection = lake_connection  # Borrowed; NEVER disconnected here.
        self.lake_controller = AsyncMinioController(
            connection_manager=lake_connection,
            logger=self.logger,
        )

    @classmethod
    async def init_service(
        cls,
        lake_connection: AsyncMinioConnectionManger,
        max_upload_bytes: int = 25 * 1024 * 1024,
        logger=None,
    ) -> "ParsePDFBooks":
        return cls(
            lake_connection=lake_connection,
            max_upload_bytes=max_upload_bytes,
            logger=logger,
        )



    async def read_pdf(self, file: UploadFile) -> bytes:
        await file.seek(0)
        return await file.read()





    # ==========================================
    # Run The Pipeline
    # ==========================================

    
    async def run(self, file: UploadFile, bucket_name: str) -> str:
        if not bucket_name:
            raise ValueError("bucket_name is required")

        pdf_bytes = await self.read_pdf(file)

        # Keep original filename without appending another .pdf
        filename = PurePosixPath(file.filename).name
        object_key = f"uploads/{filename}"
        exists = await self.lake_controller.bucket_exists(bucket_name)
        if not exists:
            await self.lake_controller.create_bucket(bucket_name)

        await self.lake_controller.upload_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=BytesIO(pdf_bytes),
            length=len(pdf_bytes),
        )

        self.logger.info(
            "PDF uploaded to MinIO: {}/{}",
            bucket_name,
            object_key,
        )

        return object_key




