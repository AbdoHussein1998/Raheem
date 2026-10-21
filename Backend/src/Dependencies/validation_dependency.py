"""Request-scoped access-token verification."""
from fastapi import Depends, HTTPException, Request, status

from Api.ApiConfiguration.api_services import ApplicationServices
from Services.Services.validation_service import ValidationService
from .app_dependency import get_app_services


async def get_validation_service(
    services: ApplicationServices = Depends(get_app_services),
) -> ValidationService:
    return await ValidationService.init_service(
        logger=services.logger_manager.get_logger("ValidationService")
    )
