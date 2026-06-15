"""PostgreSQL connection helpers (Neon via DATABASE_URL)."""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from psycopg2 import pool as pg_pool

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _require_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("Missing DATABASE_URL. Set it in .env (Neon connection string).")
    return url


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    # ponytail: lazy double-checked init so importing this module never opens a socket
    # (tests import without DATABASE_URL); the pool is built on first real query.
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                minconn = int(os.environ.get("DB_POOL_MIN", "1"))
                maxconn = int(os.environ.get("DB_POOL_MAX", "10"))
                _pool = pg_pool.ThreadedConnectionPool(
                    minconn, maxconn, dsn=_require_database_url()
                )
    return _pool


@contextmanager
def get_connection():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        # ponytail: pooled connections are reused, so always return them with no open
        # transaction. A caller's explicit commit() has already persisted; this rollback
        # is a no-op for it, but it clears aborted/idle transactions (errors, plain SELECTs)
        # that would otherwise poison the next borrower. Ceiling: no per-call retry on a
        # dead connection — a broken conn is dropped from the pool and recreated on demand.
        try:
            if not conn.closed:
                conn.rollback()
        finally:
            pool.putconn(conn, close=bool(conn.closed))


def close_pool() -> None:
    """Close all pooled connections (used on shutdown / test teardown)."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
