"""FastAPI application factory (Phase 1 foundation)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from metropolis.core.config import settings
from metropolis.core.db import dispose_db, init_db
from metropolis.core.errors import register_exception_handlers
from metropolis.core.limiter import limiter
from metropolis.routers import (
    analytics,
    auth,
    bookings,
    fleet,
    health,
    listings,
    me,
    messages,
    uploads,
    users,
    webhooks,
)
from metropolis.security import validate_security_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    from metropolis.sockets.booking_chat import bind_emit_loop, clear_emit_loop

    validate_security_config(
        jwt_secret=settings.jwt_secret,
        debug=settings.debug,
        cors_origins=settings.cors_origins,
    )
    if settings.database_url:
        max_overflow = max(0, settings.db_pool_max - settings.db_pool_min)
        init_db(
            settings.database_url,
            pool_size=settings.db_pool_min,
            max_overflow=max_overflow,
        )
    bind_emit_loop(asyncio.get_running_loop())
    yield
    clear_emit_loop()
    dispose_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    limiter.enabled = settings.ratelimit_enabled
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(analytics.router)
    app.include_router(users.router)
    app.include_router(fleet.router)
    app.include_router(listings.router)
    app.include_router(bookings.router)
    app.include_router(messages.router)
    app.include_router(uploads.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
