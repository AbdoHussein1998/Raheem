from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()
import argparse
import asyncio
import subprocess
import sys
import time

from Config.setting import get_basic_settings
from Infrastructure.Logging.start import LoggerManager
from Infrastructure.Temporal.async_connection import TemporalConnectionManager
from Workers.pdf_worker import pdf_worker

# ---------------------------------------------------------------------------
# Register workers here: just import the worker function and .append() it
# ---------------------------------------------------------------------------
WORKERS = []
WORKERS.append(pdf_worker)


async def _start_single_worker(worker_fn, settings, client, loggers, logger) -> None:
    """Enter the worker's async context manager and run it until stopped."""
    async with worker_fn(settings, client, loggers) as worker:
        logger.info("Registered worker={}", worker_fn.__name__)
        await worker.run()


async def run_shared(selected_workers: list) -> None:
    """One event loop, one Temporal client, multiple independent Worker objects."""
    settings = get_basic_settings()
    loggers = LoggerManager()
    logger = loggers.get_logger("TemporalLauncher")

    temporal = await TemporalConnectionManager.init_class(
        address=settings.TEMPORAL_ADDRESS,
        namespace=settings.TEMPORAL_NAMESPACE,
        tls=settings.TEMPORAL_TLS,
        api_key=settings.TEMPORAL_API_KEY,
        logger=loggers.get_logger("TemporalConnection"),
    )

    try:
        client = temporal.get_client()

        # TaskGroup runs all workers concurrently; if one crashes, it cancels the rest.
        async with asyncio.TaskGroup() as group:
            for worker_fn in selected_workers:
                group.create_task(
                    _start_single_worker(worker_fn, settings, client, loggers, logger)
                )
    finally:
        await temporal.disconnect()


def run_processes(selected_workers: list) -> int:
    """Start one fresh interpreter per worker (safe on Windows and Linux)."""
    processes: dict[str, subprocess.Popen] = {}
    try:
        for worker_fn in selected_workers:
            name = worker_fn.__name__
            process = subprocess.Popen(
                [
                    sys.executable, "-m", "Temporal.all_workers",
                    "--mode", "shared", "--worker", name,
                ],
            )
            processes[name] = process
            print(f"Started Temporal worker={name} pid={process.pid}", flush=True)

        while True:
            for name, process in processes.items():
                status = process.poll()
                if status is not None:
                    print(
                        f"Temporal worker={name} exited with status={status}",
                        file=sys.stderr,
                        flush=True,
                    )
                    return status if status != 0 else 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Temporal workers...", flush=True)
        return 0
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        for process in processes.values():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> None:
    # Map function names (e.g. "pdf_worker") automatically from the WORKERS list
    worker_map = {fn.__name__: fn for fn in WORKERS}

    parser = argparse.ArgumentParser(description="Temporal worker launcher")
    parser.add_argument(
        "--mode", choices=("shared", "process"), default="shared",
        help="shared: all workers in one PID; process: one PID per worker",
    )
    parser.add_argument(
        "--worker", choices=tuple(worker_map.keys()), action="append",
        help="Worker to run (repeatable); defaults to all registered workers",
    )
    args = parser.parse_args()

    if args.worker:
        selected_names = list(dict.fromkeys(args.worker))
        selected_workers = [worker_map[name] for name in selected_names]
    else:
        selected_workers = WORKERS

    if args.mode == "shared":
        try:
            asyncio.run(run_shared(selected_workers))
        except KeyboardInterrupt:
            pass
    else:
        raise SystemExit(run_processes(selected_workers))


if __name__ == "__main__":
    main()


    