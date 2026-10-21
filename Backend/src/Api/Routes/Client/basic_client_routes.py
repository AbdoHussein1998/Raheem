"""Authenticated welcome-task submission endpoint."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from Dependencies.validation_dependency import get_validation_service
from Services.Services.validation_service import ValidationService
from Celery.Config.celery_defination import celery_app

basic_client_router = APIRouter(prefix="/api/v1/client", tags=["Client"])


@basic_client_router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def basic_client_enqueue(
    request: Request,
    valid_handler: ValidationService = Depends(get_validation_service),
):
    if not await valid_handler.verify_access_tokens(request=request):
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"},
        )
        valid_handler.jwt.clear_auth_cookies(response=response)
        return response



    try:
        task = celery_app.send_task("Welcome_Task")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task broker unavailable",
        ) from exc

    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Welcome task has been enqueued",
    }
