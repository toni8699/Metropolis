"""Payout / Stripe Connect API schemas."""

from __future__ import annotations

from pydantic import Field

from metropolis.schemas.camel import CamelModel


class ConnectStatusResponse(CamelModel):
    account_id: str | None = None
    details_submitted: bool = False
    charges_enabled: bool = False
    payouts_enabled: bool = False
    ready: bool = False


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


class PayoutOnboardResponse(CamelModel):
    status: str = "success"
    onboarding_url: str
    account_id: str
