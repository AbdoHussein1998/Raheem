"""Register original PDF documents without starting a Temporal workflow.

Filename SHA-256 uniqueness remains the business rule. The database row is
reserved before MinIO is touched; individual PostgresDML writes commit alone.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from io import BytesIO

from fastapi import UploadFile
from loguru import logger as default_logger

from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML

SCHEMA = "processing_catalog"
TABLE = "pdf_index"


class InvalidPDFError(ValueError):
    pass


class PDFTooLargeError(ValueError):
    pass


class PDFAlreadyExistsError(ValueError):
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"A PDF with this filename already exists: {filename}")



class PDFRegistration:
    def __init__(
        self, *, lake_controller: AsyncMinioController,
        postgres_dml: PostgresDML, max_upload_bytes: int = 60 * 1024 * 1024,
        logger=None,
    ):
        self.lake = lake_controller
        self.postgres = postgres_dml
        self.max_upload_bytes = max_upload_bytes
        self.logger = logger or default_logger

    async def run(self, file: UploadFile, bucket_name: str,ocr:bool) -> dict:
        filename = self._normalized_filename(file.filename)
        if not bucket_name:
            raise ValueError("bucket_name is required")
        document_id = self._hashed_filename(filename)
        ocr_required = "ocr_required" if ocr else "ocr_not_required"
        object_key = f"uploads/{ocr_required}/{document_id}.pdf"

        # The endpoint first calls ValidationService.validate_pdf(...).
        # Here we still validate the actual bytes and enforce the upload limit.
        await file.seek(0)
        contents = await file.read(self.max_upload_bytes + 1)
        if len(contents) > self.max_upload_bytes:
            raise PDFTooLargeError("PDF exceeds the configured maximum upload size")
        if not contents.startswith(b"%PDF-"):
            raise InvalidPDFError("File does not contain a valid PDF header")

        # Atomic single-row reservation. A concurrent duplicate cannot reach MinIO.
        reserved = await self.postgres.insert_into_table(
            table_name=TABLE, schema=SCHEMA,
            data={
                "hashed_name": document_id,
                "file_name": filename,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "ocr_required": ocr,
                "registration_status": "uploading",
            },
            on_conflict="do_nothing",
        )
        if reserved != 1:
            raise PDFAlreadyExistsError(filename)

        try:
            if not await self.lake.bucket_exists(bucket_name):
                await self.lake.create_bucket(bucket_name)
            await self.lake.upload_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=BytesIO(contents),
                length=len(contents),
            )
            await self._set_registration_status(document_id, "ready")
        except Exception:
            # Leave the reservation in place, preventing later overwrite.
            # Administrator can reconcile an interrupted registration.
            try:
                await self._set_registration_status(document_id, "failed")
            except Exception:
                self.logger.exception("Unable to mark registration failed: {}", document_id)
            raise
        finally:
            await file.close()

        self.logger.info("Registered PDF {} at {}/{}", document_id, bucket_name, object_key)
        return {
            "document_id": document_id,
            "filename": filename,
            "object_key": object_key,
            "status": "registered",
        }

    async def _set_registration_status(self, document_id: str, state: str) -> None:
        if state not in {"ready", "failed"}:
            raise ValueError("Unsupported registration state")
        updated = await self.postgres.update_table(
            table_name=TABLE,
            schema=SCHEMA,
            updates={"registration_status": state, "updated_at": datetime.now(timezone.utc)},
            conditions={"hashed_name": document_id, "registration_status": "uploading"},
        )
        if updated != 1:
            raise RuntimeError("PDF registration is not in uploading state")




        
    def _normalized_filename(self, filename: str | None) -> str:
        name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not name or not name.lower().endswith(".pdf"):
            raise InvalidPDFError("File name must end with .pdf")
        return name


    def _hashed_filename(self, filename: str) -> str:
        return hashlib.sha256(filename.strip().lower().encode("utf-8")).hexdigest()
