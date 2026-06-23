"""Pydantic upload schemas."""

from __future__ import annotations

from pydantic import Field, ValidationInfo, field_validator

from metropolis.schemas.camel import CamelModel
from metropolis.trip_inspection_angles import STANDARD_ANGLE_KEYS


class UploadPresignRequest(CamelModel):
    file_name: str
    content_type: str
    scope: str
    listing_id: int | None = None
    booking_id: int | None = None
    phase: str | None = None
    angle_key: str | None = Field(default=None, alias="angleKey")
    is_extra: bool = Field(default=False, alias="isExtra")

    @field_validator("angle_key")
    @classmethod
    def check_angle_key(cls, value: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("is_extra"):
            return value
        if not value:
            raise ValueError("angleKey is required for standard inspection photos.")
        if value not in STANDARD_ANGLE_KEYS:
            raise ValueError(f"unknown angle_key: {value}")
        return value

    @field_validator("phase")
    @classmethod
    def check_phase(cls, value: str | None, info: ValidationInfo) -> str | None:
        scope = str(info.data.get("scope", "")).upper()
        if scope != "TRIP_INSPECTION":
            return value
        if not value:
            raise ValueError("phase is required for TRIP_INSPECTION uploads.")
        phase = value.upper()
        if phase not in {"CHECK_IN", "CHECK_OUT"}:
            raise ValueError("phase must be CHECK_IN or CHECK_OUT.")
        return phase

    @field_validator("booking_id")
    @classmethod
    def check_booking_id(cls, value: int | None, info: ValidationInfo) -> int | None:
        scope = str(info.data.get("scope", "")).upper()
        if scope == "TRIP_INSPECTION" and value is None:
            raise ValueError("bookingId is required for TRIP_INSPECTION uploads.")
        return value


class UploadPresignResponse(CamelModel):
    status: str
    presigned_url: str
    object_key: str
    file_url: str
    expires_in: int


class UploadCompleteRequest(CamelModel):
    object_key: str
    content_type: str | None = None
    size_bytes: int | None = None
    scope: str
    listing_id: int | None = None
    booking_id: int | None = None
    phase: str | None = None
    angle_key: str | None = Field(default=None, alias="angleKey")
    is_extra: bool = Field(default=False, alias="isExtra")

    @field_validator("angle_key")
    @classmethod
    def check_angle_key(cls, value: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("is_extra"):
            return value
        if not value:
            raise ValueError("angleKey is required for standard inspection photos.")
        if value not in STANDARD_ANGLE_KEYS:
            raise ValueError(f"unknown angle_key: {value}")
        return value

    @field_validator("phase")
    @classmethod
    def check_phase(cls, value: str | None, info: ValidationInfo) -> str | None:
        scope = str(info.data.get("scope", "")).upper()
        if scope != "TRIP_INSPECTION":
            return value
        if not value:
            raise ValueError("phase is required for TRIP_INSPECTION uploads.")
        phase = value.upper()
        if phase not in {"CHECK_IN", "CHECK_OUT"}:
            raise ValueError("phase must be CHECK_IN or CHECK_OUT.")
        return phase

    @field_validator("booking_id")
    @classmethod
    def check_booking_id(cls, value: int | None, info: ValidationInfo) -> int | None:
        scope = str(info.data.get("scope", "")).upper()
        if scope == "TRIP_INSPECTION" and value is None:
            raise ValueError("bookingId is required for TRIP_INSPECTION uploads.")
        return value


class UploadCompleteResponse(CamelModel):
    status: str
    file_id: int
    object_key: str
    file_url: str
