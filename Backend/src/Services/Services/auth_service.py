"""Authentication application service (incremental dependency-injection refactor)."""
import os
from typing import Optional

import loguru
from fastapi import Request
from fastapi.responses import FileResponse, Response

from Services.service_interface import ServiceInterface
from Infrastructure.Authentication.Providers.google_oauth_provider import GoogleOAuthHandler
from Infrastructure.Authentication.Providers.jwt_services_provider import JWTHandler
from Backend.src.Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from Infrastructure.Authentication.Schema.models import TokenPayload


class AuthServiceError(Exception):
    """Expected authentication use-case error, independent of HTTP transport."""

    def __init__(self, message: str, code: str = "auth_failed") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class AuthService(ServiceInterface):
    def __init__(
        self,
        *,
        google_auth_handler: GoogleOAuthHandler,
        jwt_handler: JWTHandler,
        postgres: PostgresDML,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> None:
        super().__init__(logger=logger)
        self.google_auth_handler = google_auth_handler
        self.jwt_handler = jwt_handler
        self.postgres = postgres

        # Temporary compatibility: move path to typed application settings later.
        self.welcome_page_path = os.getenv(
            "WELCOME_PAGE_PATH",
            r"E:\SPgroup\Technical\Current\Ai Analysis Qualuity System\Frontend\welcome.html",
        )

    @classmethod
    async def init_service(
        cls,
        *,
        google_auth_handler: GoogleOAuthHandler,
        jwt_handler: JWTHandler,
        postgres: PostgresDML,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> "AuthService":
        """Construct the service; all providers are already supplied by DI."""
        return cls(
            google_auth_handler=google_auth_handler,
            jwt_handler=jwt_handler,
            postgres=postgres,
            logger=logger,
        )

    # Existing OAuth/response integration is preserved to avoid changing
    # the provider's transport contract in an untested patch.
    async def redirect_to_google(self, request: Request):
        return await self.google_auth_handler.redirect_to_google(request)

    async def receiving_from_google(self, request: Request):
        return await self.google_auth_handler.receiving_from_google(request)

    async def save_to_database(self, data: dict) -> None:
        db_data = {
            "google_sub": data.get("sub"),
            "email": data.get("email"),
            "email_verified": data.get("email_verified", False),
            "name": data.get("name"),
            "given_name": data.get("given_name"),
            "family_name": data.get("family_name"),
            "picture_url": data.get("picture"),
        }
        if not db_data["google_sub"] or not db_data["email"]:
            raise AuthServiceError("Missing required user identity fields", code="invalid_identity")
        if not db_data["email_verified"]:
            raise AuthServiceError("Email must be verified", code="email_unverified")

        try:
            await self.postgres.insert_into_table(
                table_name="users", data=db_data, schema="auth",
            )
        except Exception as exc:
            self.logger.exception("Could not persist authenticated user")
            raise AuthServiceError("Authentication persistence unavailable", code="storage_failure") from exc

    async def generate_tokens(self, data: dict) -> dict:
        google_sub = data.get("google_sub") or data.get("sub")
        email = data.get("email")
        if not google_sub or not email:
            raise AuthServiceError("Missing required user identity fields", code="invalid_identity")

        payload = TokenPayload(
            sub=google_sub,
            name=data.get("name") or data.get("given_name"),
        )
        access_token = await self.jwt_handler.generate_access_token(payload)
        refresh_token = await self.jwt_handler.generate_refresh_token(payload)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_handler.access_token_expire_minutes * 60,
        }

    async def go_to_home_and_store_token(self, token_data: dict) -> Response:
        """Compatibility method: creating HTTP responses should move to the router."""
        response = FileResponse(self.welcome_page_path)
        self.jwt_handler.set_auth_cookies(
            response=response,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
        )
        return response
