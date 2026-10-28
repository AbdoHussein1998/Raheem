"""FastAPI factory, route registration, middleware, and application lifespan."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
load_dotenv()

from Infrastructure.Logging.start import LoggerManager
from .api_services import ApplicationServices
from .api_settings import get_basic_settings

# Imports occur after dotenv loading: auth SDKs read configuration on init.
from Api.Routes.Auth.auth_routes import auth_router
from Api.Routes.Client.basic_client_routes import basic_client_router
from Api.Routes.PDF.parse_pdf import pdf_router





def create_lifespan(logger_manager: LoggerManager):
    logger = logger_manager.get_logger("lifespan")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("API backend starting")
        app.state.basic_settings = get_basic_settings()
        services = ApplicationServices(
            settings=app.state.basic_settings,
            logger_manager=logger_manager,
        )
        app.state.services = services
        try:
            await services.startup()
            yield
        finally:
            logger.info("API backend shutting down")
            await services.shutdown()
            # The scoped service container must not be reused after shutdown.
            app.state.services = None

    return lifespan


def create_app(*, logger_manager: LoggerManager | None = None) -> FastAPI:

    manager = logger_manager or LoggerManager()
    if logger_manager is None:
        manager.configure_logger(level=os.getenv("LOG_LEVEL", "INFO"))

    secret_key = os.getenv("MIDDLEWARE_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("MIDDLEWARE_SECRET_KEY is required for OAuth sessions")

  

    app = FastAPI(lifespan=create_lifespan(manager),docs_url="/docs")
    app.include_router(basic_client_router)
    app.include_router(auth_router)
    app.include_router(pdf_router)
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        same_site="lax",
        https_only=os.getenv("SESSION_COOKIE_HTTPS_ONLY", "false").lower()
        in ("1", "true", "yes", "on"),
    )
    return app
