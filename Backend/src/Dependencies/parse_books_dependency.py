"""Document parser dependencies using the application-owned MinIO connection."""
from fastapi import Depends, HTTPException, status

from Api.ApiConfiguration.api_services import ApplicationServices
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Services.Celery.parse_pdf_enqueu import EnqueueParsePDF
from Services.Endpoints.parse_pdf_service import ParsePDFBooks, InvalidPDFError, PDFTooLargeError
from .app_dependency import get_app_services
from fastapi import Request

from fastapi import Depends, Request

async def get_pdf_parser_service(request: Request,) -> ParsePDFBooks:
    app_services: ApplicationServices = get_app_services(request)

    minio_connection = app_services.minio.omni_minio_conn
    sql_connection = app_services.postgres.omni_postgres_conn

    endpoint_service = await ParsePDFBooks.init_service(
        lake_connection=minio_connection,
        sql_connection=sql_connection,
    )

    return endpoint_service




