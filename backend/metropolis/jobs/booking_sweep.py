"""ARQ worker: durable booking sweep."""

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
    # ponytail: off when DEBUG=1 unless BOOKING_SWEEP_ENABLED is set
    return not settings.debug


def _upload_sweep_enabled() -> bool:
    if settings.upload_sweep_enabled is not None:
        return settings.upload_sweep_enabled
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


async def sweep_orphan_listing_uploads(ctx: dict) -> dict:
    """Delete abandoned owner listing photos from S3."""
    if not _upload_sweep_enabled():
        return {"status": "skipped", "deleted": 0, "scanned": 0}

    from metropolis.services import uploads_service

    result = await asyncio.to_thread(uploads_service.sweep_orphan_listing_uploads)
    deleted = int(result.get("deleted") or 0)
    if deleted:
        _logger.info("upload sweep removed %s orphan listing object(s)", deleted)
    return result


def _redis_settings() -> RedisSettings:
    dsn = settings.redis_url or "redis://127.0.0.1:6379/0"
    return RedisSettings.from_dsn(dsn)


async def sweep_trip_reminders(ctx: dict) -> dict:
    """Email renters ~24h before trip start."""
    if not _sweep_enabled():
        return {"status": "skipped", "sent": 0}

    from metropolis.services import booking_service

    result = await asyncio.to_thread(booking_service.sweep_trip_reminders)
    sent = int(result.get("sent") or 0)
    if sent:
        _logger.info("trip reminder sweep sent %s email(s)", sent)
    return result


async def sweep_stale_unpaid_bookings(ctx: dict) -> dict:
    """Drop ghost checkouts that never completed payment."""
    if not _sweep_enabled():
        return {"status": "skipped", "cancelled": 0}

    from metropolis.services import booking_service

    result = await asyncio.to_thread(booking_service.sweep_stale_unpaid_bookings)
    cancelled = int(result.get("cancelled") or 0)
    if cancelled:
        _logger.info("booking sweep cancelled %s stale unpaid booking(s)", cancelled)
    return result


class WorkerSettings:
    """arq worker entrypoint: arq metropolis.jobs.booking_sweep.WorkerSettings"""

    functions = [
        sweep_expired_bookings,
        sweep_orphan_listing_uploads,
        sweep_trip_reminders,
        sweep_stale_unpaid_bookings,
    ]
    cron_jobs = [
        cron(sweep_expired_bookings, minute=set(range(0, 60, 15))),
        cron(sweep_stale_unpaid_bookings, minute=set(range(0, 60, 30))),
        cron(sweep_orphan_listing_uploads, hour={3}, minute={30}),
        cron(sweep_trip_reminders, hour={8}, minute={0}),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = _redis_settings()
