"""PostgreSQL connection helpers (Neon via DATABASE_URL)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")


def _require_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "Missing DATABASE_URL. Set it in .env (Neon connection string)."
        )
    return url


@contextmanager
def get_connection():
    conn = psycopg2.connect(_require_database_url())
    try:
        yield conn
    finally:
        conn.close()
