from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from io import BytesIO

from temporalio import activity
from temporalio.exceptions import ApplicationError

from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController

from Schemas.pdf_models import (
    PDFIndexDownloadRequest,
    PDFObjectKeyRequest,
    PDFUpdateIndexRequest,
)

from docling.datamodel.base_models import ConversionStatus, DocumentStream, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

SCHEMA = "processing_catalog"
TABLE = "pdf_index"


class PDFProcessingActivities:
    def __init__(
        self,
        postgres_dml: PostgresDML,
        lake_controller: AsyncMinioController,
        logger,
        max_concurrent_conversions: int = 1,
    ):
        if max_concurrent_conversions < 1:
            raise ValueError("max_concurrent_conversions must be positive")

        self.postgres = postgres_dml
        self.lake = lake_controller
        self.logger = logger
        self.conversion_limit = asyncio.Semaphore(max_concurrent_conversions)
        self._converters: dict[bool, DocumentConverter] = {}
        self._converter_lock = threading.Lock()

    # ==========================================================
    # 1. ACTIVITY: GET PDF INDEX FROM POSTGRESQL
    # ==========================================================

    @activity.defn(name="pdf_get_index")
    async def get_pdf_index(
        self,
        request: PDFIndexDownloadRequest,
    ) -> PDFObjectKeyRequest:
        rows = await self.postgres.get_table_data(
            table_name=TABLE,
            schema=SCHEMA,
            conditions={"hashed_name": request.document_id},
            limit=1,
        )

        if not rows:
            raise ApplicationError(
                "PDF document is not registered",
                type="DocumentNotFound",
                non_retryable=True,
            )

        row = rows[0]

        if row.registration_status not in ("ready", "completed"):
            raise ApplicationError(
                f"PDF is not ready: {row.registration_status}",
                type="DocumentNotReady",
                non_retryable=True,
            )

        if not row.bucket_name or not row.object_key:
            raise ApplicationError(
                "PDF storage metadata is missing",
                type="MissingObjectReference",
                non_retryable=True,
            )

        self.logger.info(
            "Resolved PDF document={} OCR={} object={}/{}",
            row.hashed_name,
            row.ocr_required,
            row.bucket_name,
            row.object_key,
        )

        return PDFObjectKeyRequest(
            document_id=row.hashed_name,
            using_ocr=row.ocr_required,
            bucket_name=row.bucket_name,
            object_key=row.object_key,
        )

    # ==========================================================
    # 2. INTERNAL HELPERS (SEPARATION OF CONCERNS IN MEMORY)
    # ==========================================================

    def _get_or_create_converter(self, using_ocr: bool) -> DocumentConverter:
        with self._converter_lock:
            if using_ocr not in self._converters:
                self.logger.info(
                    "Initializing Docling DocumentConverter (using_ocr={})...",
                    using_ocr,
                )
                pipeline_options = PdfPipelineOptions(
                    do_ocr=using_ocr,
                    force_backend_text=not using_ocr,
                )
                self._converters[using_ocr] = DocumentConverter(
                    allowed_formats=[InputFormat.PDF],
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_options=pipeline_options,
                        ),
                    },
                )
            return self._converters[using_ocr]

    def _run_docling_sync(
        self,
        pdf_content: bytes,
        document_id: str,
        using_ocr: bool,
    ) -> str:
        """Runs entirely inside the worker thread (off the asyncio loop)."""
        converter = self._get_or_create_converter(using_ocr)
        with BytesIO(pdf_content) as stream:
            source = DocumentStream(name=f"{document_id}.pdf", stream=stream)
            result = converter.convert(source)

        if result.status != ConversionStatus.SUCCESS:
            raise RuntimeError(f"Docling conversion failed: {result.status}")

        return result.document.export_to_markdown()

    async def _download_and_validate_pdf(
        self,
        request: PDFObjectKeyRequest,
    ) -> bytes:
        """Step 2a: Downloads PDF bytes into memory and validates header."""
        pdf_content = await self.lake.download_object(
            bucket_name=request.bucket_name,
            object_name=request.object_key,
        )

        if not pdf_content.startswith(b"%PDF-"):
            raise ApplicationError(
                "Invalid PDF header",
                type="InvalidPDF",
                non_retryable=True,
            )

        self.logger.info(
            "Downloaded & validated PDF document={} bytes={}",
            request.document_id,
            len(pdf_content),
        )
        return pdf_content

    async def _convert_pdf_in_memory(
        self,
        pdf_content: bytes,
        document_id: str,
        using_ocr: bool,
    ) -> str:
        """Step 2b: Acquires semaphore, heartbeats, and converts bytes -> Markdown."""
        while True:
            activity.heartbeat("waiting-for-docling-slot")
            try:
                await asyncio.wait_for(self.conversion_limit.acquire(), timeout=20)
                break
            except asyncio.TimeoutError:
                continue

        conversion_task = None
        try:
            self.logger.info(
                "Starting Docling conversion for document={}...",
                document_id,
            )
            conversion_task = asyncio.create_task(
                asyncio.to_thread(
                    self._run_docling_sync,
                    pdf_content,
                    document_id,
                    using_ocr,
                )
            )

            while not conversion_task.done():
                activity.heartbeat("docling-running")
                await asyncio.wait({conversion_task}, timeout=10)

            markdown_content = conversion_task.result()
            self.logger.info(
                "Docling conversion finished for document={}",
                document_id,
            )
        finally:
            try:
                if conversion_task is not None:
                    while not conversion_task.done():
                        try:
                            await asyncio.wait({conversion_task}, timeout=10)
                        except asyncio.CancelledError:
                            continue
            finally:
                self.conversion_limit.release()

        if not markdown_content.strip():
            raise ApplicationError(
                "Docling returned empty Markdown",
                type="EmptyMarkdown",
                non_retryable=True,
            )

        return markdown_content

    async def _upload_markdown(
        self,
        bucket_name: str,
        document_id: str,
        using_ocr: bool,
        markdown_content: str,
    ) -> str:
        """Step 2c: Uploads Markdown directly to processed/{ocr|no_ocr}/{document_id}.md."""
        markdown_bytes = markdown_content.encode("utf-8")
        ocr_folder = "ocr" if using_ocr else "no_ocr"
        result_object_key = f"processed/{ocr_folder}/{document_id}.md"

        await self.lake.upload_object(
            bucket_name=bucket_name,
            object_name=result_object_key,
            data=BytesIO(markdown_bytes),
            length=len(markdown_bytes),
        )

        self.logger.info(
            "Uploaded Markdown document={} bytes={} key={}",
            document_id,
            len(markdown_bytes),
            result_object_key,
        )
        return result_object_key

    # ==========================================================
    # 3. ACTIVITY: WRAPPER FOR IN-MEMORY DOWNLOAD -> CONVERT -> UPLOAD
    # ==========================================================

    @activity.defn(name="pdf_convert")
    async def convert(
        self,
        request: PDFObjectKeyRequest,
    ) -> PDFUpdateIndexRequest:
        # 1. Download into RAM
        pdf_bytes = await self._download_and_validate_pdf(request)

        # 2. Convert in RAM (freeing pdf_bytes immediately after)
        markdown_text = await self._convert_pdf_in_memory(
            pdf_content=pdf_bytes,
            document_id=request.document_id,
            using_ocr=request.using_ocr,
        )
        del pdf_bytes  # Explicitly release raw PDF bytes before upload

        # 3. Upload Markdown to final MinIO path
        result_object_key = await self._upload_markdown(
            bucket_name=request.bucket_name,
            document_id=request.document_id,
            using_ocr=request.using_ocr,
            markdown_content=markdown_text,
        )

        return PDFUpdateIndexRequest(
            document_id=request.document_id,
            registration_status="completed",
            result_object_key=result_object_key,
        )

    # ==========================================================
    # 4. ACTIVITY: REGISTER CONVERTED MARKDOWN IN POSTGRESQL
    # ==========================================================

    @activity.defn(name="pdf_update_pdf_index")
    async def update_pdf_index(
        self,
        request: PDFUpdateIndexRequest,
    ) -> PDFUpdateIndexRequest:
        if request.registration_status != "completed":
            raise ApplicationError(
                "Only completed conversions may be registered",
                type="InvalidRegistrationStatus",
                non_retryable=True,
            )

        updated = await self.postgres.update_table(
            table_name=TABLE,
            schema=SCHEMA,
            conditions={"hashed_name": request.document_id},
            updates={
                "registration_status": request.registration_status,
                "result_object_key": request.result_object_key,
                "updated_at": datetime.now(timezone.utc),
            },
        )

        if updated != 1:
            raise ApplicationError(
                "PDF record was not updated",
                type="PDFIndexUpdateFailed",
            )

        self.logger.info(
            "Completed PDF processing document={} key={}",
            request.document_id,
            request.result_object_key,
        )

        return request



