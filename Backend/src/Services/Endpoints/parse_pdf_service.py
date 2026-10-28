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



    async def register_file(self, file_name: str, object_key: str) -> bool:
        """
        Register a file in files_main and initialize its processing status
        in pdfs_progress.

        Returns:
            bool: True if both database insertions succeed.

        Raises:
            HTTPException: If registration fails.
        """

        

        self.logger.info(
            "Starting file registration | file_name=%s | object_key=%s",
            file_name,
            object_key,
        )

        try:
            # Generate a consistent hash for file identification.
            hashed_name = hashlib.sha256(
                file_name.lower().strip().encode("utf-8")
            ).hexdigest()

            self.logger.debug(
                "Generated file hash | file_name=%s | hashed_name=%s",
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

            # Step 1: Register file metadata.
            self.logger.info(
                "Inserting file metadata | table=processing_catalog.files_main "
                "| hashed_name=%s",
                hashed_name,
            )

            case_1 = await self.dml.insert_into_table(
                table_name="files_main",
                schema="processing_catalog",
                data=files_main,
            )

            if not case_1:
                self.logger.error(
                    "File metadata insertion failed | table=files_main "
                    "| file_name=%s | hashed_name=%s",
                    file_name,
                    hashed_name,
                )
                raise RuntimeError("Failed to insert file metadata.")

            self.logger.success(
                "File metadata inserted successfully | table=files_main "
                "| file_name=%s | hashed_name=%s",
                file_name,
                hashed_name,
            )

            # Step 2: Initialize PDF processing status.
            self.logger.info(
                "Initializing PDF processing status | table=pdfs_progress "
                "| status=pending | hashed_name=%s",
                hashed_name,
            )

            case_2 = await self.dml.insert_into_table(
                table_name="pdfs_progress",
                schema="processing_catalog",
                data=pdfs_progress,
            )

            if not case_2:
                self.logger.error(
                    "PDF progress initialization failed | table=pdfs_progress "
                    "| file_name=%s | hashed_name=%s",
                    file_name,
                    hashed_name,
                )
                raise RuntimeError("Failed to initialize PDF processing status.")

            self.logger.success(
                "PDF processing status initialized successfully "
                "| table=pdfs_progress | file_name=%s | status=pending",
                file_name,
            )

            self.logger.success(
                "File registration completed successfully | file_name=%s "
                "| object_key=%s | hashed_name=%s",
                file_name,
                object_key,
                hashed_name,
            )

            return True

        except Exception as exc:
            self.logger.exception(
                "File registration failed | file_name=%s | object_key=%s "
                "| error_type=%s | error=%s",
                file_name,
                object_key,
                type(exc).__name__,
                str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register the uploaded file.",
            ) from exc

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




