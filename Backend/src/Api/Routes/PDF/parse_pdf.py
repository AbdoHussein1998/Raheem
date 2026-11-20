"""PDF registration, Temporal submission, and PDF status endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile, status
from temporalio.client import Client, RPCError, RPCStatusCode
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

from Api.ApiConfiguration.api_services import ApplicationServices
from Dependencies.app_dependency import get_app_services
from Dependencies.temporal_dependency import get_omni_temporal_client
from Dependencies.validation_dependency import get_validation_service
from Infrastructure.Databases.Minio.async_controller import AsyncMinioController
from Services.Endpoints.pdf_registration import (
    PDFAlreadyExistsError,
    PDFRegistration,
    PDFTooLargeError,
    InvalidPDFError,
)
from Services.Endpoints.validation_service import ValidationService



pdf_router = APIRouter(prefix="/api/v1/pdfs", tags=["PDF"])
DocumentID = Annotated[str, Path(pattern=r"^[0-9a-f]{64}$")]


@pdf_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def register_pdf(
    file: UploadFile = File(...),
    ocr: bool = Form(False),
    services: ApplicationServices = Depends(get_app_services),
    validator: ValidationService = Depends(get_validation_service),
) -> dict:
    await validator.validate_pdf(
        file=file,
        size=services.settings.OMNI_PDF_MAX_UPLOAD_BYTES / (1024 * 1024),
    )

    if services.minio.omni_minio_conn is None:
        raise HTTPException(status_code=503, detail="MinIO is unavailable")

    dml = services.postgres.omni_postgres_dml
    if dml is None:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")

    lake = await AsyncMinioController.init_class(
        connection_manager=services.minio.omni_minio_conn,
        logger=services.logger_manager.get_logger("PDFRegistrationMinIO"),
    )
    registration = PDFRegistration(
        postgres_dml=dml,
        lake_controller=lake,
        max_upload_bytes=services.settings.OMNI_PDF_MAX_UPLOAD_BYTES,
        logger=services.logger_manager.get_logger("PDFRegistration"),
    )

    try:
        return await registration.run(
            file=file,
            bucket_name=services.settings.OMNI_MINIO_PDF_BUCKET or "parse-easy",
            ocr=ocr,
        )
    except PDFAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidPDFError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PDFTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@pdf_router.post("/parse", status_code=status.HTTP_202_ACCEPTED)
async def parse_pdf(document_id: str,temporal_client: Client = Depends(get_omni_temporal_client),
                    services: ApplicationServices = Depends(get_app_services),
) -> dict:
    dml = services.postgres.omni_postgres_dml
    if dml is None:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")

    rows = await dml.get_table_data(
        table_name="pdf_index",
        schema="processing_catalog",
        conditions={"hashed_name": document_id},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="PDF not found")
    if rows[0].registration_status not in ("ready", "completed"):
        raise HTTPException(status_code=409, detail="PDF registration is not ready")

    workflow_id = f"pdf-processing-{document_id}"
    try:
        handle = await temporal_client.start_workflow(
            "PDFProcessingWorkflow",  # <-- Pass workflow class name as a string
            {"document_id": document_id},  # <-- Pass dict matching PDFIndexDownloadRequest fields
            id=workflow_id,
            task_queue=services.settings.TEMPORAL_PDF_TASK_QUEUE,
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to submit PDF workflow to Temporal",
        ) from exc

    return {
        "document_id": document_id,
        "workflow_id": handle.id,
        "using_ocr": rows[0].ocr_required,
        "status": "accepted",
    }

@pdf_router.get("/{document_id}/metadata/")
async def get_pdf_metadata(
    document_id: DocumentID,
    services: ApplicationServices = Depends(get_app_services),
) -> dict:
    dml = services.postgres.omni_postgres_dml
    if dml is None:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")

    rows = await dml.get_table_data(
        table_name="pdf_index",
        schema="processing_catalog",
        conditions={"hashed_name": document_id},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="PDF not found")

    row = rows[0]
    return {
        "document_id": row.hashed_name,
        "filename": row.file_name,
        "bucket_name": row.bucket_name,
        "object_key": row.object_key,
        "ocr_required": row.ocr_required,
        "registration_status": row.registration_status,
        "result_object_key": row.result_object_key,
    }


@pdf_router.get("/{document_id}/processing-status/")
async def get_pdf_processing_status(
    document_id: DocumentID,
    temporal_client: Client = Depends(get_omni_temporal_client),
    services: ApplicationServices = Depends(get_app_services),
) -> dict:
    dml = services.postgres.omni_postgres_dml
    if dml is None:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")

    rows = await dml.get_table_data(
        table_name="pdf_index",
        schema="processing_catalog",
        conditions={"hashed_name": document_id},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="PDF not found")

    workflow_id = f"pdf-processing-{document_id}"
    try:
        description = await temporal_client.get_workflow_handle(workflow_id).describe()
        workflow_status = (
            description.status.name.lower() if description.status else "unknown"
        )
        run_id = description.run_id
    except RPCError as exc:
        if exc.status != RPCStatusCode.NOT_FOUND:
            raise HTTPException(status_code=503, detail="Temporal is unavailable") from exc
        workflow_status = "not_found_or_expired"
        run_id = None

    return {
        "document_id": document_id,
        "registration_status": rows[0].registration_status,
        "workflow_id": workflow_id,
        "workflow_status": workflow_status,
        "run_id": run_id,
    }


@pdf_router.get("/{document_id}/converted-markdown/")
async def get_pdf_converted_markdown_reference(
    document_id: DocumentID,
    services: ApplicationServices = Depends(get_app_services),
) -> dict:
    dml = services.postgres.omni_postgres_dml
    if dml is None:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")

    rows = await dml.get_table_data(
        table_name="pdf_index",
        schema="processing_catalog",
        conditions={"hashed_name": document_id},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="PDF not found")

    row = rows[0]
    if not row.result_object_key:
        raise HTTPException(status_code=409, detail="PDF conversion is not completed")

    return {
        "document_id": document_id,
        "registration_status": row.registration_status,
        "result_bucket": row.bucket_name,
        "result_object_key": row.result_object_key,
    }
