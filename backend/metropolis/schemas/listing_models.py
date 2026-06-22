"""Pydantic listing schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
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
    status: str = "BLOCKED"


class ListingAvailabilityResponse(CamelModel):
    availability_id: int
    listing_id: int
    start_at: datetime
    end_at: datetime
    status: str


class ListingAvailabilityCollectionResponse(CamelModel):
    status: str
    availability: list[ListingAvailabilityResponse]


class ListingCreateRequest(CamelModel):
    title: str | None = None
    listing_title: str | None = Field(
        default=None, validation_alias=AliasChoices("listingTitle", "listing_title")
    )
    vin: str | None = None
    make: str | None = Field(default=None, validation_alias=AliasChoices("make", "brand"))
    model: str | None = None
    year: int | None = None
    body_type_id: int | None = Field(
        default=None, validation_alias=AliasChoices("bodyTypeId", "body_type_id")
    )
    body_type_other: str | None = Field(
        default=None, validation_alias=AliasChoices("bodyTypeOther", "body_type_other")
    )
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = Field(
        default=None, validation_alias=AliasChoices("guidelines", "rules")
    )
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    feature_ids: list[int] | None = Field(
        default=None, validation_alias=AliasChoices("featureIds", "feature_ids")
    )
    images: list[str] | None = Field(
        default=None, validation_alias=AliasChoices("images", "photos")
    )
    lat: float | None = Field(default=None, validation_alias=AliasChoices("lat", "latitude"))
    lng: float | None = Field(default=None, validation_alias=AliasChoices("lng", "longitude"))
    pickup_notes_template: str | None = None
    price_per_day: float
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
    listing_title: str | None = Field(
        default=None, validation_alias=AliasChoices("listingTitle", "listing_title")
    )
    vin: str | None = None
    make: str | None = Field(default=None, validation_alias=AliasChoices("make", "brand"))
    model: str | None = None
    year: int | None = None
    body_type_id: int | None = Field(
        default=None, validation_alias=AliasChoices("bodyTypeId", "body_type_id")
    )
    body_type_other: str | None = Field(
        default=None, validation_alias=AliasChoices("bodyTypeOther", "body_type_other")
    )
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = Field(
        default=None, validation_alias=AliasChoices("guidelines", "rules")
    )
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    feature_ids: list[int] | None = Field(
        default=None, validation_alias=AliasChoices("featureIds", "feature_ids")
    )
    images: list[str] | None = Field(
        default=None, validation_alias=AliasChoices("images", "photos")
    )
    lat: float | None = Field(default=None, validation_alias=AliasChoices("lat", "latitude"))
    lng: float | None = Field(default=None, validation_alias=AliasChoices("lng", "longitude"))
    pickup_notes_template: str | None = None
    pickup_address: str | None = None
    price_per_day: float | None = None
    active: bool | None = None
    status: str | None = None
    is_company_owned: bool | None = None
    city_zone: str | None = None
    instant_book: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def coerce_empty_numeric_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        for key in (
            "year",
            "vehicleClassId",
            "vehicle_class_id",
            "bodyTypeId",
            "body_type_id",
        ):
            if cleaned.get(key) == "":
                cleaned[key] = None
        return cleaned


class ListingListQuery(CamelModel):
    """GET /api/listings query parameters (public search + scoped lists)."""

    scope: str | None = None
    bbox: str | None = Field(
        default=None,
        description="minLng,minLat,maxLng,maxLat",
    )
    start_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("start_at", "start", "startAt"),
    )
    end_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("end_at", "end", "endAt"),
    )
    city_zone: str | None = Field(
        default=None,
        validation_alias=AliasChoices("city_zone", "cityZone"),
    )
    min_price: float | None = Field(
        default=None,
        validation_alias=AliasChoices("min_price", "minPrice"),
    )
    max_price: float | None = Field(
        default=None,
        validation_alias=AliasChoices("max_price", "maxPrice"),
    )
    body_type_ids: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("body_type_ids", "bodyTypeIds"),
    )
    transmission: Literal["AUTOMATIC", "MANUAL"] | None = None
    fuel_types: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("fuel_types", "fuelTypes"),
    )
    seats: list[int] | None = None
    seats_gte: int | None = Field(
        default=None,
        validation_alias=AliasChoices("seats_gte", "seatsGte"),
    )
    feature_ids: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("feature_ids", "featureIds"),
    )
    limit: int = Field(default=24, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("body_type_ids", "seats", "feature_ids", mode="before")
    @classmethod
    def parse_comma_separated_ints(cls, value: object) -> object:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return [int(part) for part in parts if part.isdigit()]
        return value

    @field_validator("fuel_types", mode="before")
    @classmethod
    def parse_comma_separated_strings(cls, value: object) -> object:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


class ListingResponse(CamelModel):
    listing_id: int
    vehicle_id: int | None = None
    source_type: str
    title: str
    listing_title: str | None = Field(default=None, serialization_alias="listingTitle")
    vin: str | None = None
    is_vin_verified: bool | None = Field(default=None, serialization_alias="isVinVerified")
    make: str | None = None
    model: str | None = None
    year: int | None = None
    body_type_id: int | None = Field(default=None, serialization_alias="bodyTypeId")
    body_type_other: str | None = Field(default=None, serialization_alias="bodyTypeOther")
    vehicle_class_id: int | None = None
    description: str | None = None
    guidelines: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    seats: int | None = None
    doors: int | None = None
    features: list[str] | None = None
    feature_ids: list[int] | None = Field(default=None, serialization_alias="featureIds")
    images: list[str] | None = None
    lat: float | None = None
    lng: float | None = None
    pickup_notes_template: str | None = None
    price_per_day: float
    active: bool
    status: str | None = None
    owner_user_id: int | None = None
    is_company_owned: bool
    owner_name: str | None = None
    owner_profile_photo_url: str | None = None
    fleet_vehicle_vin: str | None = None
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

    @computed_field
    @property
    def brand(self) -> str | None:
        return self.make

    @computed_field
    @property
    def latitude(self) -> float | None:
        return self.lat

    @computed_field
    @property
    def longitude(self) -> float | None:
        return self.lng

    @computed_field
    @property
    def photos(self) -> list[str] | None:
        return self.images

    @computed_field
    @property
    def rules(self) -> str | None:
        return self.guidelines


class ListingCollectionResponse(CamelModel):
    status: str
    scope: str | None = None
    listings: list[ListingResponse] | None = None
    total_count: int | None = Field(default=None, serialization_alias="totalCount")
    limit: int | None = None
    offset: int | None = None
    links: dict[str, LinkResponse] | None = Field(default=None, alias="_links")


class ListingCountResponse(CamelModel):
    status: str
    total_count: int = Field(serialization_alias="totalCount")


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


class SavedListingsResponse(CamelModel):
    status: str
    saved_listing_ids: list[int] = Field(serialization_alias="savedListingIds")
    listings: list[ListingResponse]


class SavedListingToggleResponse(CamelModel):
    status: str
    listing_id: int = Field(serialization_alias="listingId")
    saved: bool
    saved_listing_ids: list[int] = Field(serialization_alias="savedListingIds")
