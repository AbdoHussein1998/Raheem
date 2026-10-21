


from asgiref.sync import async_to_sync
from fastapi import UploadFile
from Celery.Config.celery_defination import celery_app
from Api.ApiConfiguration.api_settings import get_basic_settings
from Dependencies.parse_books_dependency import (get_easy_pdf_parser_service,get_ocr_pdf_parser_service)



@celery_app.task(name="parse_easy_pdf", bind=True, max_retries=3)
def parse_easy_pdf_task(self, file:UploadFile,bucket_name:str):
    try:
        settings = get_basic_settings()
        service = async_to_sync(get_easy_pdf_parser_service)()
        result = async_to_sync(service.run)(file,bucket_name)
        return {
            "result": result,
            "metadata": {
                "AppName": settings.APP_NAME,
                "AppVersion": settings.APP_VERSION,
            },
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc

    

celery_app.task(name="parse_ocr_pdf", bind=True, max_retries=3)
def parse_ocr_pdf_task(self, file: UploadFile, bucket_name: str):
    try:
        settings = get_basic_settings()
        service = async_to_sync(get_ocr_pdf_parser_service)()
        result = async_to_sync(service.run)(file,bucket_name)
        return {
            "result": result,
            "metadata": {
                "AppName": settings.APP_NAME,
                "AppVersion": settings.APP_VERSION,
            },
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc