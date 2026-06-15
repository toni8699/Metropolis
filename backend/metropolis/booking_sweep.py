"""Background sweep for past-due bookings.

Deprecated: production uses ARQ worker (metropolis.jobs.booking_sweep).
This Flask greenlet remains for run.py until Flask is removed.
"""

from __future__ import annotations

import logging
import os

from flask import Flask

_logger = logging.getLogger("metropolis")
_started = False


def _enabled() -> bool:
    raw = os.environ.get("BOOKING_SWEEP_ENABLED")
    if raw is not None:
        return raw.strip().lower() not in {"0", "false", "no", "off"}
    # ponytail: off when FLASK_DEBUG=1 unless explicitly enabled; prod Render uses FLASK_DEBUG=0
    return os.environ.get("FLASK_DEBUG", "0") != "1"


def _interval_sec() -> int:
    return max(60, int(os.environ.get("BOOKING_SWEEP_INTERVAL_SEC", "900")))


def _run_once(app: Flask) -> None:
    from metropolis.services import booking_service

    with app.app_context():
        result = booking_service.sweep_expired_bookings()
        completed = int(result.get("completed") or 0)
        if completed:
            _logger.info("booking sweep auto-completed %s trip(s)", completed)


def _loop(app: Flask) -> None:
    import eventlet

    interval = _interval_sec()
    while True:
        try:
            _run_once(app)
        except Exception:
            _logger.exception("booking sweep failed")
        eventlet.sleep(interval)


def register_booking_sweep(app: Flask) -> None:
    """Start a daemon greenlet that completes expired trips on an interval."""
    global _started
    if _started or not _enabled():
        return
    _started = True

    import eventlet

    eventlet.spawn(_loop, app)
    _logger.info("booking sweep scheduled every %ss", _interval_sec())
