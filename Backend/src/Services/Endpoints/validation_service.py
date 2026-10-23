"""Validate access-token authentication independently of route handling."""

from typing import Optional

import loguru
from fastapi import HTTPException, Request,UploadFile,status
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
        self.max_pdf_mg=25 

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







    async def validate_pdf(
        self,
        file: UploadFile,
        size: Optional[float] = None,
    ) -> None:
        filename = file.filename or ""

        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "INVALID_FILE_EXTENSION",
                    "message": "File name must end with .pdf",
                },
            )

        max_size_mb = size if size is not None else self.max_pdf_mb

        if max_size_mb <= 0:
            raise ValueError("Maximum PDF size must be positive")

        max_size_bytes = int(max_size_mb * 1024 * 1024)

        if file.size is not None and file.size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "PDF_TOO_LARGE",
                    "message": f"PDF exceeds the maximum of {max_size_mb} MB",
                    "max_size_mb": max_size_mb,
                    "actual_size_mb": round(file.size / (1024 * 1024), 2),
                },
            )


