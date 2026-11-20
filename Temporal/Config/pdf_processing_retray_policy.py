from datetime import timedelta
from temporalio.common import RetryPolicy


class PDFProcessingRetrayPolicy:

    # ==========================================
    # 1. GET PDF INDEX
    # ==========================================

    GET_INDEX = RetryPolicy(
        initial_interval=timedelta(seconds=2),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=10),
        maximum_attempts=3,
    )

    # ==========================================
    # 2. DOWNLOAD PDF
    # ==========================================

    DOWNLOAD = RetryPolicy(
        initial_interval=timedelta(seconds=5),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=3,
    )

    # ==========================================
    # 3. CONVERT PDF
    # ==========================================

    CONVERT = RetryPolicy(
        initial_interval=timedelta(seconds=30),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=2),
        maximum_attempts=2,
    )

    # ==========================================
    # 4. UPLOAD MARKDOWN
    # ==========================================

    UPLOAD = RetryPolicy(
        initial_interval=timedelta(seconds=5),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=3,
    )

    # ==========================================
    # 5. UPDATE POSTGRESQL INDEX
    # ==========================================

    UPDATE_INDEX = RetryPolicy(
        initial_interval=timedelta(seconds=2),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=5,
    )