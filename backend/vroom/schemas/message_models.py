"""Pydantic inbox thread schemas."""

from __future__ import annotations

from vroom.schemas.camel import CamelModel


class ThreadParticipantResponse(CamelModel):
    user_id: int
    name: str | None = None
    email: str | None = None


class ThreadLatestMessageResponse(CamelModel):
    message_text: str
    created_at: str


class ThreadListingResponse(CamelModel):
    listing_id: int
    title: str | None = None
    price_per_day: float
    cover_photo: str | None = None


class ThreadPricingResponse(CamelModel):
    price_per_day: float
    day_count: int | None = None
    total: float
    currency: str


class MessageThreadResponse(CamelModel):
    booking_id: int
    listing_id: int
    status: str
    start_at: str
    end_at: str
    city_zone: str | None = None
    user_role: str
    renter_user_id: int
    owner_user_id: int
    other_party: ThreadParticipantResponse
    listing: ThreadListingResponse
    pricing: ThreadPricingResponse
    latest_message: ThreadLatestMessageResponse | None = None
    unread_count: int


class MessageThreadCollectionResponse(CamelModel):
    threads: list[MessageThreadResponse]
