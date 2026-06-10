"""Startup security checks for production configuration."""

from __future__ import annotations

import logging

logger = logging.getLogger("metropolis")

DEV_JWT_SECRET = "change-me-dev-secret"
MIN_JWT_SECRET_LEN = 32


def validate_security_config(*, jwt_secret: str, debug: bool, cors_origins: list[str]) -> None:
    if not debug and jwt_secret == DEV_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET must not use the development default when FLASK_DEBUG=0. "
            "Generate one with: openssl rand -hex 32"
        )

    if len(jwt_secret) < MIN_JWT_SECRET_LEN:
        logger.warning(
            "JWT_SECRET is shorter than %s characters; use a stronger secret in production.",
            MIN_JWT_SECRET_LEN,
        )

    if not debug:
        joined = ",".join(cors_origins)
        if "*" in joined:
            logger.warning(
                "CORS_ORIGINS contains a wildcard with FLASK_DEBUG=0; restrict to your SPA origin."
            )
