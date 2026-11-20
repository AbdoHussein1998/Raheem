from __future__ import annotations

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from Schemas.pdf_models import (
        PDFIndexDownloadRequest,
        PDFObjectKeyRequest,
        PDFUpdateIndexRequest,
    )


@workflow.defn(name="PDFProcessingWorkflow")
class PDFProcessingWorkflow:
    @workflow.run
    async def run(
        self,
        request: PDFIndexDownloadRequest,
    ) -> PDFUpdateIndexRequest:
        db_retry = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        # 1. Fetch metadata from PostgreSQL
        object_key_req: PDFObjectKeyRequest = await workflow.execute_activity(
            "pdf_get_index",
            request,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=db_retry,
        )

        # 2. Download -> Validate -> Convert -> Upload (All in memory)
        update_req: PDFUpdateIndexRequest = await workflow.execute_activity(
            "pdf_convert",
            object_key_req,
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(seconds=45),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=2,
            ),
        )

        # 3. Update PostgreSQL index record
        final_result: PDFUpdateIndexRequest = await workflow.execute_activity(
            "pdf_update_pdf_index",
            update_req,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=db_retry,
        )

        return final_result