"""Database connection helper. All settings come from environment variables (.env locally,
GitHub Secrets in CI), so no credential is ever written in code."""

from __future__ import annotations

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def conninfo() -> str:
    """Build a libpq connection string from POSTGRES_* environment variables."""
    return psycopg.conninfo.make_conninfo(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "resort"),
        user=os.getenv("POSTGRES_USER", "pipeline_rw"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        sslmode=os.getenv("POSTGRES_SSLMODE", "disable"),
    )


def connect() -> psycopg.Connection:
    """Open a new connection. Use as a context manager: `with connect() as conn: ...`."""
    return psycopg.connect(conninfo())
