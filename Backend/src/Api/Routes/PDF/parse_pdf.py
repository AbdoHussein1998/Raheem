from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from Dependencies.parse_books_dependency import get_pdf_parser_service
from Celery.Tasks.parse_pdf_task import parse_pdf_task 
from Services.Endpoints.parse_pdf_service import ParsePDFBooks
from Services.Endpoints.validation_service import ValidationService
from fastapi.responses import JSONResponse
from Dependencies.validation_dependency import get_validation_service

pdf_router = APIRouter(
    prefix="/api/v1/pdf",
    tags=["PDF"],
)


# ==========================================
# Easy PDF Endpoint
# ==========================================

@pdf_router.post(
    "/parse_easy/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def parse_easy_pdf(
    file: UploadFile = File(...),
    service: ParsePDFBooks = Depends(get_pdf_parser_service),
    validator: ValidationService = Depends(get_validation_service)
) -> dict:

    await  validator.validate_pdf(file=file,size=25)
    #################################
    # Processing the Normal Method 
    #################################
    object_key=await service.run(file=file,bucket_name="parse-easy")


    # ==========================================
    # OCR PDF Endpoint
    # ==========================================
    task = parse_pdf_task.delay(
        bucket_name="parse-easy",
        object_key=object_key,
        using_ocr=False,
    )



    return JSONResponse(
        content={"message": "File parsed successfully", "task_id": task.id},
        status_code=status.HTTP_202_ACCEPTED,
        headers={"Task-ID": task.id}
    )