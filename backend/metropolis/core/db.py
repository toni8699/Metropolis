"""SQLAlchemy connection pool wrapping psycopg2 (raw SQL unchanged in services)."""

from __future__ import annotations

import threading
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

_engine: Engine | None = None
_engine_lock = threading.Lock()


def init_db(
    database_url: str,
    *,
    pool_size: int = 1,
    max_overflow: int = 9,
) -> None:
    """Create the SQLAlchemy engine pool (no-op when DATABASE_URL is empty)."""
    global _engine
    if not database_url.strip():
        return
    with _engine_lock:
        if _engine is not None:
            return
        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=300,
        )


def _ensure_engine() -> Engine:
    """Lazy init so scripts/tests with DATABASE_URL work without explicit init_db()."""
    global _engine
    if _engine is not None:
        return _engine
    from metropolis.core.config import settings

    url = settings.database_url.strip()
    if not url:
        raise RuntimeError("Missing DATABASE_URL. Set it in .env (Neon connection string).")
    max_overflow = max(0, settings.db_pool_max - settings.db_pool_min)
    init_db(url, pool_size=settings.db_pool_min, max_overflow=max_overflow)
    if _engine is None:
        raise RuntimeError("Database pool not initialized.")
    return _engine


def dispose_db() -> None:
    """Release all pooled connections (FastAPI lifespan shutdown)."""
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
            _engine = None


@contextmanager
def get_connection():
    conn = _ensure_engine().raw_connection()
    try:
        yield conn
    finally:
        # ponytail: rollback-on-return clears idle/aborted tx before pool reuse
        try:
            if not conn.closed:
                conn.rollback()
        finally:
            conn.close()


__all__ = ["RealDictCursor", "dispose_db", "get_connection", "init_db"]
