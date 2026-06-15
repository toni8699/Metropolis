"""Pydantic listing schemas (FastAPI — mirrors Marshmallow marketplace.py)."""

from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from metropolis.schemas.camel import CamelModel


class LinkResponse(CamelModel):
    href: str
    method: str


class ListingLocationInputRequest(CamelModel):
    lat: float
    lng: float
    city_zone: str
    pickup_address: str | None = None


class ListingAvailabilityRequest(CamelModel):
    start_at: datetime
    end_at: datetime
    status: str = "AVAILABLE"


class ListingAvailabilityResponse(ListingAvailabilityRequest):
    pass


class ListingCreateRequest(CamelModel):
    title: str
    brand: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = None
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    images: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
    rules: str | None = None
    pickup_notes_template: str | None = None
    price_per_day: float
    photos: list[str] | None = None
    lat: float | None = None
    lng: float | None = None
    city_zone: str | None = None
    pickup_address: str | None = None
    is_company_owned: bool | None = None
    area_id: int | None = None
    location_source_type: str | None = None
    branch_id: int | None = None
    parking_spot_id: int | None = None
    instant_book: bool | None = None


class ListingUpdateRequest(CamelModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        serialize_by_alias=True,
        extra="ignore",
    )

    title: str | None = None
    brand: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = None
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    images: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
    rules: str | None = None
    pickup_notes_template: str | None = None
    pickup_address: str | None = None
    price_per_day: float | None = None
    photos: list[str] | None = None
    active: bool | None = None
    status: str | None = None
    is_company_owned: bool | None = None
    lat: float | None = None
    lng: float | None = None
    city_zone: str | None = None
    instant_book: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def coerce_empty_numeric_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        for key in ("year", "mileage", "vehicleClassId", "vehicle_class_id"):
            if cleaned.get(key) == "":
                cleaned[key] = None
        return cleaned


class ListingListQuery(CamelModel):
    """GET /api/listings query parameters (public search + scoped lists)."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        serialize_by_alias=True,
        extra="ignore",
    )

    scope: str | None = None
    bbox: str | None = Field(
        default=None,
        description="minLng,minLat,maxLng,maxLat",
    )
    start_at: datetime | None = None
    end_at: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    city_zone: str | None = None

    def to_service_query(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        # ponytail: service reads start_at/end_at or start/end — not camelCase startAt
        if data.get("start_at") is None:
            data["start_at"] = data.get("startAt") or data.get("start")
        if data.get("end_at") is None:
            data["end_at"] = data.get("endAt") or data.get("end")
        if data.get("city_zone") is None and data.get("cityZone") is not None:
            data["city_zone"] = data["cityZone"]
        return data


class ListingResponse(CamelModel):
    listing_id: int
    vehicle_id: int | None = None
    source_type: str
    title: str
    brand: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = None
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    images: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
    rules: str | None = None
    pickup_notes_template: str | None = None
    price_per_day: float
    photos: list[str]
    active: bool
    status: str | None = None
    owner_user_id: int | None = None
    is_company_owned: bool
    owner_name: str | None = None
    owner_profile_photo_url: str | None = None
    fleet_vehicle_vin: str | None = None
    lat: float | None = None
    lng: float | None = None
    city_zone: str | None = None
    geohash: str | None = None
    pickup_address: str | None = None
    location_source_type: str | None = None
    branch_id: int | None = None
    parking_spot_id: int | None = None
    created_by_user_id: int | None = None
    created_at: str
    updated_at: str
    average_rating: float | None = None
    review_count: int
    instant_book: bool
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class ListingCollectionResponse(CamelModel):
    status: str
    scope: str | None = None
    listings: list[ListingResponse] | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class ListingItemResponse(CamelModel):
    status: str
    listing: ListingResponse | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class BookedRangeResponse(CamelModel):
    start_at: str
    end_at: str


class BookedRangeCollectionResponse(CamelModel):
    status: str
    ranges: list[BookedRangeResponse]


class StatusResponse(CamelModel):
    status: str


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


class ReviewCollectionResponse(CamelModel):
    status: str
    reviews: list[ReviewResponse]
