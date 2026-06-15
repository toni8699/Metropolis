"""ARQ worker: durable booking sweep (replaces Eventlet greenlet in booking_sweep.py)."""

from __future__ import annotations

import asyncio
import logging

from arq import cron
from arq.connections import RedisSettings

from metropolis.core.config import settings

_logger = logging.getLogger("metropolis")


def _sweep_enabled() -> bool:
    if settings.booking_sweep_enabled is not None:
        return settings.booking_sweep_enabled
    # ponytail: off in FLASK_DEBUG=1 unless BOOKING_SWEEP_ENABLED set (matches old greenlet)
    return not settings.debug


async def startup(ctx: dict) -> None:
    if not settings.database_url:
        return
    from metropolis.core.db import init_db

    max_overflow = max(0, settings.db_pool_max - settings.db_pool_min)
    init_db(
        settings.database_url,
        pool_size=settings.db_pool_min,
        max_overflow=max_overflow,
    )


async def shutdown(ctx: dict) -> None:
    from metropolis.core.db import dispose_db

    dispose_db()


async def sweep_expired_bookings(ctx: dict) -> dict:
    """Complete past-due CONFIRMED/IN_PROGRESS trips."""
    if not _sweep_enabled():
        return {"status": "skipped", "completed": 0}

    from metropolis.services import booking_service

    result = await asyncio.to_thread(booking_service.sweep_expired_bookings)
    completed = int(result.get("completed") or 0)
    if completed:
        _logger.info("booking sweep auto-completed %s trip(s)", completed)
    return result


def _redis_settings() -> RedisSettings:
    dsn = settings.redis_url or "redis://127.0.0.1:6379/0"
    return RedisSettings.from_dsn(dsn)


class WorkerSettings:
    """arq worker entrypoint: arq metropolis.jobs.booking_sweep.WorkerSettings"""

    functions = [sweep_expired_bookings]
    cron_jobs = [cron(sweep_expired_bookings, minute=set(range(0, 60, 15)))]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = _redis_settings()
