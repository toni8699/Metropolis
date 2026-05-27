"""Structured request context and production logging to stdout."""

from __future__ import annotations

import logging
import os
from typing import Any

import jwt
from flask import Flask, current_app, g, has_request_context, request

logger = logging.getLogger("metropolis")


def _decode_user_id_from_bearer() -> int | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None


def _extract_booking_id() -> int | None:
    view_args = request.view_args or {}
    raw = view_args.get("booking_id")
    if raw is not None:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    if request.is_json:
        body = request.get_json(silent=True) or {}
        for key in ("bookingId", "booking_id"):
            if key in body:
                try:
                    return int(body[key])
                except (TypeError, ValueError):
                    return None
    return None


def _extract_listing_id() -> int | None:
    view_args = request.view_args or {}
    raw = view_args.get("listing_id")
    if raw is not None:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    if request.is_json:
        body = request.get_json(silent=True) or {}
        for key in ("listingId", "listing_id"):
            if key in body:
                try:
                    return int(body[key])
                except (TypeError, ValueError):
                    return None
    return None


class RequestContextFilter(logging.Filter):
    """Attach request-scoped ids to every log record in a request."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.user_id = None
        record.booking_id = None
        record.listing_id = None
        record.request_id = None
        record.path = None

        if not has_request_context():
            return True

        current_user = getattr(g, "current_user", None)
        if isinstance(current_user, dict) and current_user.get("userId") is not None:
            record.user_id = current_user["userId"]
        elif getattr(g, "_log_user_id", None) is not None:
            record.user_id = g._log_user_id

        record.booking_id = getattr(g, "_log_booking_id", None)
        record.listing_id = getattr(g, "_log_listing_id", None)
        record.request_id = request.headers.get("X-Request-Id")
        record.path = request.path
        return True


def configure_logging(app: Flask) -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO" if not app.debug else "DEBUG").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_format = os.environ.get(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s [%(name)s] "
        "user=%(user_id)s booking=%(booking_id)s listing=%(listing_id)s "
        "path=%(path)s — %(message)s",
    )

    logging.basicConfig(level=level, format=log_format, force=True)
    context_filter = RequestContextFilter()
    for handler in logging.root.handlers:
        handler.addFilter(context_filter)

    app.logger.setLevel(level)


def register_observability(app: Flask) -> None:
    configure_logging(app)

    @app.before_request
    def _bind_request_logging_context() -> None:
        user_id = _decode_user_id_from_bearer()
        booking_id = _extract_booking_id()
        listing_id = _extract_listing_id()

        g._log_user_id = user_id
        g._log_booking_id = booking_id
        g._log_listing_id = listing_id

        if hasattr(g, "current_user") and isinstance(g.current_user, dict):
            g._log_user_id = g.current_user.get("userId") or user_id

    @app.after_request
    def _log_server_errors(response: Any) -> Any:
        if response.status_code >= 500:
            logger.error(
                "HTTP %s %s",
                response.status_code,
                request.path,
                extra={
                    "user_id": getattr(g, "_log_user_id", None),
                    "booking_id": getattr(g, "_log_booking_id", None),
                    "listing_id": getattr(g, "_log_listing_id", None),
                },
            )
        return response
