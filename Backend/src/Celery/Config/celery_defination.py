from dotenv import load_dotenv
load_dotenv()
import os
from celery import Celery




celery_app=Celery(
        main="ScaleableAiProject", # the name of the celery appluiction 
        broker_url=os.getenv("CELERY_BROKER_URL"), # the connection url to borker used by celery
        result_backend=os.getenv("CELERY_RESULT_BACKEND"), # the connection url to the backend used by celery to store results
        broker_pool_limit=int(os.getenv("CELERY_BROKER_CONNECTUIONS_POOL")),   
        include=[
                "Celery.Tasks.welcome_task",
                "Celery.Tasks.parse_pdf_task",
            ],                      # Limit the number of active connections to the broker
        
        # Serialization & Security Whitelist
        task_serializer="json",       # Outbound format for task arguments sent by clients
        result_serializer="json",     # Outbound format for task outputs sent by workers 
        accept_content=["json"],      # Inbound security whitelist for deserializing incoming payloads For Both WOKRKER and CLEINT
        
        # Operational Celery Configutations 
        timezone="UTC",               # Enforce UTC for consistent scheduling across servers
        enable_utc=True,
        task_track_started=True,      # Track when tasks move from QUEUED to STARTED
        task_time_limit=3600,         # Hard limit: kill tasks hanging longer than 1 hour
        task_soft_time_limit=3300,    # Soft limit: raise SoftTimeLimitExceeded at 55 mins for graceful cleanup
    )
   



celery_app.conf.update(
    worker_cancel_long_running_tasks_on_connection_loss=True
)

