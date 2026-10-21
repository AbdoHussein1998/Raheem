"""Lightweight welcome job; the API process does not initialize this service."""
from asgiref.sync import async_to_sync
from Celery.Config.celery_defination import celery_app
from Api.ApiConfiguration.api_settings import get_basic_settings
from Dependencies.welcome_dependency import get_welcome_service


@celery_app.task(name="welcome_task", bind=True, max_retries=3)
def welcome_task(self):
    try:
        settings = get_basic_settings()
        service = async_to_sync(get_welcome_service)()
        result = async_to_sync(service.run)()
        return {
            "result": result,
            "metadata": {
                "AppName": settings.APP_NAME,
                "AppVersion": settings.APP_VERSION,
            },
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc
