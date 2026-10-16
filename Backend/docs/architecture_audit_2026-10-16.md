# Raheem backend standards alignment — reviewable patch

Date: 2026-10-16  
Source: `https://github.com/AbdoHussein1998/Raheem` (public `main` branch)  
Reference: `backend_development_standards.md` from this conversation.

## Scope and accuracy

This is a **local, uncommitted patch**, not a change to GitHub. Its four source files were transcribed from the public repository's raw GitHub views on October 16, 2026. The patch applies cleanly to those captured files; syntax compilation and isolated resource-lifecycle smoke tests passed. The entire repository was not cloned or executed; full integration testing is still required.

## Files updated by the patch

1. `Backend/src/Api/ApiConfiguration/fast_api_config.py`
   - Removes a reference to undefined `QdrantManager`. Qdrant registration remains deferred until its implementation is enabled.
   - Attempts to clean up already-created application resources after partial startup failure.
   - Disconnects managers in reverse initialization order and continues even when cleanup raises an exception.
   - Uses `try/finally` around the application lifespan.
   - Preserves the repository's existing decision to leave LLM startup disabled.
2. `Backend/src/Dependencies/auth_dependency.py`
   - Assembles short-lived Google OAuth, JWT and PostgreSQL DML adapters in the dependency layer.
   - Injects these collaborators into `AuthService` through `init_service()`.
   - Detects an uninitialized PostgreSQL connection early.
3. `Backend/src/Services/Services/auth_service.py`
   - Accepts injected providers, rather than calling provider `init_class()` itself.
   - Makes `init_service()` construction-only, matching `ServiceInterface` standards.
   - Introduces `AuthServiceError` with explicit error codes.
   - Stops logging complete user profile dictionaries and printing token payloads.
   - Keeps existing OAuth/FastAPI transport functions temporarily to avoid unsafe unverified provider changes.
4. `Backend/src/Api/Routes/Auth/auth_routes.py`
   - Maps expected authentication service failures to HTTP 400, 403, or 503.
   - Maintains existing login, callback, and refresh endpoint behavior.

## Apply from repository root

```bash
git checkout -b fix/backend-standards-alignment
git apply --check raheem_standards_update.patch
git apply raheem_standards_update.patch
python -m compileall -q Backend/src
# Then run the project's configured unit and integration tests.
git diff --check
git diff
```

Place `raheem_standards_update.patch` in the repository root before running those commands. Review the changes before committing. If the branch has changed since the public snapshot, the patch may need manual conflict resolution.

## Additional work required for *full* standards compliance

**Must do next:**

- Remove FastAPI `Request`, `Response` and `FileResponse` from `AuthService`; move response/cookie construction into the HTTP boundary. The current Google OAuth handler is HTTP-coupled, so this requires coordinating its interface before changing it.
- Move `WELCOME_PAGE_PATH` into typed application configuration and remove the current machine-specific Windows fallback.
- Adopt one consistent import root across `main.py`, routers, dependencies, services, and infrastructure. The existing project mixes `Raheem.src.*` and top-level `Api.*`/`Services.*`/`Infrastructure.*`. Choose the canonical run command and adjust imports and packaging together.
- Make sure OAuth/JWT adapter initialization is lightweight. If it opens network clients or other costly resources, initialize it once under `ApplicationServices` instead of on every request.
- Implement an active `QdrantManager` with proper startup, health/readiness and cleanup *when Qdrant functionality is enabled*, rather than enabling its commented-out stub.
- Document explicitly whether `LLMManager` is intentionally disabled in this deployment; do not silently enable expensive model initialization as part of a refactor.
- Audit other services for dedicated exceptions and constructor injection; audit Celery for independent worker resource ownership; review middleware configuration (`https_only=False`) before production deployment.

**Testing before merge:**

- Verify Python import resolution from the actual Docker/container and local launch commands.
- Exercise Google login, callback (success/error), token generation, cookie settings, refresh, and an unverified-email case.
- Exercise DB downtime during startup and auth writes. Confirm no profile data or tokens appear in logs.
- Verify shutdown invokes all disconnect operations, including after partial startup failure.
- Run unit and integration tests with the repo's dependency versions. These were **not** run against the live repository in this environment.

## Evidence (public source)

- Main lifecycle: `https://github.com/AbdoHussein1998/Raheem/blob/main/Backend/src/Api/ApiConfiguration/fast_api_config.py`
- Resource managers: `https://github.com/AbdoHussein1998/Raheem/blob/main/Backend/src/Api/ApiConfiguration/api_application_services.py`
- Authentication composition: `https://github.com/AbdoHussein1998/Raheem/blob/main/Backend/src/Dependencies/auth_dependency.py`
- Authentication service: `https://github.com/AbdoHussein1998/Raheem/blob/main/Backend/src/Services/Services/auth_service.py`
- Authentication routes: `https://github.com/AbdoHussein1998/Raheem/blob/main/Backend/src/Api/Routes/Auth/auth_routes.py`
