"""Only resolve the already configured Temporal Client from app.services."""
from fastapi import Depends, HTTPException, status
from temporalio.client import Client

from Api.ApiConfiguration.api_services import ApplicationServices
from Dependencies.app_dependency import get_app_services


async def get_omni_temporal_client(
    services: ApplicationServices = Depends(get_app_services),
) -> Client:
    try:
        # Lazily connect so uploads can still work when Temporal is offline.
        if services.temporal.omni_temporal_conn is None:
            await services.temporal.connect(services.settings)
        connection = services.temporal.get_connection("omni")
        return await connection.ensure_connected()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is unavailable",
        ) from exc
