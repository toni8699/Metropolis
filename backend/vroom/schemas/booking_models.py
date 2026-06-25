"""Pydantic booking/payment schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from vroom.schemas.camel import CamelModel
from vroom.schemas.listing_models import LinkResponse


class ListingLocationResponse(CamelModel):
    lat: float | None = None
    lng: float | None = None
    city_zone: str | None = None
    pickup_address: str | None = None
    address: str | None = None
    geohash: str | None = None


class BookingCreateRequest(CamelModel):
    listing_id: int
    start_at: datetime
    end_at: datetime


class BookingPatchRequest(CamelModel):
    """State transitions: CONFIRMED, CANCELLED, IN_PROGRESS, COMPLETED."""

    status: str | None = None


class BookingListQuery(CamelModel):
    scope: str


class HostProfileResponse(CamelModel):
    user_id: int | None = None
    name: str | None = None
    email: str | None = None
    verified: bool


class RenterProfileResponse(CamelModel):
    user_id: int | None = None
    name: str | None = None
    email: str | None = None


class HostEarningsResponse(CamelModel):
    price_per_day: float
    day_count: int
    subtotal: float
    cleaning_fee: float
    gross_payout: float
    currency: str


class PriceBreakdownResponse(CamelModel):
    price_per_day: float
    day_count: int
    subtotal: float
    service_fee: float
    cleaning_fee: float
    security_deposit: float
    total: float
    currency: str


class TripEventResponse(CamelModel):
    event_id: int
    event_type: str
    actor_user_id: int | None = None
    event_at: str
    metadata: Any = None


class BookingResponse(CamelModel):
    booking_id: int
    listing_id: int
    listing_title: str | None = None
    source_type: str
    owner_user_id: int | None = None
    renter_user_id: int
    renter_email: str | None = None
    city_zone: str | None = None
    start_at: str
    end_at: str
    status: str
    price_snapshot: Any
    created_at: str
    updated_at: str
    needs_review: bool
    listing_photo: str | None = None
    pickup_notes: str | None = None
    listing_location: ListingLocationResponse | None = None
    host: HostProfileResponse | None = None
    renter: RenterProfileResponse | None = None
    user_role: str | None = None
    pricing: PriceBreakdownResponse | None = None
    earnings: HostEarningsResponse | None = None
    trip_events: list[TripEventResponse] | None = None
    can_cancel: bool | None = None
    can_confirm_pickup: bool | None = None
    can_complete_trip: bool | None = None
    has_inspection_photos: bool | None = None
    can_upload_check_in: bool | None = None
    can_upload_check_out: bool | None = None
    can_approve: bool | None = None
    can_reject: bool | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class BookingCollectionResponse(CamelModel):
    status: str
    scope: str | None = None
    bookings: list[BookingResponse] | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class BookingItemResponse(CamelModel):
    status: str
    booking: BookingResponse | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class PaymentIntentResponse(CamelModel):
    booking_id: int
    client_secret: str | None = None
    mock: bool | None = None
    already_paid: bool | None = None


class BookingMessageResponse(CamelModel):
    message_id: int
    booking_id: int
    sender_id: int
    sender_name: str | None = None
    message_text: str
    created_at: str


class BookingMessageCreateRequest(CamelModel):
    message_text: str


class BookingMessageItemResponse(CamelModel):
    message: BookingMessageResponse


class BookingMessageCollectionResponse(CamelModel):
    messages: list[BookingMessageResponse]


class ReviewSubmitRequest(CamelModel):
    target_type: str
    rating: int
    cleanliness: int | None = None
    accuracy: int | None = None
    communication: int | None = None
    comment: str | None = None


class ReviewResponse(CamelModel):
    review_id: int
    booking_id: int
    author_user_id: int
    author_name: str | None = None
    target_type: str
    target_user_id: int | None = None
    target_listing_id: int | None = None
    rating: int
    cleanliness: int | None = None
    accuracy: int | None = None
    communication: int | None = None
    comment: str | None = None
    created_at: str


class ReviewItemResponse(CamelModel):
    status: str
    review: ReviewResponse


class InspectionPhotoSlotResponse(CamelModel):
    angle_key: str
    group: str | None = None
    title: str
    instruction: str
    icon: str
    recommended_first: bool = False
    is_extra: bool = False
    photo: dict | None = None


class InspectionPhaseResponse(CamelModel):
    slots: list[InspectionPhotoSlotResponse]
    uploaded: int
    standard_uploaded: int | None = None
    recommended: int
    standard_total: int | None = None
    can_upload: bool


class BookingInspectionResponse(CamelModel):
    status: str
    check_in: InspectionPhaseResponse
    check_out: InspectionPhaseResponse
    expires_at: str | None = None
    purged: bool = False


class BookingInspectionDeleteResponse(CamelModel):
    status: str


class StripeWebhookResponse(CamelModel):
    received: bool = True
    status: str
