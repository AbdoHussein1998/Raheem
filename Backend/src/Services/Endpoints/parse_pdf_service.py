"""HTTP-side PDF validation and upload using the injected API-owned MinIO manager.

This service intentionally does not import Docling or create a MinIO connection.
Connection lifecycle belongs to FastAPI ApplicationServices.
"""
from __future__ import annotations

from io import BytesIO
from uuid import uuid4
import hashlib
import hashlib

from fastapi import HTTPException, status



from fastapi import UploadFile
from loguru import logger as default_logger
from pathlib import PurePosixPath
from fastapi import HTTPException 
from fastapi.responses import JSONResponse
from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Infrastructure.Databases.PostgreSQL.async_connection import PostgresConnectionManager
from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML


class InvalidPDFError(ValueError):
    """Invalid file name, empty file, or missing PDF header."""


class PDFTooLargeError(ValueError):
    """Upload exceeds the permitted byte limit."""


class ParsePDFBooks:
    """Validate and stage an uploaded PDF; return its MinIO object key."""

    def __init__(
        self,
        lake_connection: AsyncMinioConnectionManger,
        sql_connection:PostgresConnectionManager,
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
        self.sql_connection=sql_connection
        self.lake_controller : AsyncMinioController=None
        self.dml:PostgresDML=None
    @classmethod
    async def init_service(
        cls,
        lake_connection: AsyncMinioConnectionManger,
        sql_connection:PostgresConnectionManager,
        max_upload_bytes: int = 25 * 1024 * 1024,
        logger=None,
    ) -> "ParsePDFBooks":
        """Initialize the service's dependent controllers."""
        log = logger or default_logger
        log.info("Initializing PDF parser service")


        # Inject the initialized controller back into the service
        # for use in the `run` method
        instance = cls(
            lake_connection=lake_connection,
            max_upload_bytes=max_upload_bytes,
            sql_connection=sql_connection,
            logger=log,
        )

        instance.lake_controller =await AsyncMinioController.init_class(
            connection_manager=lake_connection,
            logger=log,)
        instance.dml =await PostgresDML.init_class(
            manager=sql_connection,
            logger=log,)

        log.success("PDF parser service initialization completed")
        return instance



    async def __read_pdf(self, file: UploadFile) -> bytes:
        await file.seek(0)
        return await file.read()



    # ==========================================
    # Run The Pipeline
    # ==========================================

    
    async def upload_to_datalake(self, file: UploadFile, bucket_name: str) -> str:
        if not bucket_name:
            raise ValueError("bucket_name is required")

        pdf_bytes = await self.__read_pdf(file)

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


    async def register_file(self, file_name: str, object_key: str) -> bool:
        """
        Register file metadata and initialize PDF processing status.

        Returns:
            bool: True if both insertions succeed, otherwise False.
        """

        hashed_name = hashlib.sha256(
            file_name.lower().strip().encode("utf-8")
        ).hexdigest()

        self.logger.info(
            "Starting file registration | file_name=%s | hashed_name=%s",
            file_name,
            hashed_name,
        )

        files_main = {
            "file_name": file_name,
            "object_key": object_key,
            "hashed_name": hashed_name,
        }

        pdfs_progress = {
            "hashed_name": hashed_name,
            "status": "pending",
        }

        files_main_success = False
        pdfs_progress_success = False

        # Process 1: Insert into files_main.
        try:
            files_main_success = await self.dml.insert_into_table(
                table_name="files_main",
                schema="processing_catalog",
                data=files_main,
            )

        except Exception as exc:
            self.logger.error(
                "Failed to insert file metadata | file_name=%s | error=%s",
                file_name,
                str(exc),
            )

        if not files_main_success:
            self.logger.error(
                "File metadata insertion failed | table=files_main | "
                "file_name=%s | hashed_name=%s",
                file_name,
                hashed_name,
            )

        
        # Process 2: Insert into pdfs_progress.
        try:
            pdfs_progress_success = await self.dml.insert_into_table(
                table_name="pdfs_progress",
                schema="processing_catalog",
                data=pdfs_progress,
            )

            if pdfs_progress_success:
                self.logger.success(
                    "PDF progress initialized successfully | "
                    "table=pdfs_progress | file_name=%s | "
                    "hashed_name=%s | status=pending",
                    file_name,
                    hashed_name,
                )

        except Exception:
            pdfs_progress_success = False

        return files_main_success or pdfs_progress_success








