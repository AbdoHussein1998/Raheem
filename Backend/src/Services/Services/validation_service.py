"""Validate access-token authentication independently of route handling."""

from typing import Optional

import loguru
from fastapi import HTTPException, Request
from loguru._logger import Logger

from Infrastructure.Authentication.Providers.jwt_services_provider import JWTHandler


class ValidationService:
    def __init__(
        self,
        logger: Optional[Logger] = None,
        jwt_handler: Optional[JWTHandler] = None,
    ) -> None:
        self.jwt: Optional[JWTHandler] = jwt_handler
        self.logger = logger or loguru.logger

    @classmethod
    async def init_service(
        cls,
        logger: Optional[Logger] = None,
        jwt_handler: Optional[JWTHandler] = None,
    ) -> "ValidationService":
        log = logger or loguru.logger
        jwt = jwt_handler or await JWTHandler.init_class(logger=log)
        return cls(logger=log, jwt_handler=jwt)

    async def verify_access_tokens(self, request: Request) -> bool:
        if self.jwt is None:
            raise RuntimeError("JWT handler has not been initialized")
        try:
            access_token = await self.jwt.get_access_token_from_request(request=request)
            await self.jwt.verify_access_token(token=access_token)
        except HTTPException as exc:
            # The client route expects False and clears invalid cookies.
            if exc.status_code == 401:
                return False
            raise
        return True
