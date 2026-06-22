"""Stripe Connect payout routes for hosts."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from metropolis.core.errors import raise_for_service_result
from metropolis.dependencies.auth import UserContext, get_current_user
from metropolis.schemas.payout_models import PayoutConnectStatusResponse, PayoutOnboardResponse
from metropolis.services.payout_service import payout_service

router = APIRouter(prefix="/api/payouts", tags=["payouts"])


@router.get("/connect/status", response_model=PayoutConnectStatusResponse)
def connect_status(user: UserContext = Depends(get_current_user)) -> dict:
    """Connect onboarding status and recent host payouts."""
    return payout_service.get_connect_status(user.user_id)


@router.post("/connect/onboard", response_model=PayoutOnboardResponse)
def connect_onboard(user: UserContext = Depends(get_current_user)) -> dict:
    """Create or resume Stripe Express onboarding."""
    result = payout_service.create_onboarding_link(user.user_id, user.email)
    raise_for_service_result(result)
    return result


@router.post("/connect/refresh", response_model=PayoutOnboardResponse)
def connect_refresh(user: UserContext = Depends(get_current_user)) -> dict:
    """Refresh expired AccountLink (same as onboard)."""
    result = payout_service.create_onboarding_link(user.user_id, user.email)
    raise_for_service_result(result)
    return result
