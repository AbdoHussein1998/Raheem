"""Document parser dependencies using the application-owned MinIO connection."""
from fastapi import Depends, HTTPException, status

from Api.ApiConfiguration.api_services import ApplicationServices
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Services.Services.parse_PDF_books import ParsePDFBooks

from .app_dependency import get_app_services




async def get_easy_pdf_parser_service() -> ParsePDFBooks:
    app_services: ApplicationServices =  get_app_services()
    lake_controller: AsyncMinioController = await AsyncMinioController.init_class(connection=app_services.minio_connection,
                                                                             logger=app_services.logger_manager.get_logger("OmniMinioController"))
    serivce=await ParsePDFBooks.init_service(lake_controller=lake_controller,logger=app_services.logger_manager.get_logger("ParseEasyPDFBooks"),using_ocr=False)

    return serivce




async def get_ocr_pdf_parser_service() -> ParsePDFBooks:
    app_services: ApplicationServices =  get_app_services()
    lake_controller: AsyncMinioController = await AsyncMinioController.init_class(connection=app_services.minio_connection,
                                                                             logger=app_services.logger_manager.get_logger("OmniMinioController"))
    serivce=await ParsePDFBooks.init_service(lake_controller=lake_controller,logger=app_services.logger_manager.get_logger("ParseOCRPDFBooks"),using_ocr=True)

    return serivce

