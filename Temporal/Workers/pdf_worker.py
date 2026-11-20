"""PDF worker factory. The main launcher owns the Temporal client and process.

This module only builds this worker's dependencies and registers its handlers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from temporalio.client import Client
from temporalio.worker import Worker

from Config.setting import ApplicationBasicSettings
from Infrastructure.Logging.start import LoggerManager
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Infrastructure.Databases.Minio.async_conncetion import AsyncMinioConnectionManger
from Infrastructure.Databases.PostgreSQL.async_connection import PostgresConnectionManager
from Infrastructure.Databases.PostgreSQL.async_dml import PostgresDML
from Activities.pdf_processing_activities import PDFProcessingActivities
from Workflows.pdf_processing_workflow import PDFProcessingWorkflow


@asynccontextmanager
async def pdf_worker(
    settings: ApplicationBasicSettings,
    client: Client,
    loggers: LoggerManager,
) -> AsyncIterator[Worker]:
    """Initialize PDF dependencies, yield its worker, and clean up on exit."""
    postgres = None
    dml = None
    minio = None

    try:
        postgres = await PostgresConnectionManager.init_class(
            host=settings.OMNI_POSTGRES_HOST,
            port=settings.OMNI_POSTGRES_PORT,
            username=settings.OMNI_POSTGRES_USER,
            password=settings.OMNI_POSTGRES_PASSWORD,
            database=settings.OMNI_POSTGRES_DB,
            echo=settings.OMNI_POSTGRES_ECHO,
            logger=loggers.get_logger("TemporalPostgreSQL"),
        )
        dml = await PostgresDML.init_class(
            manager=postgres,
            schema="processing_catalog",
            logger=loggers.get_logger("TemporalPostgresDML"),
        )
        minio = await AsyncMinioConnectionManger.init_class(
            url=settings.OMNI_MINIO_ENDPOINT,
            access_key=settings.OMNI_MINIO_ACCESS_KEY,
            secret_key=settings.OMNI_MINIO_SECRET_KEY,
            logger=loggers.get_logger("TemporalMinIO"),
        )
        lake_controller = await AsyncMinioController.init_class(
            connection_manager=minio,
            logger=loggers.get_logger("TemporalPDFMinIOController"),
        )
        activities = PDFProcessingActivities(
            postgres_dml=dml,
            lake_controller=lake_controller,
            logger=loggers.get_logger("TemporalPDFWorker"),
            max_concurrent_conversions=settings.TEMPORAL_MAX_PDF_CONVERSIONS,
        )
        worker = Worker(
            client,
            task_queue=settings.TEMPORAL_PDF_TASK_QUEUE,
            workflows=[PDFProcessingWorkflow],
            activities=[
                activities.get_pdf_index,
                activities.convert,
                activities.update_pdf_index,
            ],
            max_concurrent_activities=8,
        )
        yield worker
    finally:
        # The launcher cancels worker.run() before leaving this context.
        if dml is not None:
            await dml.close()
        if minio is not None:
            await minio.disconnect()
        if postgres is not None:
            await postgres.disconnect()
