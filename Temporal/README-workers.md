# Temporal worker launcher

Run commands from the **directory that contains `Temporal/`**, with the project's Python environment activated.

```powershell
python -m Temporal.all_workers --mode shared
python -m Temporal.all_workers --mode process
python -m Temporal.all_workers --mode shared --worker pdf
```

- `shared` (default): all registered `Worker` objects run in one Python process and event loop, sharing one `TemporalConnectionManager` / client. Each worker factory owns any worker-specific PostgreSQL or MinIO dependencies.
- `process`: the launcher supervises one subprocess per registered worker. Each subprocess creates its own settings, Temporal client and resource pools. Connections cannot be shared across processes.
- `--worker pdf`: run only the PDF worker; repeat the flag to select more workers when registered.

## Configuration

Create `Temporal/.env` (next to this README) or set environment variables in your shell/deployment. Required settings include:

```dotenv
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_PDF_TASK_QUEUE=pdf-processing
TEMPORAL_MAX_PDF_CONVERSIONS=1
OMNI_POSTGRES_HOST=localhost
OMNI_POSTGRES_PORT=5432
OMNI_POSTGRES_USER=your_user
OMNI_POSTGRES_PASSWORD=your_password
OMNI_POSTGRES_DB=your_db
OMNI_MINIO_ENDPOINT=http://localhost:9000
OMNI_MINIO_ACCESS_KEY=your_access_key
OMNI_MINIO_SECRET_KEY=your_secret_key
```

Do not commit real secrets.

## Add a worker

1. Implement an async context manager in `Temporal/Workers/<name>_worker.py` that takes `(settings, client, loggers)`, creates its dependencies and yields a `temporalio.worker.Worker`.
2. Add it to `WORKER_FACTORIES` in `Temporal/all_workers.py`.
3. Supply any new settings in `Temporal/Config/setting.py`.

## Lifecycle and isolation

The parent launcher owns the Temporal connection per process. The PDF worker factory owns the PostgreSQL and MinIO resources it opens. In single-process mode, workers share only the Temporal client by default. In subprocess mode, nothing mutable is shared between Python processes.

The subprocess supervisor **does not automatically restart** crashed workers: it stops its siblings and exits with a failure code so Docker/systemd/Kubernetes can restart the deployment. On Windows, termination is not a graceful drain; use your deployment's worker-shutdown controls for running long PDF conversions.

This layout changes neither the PDF workflow nor its Activities. File bytes are still passed through Temporal history; larger PDFs may violate Temporal payload limits.
