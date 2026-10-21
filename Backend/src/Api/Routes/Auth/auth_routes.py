"""OAuth and refresh endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from Dependencies.auth_dependency import get_auth_service
from Services.Services.auth_service import AuthService, AuthServiceError


auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth", "Google"])


def _auth_http_error(exc: AuthServiceError) -> HTTPException:
    return HTTPException(
        status_code={
            "invalid_identity": 400,
            "email_unverified": 403,
            "storage_failure": 503,
        }.get(exc.code, 400),
        detail=exc.message,
    )


@auth_router.get("/google/login", name="google_login")
async def google_login(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.redirect_to_google(request)


@auth_router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
):
    try:
        data = await auth_service.receiving_from_google(request)
        await auth_service.save_to_database(data=data)
        token_data = await auth_service.generate_tokens(data=data)
        return await auth_service.go_to_home_and_store_token(token_data=token_data)
    except AuthServiceError as exc:
        raise _auth_http_error(exc) from exc


@auth_router.post("/refresh")
async def refresh_tokens(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
):
    jwt_handler = auth_service.jwt_handler
    refresh_token = await jwt_handler.get_refresh_token_from_request(request=request)
    tokens_data = await jwt_handler.rotate_tokens(refresh_token)
    response = JSONResponse({
        "token_type": tokens_data["token_type"],
        "expires_in": tokens_data["expires_in"],
        "message": "Tokens refreshed successfully",
    })
    jwt_handler.set_auth_cookies(
        response=response,
        access_token=tokens_data["access_token"],
        refresh_token=tokens_data["refresh_token"],
    )
    # Existing JWTHandler rotates token values but does NOT persist old/new JTIs.
    # Replay prevention requires a separate Services/Infrastructure change.
    return response
