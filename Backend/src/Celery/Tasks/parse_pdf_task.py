"""Celery task adapter: initializes worker-owned MinIO then invokes EnqueueParsePDF."""
from __future__ import annotations

from asgiref.sync import async_to_sync
from loguru import logger as default_logger
from minio.error import S3Error

from Api.ApiConfiguration.api_settings import get_basic_settings
from Celery.Config.celery_defination import celery_app
from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Services.Celery.parse_pdf_enqueu import EnqueueParsePDF


_RETRYABLE_S3_CODES = {
    "InternalError", "RequestTimeout", "ServiceUnavailable", "SlowDown"
}


async def _execute_pdf_job(
    bucket_name: str,
    object_key: str,
    using_ocr: bool,
) -> dict:
    """One event-loop boundary owns connection creation, processing and cleanup."""
    settings = get_basic_settings()
    log = default_logger.bind(context="CeleryParsePDF", object_key=object_key)
    connection = None
    try:
        connection = await AsyncMinioConnectionManger.init_class(
            url=settings.OMNI_MINIO_ENDPOINT,
            access_key=settings.OMNI_MINIO_ACCESS_KEY,
            secret_key=settings.OMNI_MINIO_SECRET_KEY,
            logger=log,
        )
        controller = await AsyncMinioController.init_class(
            connection_manager=connection,
            logger=log,
        )
        service = await EnqueueParsePDF.init_service(
            lake_controller=controller,
            logger=log,
        )
        return await service.run(
            bucket_name=bucket_name,
            object_key=object_key,
            using_ocr=using_ocr,
        )
    finally:
        if connection is not None:
            await connection.disconnect()


@celery_app.task(name="parse_pdf", bind=True, max_retries=3)
def parse_pdf_task(
    self,
    bucket_name: str,
    object_key: str,
    using_ocr: bool = False,
) -> dict:
    """Pass only JSON-serializable identifiers over the broker."""
    try:
        result = async_to_sync(_execute_pdf_job)(
            bucket_name=bucket_name,
            object_key=object_key,
            using_ocr=using_ocr,
        )
        settings = get_basic_settings()
        return {
            "result": result,
            "metadata": {
                "AppName": settings.APP_NAME,
                "AppVersion": settings.APP_VERSION,
            },
        }
    except S3Error as exc:
        if exc.code in _RETRYABLE_S3_CODES:
            raise self.retry(exc=exc, countdown=60) from exc
        raise
    except (TimeoutError, ConnectionError) as exc:
        raise self.retry(exc=exc, countdown=60) from exc
