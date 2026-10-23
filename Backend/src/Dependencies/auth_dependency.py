"""Request-scoped authentication adapters; shared pool stays app-scoped."""
from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, status

from Services.Endpoints.auth_service import AuthService
from Infrastructure.Authentication.Providers.google_oauth_provider import GoogleOAuthHandler
from Infrastructure.Authentication.Providers.jwt_services_provider import JWTHandler
from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from Api.ApiConfiguration.api_services import ApplicationServices
from .app_dependency import get_app_services


async def get_auth_service(
    app_services: ApplicationServices = Depends(get_app_services),
) -> AsyncIterator[AuthService]:
    postgres_connection = app_services.postgres.omni_postgres_conn
    if postgres_connection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL is not ready",
        )

    logger = app_services.logger_manager.get_logger("AuthService")
    google_auth_handler = await GoogleOAuthHandler.init_class(logger=logger)
    jwt_handler = await JWTHandler.init_class(logger=logger)
    postgres = await PostgresDML.init_class(manager=postgres_connection, logger=logger)
    try:
        service = await AuthService.init_service(
            google_auth_handler=google_auth_handler,
            jwt_handler=jwt_handler,
            postgres=postgres,
            logger=logger,
        )
        yield service
    finally:
        await postgres.close()
