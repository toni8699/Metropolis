"""SQLAlchemy connection pool wrapping psycopg2 (raw SQL unchanged in services)."""

from __future__ import annotations

from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

_engine: Engine | None = None


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


def dispose_db() -> None:
    """Release all pooled connections (FastAPI lifespan shutdown)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


@contextmanager
def get_connection():
    if _engine is None:
        raise RuntimeError("Database pool not initialized. Call init_db() during app startup.")
    conn = _engine.raw_connection()
    try:
        yield conn
    finally:
        # ponytail: same rollback-on-return contract as metropolis/db.py
        try:
            if not conn.closed:
                conn.rollback()
        finally:
            conn.close()


__all__ = ["RealDictCursor", "dispose_db", "get_connection", "init_db"]
