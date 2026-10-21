# Raheem Backend Development Guide

**A practical, repeatable playbook for creating services, using them from FastAPI routes, and running the same logic as Celery tasks**

- **Project:** Raheem / AlHakimAIProject
- **Document date:** 2026-10-16
- **Target:** `Backend/src/` on the project's `main`-branch layout
- **Status:** Development standard and implementation recipe; **not** a claim that every example file already exists
- **Baseline:** The project tree supplied in this conversation, the existing `backend_development_standards.md`, and four public-repository source files captured earlier on 2026-10-16 (`fast_api_config.py`, `auth_dependency.py`, `auth_service.py`, `auth_routes.py`). **A fresh GitHub fetch was not possible during this review**, so any changes after that capture are unverified. Celery configuration and task file *contents* were not available for direct inspection; their paths are confirmed by the supplied tree.

> **Golden rule:** Initialize infrastructure at the appropriate application/worker lifecycle, inject collaborators into services, implement a business operation once, and call that operation from either an HTTP route or a Celery task. **Never import a FastAPI `Request` or `app.state` into a Celery task.**

---

## 1. The architecture to preserve

Raheem uses a layered service-oriented backend with constructor dependency injection, application-scoped resource managers, thin dependency modules, and explicit errors.

### HTTP execution

```text
Client request
   -> Api/Routes/*                  HTTP boundary (FastAPI)
   -> Dependencies/get_*_service()   Retrieve live application resources
   -> Service.init_service(...)      Assemble a service; do not connect a database
   -> Service.method(...)            Run business logic
   -> Infrastructure / LLM adapters  Execute external operations
   -> HTTP response or error mapping
```

### Celery execution

```text
Client request
   -> FastAPI route validates request and publishes job
   -> Message broker
   -> Separate Celery worker process
   -> Celery/Tasks/*                 Decode/validate job, orchestrate retries
   -> Worker-safe composition        Acquire worker-owned dependencies
   -> SAME Service.init_service(...) Create a service
   -> SAME Service.method(...)       Execute business logic
   -> Result backend / persistent job record
   -> Client polls a status endpoint
```

**The service is the reusable center.** HTTP and Celery are two delivery/execution mechanisms; neither should contain duplicate business rules.

### Ownership by layer

| Layer | Owns | Must not do |
| --- | --- | --- |
| `Api/ApiConfiguration/` | Typed settings, FastAPI startup/shutdown, shared app resource managers | Implement application use cases |
| `Api/Routes/` | Request/response validation, status codes, enqueue and task-status HTTP boundaries | Open database pools, perform business workflows |
| `Dependencies/` | Resolve resource handles and assemble services | Reinitialize shared connections per request |
| `Services/Services/` | Business decisions, orchestration, service-specific exceptions | Import FastAPI/Celery, instantiate database clients |
| `Services/service_interface.py` | Abstract service contract | Know any specific provider |
| `Infrastructure/` | Database, Redis, storage, vector, authentication implementations | Choose HTTP codes or implement use cases |
| `Infrastructure/Interfaces/` | Reusable persistence/storage/vector contracts | Own endpoint behavior |
| `LLM/` | Embedding and generation implementations/factories | Build HTTP responses |
| `Celery/Config/`, `celery_app.py` | Celery instance, broker/backend, registration, worker settings | Implement application use cases |
| `Celery/Tasks/` | Thin background entry points and retry/result policy | Duplicate service logic; use FastAPI `Request` |

**Important terminology:** `ApplicationServices` is the application *resource container*; a subclass of `ServiceInterface` is a *business service*. These are different responsibilities.

---

## 2. Project structure and where a new feature belongs

The repository layout supplied for this iteration is:

```text
Backend/
└── src/
    ├── Api/
    │   ├── ApiConfiguration/
    │   │   ├── api_application_services.py
    │   │   ├── api_settings.py
    │   │   └── fast_api_config.py
    │   └── Routes/
    │       ├── Auth/auth_routes.py
    │       └── Client/basic_client_routes.py
    ├── Celery/
    │   ├── Config/
    │   │   ├── celery_configurations.py
    │   │   └── celery_defination.py
    │   └── Tasks/
    │       ├── tasks.py
    │       └── welcome_task.py
    ├── Dependencies/
    │   ├── app_dependency.py
    │   ├── auth_dependency.py
    │   ├── validation_dependency.py
    │   └── welcome_dependency.py
    ├── Infrastructure/
    │   ├── Authentication/
    │   │   ├── Providers/google_oauth_provider.py
    │   │   ├── Providers/jwt_services_provider.py
    │   │   └── Schema/models.py
    │   ├── Interfaces/{connection.py,document_dml.py,vector.py}
    │   ├── Minio/async_conncetion.py
    │   ├── Mongodb/{async_connection.py,async_ddl.py,async_dml.py,mongo_utility.py}
    │   ├── PostgreSQL/{async_connection.py,async_ddl.py,async_dml.py,post_utility.py}
    │   ├── Qdrant/qdrant_provider.py
    │   └── Redis/{async_connection.py,async_dml.py}
    ├── LLM/
    │   ├── Embedding/embedding_factory.py
    │   └── Generation/generation_factory.py
    ├── Services/
    │   ├── Services/{auth_service.py,clean_conversion.py,validation_service.py,welcome_service.py}
    │   └── service_interface.py
    ├── celery_app.py
    ├── main.py
    ├── notebook.ipynb
    └── test.py
```

The `__init__.py` files are omitted from this abbreviated view; retain existing package initializers.

### Add one reusable feature (example: text processing)

Only the following *new* modules are necessary for the example below:

```text
Backend/src/
├── Services/Services/text_processing_service.py   # Business logic + error
├── Dependencies/text_processing_dependency.py     # Shared assembly + FastAPI adapter
├── Celery/Tasks/text_processing_task.py           # Thin task wrapper
└── Api/Routes/Client/text_processing_routes.py    # Direct/job/status routes
```

Also **modify the existing** FastAPI router registration and Celery task discovery/configuration. Do **not** create another `ApplicationServices` class, another Celery app instance, or another `ServiceInterface`.

For a feature with multiple domain files, group them consistently, but do not refactor the entire project tree just to add a feature.

---

## 3. Naming and contracts (mandatory)

- **Classes:** `PascalCase` (`WelcomeService`, `TextProcessingService`, `TextProcessingServiceError`).
- **Python modules/functions/variables:** `lower_snake_case` (`text_processing_service.py`, `get_text_processing_service`).
- **Constants and environment fields:** `UPPER_SNAKE_CASE`.
- **Existing folder naming:** preserve `Api`, `ApiConfiguration`, `Celery`, `Dependencies`, `Infrastructure`, `PostgreSQL`, `Services`, `LLM` exactly until a coordinated rename.
- **Business service:** inherits from `ServiceInterface`, provides `@classmethod async def init_service(...)` and accepts dependencies through `__init__`.
- **Infrastructure provider requiring async initialization:** exposes `@classmethod async def init_class(...)` that yields a usable instance; its owner controls closing.
- **Connection lifecycle manager:** owns shared long-lived clients and has `connect(settings)` / `disconnect()`.
- **Exception:** a dedicated `*ServiceError` for expected failures.
- **Serialization:** HTTP schemas are Pydantic; Celery arguments and results are JSON-serializable primitives and dictionaries.

**Import policy for new code:** choose one supported import root and use it consistently. This guide illustrates imports relative to `Backend/src` (for example `from Services.Services...`). The earlier repository capture mixes `Raheem.src.*` and `Services.*`; reconcile that before copying code into your runtime. Do not mix both styles in one feature.

---

## 4. First decide: direct HTTP, background task, or both?

| Situation | Execution |
| --- | --- |
| Quick validation, small read, ordinary CRUD | Route -> service directly |
| PDF extraction, large batch, embedding, indexing, slow provider requests | Route -> Celery -> same service |
| Feature needs both quick operations and heavy jobs | Expose both routes using one service |
| User must retrieve an artifact later | Celery job + persistent result/status + object-storage reference |

Avoid making an operation asynchronous *just because it is `async def`*. `async def` helps nonblocking I/O; **Celery** is what moves work to another process. CPU-heavy work or blocking model calls should not run inside the FastAPI event loop.

---

## 5. Complete example, step 1: implement the service

Use a deliberately simple, dependency-free service so the wiring can be copied and tested before involving real databases or LLMs. Replace its business logic with your document/LLM/domain operations when building a real feature.

**File:** `src/Services/Services/text_processing_service.py`

```python
from typing import Optional
import loguru

from Services.service_interface import ServiceInterface


class TextProcessingServiceError(Exception):
    def __init__(self, message: str, code: str = "processing_failed") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class TextProcessingService(ServiceInterface):
    def __init__(
        self,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> None:
        super().__init__(logger=logger)

    @classmethod
    async def init_service(
        cls,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> "TextProcessingService":
        # Construction ONLY. No database or model initialization here.
        return cls(logger=logger)

    async def process(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise TextProcessingServiceError(
                "Text must not be empty", code="invalid_text"
            )

        normalized = " ".join(text.split())
        return {
            "normalized_text": normalized,
            "word_count": len(normalized.split()),
        }
```

**Why this follows Raheem's pattern:** the class derives from `ServiceInterface`; `init_service()` returns a constructed instance; the method contains business logic and raises a dedicated error; it has **no imports from FastAPI, Celery, or connection-manager modules**.

For a real service, inject ready collaborators into its constructor:

```python
class MyService(ServiceInterface):
    def __init__(self, *, postgres_dml, storage, embedding_model, logger=None):
        super().__init__(logger=logger)
        self.postgres_dml = postgres_dml
        self.storage = storage
        self.embedding_model = embedding_model

    @classmethod
    async def init_service(cls, *, postgres_dml, storage, embedding_model, logger=None):
        return cls(
            postgres_dml=postgres_dml,
            storage=storage,
            embedding_model=embedding_model,
            logger=logger,
        )

    async def process(self, document_id: str):
        # Use injected dependencies; do not initialize them here.
        ...
```

The latter is a **signature template**, not a fully implemented integration; `storage` and `embedding_model` must be real adapters assembled by the dependency/worker composition code.

---

## 6. Step 2: write a thin dependency and a reusable builder

**File:** `src/Dependencies/text_processing_dependency.py`

```python
from typing import Optional
import loguru
from fastapi import Request

from Api.ApiConfiguration.fast_api_config import ApplicationServices
from Dependencies.app_dependency import get_app_services
from Services.Services.text_processing_service import TextProcessingService


async def build_text_processing_service(
    *, logger: Optional[loguru._logger.Logger] = None
) -> TextProcessingService:
    """Worker-safe assembly: does NOT access Request or app.state."""
    return await TextProcessingService.init_service(logger=logger)


async def get_text_processing_service(request: Request) -> TextProcessingService:
    """HTTP-specific adapter: fetch initialized application state."""
    app_services: ApplicationServices = get_app_services(request=request)
    return await build_text_processing_service(logger=app_services.logger)
```

**Key separation:** `build_text_processing_service()` can be called without a FastAPI request; `get_text_processing_service()` is the HTTP adapter that consults `ApplicationServices`.

When the service needs PostgreSQL, follow the actual project's current adapter pattern (confirmed in the earlier `auth_dependency.py` capture):

```python
from Infrastructure.PostgreSQL.async_dml import PostgresDML

async def get_my_service(request: Request):
    app_services = get_app_services(request=request)
    connection = app_services.postgres.omni_postgres_conn
    if connection is None:
        raise RuntimeError("PostgreSQL is not initialized")

    dml = await PostgresDML.init_class(manager=connection)
    return await MyService.init_service(
        postgres_dml=dml,
        storage=...,          # Resolve the already initialized storage adapter
        embedding_model=...,  # Resolve an initialized embedding model, if enabled
        logger=app_services.logger,
    )
```

`...` means **supply real injected adapters before running**; never leave ellipses in a production dependency. Do not call `PostgresConnectionManager.init_class()` per request: the pool already belongs to `PostgresManager`.

---

## 7. Step 3: expose the service directly through FastAPI

**File:** `src/Api/Routes/Client/text_processing_routes.py`

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from Dependencies.text_processing_dependency import get_text_processing_service
from Services.Services.text_processing_service import (
    TextProcessingService,
    TextProcessingServiceError,
)

text_processing_router = APIRouter(
    prefix="/api/v1/text-processing", tags=["Text Processing"]
)


class TextProcessingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class TextProcessingResponse(BaseModel):
    normalized_text: str
    word_count: int


@text_processing_router.post("/process", response_model=TextProcessingResponse)
async def process_direct(
    payload: TextProcessingRequest,
    service: Annotated[TextProcessingService, Depends(get_text_processing_service)],
):
    try:
        return await service.process(payload.text)
    except TextProcessingServiceError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
```

At this point, the service is usable directly from HTTP; no Celery is involved. A single request-scoped service object is assembled using an already initialized application container.

### Register the router

Find the file that currently calls `include_router()` (typically `src/main.py` or the API configuration module; **the exact call site has not been verified in the current checkout**), and add:

```python
from Api.Routes.Client.text_processing_routes import text_processing_router

app.include_router(text_processing_router)
```

If the application uses a central router rather than a direct `app.include_router`, register it with that router instead. Ensure registration happens only once and **after** the `FastAPI` app is created. Avoid importing a router into a service.

---

## 8. Step 4: turn the same service method into a Celery task

**Do not move business logic from the service into the task.** A task is an execution adapter that translates broker payloads into one call to the same service method.

**File:** `src/Celery/Tasks/text_processing_task.py`

```python
import asyncio
import loguru

from celery_app import celery_app
from Dependencies.text_processing_dependency import build_text_processing_service


async def _execute_text_processing(text: str) -> dict:
    service = await build_text_processing_service(logger=loguru.logger)
    return await service.process(text)


@celery_app.task(name="raheem.text_processing.process")
def process_text_task(text: str) -> dict:
    """Synchronous Celery entry point for an asynchronous service operation."""
    return asyncio.run(_execute_text_processing(text))
```

This example assumes the **existing** `src/celery_app.py` exports the configured Celery instance as `celery_app`. If the repository uses a different exported name, adjust the import; **do not instantiate a second Celery application here**.

### Why `asyncio.run()`?

Traditional Celery tasks are regular `def` functions; they can invoke an `async` service via `asyncio.run()` when there is no running event loop in the worker task thread. This is suitable for the self-contained example and for *per-task* asynchronous resources created and closed within the same call. Do **not** share event-loop-bound async pools across repeated `asyncio.run()` calls. See Section 12 before adding databases or LLM clients to a worker.

### Register the task with the existing Celery app

Inspect these **existing** files before changing them:

```text
src/celery_app.py
src/Celery/Config/celery_defination.py
src/Celery/Config/celery_configurations.py
src/Celery/Tasks/tasks.py
src/Celery/Tasks/welcome_task.py
```

There must be **one** configured Celery app, and the worker must import/discover `Celery.Tasks.text_processing_task`. Depending on how the existing Celery app is built, add the module to its `imports` or `include` configuration, for example:

```python
# Add to the existing Celery instance's configuration BEFORE worker startup.
# Do not replace the current configuration or drop existing welcome tasks.
existing_imports = tuple(celery_app.conf.imports or ())
new_module = "Celery.Tasks.text_processing_task"
celery_app.conf.imports = tuple(dict.fromkeys((*existing_imports, new_module)))
```

This is a **registration snippet**, not a replacement for `celery_defination.py`. If the repo already uses explicit task imports, update that list instead. Validate registration with `celery inspect registered` after the worker starts. The definitive task name is `raheem.text_processing.process`.

**Celery settings:** keep the existing broker, result backend, serializer, queues and retry settings defined in the project's configuration. Add a JSON result backend if task-status polling is required; a broker alone is insufficient for reliable result lookup. Keep task arguments/results JSON-compatible. Use task names and queue routing consistently.

---

## 9. Step 5: add background HTTP submission and status endpoints

Append to the **same** `src/Api/Routes/Client/text_processing_routes.py` from Section 7. Reuse its existing `text_processing_router` and `TextProcessingRequest`; **do not create a duplicate router object**.

```python
from fastapi import status
from starlette.concurrency import run_in_threadpool

from celery_app import celery_app
from Celery.Tasks.text_processing_task import process_text_task


@text_processing_router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_text_processing_job(payload: TextProcessingRequest):
    # Publishing to a broker is synchronous I/O; keep it off the event loop.
    job = await run_in_threadpool(
        process_text_task.apply_async,
        kwargs={"text": payload.text},
    )
    return {
        "task_id": job.id,
        "state": "PENDING",
        "status_url": f"/api/v1/text-processing/jobs/{job.id}",
    }


@text_processing_router.get("/jobs/{task_id}")
async def get_text_processing_job(task_id: str):
    def read_status() -> dict:
        job = celery_app.AsyncResult(task_id)
        state = job.state
        response = {"task_id": task_id, "state": state}
        if state == "SUCCESS":
            response["result"] = job.result
        elif state == "FAILURE":
            # Do not send traceback / secrets / raw driver exceptions to users.
            response["error"] = "Task execution failed"
        return response

    return await run_in_threadpool(read_status)
```

**Important production requirements:**

1. `PENDING` is not proof that a task exists: Celery can return it for an unknown ID or an unfinished task. If users need reliable status, create a durable `jobs` record on submission and look it up by user/account + job ID.
2. Secure the submission and status endpoints if jobs involve private data. A random task ID is **not** an authorization policy. Enforce job ownership in the route/application layer.
3. Configure the Celery **result backend** and expiration policy; status polling requires stored results or your own job table.
4. Do not return large PDFs/images in task results. Return an object-storage key, document ID, or URI that can be authorized and resolved separately.
5. Broker publish failures need an HTTP-appropriate failure path (typically `503`); do not claim a job was accepted when `apply_async()` failed.
6. For guaranteed job submission alongside a database transaction, use a transactional outbox or another appropriate coordination mechanism; database commit and message publish are not atomic by default.

### API behavior

```text
POST /api/v1/text-processing/process
  -> 200 with result (direct)

POST /api/v1/text-processing/jobs
  -> 202 with task_id and status_url (queued)

GET  /api/v1/text-processing/jobs/{task_id}
  -> current state, and result if successful
```

A typical Celery job state sequence is `PENDING -> STARTED -> SUCCESS`, but `STARTED` is only visible if tracking is enabled, and other states such as `RETRY` and `FAILURE` are possible.

---

## 10. Step 6: configure, launch, and verify

The repository snapshot establishes these component paths but **not** the exact Celery app object's exported name or production startup command. Check the relevant definitions before running these commands.

### Local import-root example

```bash
cd Backend
export PYTHONPATH="$PWD/src"
```

On PowerShell:

```powershell
cd Backend
$env:PYTHONPATH = (Resolve-Path ./src).Path
```

### Start API (illustrative)

```bash
uvicorn main:app --app-dir src --reload
```

This assumes `src/main.py` exports `app`. If the project uses an app factory or another target, use the target defined in the repository.

### Start Celery worker (illustrative)

```bash
celery -A celery_app:celery_app worker --loglevel=INFO
```

This assumes `src/celery_app.py` exposes `celery_app`. Replace the `-A` target with the exact exported object if different. For worker pools on Windows, consult the project's supported Celery worker environment; Linux container execution is usually a more predictable baseline.

### Confirm task registration

```bash
celery -A celery_app:celery_app inspect registered
```

Look for:

```text
raheem.text_processing.process
```

### Try both routes

```bash
curl -X POST http://127.0.0.1:8000/api/v1/text-processing/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello     Raheem"}'

curl -X POST http://127.0.0.1:8000/api/v1/text-processing/jobs \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello     Celery"}'
```

Expected direct result:

```json
{"normalized_text":"Hello Raheem","word_count":2}
```

Expected queued response **shape**, with actual task ID generated at runtime:

```json
{
  "task_id": "<generated-id>",
  "state": "PENDING",
  "status_url": "/api/v1/text-processing/jobs/<generated-id>"
}
```

Check status via:

```bash
curl http://127.0.0.1:8000/api/v1/text-processing/jobs/<generated-id>
```

---

## 11. How the existing application resource lifecycle works

In the earlier public repository capture, `src/Api/ApiConfiguration/fast_api_config.py` defines `ApplicationServices`, builds managers, and attaches the instance to `app.state.services` during FastAPI lifespan. Its startup connects MongoDB, Redis and PostgreSQL; the captured patched version keeps LLM startup disabled and does not register Qdrant yet. **Do not assume that the current checkout has since enabled these integrations.**

The related module `api_application_services.py` implements the managers, including:

```text
MongoManager    -> omni_mongo_connection
PostgresManager -> omni_postgres_conn
RedisManager    -> omni_redis_conn
LLMManager      -> model resources, when explicitly enabled
```

### Rule for new dependencies

1. Check whether a ready app-scoped resource already exists.
2. Reuse that resource through `get_app_services(request)`.
3. If it does not exist, implement its provider/interface, add a manager only if it needs a managed lifecycle, and register it in `ApplicationServices`.
4. Handle startup failure/cleanup; do not let a missing optional integration prevent unrelated features from starting unless it is explicitly required.
5. Assemble lightweight DML/vector/storage adapters in dependency code, with already initialized clients.
6. Pass those adapters to `Service.init_service()`.

### Distinguish factory and manager lifecycle

```text
Infrastructure.PostgresConnectionManager.init_class(...)  # Ready connection / pool
              ^ called by
PostgresManager.connect(settings)                            # Owner, once on startup
              |
ApplicationServices.postgres.omni_postgres_conn               # Shared handle
              |
Dependencies.get_my_service()                                 # Reads handle
              |
PostgresDML.init_class(manager=handle)                         # Lightweight adapter
              |
MyService.init_service(postgres_dml=adapter)                  # Creates service
```

`init_class()` is the infrastructure construction/init boundary. `init_service()` is the business-service assembly boundary. They are **not interchangeable**.

---

## 12. Worker lifecycle: the critical difference from HTTP

**A Celery worker is a separate process.** The FastAPI connection pools held in `app.state.services` do not transfer to it. Task messages cannot carry SQLAlchemy sessions, Redis clients, Qdrant clients, OAuth handlers, filesystem handles, or embedding model instances.

### Safe baseline for a database-backed task: per-task resources

If you have not yet implemented a dedicated worker resource lifecycle, create and close required async resources within the *same task event loop*:

```python
import asyncio
import loguru

from Api.ApiConfiguration.api_settings import get_basic_settings
from Api.ApiConfiguration.api_application_services import PostgresManager
from Infrastructure.PostgreSQL.async_dml import PostgresDML
from Services.Services.my_service import MyService


async def _run_db_job(document_id: str) -> dict:
    settings = get_basic_settings()
    manager = PostgresManager(logger=loguru.logger)
    try:
        await manager.connect(settings)
        connection = manager.omni_postgres_conn
        if connection is None:
            raise RuntimeError("Worker PostgreSQL connection unavailable")
        dml = await PostgresDML.init_class(manager=connection)
        service = await MyService.init_service(postgres_dml=dml, logger=loguru.logger)
        return await service.process(document_id)
    finally:
        await manager.disconnect()


def run_db_job(document_id: str) -> dict:
    return asyncio.run(_run_db_job(document_id))
```

This is a **pattern example** requiring a real `MyService` implementation. It deliberately reconnects *per task* for correctness and deterministic cleanup; that can be expensive at scale. Do not paste it into every task when a reusable worker-scoped manager is justified.

### High-throughput workers: optimize deliberately

For frequent database/LLM operations, design a **worker-owned** `WorkerServices`/factory that provides the relevant resources and explicit shutdown. However, with asyncio drivers, initialization and reuse must respect **event-loop and process affinity**. A connection pool created in one event loop cannot automatically be reused safely inside a different `asyncio.run()` loop. Do not create async clients before process forks, and do not share them between worker processes.

Implement worker startup/shutdown hooks and a consistent async execution strategy only after reviewing the installed Celery pool, platform, adapter semantics, and load needs. Keep that logic in worker composition/configuration, **not** in `MyService`.

### Reliable background-job rules

- Pass IDs, small strings and serializable options; load large files through Minio/storage using a reference.
- Persist enough metadata to support job ownership, retries, progress, and debugging.
- Make side effects idempotent; broker redelivery or retry may execute a task more than once.
- Retry transient infrastructure/network failures with bounded exponential backoff; do not retry invalid input or permission errors.
- Never log tokens, signed URLs, full OAuth profiles, credentials, document contents, or sensitive prompt payloads.
- Keep task result values small and serializable; use storage references for large artifacts.
- Separate task execution and task publication from business-service construction.

---

## 13. Error handling: service, task and route

**Service:** raises its own exception for an expected business failure.

```python
raise TextProcessingServiceError("Text must not be empty", code="invalid_text")
```

**Direct route:** translates it into a client-safe HTTP response.

```python
except TextProcessingServiceError as exc:
    raise HTTPException(status_code=422, detail=exc.message) from exc
```

**Celery task:** lets permanent validation/business failures fail normally (or records an explicit domain failure status). Retry only known transient errors; do not wrap every exception in `self.retry(...)`.

**Unexpected errors:** log safe diagnostic context at the appropriate boundary and return a generic HTTP failure. Preserve exception chaining and do not hide programmer errors under `400 Bad Request`.

A status endpoint must not serialize `job.result` when the state is `FAILURE`, since it can be an exception object containing implementation details.

---

## 14. Testing the feature at each boundary

### Unit-test the service without FastAPI, Celery or a database

**File suggestion:** `Backend/tests/test_text_processing_service.py`

```python
import pytest

from Services.Services.text_processing_service import (
    TextProcessingService,
    TextProcessingServiceError,
)


@pytest.mark.asyncio
async def test_processing_success():
    service = await TextProcessingService.init_service()
    result = await service.process("Hello   Raheem")
    assert result == {"normalized_text": "Hello Raheem", "word_count": 2}


@pytest.mark.asyncio
async def test_processing_rejects_empty():
    service = await TextProcessingService.init_service()
    with pytest.raises(TextProcessingServiceError) as err:
        await service.process("   ")
    assert err.value.code == "invalid_text"
```

This example requires `pytest` and `pytest-asyncio`. If your test setup uses AnyIO instead, use its configured async-test marker.

### Test dependency injection

Provide a fake `ApplicationServices` with a logger and mock/override `get_app_services`, then verify `get_text_processing_service()` calls the builder correctly. For DB-backed services, test that the connection comes from `app_services.postgres.omni_postgres_conn`, not from a new `PostgresConnectionManager`.

### Test the route

Use FastAPI dependency overrides with a fake service. Assert the direct response shape, 422 for invalid values, and that the route invokes the service exactly once. Mock `process_text_task.apply_async()` for the job-submission route so tests do not require a live broker.

### Test the task

Invoke the task in Celery's eager-test mode or call the underlying `_execute_text_processing()` in a unit test. Then run **one** integration test with a real broker + worker + result backend to verify discovery, serialization, execution and polling.

### Integration checklist

- [ ] FastAPI can start and shut down cleanly with configured infrastructure.
- [ ] Route is visible in OpenAPI documentation.
- [ ] `/process` returns the correct service output.
- [ ] `/jobs` returns HTTP 202 with a real task ID only on successful publish.
- [ ] Worker lists `raheem.text_processing.process` as registered.
- [ ] Worker can execute the task without any FastAPI request/application state.
- [ ] Result backend exposes successful completion.
- [ ] Validation errors are not retried indefinitely.
- [ ] Authorized users cannot read another user's job results.
- [ ] Timeouts/failures do not leak sensitive internals.
- [ ] A deliberately repeated job does not duplicate irreversible side effects.

---

## 15. Adding a feature that needs MongoDB, PostgreSQL, Redis, Minio, Qdrant or LLM

Use the same steps, with explicit injected dependencies:

1. **Choose the business operation:** define the method and expected input/result contracts first.
2. **Check existing adapters:** use `Infrastructure/Mongodb`, `PostgreSQL`, `Redis`, `Minio`, `Qdrant`, `Interfaces`, and `LLM` rather than reimplementing drivers.
3. **Add missing concrete adapter, if needed:** implement a small capability and `init_class()` where asynchronous initialization is required.
4. **Register long-lived connection lifecycle:** adjust `api_application_services.py` and `fast_api_config.py` if a *new shared* client is needed. A new business service does **not** normally need a new manager.
5. **Compose in Dependencies:** fetch existing handles, construct lightweight adapters, then call `YourService.init_service(...)`.
6. **Implement business logic in Services:** no FastAPI/Celery imports. Inject model, vector, storage and database capabilities.
7. **Add direct API route:** validate, call service, return a documented response.
8. **Add Celery task if needed:** initialize worker-owned resources and call **the same** service method.
9. **Publish from route and expose status:** use durable job IDs and authorization for private workloads.
10. **Write tests:** unit, dependency, HTTP, worker and infrastructure integration.

For PDF or image inputs, the preferred large-job sequence is:

```text
HTTP Upload -> validate metadata/size/type
            -> save bytes to storage (e.g., Minio)
            -> persist job metadata + owner
            -> enqueue task with object key / document ID
            -> worker loads document
            -> Document/PDF engine -> LLM -> Vector/DB/storage adapters
            -> service writes result reference + job state
            -> GET job status returns authorized result reference
```

Never put a full uploaded PDF, image binary, or model instance into a Celery broker message. If a document engine is added to the application later, keep engine/provider construction outside the business service.

---

## 16. Exception, reliability, security, and observability standards

- Give each service a dedicated exception class. Keep stable error codes and safe messages.
- Choose HTTP status codes based on failure semantics (`400/422`, `401/403`, `404`, `409`, `503`, `500`); not every failure is a `400`.
- Use Loguru consistently, including job IDs and request correlation IDs where available.
- Never use global mutable request state or reuse a FastAPI database session in Celery.
- Do not keep per-user secrets in logs, task arguments, or result-backend payloads.
- Validate uploads, authorization, file ownership and object-storage access at every boundary.
- Prefer operation IDs/idempotency keys for writes before retrying tasks.
- Document which resources are required/optional on startup. In the captured snapshot, Qdrant and LLM were not both active application resources; do not assume otherwise without checking your local branch.
- Keep runtime-specific connection URLs, ports, queue names and timeouts in typed settings, not inside services.
- Existing filename typos (`async_conncetion.py`, `celery_defination.py`) are not permission to create new typos; rename old paths only in a separate import-aware refactor.

---

## 17. Common mistakes and how to avoid them

| Mistake | Correct approach |
| --- | --- |
| Instantiate Mongo/Postgres/Redis inside a service | Inject initialized adapter/client |
| Open a DB connection on every HTTP request | Reuse the application-scoped manager connection |
| Call `get_app_services(Request)` inside Celery | Construct worker-owned resources and assemble the service |
| Copy service logic into a `@celery_app.task` | Have the task call the existing service method |
| Start another Celery app in the task module | Import the configured app instance |
| Pass `UploadFile` or bytes through Celery | Store bytes first; pass storage/document ID |
| Return complete PDFs/embeddings in task results | Persist the artifact and return a reference |
| Share async pools across repeated `asyncio.run()` loops | Keep each pool within its owning loop, or design a consistent worker loop |
| Call `job.get()` in an HTTP request and wait | Enqueue and return `202`, then poll status |
| Treat `PENDING` as a confirmed accepted job | Maintain a durable job record |
| Let any user poll any task ID | Enforce ownership in status/result endpoints |
| Retry every exception | Retry only bounded transient failures |
| Import routes into services | Keep dependencies flowing inward |
| Introduce new `QdrantManager` without enabling/configuring it | Explicitly register/connect/close it when actually needed |
| Copy legacy HTTP-coupled `AuthService` patterns into new services | Treat them as migration targets, not reference templates |

---

## 18. The 12-step developer checklist for every new service

1. [ ] Name the feature and choose service method names and data contracts.
2. [ ] Create `Services/Services/<feature>_service.py` with `ServiceInterface` inheritance.
3. [ ] Add `__init__` injection, a construction-only `async init_service()`, and a dedicated `<Feature>ServiceError`.
4. [ ] Put all business logic into service methods, with no FastAPI/Celery dependencies.
5. [ ] Identify existing infrastructure/LLM adapters; add new ones only if needed.
6. [ ] Add `Dependencies/<feature>_dependency.py`; use initialized app resources for HTTP.
7. [ ] Add `Api/Routes/<area>/<feature>_routes.py` with Pydantic validation and HTTP mapping.
8. [ ] Register the router in the application's existing include-router mechanism.
9. [ ] If background execution is needed, add `Celery/Tasks/<feature>_task.py` that calls the *same service* using worker-owned resources.
10. [ ] Register the task in the current Celery app and ensure the result backend/status/ownership policy are defined.
11. [ ] Write unit, API, task, and integration tests; check idempotency, failure and cleanup behavior.
12. [ ] Check imports, package names, typed settings, logs, docs and deployment commands before merging.

---

## 19. Repository-specific verification before merging

Because fresh access to live GitHub `main` was unavailable in this session, verify these items against the actual checkout before treating a new implementation as production-ready:

- **`src/Services/service_interface.py`**: confirm `super().__init__(logger=logger)` and async `init_service()` signatures.
- **`src/Api/ApiConfiguration/fast_api_config.py`**: confirm the currently enabled managers, FastAPI lifespan registration, and initialized state key.
- **`src/Dependencies/app_dependency.py`**: confirm `get_app_services(request)` reads the expected state container.
- **`src/Api/ApiConfiguration/api_application_services.py`**: confirm the manager attribute names and `connect()/disconnect()` behavior.
- **`src/main.py`**: confirm app object/export, canonical import root, and router registration mechanism.
- **`src/celery_app.py`** plus **`Celery/Config/celery_defination.py`** and **`celery_configurations.py`**: confirm the *single* Celery instance name, discovery, broker/result backend, queue routing, serializers, concurrency settings and worker command.
- **`Celery/Tasks/tasks.py`** and **`welcome_task.py`**: confirm existing registration/retry conventions. Add to them without breaking active tasks.
- **`Infrastructure/Authentication/Providers/`**: verify the existing Google/JWT providers before extending authentication.
- **Existing import inconsistencies:** the earlier source snapshot mixed `Raheem.src.*` with `Api.*`, `Services.*`, `Infrastructure.*`. Normalize at a planned boundary.

The previous patch in this conversation is **a local patch, not a confirmed upstream merge**. Do not assume it is on `main` unless verified with `git log`/`git diff` or through GitHub.
