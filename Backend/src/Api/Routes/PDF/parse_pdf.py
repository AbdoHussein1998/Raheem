from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from Dependencies.parse_books_dependency import get_pdf_parser_service
from Celery.Tasks.parse_pdf_task import parse_pdf_task 
from Services.Endpoints.parse_pdf_service import ParsePDFBooks
from Services.Endpoints.validation_service import ValidationService
from fastapi.responses import JSONResponse
from Dependencies.validation_dependency import get_validation_service
from .schema import UpladedFile
from fastapi.exceptions import HTTPException


pdf_router = APIRouter(
    prefix="/api/v1/pdf",
    tags=["PDF"],
)


# ==========================================
# Easy PDF Endpoint
# ==========================================

@pdf_router.post(
    "/parse_easy",
    status_code=status.HTTP_202_ACCEPTED,
)
async def parse_easy_pdf(
    file: UploadFile = File(...),
    service: ParsePDFBooks = Depends(get_pdf_parser_service),
    validator: ValidationService = Depends(get_validation_service)
) -> dict:

    await  validator.validate_pdf(file=file,size=60)
    #################################
    # Processing the Normal Method 
    #################################
    object_key=await service.upload_to_datalake(file=file,bucket_name="parse-easy")
    result=await service.register_file(file_name=file.filename,object_key=object_key)
    if result:
        return JSONResponse(
        content={"message": "File parsed successfully", "object_key": object_key},
        status_code=status.HTTP_202_ACCEPTED,
    )
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @pdf_router.post(
#     "/parse_easy_task",
#     status_code=status.HTTP_202_ACCEPTED,
# )
# async def parse_easy_pdf(object_key:Query(),ocr:Query(),):
#     # ==========================================
#     # OCR PDF Endpoint
#     # ==========================================
#     if not object_key:
#         raise HTTPException(status_code=400, detail="object_key is required")
#     if ocr:
#         bukcket_name="parse-easy-ocr"
#     else:
#         bukcket_name="parse-easy"
#     task = parse_pdf_task.delay(
#         bucket_name=bukcket_name,
#         object_key=object_key,
#         using_ocr=ocr,
#       )

#     return JSONResponse(
#         content={"message": "File started parsing successfully", "task_id": task.id},
#         status_code=status.HTTP_202_ACCEPTED,
#         headers={"Task-ID": task.id}
#     )

  
    