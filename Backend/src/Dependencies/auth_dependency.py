"""Thin composition adapter for request-scoped authentication services."""
from fastapi import Request

from Services.Services.auth_service import AuthService
from Infrastructure.Authentication.Providers.google_oauth_provider import GoogleOAuthHandler
from Infrastructure.Authentication.Providers.jwt_services_provider import JWTHandler
from Backend.src.Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from .app_dependency import get_app_services


async def get_auth_service(request: Request) -> AuthService:
    app_services = get_app_services(request=request)
    postgres_connection = app_services.postgres.omni_postgres_conn
    if postgres_connection is None:
        raise RuntimeError("PostgreSQL has not been initialized")

    # Only lightweight adapters are assembled per request. No database pool is opened.
    google_auth_handler = await GoogleOAuthHandler.init_class(logger=app_services.logger)
    jwt_handler = await JWTHandler.init_class(logger=app_services.logger)
    postgres = await PostgresDML.init_class(manager=postgres_connection)

    return await AuthService.init_service(
        google_auth_handler=google_auth_handler,
        jwt_handler=jwt_handler,
        postgres=postgres,
        logger=app_services.logger,
    )
