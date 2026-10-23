"""Keep this factory callable from Celery without a FastAPI request."""
import loguru
from Services.Endpoints.welcome_service import WelcomeService


async def get_welcome_service() -> WelcomeService:
    return await WelcomeService.init_service(logger=loguru.logger)
