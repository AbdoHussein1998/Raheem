"""Register original PDF documents without starting a Temporal workflow.

Filename SHA-256 uniqueness remains the business rule unless `force=True`.
The database row is reserved before MinIO is touched; individual PostgresDML
writes commit alone.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from io import BytesIO

from fastapi import UploadFile
from loguru import logger as default_logger
from fastapi.responses import JSONResponse
from Infrastructure.Databases.Minio import (
    AsyncMinioConnectionManger,
    AsyncMinioController,
)
from fastapi import status
from Infrastructure.Databases.PostgreSQL import (
    PostgresConnectionManager,
    PostgresDML,
)

#########
# Constants
#########

SCHEMA = "processing_catalog"
TABLE = "pdf_index"
DEFAULT_MAX_UPLOAD_BYTES = 60 * 1024 * 1024
PDF_MAGIC_HEADER = b"%PDF-"
VALID_FINAL_STATES = {"ready", "failed"}


#########
# Exceptions
#########

class InvalidPDFError(ValueError):
    pass


class PDFTooLargeError(ValueError):
    pass

class PDFAlreadyExistsError(ValueError):
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"A PDF with this filename already exists: {filename}")


class PDFNotFound(Exception):
    def __init__(self,document_id):
        self.document_id=document_id
        super().__init__(f"A Pdf with this ID {self.document_id} is Not Exist")

class PDFNotReady(Exception):
    def __init__(self,document_id):
        self.document_id=document_id
        super().__init__(f"A Pdf with this ID {self.document_id} is Not Ready")



#########
# Registration Service
#########

class PDFRegistration:
    #########
    # Initialization & Lifecycle
    #########

    def __init__(
        self,
        lake_connection: AsyncMinioConnectionManger,
        postgres_connection: PostgresConnectionManager,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        logger=None,
    ):
        self.lake_connection = lake_connection
        self.postgres_connection = postgres_connection
        self.max_upload_bytes = max_upload_bytes
        self.logger = logger or default_logger

        self.lake_controller: AsyncMinioController | None = None
        self.post_dml: PostgresDML | None = None

    @classmethod
    async def init_service(
        cls,
        lake_connection: AsyncMinioConnectionManger,
        postgres_connection: PostgresConnectionManager,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        logger=None,
    ) -> PDFRegistration:
        instance = cls(
            lake_connection=lake_connection,
            postgres_connection=postgres_connection,
            max_upload_bytes=max_upload_bytes,
            logger=logger,
        )
        instance.lake_controller = await AsyncMinioController.init_class(
            connection_manager=lake_connection,
            logger=instance.logger,
        )
        instance.post_dml = await PostgresDML.init_class(
            manager=postgres_connection,
            logger=instance.logger,
            schema=SCHEMA,
        )
        return instance

    def _ensure_initialized(self) -> None:
        if self.lake_controller is None or self.post_dml is None:
            raise RuntimeError(
                "PDFRegistration is not initialized. Use `await PDFRegistration.init_service(...)`."
            )

    #########
    # Public Pipeline
    #########

    async def run(
        self,
        file: UploadFile,
        bucket_name: str,
        ocr: bool,
        force: bool = False,
    ) -> dict:
        self._ensure_initialized()
        if not bucket_name:
            raise ValueError("bucket_name is required")

        try:
            filename = self._normalized_filename(file.filename)
            document_id = self._hashed_filename(filename)
            object_key = self._build_object_key(document_id, ocr)
            contents = await self._validate_and_read(file)

            await self._reserve_document(
                document_id=document_id,
                filename=filename,
                bucket_name=bucket_name,
                object_key=object_key,
                ocr=ocr,
                force=force,
            )

            try:
                await self._upload_to_lake(bucket_name, object_key, contents)
                await self._set_registration_status(document_id, "ready")
            except Exception:
                await self._mark_failed_safely(document_id)
                raise
        finally:
            await file.close()

        self.logger.info(
            "Registered PDF {} at {}/{} (force={})",
            document_id,
            bucket_name,
            object_key,
            force,
        )
        return {
            "document_id": document_id,
            "filename": filename,
            "bucket_name":bucket_name,
            "object_key": object_key,
            "status": "registered",
        }

    #########
    # Validation & File Helpers
    #########

    async def _validate_and_read(self, file: UploadFile) -> bytes:
        await file.seek(0)
        contents = await file.read(self.max_upload_bytes + 1)

        if len(contents) > self.max_upload_bytes:
            raise PDFTooLargeError("PDF exceeds the configured maximum upload size")
        if not contents.startswith(PDF_MAGIC_HEADER):
            raise InvalidPDFError("File does not contain a valid PDF header")

        return contents

    @staticmethod
    def _normalized_filename(filename: str | None) -> str:
        name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not name or not name.lower().endswith(".pdf"):
            raise InvalidPDFError("File name must end with .pdf")
        return name

    @staticmethod
    def _hashed_filename(filename: str) -> str:
        return hashlib.sha256(filename.strip().lower().encode("utf-8")).hexdigest()

    @staticmethod
    def _build_object_key(document_id: str, ocr: bool) -> str:
        ocr_folder = "ocr_required" if ocr else "ocr_not_required"
        return f"uploads/{ocr_folder}/{document_id}.pdf"

    #########
    # Database Operations
    #########

    async def _reserve_document(
        self,
        document_id: str,
        filename: str,
        bucket_name: str,
        object_key: str,
        ocr: bool,
        force: bool,
    ) -> None:
        record = {
            "hashed_name": document_id,
            "file_name": filename,
            "bucket_name": bucket_name,
            "object_key": object_key,
            "ocr_required": ocr,
            "registration_status": "uploading",
        }

        # Atomic single-row reservation. A concurrent duplicate cannot reach MinIO.
        reserved = await self.post_dml.insert_into_table(
            table_name=TABLE,
            schema=SCHEMA,
            data=record,
            on_conflict="do_nothing",
        )
        if reserved == 1:
            return

        if not force:
            raise PDFAlreadyExistsError(filename)

        # Force re-registration: reset existing row back to "uploading".
        updated = await self.post_dml.update_table(
            table_name=TABLE,
            schema=SCHEMA,
            updates={
                "file_name": filename,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "ocr_required": ocr,
                "registration_status": "uploading",
                "updated_at": datetime.now(timezone.utc),
            },
            conditions={"hashed_name": document_id},
        )
        if updated != 1:
            raise RuntimeError(f"Failed to force-reserve existing PDF: {document_id}")

    async def _set_registration_status(self, document_id: str, state: str) -> None:
        if state not in VALID_FINAL_STATES:
            raise ValueError(f"Unsupported registration state: {state}")

        updated = await self.post_dml.update_table(
            table_name=TABLE,
            schema=SCHEMA,
            updates={
                "registration_status": state,
                "updated_at": datetime.now(timezone.utc),
            },
            conditions={
                "hashed_name": document_id,
                "registration_status": "uploading",
            },
        )
        if updated != 1:
            raise RuntimeError("PDF registration is not in uploading state")

    async def _mark_failed_safely(self, document_id: str) -> None:
        try:
            await self._set_registration_status(document_id, "failed")
        except Exception:
            self.logger.exception("Unable to mark registration failed: {}", document_id)

    #########
    # Object Storage Operations
    #########

    async def _upload_to_lake(
        self,
        bucket_name: str,
        object_key: str,
        contents: bytes,
    ) -> None:
        if not await self.lake_controller.bucket_exists(bucket_name):
            await self.lake_controller.create_bucket(bucket_name)

        await self.lake_controller.upload_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=BytesIO(contents),
            length=len(contents),
        )

    #########
    # ExtraFynction 
    # Note: may be transffred out later
    #########
    async def get_file_row(self,document_id:str):
        rows=await self.post_dml.get_table_data(
                table_name="pdf_index",
                schema="processing_catalog",
                conditions={"hashed_name": document_id},
                limit=1,
            )



        if not rows:
            raise PDFNotFound(document_id=document_id)
        if rows[0].registration_status not in ("ready", "completed"):
            raise PDFNotReady(document_id=document_id)
        return rows