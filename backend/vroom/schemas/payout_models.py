"""Payout / Stripe Connect API schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from vroom.schemas.camel import CamelModel


class ConnectStatusResponse(CamelModel):
    account_id: str | None = None
    details_submitted: bool = False
    charges_enabled: bool = False
    payouts_enabled: bool = False
    ready: bool = False
    onboarding_required: bool = False
    pending_verification: bool = False


class HostPayoutItemResponse(CamelModel):
    payout_id: int
    booking_id: int
    listing_title: str | None = None
    amount_cents: int
    currency: str
    status: str
    stripe_transfer_id: str | None = None
    created_at: str


class PayoutConnectStatusResponse(CamelModel):
    status: str = "success"
    connect: ConnectStatusResponse
    recent_payouts: list[HostPayoutItemResponse] = Field(default_factory=list)


class PayoutSessionRequest(CamelModel):
    component: Literal["onboarding", "management"] = "onboarding"


class PayoutSessionResponse(CamelModel):
    status: str = "success"
    client_secret: str
    account_id: str
    component: Literal["onboarding", "management"] = "onboarding"


class PayoutDashboardLinkResponse(CamelModel):
    status: str = "success"
    dashboard_url: str
    account_id: str


class PayoutResetResponse(CamelModel):
    status: str = "success"
    message: str
