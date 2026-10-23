"""PDF conversion pipeline invoked within the Celery worker process.

The task constructs/injects its worker-owned MinIO controller. This service owns
Docling configuration, download, conversion and uploading the Markdown result.
"""
from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import PurePosixPath

from loguru import logger as default_logger
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import DocumentStream
from docling.datamodel.document import ConversionStatus


class EnqueueParsePDF:
    """Execute (not enqueue) a PDF processing job; name kept by design request."""

    def __init__(
        self,
        lake_controller: AsyncMinioController,
        logger=None,
    ) -> None:
        self.logger = logger or default_logger
        self.lake_controller:AsyncMinioController = lake_controller
        self.converter = None

    @classmethod
    async def init_service(
        cls,
        lake_controller: AsyncMinioController,
        logger=None,
    ) -> "EnqueueParsePDF":
        return cls(lake_controller=lake_controller, logger=logger)

    # ==========================================
    # Prepare Converter
    # ==========================================

    async def prepare_converter(self, using_ocr: bool = False) -> None:
        """Only called from the Celery processing path, never from FastAPI."""
        
        pipeline_options = PdfPipelineOptions(
            do_ocr=using_ocr,
            force_backend_text=not using_ocr,
        )
        self.converter = await asyncio.to_thread(
            DocumentConverter,
            show_progress=True,
            allowed_formats=[InputFormat.PDF],

            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )
        self.logger.info("Docling initialized, OCR={}", using_ocr)
        return self.converter

    # ==========================================
    # Download File
    # ==========================================

    async def download(self, bucket_name: str, object_key: str) -> bytes:
        try:
            # it is already transformed into bytes and saved there
            pdf_object = await self.lake_controller.download_object(
                bucket_name=bucket_name,
                object_name=object_key,
            )
            return pdf_object
        except Exception as e :
            self.logger.error(f"Error: Downloading the pdf {e} ")

    # ==========================================
    # Parsing
    # ==========================================

    async def parse(self, pdf_object: bytes, filename: str,converter:DocumentConverter) -> str:
        
        if not isinstance(pdf_object,BytesIO):
            stream = BytesIO(pdf_object)
        else :
            stream=pdf_object
        try:

            source = DocumentStream(name=filename, stream=stream)
            result = await asyncio.to_thread(converter.convert, source)

        finally:
            stream.close()
        if result.status != ConversionStatus.SUCCESS:
            raise RuntimeError(f"Docling conversion failed: {result.status}")

        return result.document.export_to_markdown()

    # ==========================================
    # Upload Converted File
    # ==========================================

    async def upload_converted(self,markdown_file: str,bucket_name: str,
                               output_key: str,) -> None:
        data = markdown_file.encode("utf-8")
        await self.lake_controller.upload_object(
            bucket_name=bucket_name,
            object_name=output_key,
            data=BytesIO(data),
            length=len(data),
        )

    # ==========================================
    # RUN The Pipeline
    # ==========================================

    async def run(
        self,
        bucket_name: str,
        object_key: str,
        using_ocr: bool = False,
    ) -> dict:
        if not bucket_name or not object_key:
            raise ValueError("bucket_name and object_key are required")
        if not isinstance(using_ocr, bool):
            raise TypeError("using_ocr must be a boolean")
        if PurePosixPath(object_key).suffix.lower() != ".pdf":
            raise ValueError("Source object must have a .pdf suffix")

        # Input can be acquired before allocating the heavy Docling converter.
        pdf_bytes = await self.download(bucket_name, object_key)
        converter =await self.prepare_converter(using_ocr=using_ocr)
        markdown_file = await self.parse(pdf_object=pdf_bytes,filename=PurePosixPath(object_key).name,converter=converter)
        # OCR and non-OCR results do not overwrite one another.
        output_key = f"processed/{PurePosixPath(object_key).stem}.md"
        await self.upload_converted(markdown_file=markdown_file,bucket_name=bucket_name,output_key=output_key,)


        self.logger.success("Converted {}/{} -> {}", bucket_name, object_key, output_key)
        return {
                    "status": "completed",
                    "source_bucket": bucket_name,
                    "source_key": object_key,
                    "result_bucket": bucket_name,
                    "result_key": output_key,
                    "using_ocr": using_ocr,
                }



  