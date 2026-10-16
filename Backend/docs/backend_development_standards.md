# Backend Development Standards

**Project:** AlHakimAI  
**Architecture:** Layered, service-oriented, dependency-injected, asynchronous Python backend  
**Status:** Updated to reflect the current project structure, including authentication providers under `Infrastructure/Authentication/`. Future suggestions are explicitly labeled **Proposed**.

## 1. Architectural principles

The backend separates HTTP transport, application composition, business logic, and integrations with external systems. It uses FastAPI for HTTP, dependency injection for wiring, service classes for use cases, infrastructure adapters for persistence and external resources, and custom exceptions for controlled failure handling.

Core rules:

1. **Routers handle transport, not business logic.**
2. **Services own use-case logic, not the creation of their dependencies.**
3. **Infrastructure adapters implement external-system operations.**
4. **Application managers own long-lived connection lifecycles.**
5. **Dependency functions are thin adapters from initialized application resources to services.**
6. **Services raise domain/application errors; HTTP layers translate them into responses.**
7. **Celery workers initialize their own resources and never depend on FastAPI request state.**
8. **Interfaces are preferred at boundaries where multiple implementations are expected.**

The current HTTP execution path is:

```text
HTTP Request
    |
    v
FastAPI Router
    |
    v
Dependencies/get_*_service()
    |                 
    +--> FastAPI Request -> ApplicationServices (already initialized)
    |                          |
    |                          +--> MongoManager -> ready Mongo connection
    |                          +--> PostgresManager -> ready PostgreSQL connection/pool
    |                          +--> RedisManager -> ready Redis connection
    |                          +--> other managed providers as configured
    |
    +--> Service.init_service(injected dependencies)
              |
              v
        Service business logic
              |
              v
        Infrastructure / LLM adapters
              |
              v
        Result or service exception
              |
              v
      HTTP response / exception handler
```

**Important:** Exception handling is not a sequential business-logic layer; it is a failure path across the layers.

## 2. Current project layout

The following tree is the **current source layout** as provided for this project. Document and follow these paths when writing imports, dependencies, examples, and new features. Do not treat a previous top-level `Authentication/` directory as current.

```text
src/
├── Api/
│   ├── ApiConfiguration/
│   │   ├── api_application_services.py
│   │   ├── api_settings.py
│   │   └── fast_api_config.py
│   └── Routes/
│       ├── Auth/
│       │   └── auth_routes.py
│       └── Client/
│           └── basic_client_routes.py
├── Celery/
│   ├── Config/
│   │   ├── celery_configurations.py
│   │   ├── celery_defination.py
│   │   └── __init__.py
│   ├── Tasks/
│   │   ├── tasks.py
│   │   ├── welcome_task.py
│   │   └── __init__.py
│   └── __init__.py
├── Dependencies/
│   ├── app_dependency.py
│   ├── auth_dependency.py
│   ├── validation_dependency.py
│   ├── welcome_dependency.py
│   └── __init__.py
├── Infrastructure/
│   ├── Authentication/
│   │   ├── Providers/
│   │   │   ├── google_oauth_provider.py
│   │   │   └── jwt_services_provider.py
│   │   └── Schema/
│   │       ├── models.py
│   │       └── __init__.py
│   ├── Interfaces/
│   │   ├── connection.py
│   │   ├── document_dml.py
│   │   ├── vector.py
│   │   └── __init__.py
│   ├── Minio/
│   │   └── async_conncetion.py
│   ├── Mongodb/
│   │   ├── async_connection.py
│   │   ├── async_ddl.py
│   │   ├── async_dml.py
│   │   ├── mongo_utility.py
│   │   └── __init__.py
│   ├── PostgreSQL/
│   │   ├── async_connection.py
│   │   ├── async_ddl.py
│   │   ├── async_dml.py
│   │   ├── post_utility.py
│   │   └── __init__.py
│   ├── Qdrant/
│   │   └── qdrant_provider.py
│   └── Redis/
│       ├── async_connection.py
│       └── async_dml.py
├── LLM/
│   ├── Embedding/
│   │   ├── embedding_factory.py
│   │   └── __init__.py
│   ├── Generation/
│   │   ├── generation_factory.py
│   │   └── __init__.py
│   └── __init__.py
├── Services/
│   ├── Services/
│   │   ├── auth_service.py
│   │   ├── clean_conversion.py
│   │   ├── validation_service.py
│   │   └── welcome_service.py
│   └── service_interface.py
├── celery_app.py
├── main.py
├── notebook.ipynb
└── test.py
```

`Infrastructure/` is the shared home for integrations and persistence mechanisms, replacing the older database-only `DatabaseInfrastructure/` design. **Authentication providers and their current schemas have already moved into this layer.** Infrastructure can accommodate future data-lake storage and additional vector backends without changing the responsibilities of services.

`notebook.ipynb` and `test.py` are present at the `src/` root in the current tree. This records the layout; it does not establish notebooks as production modules or replace a dedicated test suite.

## 3. Naming and file conventions

- **Classes and exception types:** `PascalCase` (also called UpperCamelCase). Examples: `MongoManager`, `PostgresConnectionManager`, `AuthService`, `AuthServiceError`.
- **Functions, methods, variables, and Python module files:** `lower_snake_case`. Examples: `get_auth_service`, `init_service`, `async_connection.py`.
- **Constants and environment-setting fields:** `UPPER_SNAKE_CASE`. Examples: `OMNI_MONGO_URL`, `OMNI_POSTGRES_POOL_SIZE`.
- **Packages/directories:** follow the project's established capitalized convention, including current acronyms (`Api`, `ApiConfiguration`, `Infrastructure`, `PostgreSQL`, `LLM`). Preserve existing spellings in imports unless a coordinated refactor changes them.
- **Python package initialization files:** always `__init__.py`.
- **One primary responsibility per module.** Avoid generic files that accumulate unrelated logic.

**Proposed housekeeping:** Rename existing misspellings, such as `async_conncetion.py` and `celery_defination.py`, in a separate import-aware refactor. Do not silently change paths in unrelated feature work.

## 4. Infrastructure adapters and interfaces

Infrastructure includes database connections, DML/DDL adapters, object storage, vector stores, cache/Redis, external API clients, authentication providers, and other external integrations. `LLM/` remains a separate top-level package in the **current** layout and follows the same injection principles.

A concrete infrastructure component that requires asynchronous setup should expose `init_class()`:

```python
class SomeConnectionManager:
    @classmethod
    async def init_class(cls, *, configuration, logger=None):
        instance = cls(configuration=configuration, logger=logger)
        await instance.connect()
        return instance
```

`init_class()` returns a **ready-to-use instance**; for connection managers, readiness may require establishing a connection or a pool. It does not imply that the caller owns cleanup indefinitely. The resource owner must still release it through the supported `disconnect()` or `close()` operation.

Interfaces under `Infrastructure/Interfaces/` define capabilities and contracts; they do **not** have to implement `init_class()` merely because a concrete provider does. Pure utility classes and stateless helpers also do not require async factory methods when no async setup is needed.

Services should depend on an interface or protocol when doing so reduces coupling, especially for storage, document DML, or vector search implementations. Concrete types may be used temporarily where only one provider exists.

## 5. Application service managers and resource lifecycle

`Api/ApiConfiguration/api_application_services.py` currently defines the `ServiceManager` protocol and resource managers such as `MongoManager`, `PostgresManager`, and `RedisManager`.

Their key contract is:

```python
@runtime_checkable
class ServiceManager(Protocol):
    async def connect(self, settings: ApplicationBasicSettings) -> None: ...
    async def disconnect(self) -> None: ...
```

Managers orchestrate infrastructure initialization and cleanup. They are **not** business services and do not inherit from `ServiceInterface`.

The application owns a shared `ApplicationServices` container, made accessible to request dependencies through `get_app_services(request)`. The resource lifecycle is:

```text
FastAPI lifespan/startup
    -> load and validate ApplicationBasicSettings
    -> create ApplicationServices and its resource managers
    -> connect managers and initialize shared resources
    -> expose the initialized container to requests

FastAPI lifespan/shutdown
    -> stop accepting new work
    -> disconnect initialized managers
    -> release pools/clients in the appropriate order
```

Startup must fail visibly when a required connection cannot initialize. If startup partially succeeds, already-created resources should be cleaned up. Shutdown should attempt cleanup of all initialized managers even if one disconnect fails. Connection ownership and cleanup must be explicit.

Current primary resources include:

| Manager | Ready resource | Configuration family |
| --- | --- | --- |
| `MongoManager` | `omni_mongo_connection` | `OMNI_MONGO_*` |
| `PostgresManager` | `omni_postgres_conn` | `OMNI_POSTGRES_*` |
| `RedisManager` | `omni_redis_conn` | `OMNI_REDIS_*` |

These are the current **OMNI** resources; the design can later support separate read, write, log, tenant, or other named connections. Never create a new pool per HTTP request, and never close an application-scoped connection from a request-scoped service.

Use one owner per resource. When implementing multiple connections, give each an explicit role and lifecycle rather than duplicating anonymous clients across services.

## 6. Thin dependency modules

`Dependencies/` no longer creates the long-lived database infrastructure on every request. Its primary task is to **retrieve initialized resources and inject them into service factories**.

The current authentication dependency follows this pattern:

```python
# src/Dependencies/auth_dependency.py
from fastapi import Request
from Api.ApiConfiguration.fast_api_config import ApplicationServices
from Services.Services.auth_service import AuthService
from .app_dependency import get_app_services


async def get_auth_service(request: Request) -> AuthService:
    app_services: ApplicationServices = get_app_services(request=request)
    postgres_connection = app_services.postgres.omni_postgres_conn

    if postgres_connection is None:
        raise RuntimeError("PostgreSQL connection has not been initialized")

    return await AuthService.init_service(
        post_connection_manager=postgres_connection,
    )
```

Rules for dependency modules:

1. Resolve `ApplicationServices` or another explicitly scoped container.
2. Retrieve required initialized providers by their documented names.
3. Construct lightweight, request-scoped services through `init_service()`.
4. Do not run migrations, connect databases, or create expensive pools per request.
5. Do not embed domain workflows, SQL queries, vector-search logic, or LLM prompts.
6. Fail clearly when a required application resource is not initialized.

Transient or per-request objects may be assembled here when appropriate; this does not violate shared resource management. `get_app_services()` itself is a lookup, not a new application bootstrap.

## 7. Services and `ServiceInterface`

Every business service must inherit from `Services/service_interface.py::ServiceInterface` and implement the asynchronous class factory `init_service()`.

The service receives all required dependencies through its constructor and can optionally receive a Loguru logger. The inherited logger should be initialized through `super().__init__(logger=logger)` when the base class supports it.

```python
from typing import Optional
import loguru
from Services.service_interface import ServiceInterface


class AuthService(ServiceInterface):
    def __init__(
        self,
        post_connection_manager,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> None:
        super().__init__(logger=logger)
        self.post_connection_manager = post_connection_manager

    @classmethod
    async def init_service(
        cls,
        post_connection_manager,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> "AuthService":
        return cls(
            post_connection_manager=post_connection_manager,
            logger=logger,
        )
```

`init_service()` constructs and returns the service; it must not create or connect infrastructure resources. If a future service needs costly async initialization, distinguish that operation from plain dependency wiring and review its lifecycle deliberately.

**Not allowed inside a service:**

```python
self.mongo = await MongoConnectionManager.init_class(...)
self.redis = RedisConnectionManager(...)
self.other_service = OtherService(...)
```

**Allowed:** consume injected collaborators, call their methods, coordinate business rules and persistence, and return a framework-neutral result.

Services must not depend on `Request`, `Depends`, `HTTPException`, `JSONResponse`, or other FastAPI transport types. For uploaded files, prefer passing an application-level stream, bytes, or validated document descriptor into the service rather than requiring it to understand FastAPI `UploadFile`.

## 8. API routers and HTTP boundaries

Routers may validate transport input, resolve services through `Depends`, invoke service operations, and serialize output. They must not instantiate database clients or implement business rules.

Illustrative pattern:

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from Dependencies.auth_dependency import get_auth_service
from Services.Services.auth_service import AuthService

router = APIRouter()


@router.post("/example")
async def example_endpoint(
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.execute_example()  # Illustrative service method
```

Define request and response schemas at the boundary; do not expose raw database-driver objects. Prefer centralized FastAPI exception handlers for errors shared across routers. A router-local translation may be used when its semantics are specific to one endpoint.

## 9. Custom exceptions and failure handling

Each business service must have a dedicated exception type, such as `AuthServiceError`, `WelcomeServiceError`, or `ValidationServiceError`. Store exception classes beside the service or in a feature-specific exception module; be consistent within a feature.

```python
class AuthServiceError(Exception):
    def __init__(self, message: str, code: str = "auth_failed") -> None:
        self.message = message
        self.code = code
        super().__init__(message)
```

Rules:

- Raise the service-specific exception for expected business/application failures.
- Translate low-level infrastructure exceptions into service-specific exceptions when the service can add meaningful context; retain the cause with `raise ... from exc`.
- Do not indiscriminately convert every exception into a generic business error. Programming errors and cancellation should remain distinguishable.
- Log failures at an appropriate boundary with sufficient context, avoiding duplicate stack traces at every layer.
- Never include passwords, access tokens, connection URLs with credentials, or sensitive documents in logs or responses.
- Map errors to appropriate HTTP status codes (`400`/`422` for invalid input, `401`/`403` for authorization failures, `404` for missing resources, `409` for conflicts, `503` for unavailable dependencies, `500` for unexpected failures). Do not return `400` for every exception.

A router or registered exception handler performs the **service error -> HTTP response** mapping. It should never expose raw unexpected exception messages to clients.

## 10. Authentication architecture — current implementation

Authentication is **already organized under `Infrastructure/Authentication/`**. This is an implemented architectural decision, not a pending migration:

```text
Infrastructure/
└── Authentication/
    ├── Providers/
    │   ├── google_oauth_provider.py
    │   └── jwt_services_provider.py
    └── Schema/
        ├── models.py
        └── __init__.py

Services/
└── Services/
    └── auth_service.py

Dependencies/
└── auth_dependency.py

Api/
└── Routes/
    └── Auth/
        └── auth_routes.py
```

The responsibilities are separate:

- **`Infrastructure/Authentication/Providers/`:** Google OAuth integration, JWT creation/verification, third-party token validation, and other technical authentication mechanisms.
- **`Infrastructure/Authentication/Schema/`:** Provider-facing or infrastructure-specific authentication data contracts currently defined in `models.py`. Avoid making domain services depend on provider-specific schema types unless intentionally part of the contract.
- **`Services/Services/auth_service.py`:** Authentication use cases, such as login/registration orchestration, account rules, and coordination with injected identity/persistence providers.
- **`Dependencies/auth_dependency.py`:** Retrieve initialized resources and construct `AuthService` through its `init_service()` method.
- **`Api/Routes/Auth/auth_routes.py`:** HTTP request validation, authentication endpoints, and translation of application errors to HTTP responses.

`AuthService` must **not** move into `Infrastructure/`, and routers must not call external OAuth/JWT providers to implement business workflows directly. Prefer injecting authentication providers into the service when it needs them, rather than constructing them inside service methods.

If new transport-specific request/response schemas are added, keep them at the API boundary or in an explicitly shared API schema package; do not automatically place every authentication schema under `Infrastructure/Authentication/Schema/`.

## 11. LLM, vector stores, storage, and future data lakes

The existing `LLM/Embedding/` and `LLM/Generation/` factory packages provide model initialization and implementations. Treat their initialized models or clients as injectable dependencies rather than having business services construct models directly.

`Infrastructure/Qdrant/` provides vector persistence/search. Vector interfaces belong in `Infrastructure/Interfaces/vector.py`, allowing an alternative vector backend without rewriting use-case logic. `Infrastructure/Minio/` provides object-storage integration, while MongoDB/PostgreSQL/Redis providers retain their own responsibilities.

When a data lake is introduced, add its adapter and interface under `Infrastructure/` and register any long-lived clients in an appropriate manager. Keep dataset ingestion, indexing, transformation, and retrieval workflows in services or task-level orchestration as appropriate—not inside connection managers.

Avoid introducing unused abstractions or resource managers solely for speculative future integrations.

## 12. Celery and background execution

`Celery/Config/` configures the task system. `Celery/Tasks/` contains task entry points and orchestration, not duplicated business logic. A task should resolve a service, pass input, and handle task-specific retry/result behavior.

Celery workers run in separate processes; they **cannot** assume a FastAPI `Request`, `app.state`, or its `ApplicationServices` instance exists in their process. Workers must initialize and close their own infrastructure resources with a worker-appropriate lifecycle or shared composition helper. Do not create a fresh connection pool for every task unless required by the chosen worker lifecycle and driver constraints.

Keep retries idempotent where possible, distinguish retryable external failures from permanent business errors, and avoid passing connection objects, secrets, or large binary payloads directly through task messages.

## 13. Configuration, security, and observability

- `ApplicationBasicSettings` in `Api/ApiConfiguration/api_settings.py` is the typed source of runtime configuration for the current app composition.
- Validate required settings at startup, and inject values into managers/providers instead of reading environment variables throughout service methods.
- Prefer async clients/drivers for I/O in async paths; do not block the event loop with synchronous network or model operations.
- Use Loguru consistently. Record lifecycle events, dependency failures, and request/task correlation identifiers where supported.
- Minimize connection privileges; isolate secrets from source code and logs.
- Configure timeouts, pooling, retries, and health checks at the owning integration boundary. Retries must not accidentally duplicate writes.

## 14. Testability and change management

- **Unit tests:** construct service instances with fake/mock interfaces and test use-case behavior and service exceptions without FastAPI or real infrastructure.
- **Dependency tests:** verify the correct initialized resources are selected from the application container.
- **API tests:** override FastAPI dependencies and verify HTTP validation, success responses, and error mappings.
- **Integration tests:** exercise real or test-container infrastructure adapters, connection initialization, and cleanup.
- **Worker tests:** verify Celery task entry points invoke services and apply retry policies without relying on FastAPI request scope.

Keep startup/bootstrap changes separate from business-feature changes whenever possible. Update imports, tests, and documentation together when moving directories.

## 15. Responsibility matrix

| Layer/component | Responsibility | Must not do |
| --- | --- | --- |
| `Api/Routes/` | Transport, input/output, HTTP error mapping | Persistence logic, business workflows |
| `Api/ApiConfiguration/` | Application settings, startup/lifespan, shared resource ownership | Domain business logic |
| `Dependencies/` | Retrieve initialized resources; assemble services | Open pools on each request, perform business work |
| `Infrastructure/` | Database, cache, storage, vector, authentication, and external adapters | Decide HTTP responses or domain use cases |
| `Infrastructure/Interfaces/` | Define capability contracts | Hold connection-specific business orchestration |
| `LLM/` | Model factories and model-facing implementations | Own endpoint transport or business workflows |
| `Services/` | Business use cases and service-specific errors | Instantiate long-lived providers or use FastAPI objects |
| `Celery/Tasks/` | Task entry points, retry/result orchestration | Duplicate service business logic |

## 16. Pull-request checklist

- [ ] Names and import paths follow the current source tree (including `Infrastructure/Authentication/`).
- [ ] Names follow the existing package conventions and Python naming rules.
- [ ] Infrastructure adapters expose `init_class()` when asynchronous setup is required.
- [ ] Long-lived resources are owned, initialized, and closed by a lifecycle manager.
- [ ] Dependency functions retrieve shared resources and inject services without reconnecting them.
- [ ] Business services inherit `ServiceInterface` and implement `init_service()`.
- [ ] Services accept dependencies through constructors and remain framework-independent.
- [ ] Routers only handle transport and invoke services.
- [ ] Expected business failures use dedicated service exceptions and correct HTTP mappings.
- [ ] New tasks do not depend on FastAPI request state.
- [ ] Credentials are never logged or exposed in error responses.
- [ ] Unit/integration tests cover the affected boundaries and resource cleanup.

**Guiding rule:** Initialize shared resources once per owning process/lifecycle; assemble services where they are needed; keep domain behavior isolated from infrastructure and transport.
