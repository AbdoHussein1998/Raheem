
import asyncio

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from loguru import logger as default_logger

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import (
    DocumentStream,
    InputFormat,
)
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption
from docling.datamodel.document import ConversionStatus
from docling_core.types.doc import DoclingDocument
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController

class ParsePDFBooks:

    def __init__(self, logger=None,lake_controller: AsyncMinioController | None = None):
        self.logger = logger or default_logger
        self.converter: DocumentConverter | None = None
        self.lake_controller = lake_controller

    # ==========================================
    # Initialization
    # ==========================================

    @classmethod
    async def init_service(
        cls,
        lake_controller: AsyncMinioController,
        logger=None,
        using_ocr: bool = False, ) -> "ParsePDFBooks":

        log = logger or default_logger

        log.info(
            "Initializing ParseEasyBooks service (OCR={})",
            using_ocr,
        )

        instance = cls(logger=log, lake_controller=lake_controller)

        await instance.prepare_converter(
            using_ocr=using_ocr,
        )

        log.success(
            "ParseEasyBooks service initialized successfully"
        )

        return instance

    # ==========================================
    # Converter Configuration
    # ==========================================

    async def prepare_converter(
        self,
        using_ocr: bool = False,
    ) -> None:

        self.logger.info(
            "Preparing Docling PDF converter (OCR={})",
            using_ocr,
        )

        try:
            pipeline_options = PdfPipelineOptions(
                do_ocr=using_ocr,
                force_backend_text=not using_ocr,
            )

            self.converter = await asyncio.to_thread(
                DocumentConverter,
                allowed_formats=[InputFormat.PDF],
                format_options={InputFormat.PDF:
                                 PdfFormatOption(pipeline_options=pipeline_options)},
            )

            self.logger.success(
                "Docling PDF converter prepared successfully"
            )

        except Exception:
            self.logger.exception(
                "Failed to prepare Docling PDF converter"
            )
            raise

    # ==========================================
    # Read Uploaded File
    # ==========================================

    async def read(
        self,
        file: UploadFile,
    ) -> bytes:

        filename = file.filename or "document.pdf"

        self.logger.info(
            "Reading uploaded PDF '{}'",
            filename,
        )

        try:
            contents = await file.read()

            if not contents:
                raise ValueError(
                    f"Uploaded file '{filename}' is empty"
                )

            if not contents.startswith(b"%PDF-"):
                raise ValueError(
                    f"Uploaded file '{filename}' is not a valid PDF header"
                )

            self.logger.success(
                "PDF '{}' read successfully ({} bytes)",
                filename,
                len(contents),
            )

            return contents

        except Exception:
            self.logger.exception(
                "Failed to read uploaded PDF '{}'",
                filename,
            )
            raise

    # ==========================================
    # Parse PDF
    # ==========================================

    async def parse(
        self,
        contents: bytes,
        filename: str = "document.pdf",
    ) -> DoclingDocument:

        if self.converter is None:
            raise RuntimeError(
                "Docling converter is not initialized"
            )

        self.logger.info(
            "Starting PDF parsing for '{}'",
            filename,
        )

        try:
            if not contents:
                raise ValueError(
                    "Cannot parse empty PDF contents"
                )

            stream = DocumentStream(
                name=filename,
                stream=BytesIO(contents),
            )

            result = await asyncio.to_thread(
                self.converter.convert,
                stream,
            )

            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(
                    f"PDF conversion was not fully successful: "
                    f"{result.status}"
                )

            document = result.document

            self.logger.success(
                "PDF '{}' parsed successfully",
                filename,
            )

            return document

        except Exception:
            self.logger.exception(
                "Failed to parse PDF '{}'",
                filename,
            )
            raise



    async def push(
        self, bucket_name: str, file_name: str, file_content: DoclingDocument
    ) -> str:
        """Store the extracted text as Markdown using MinIO's stream API."""
        if self.lake_controller is None:
            raise RuntimeError("Data lake controller is not initialized")
        if not bucket_name:
            raise ValueError("bucket_name is required")

        object_name = f"{Path(file_name).stem}.md"
        markdown = file_content.export_to_markdown()
        encoded = markdown.encode("utf-8")

        try:
            await self.lake_controller.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(encoded),
                length=len(encoded),
            )
            self.logger.success(
                "File '{}' uploaded to bucket '{}'", object_name, bucket_name
            )
            return object_name
        except Exception:
            self.logger.exception(
                "Failed to upload file '{}' to bucket '{}'", object_name, bucket_name
            )
            raise

    async def run(self, file: UploadFile, bucket_name: str) -> dict:
        filename = file.filename or "document.pdf"
        try:
            contents = await self.read(file)
            document = await self.parse(contents, filename=filename)
            object_name = await self.push(bucket_name, filename, document)
            return {
                "filename": filename,
                "object_name": object_name,
                "bucket_name": bucket_name,
                "size": len(contents),
                "message": "PDF parsed and uploaded successfully",
            }
        except Exception:
            self.logger.exception("Failed to process PDF '{}'", filename)
            # Raise the original error, rather than returning an Exception as data.
            raise
