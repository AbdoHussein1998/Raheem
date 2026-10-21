"""Authenticated PDF parsing into the configured MinIO bucket."""
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from Celery.Tasks.parse_pdf_task import parse_easy_pdf_task, parse_ocr_pdf_task



pdf_router = APIRouter(prefix="/api/v1/pdf", tags=["PDF"])


@pdf_router.post("/parse_easy/", status_code=status.HTTP_201_CREATED)
async def parse_pdf(file: UploadFile = File(...),):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a PDF",
        )
    parsing_task = parse_easy_pdf_task.delay(file, bucket_name="easy-pdf-bucket")
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": "PDF parsing task has been initiated.",
            "task_id": parsing_task.id,
        },
    )

@pdf_router.post("/parse_ocr/", status_code=status.HTTP_201_CREATED)
async def parse_ocr_pdf(file: UploadFile = File(...),):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a PDF",
        )
    parsing_task = parse_ocr_pdf_task.delay(file, bucket_name="ocr-pdf-bucket")
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": "PDF parsing task has been initiated.",
            "task_id": parsing_task.id,
        },
    )