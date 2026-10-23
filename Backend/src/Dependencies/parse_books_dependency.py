"""Document parser dependencies using the application-owned MinIO connection."""
from fastapi import Depends, HTTPException, status

from Api.ApiConfiguration.api_services import ApplicationServices
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Services.Celery.parse_pdf_enqueu import EnqueueParsePDF
from Services.Endpoints.parse_pdf_service import ParsePDFBooks, InvalidPDFError, PDFTooLargeError
from .app_dependency import get_app_services

async def get_pdf_parser_service(
    app_services: ApplicationServices = Depends(get_app_services),
) -> ParsePDFBooks:
    minio_connection = app_services.minio.omni_minio_conn
    endpoint_service = await ParsePDFBooks.init_service(
        lake_connection=minio_connection
    )
    return endpoint_service


