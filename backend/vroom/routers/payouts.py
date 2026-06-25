"""Stripe Connect payout routes for hosts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor

from vroom.core.db import get_connection
from vroom.core.errors import raise_for_service_result
from vroom.dependencies.auth import UserContext, get_current_user
from vroom.schemas.payout_models import (
    PayoutConnectStatusResponse,
    PayoutDashboardLinkResponse,
    PayoutResetResponse,
    PayoutSessionRequest,
    PayoutSessionResponse,
)
from vroom.services.payout_service import payout_service

router = APIRouter(prefix="/api/payouts", tags=["payouts"])


def _resolve_host_email(user: UserContext) -> str | None:
    if user.email:
        return user.email
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT email FROM app_user WHERE user_id = %s", (user.user_id,))
            row = cur.fetchone()
    return row["email"] if row else None


@router.get("/connect/status", response_model=PayoutConnectStatusResponse)
def connect_status(user: UserContext = Depends(get_current_user)) -> dict:
    """Connect onboarding status and recent host payouts."""
    return payout_service.get_connect_status(user.user_id)


@router.post("/connect/session", response_model=PayoutSessionResponse)
def connect_session(
    body: PayoutSessionRequest | None = None,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """AccountSession client secret for embedded Connect onboarding or management."""
    payload = body or PayoutSessionRequest()
    result = payout_service.create_account_session(
        user.user_id,
        _resolve_host_email(user),
        component=payload.component,
    )
    raise_for_service_result(result)
    return result


@router.post("/connect/dashboard", response_model=PayoutDashboardLinkResponse)
def connect_dashboard(user: UserContext = Depends(get_current_user)) -> dict:
    """Stripe Express dashboard login link (ready accounts only)."""
    result = payout_service.create_express_dashboard_link(user.user_id)
    raise_for_service_result(result)
    return result


@router.post("/connect/reset", response_model=PayoutResetResponse)
def connect_reset(user: UserContext = Depends(get_current_user)) -> dict:
    """Unlink Stripe Connect account (debug only)."""
    result = payout_service.reset_connect_account(user.user_id)
    raise_for_service_result(result)
    return result
