"""PostgreSQL constants, SQL safety helpers and retry policy.

No infrastructure class inherits from this class; callers import its static
helpers and constants. Retrying database writes can duplicate transactions, so
one attempt is the default. Explicit retries are reserved for safe calls.
"""
from __future__ import annotations
import asyncio
import functools
import re
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional, Type, Union
from uuid import UUID
import numpy as np
import pandas as pd
from sqlalchemy import Executable, TextClause
from sqlalchemy.exc import OperationalError, InterfaceError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_IDENTIFIER_LENGTH = 63  # PostgreSQL's NAMEDATALEN limit (minus 1)

_PG_TYPE_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_ ]{0,29}"              # base type name, e.g. "VARCHAR", "DOUBLE PRECISION"
    r"(\(\s*\d{1,10}(\s*,\s*\d{1,10})?\s*\))?"    # optional (n) or (n,m)
    r"(\[\])?$"                                    # optional array suffix, e.g. "INTEGER[]"
)


def validate_identifier(name: str, *, label: str = "identifier") -> str:
    """
    Whitelist-validate a PostgreSQL identifier (schema, table, column, or
    constraint name) before it is interpolated into an f-string DDL
    statement. Raises ValueError on anything that isn't a plain ASCII
    word starting with a letter or underscore.

    This exists because identifiers can't be passed as bound SQL
    parameters — they must be validated (or properly quoted) manually.
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid {label}: expected a non-empty string, got {name!r}")
    if len(name) > _MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"Invalid {label}: {name!r} exceeds PostgreSQL's "
            f"{_MAX_IDENTIFIER_LENGTH}-character identifier limit"
        )
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"Invalid {label}: {name!r}. Only letters, digits, and underscores "
            "are allowed, and it must start with a letter or underscore."
        )
    return name


def render_default_literal(value: Any) -> str:
    """
    Safely render a Python value as a SQL `DEFAULT ...` clause fragment.
    Returns an empty string when `value` is None (i.e. no DEFAULT clause
    should be emitted at all).
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "DEFAULT TRUE" if value else "DEFAULT FALSE"
    if isinstance(value, (int, float)):
        return f"DEFAULT {value}"
    # Strings, dates, etc. — render as a quoted string literal, escaping
    # embedded single quotes so it can't break out of the literal.
    escaped = str(value).replace("'", "''")
    return f"DEFAULT '{escaped}'"


def validate_pg_type_literal(type_str: str) -> str:
    """
    Whitelist-validate a raw PostgreSQL type string (e.g. "VARCHAR(255)",
    "NUMERIC(10,2)", "INTEGER[]") before it is used in DDL. Returns the
    upper-cased, whitespace-normalized type string.
    """
    if not isinstance(type_str, str) or not type_str.strip():
        raise ValueError(f"Invalid PostgreSQL type: expected a non-empty string, got {type_str!r}")
    candidate = " ".join(type_str.strip().upper().split())
    if not _PG_TYPE_RE.match(candidate):
        raise ValueError(f"Refusing to use unvalidated PostgreSQL type string: {type_str!r}")
    return candidate




# ═══════════════════════════════════════════════════════════════════════════
# RETRY DECORATOR + TYPE MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════


class PostgresUtility:
    DEFAULT_MAX_ATTEMPTS = 1
    BASE_RETRY_DELAY = 0.1
    MAX_RETRY_DELAY = 2.0
    BACKOFF_FACTOR = 2.0
    RETRYABLE_ERRORS = (OperationalError, InterfaceError)

    @staticmethod
    def retry(max_attempts: int = 1, base_delay: float = 0.1,
              max_delay: float = 2.0, backoff_factor: float = 2.0,
              exceptions: tuple[type[Exception], ...] = RETRYABLE_ERRORS):
        """Retry async, *explicitly safe* operations on invalidated connections.

        Defaults to one attempt because the result of COMMIT can be ambiguous.
        Even when max_attempts > 1, only connection-invalidating errors are
        retried; the caller must guarantee operation idempotency.
        """
        if max_attempts < 1 or base_delay < 0 or max_delay < 0 or backoff_factor < 1:
            raise ValueError("Invalid PostgreSQL retry configuration")
        def decorator(func):
            @functools.wraps(func)
            async def wrapped(self, *args, **kwargs):
                delay = base_delay
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(self, *args, **kwargs)
                    except exceptions as exc:
                        if not getattr(exc, 'connection_invalidated', False):
                            raise
                        if attempt >= max_attempts:
                            raise
                        logger = getattr(self, 'logger', None)
                        if logger is not None:
                            logger.warning("{}: invalidated connection (attempt {}/{}); retrying", func.__name__, attempt, max_attempts)
                        connection = getattr(self, 'conn', None) or getattr(self, '_manager', None) or self
                        if hasattr(connection, 'reconnect'):
                            await connection.reconnect()
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
            return wrapped
        return decorator

    @staticmethod
    def debug_statement(logger: Any, stmt: Union[Executable, TextClause], *,
                        operation: Optional[str] = None,
                        table_name: Optional[str] = None,
                        log_params: bool = False) -> None:
        """Log SQL structure without exposing parameter values by default."""
        try:
            compiled = stmt.compile()
            logger.debug("Operation: {} | Table: {} | SQL: {}", operation, table_name, compiled)
            if log_params:
                logger.debug("Parameters: {}", compiled.params)
        except Exception:
            logger.exception("Failed to compile SQLAlchemy statement")

    PG_TO_PY: Dict[str, Type] = {
        "integer": int,
        "bigint": int,
        "smallint": int,
        "serial": int,
        "bigserial": int,
        "smallserial": int,
        "character varying": str,
        "varchar": str,
        "text": str,
        "character": str,
        "char": str,
        "boolean": bool,
        "bool": bool,
        "double precision": float,
        "real": float,
        "numeric": float,
        "decimal": float,
        "money": float,
        "timestamp without time zone": datetime,
        "timestamp with time zone": datetime,
        "timestamp": datetime,
        "date": date,
        "time without time zone": time,
        "time with time zone": time,
        "time": time,
        "interval": timedelta,
        "json": dict,
        "jsonb": dict,
        "uuid": UUID,
        "bytea": bytes,
        "inet": str,
        "cidr": str,
        "macaddr": str,
        "xml": str,
        "array": list,
    }

    PY_TO_PG: Dict[Type, str] = {
        int: "INTEGER",
        str: "TEXT",
        bool: "BOOLEAN",
        float: "DOUBLE PRECISION",
        datetime: "TIMESTAMP",
        date: "DATE",
        time: "TIME",
        timedelta: "INTERVAL",
        dict: "JSONB",
        list: "JSONB",
        UUID: "UUID",
        bytes: "BYTEA",

        pd.Int8Dtype: "SMALLINT",
        pd.Int16Dtype: "SMALLINT",
        pd.Int32Dtype: "INTEGER",
        pd.Int64Dtype: "BIGINT",
        pd.UInt8Dtype: "SMALLINT",
        pd.UInt16Dtype: "INTEGER",
        pd.UInt32Dtype: "BIGINT",
        pd.UInt64Dtype: "NUMERIC",
        pd.Float32Dtype: "REAL",
        pd.Float64Dtype: "DOUBLE PRECISION",
        pd.BooleanDtype: "BOOLEAN",
        pd.StringDtype: "TEXT",

        np.int8: "SMALLINT",
        np.int16: "SMALLINT",
        np.int32: "INTEGER",
        np.int64: "BIGINT",
        np.uint8: "SMALLINT",
        np.uint16: "INTEGER",
        np.uint32: "BIGINT",
        np.uint64: "BIGINT",  
        np.float16: "REAL",
        np.float32: "REAL",
        np.float64: "DOUBLE PRECISION",
        np.bool_: "BOOLEAN",
        np.str_: "TEXT",
        np.bytes_: "BYTEA",
        np.datetime64: "TIMESTAMP",
        np.timedelta64: "INTERVAL",
}

try_reconnect = PostgresUtility.retry()
PG_TO_PY = PostgresUtility.PG_TO_PY
PY_TO_PG = PostgresUtility.PY_TO_PG
retry = PostgresUtility.retry
