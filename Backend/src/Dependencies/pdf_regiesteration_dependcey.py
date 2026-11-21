
from Services.Endpoints.pdf_registration import PDFRegistration
from Infrastructure.Databases.Minio import AsyncMinioController
from Infrastructure.Databases.PostgreSQL import PostgresDML
from fastapi import Depends,Request
from Api.ApiConfiguration.api_services import ApplicationServices


async def get_pdf_registtrantion_service(request:Request)->PDFRegistration:
    services:ApplicationServices = getattr(request.app.state, "services", None)
    omni_minio_conn=services.minio.omni_minio_conn
    omni_postgres_conn=services.postgres.omni_postgres_conn
    service= await PDFRegistration.init_service(lake_connection=omni_minio_conn,postgres_connection=omni_postgres_conn)
    return service
    
    

