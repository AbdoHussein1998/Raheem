"""Access the already-started application composition root."""
from fastapi import HTTPException, Request, status

from Api.ApiConfiguration.api_services import ApplicationServices


def get_app_services(request: Request) -> ApplicationServices:
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application services are not ready",
        )
    return services



