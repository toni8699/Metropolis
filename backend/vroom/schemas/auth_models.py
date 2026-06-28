"""Pydantic auth / profile schemas."""

from __future__ import annotations

import re

from pydantic import ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel

from vroom.schemas.camel import CamelModel

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_HAS_DIGIT = re.compile(r"\d")
_PASSWORD_HAS_SPECIAL = re.compile(r"[^A-Za-z0-9]")


class AuthRegisterRequest(CamelModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=1)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Full name is required.")
        return stripped

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < _PASSWORD_MIN_LENGTH:
            raise ValueError("Password must be at least 8 characters long.")
        if not _PASSWORD_HAS_DIGIT.search(value):
            raise ValueError("Password must include at least one number.")
        if not _PASSWORD_HAS_SPECIAL.search(value):
            raise ValueError("Password must include at least one special character.")
        return value


class AuthLoginRequest(CamelModel):
    email: EmailStr
    password: str


class AuthGoogleRequest(CamelModel):
    id_token: str


class UserSummaryResponse(CamelModel):
    user_id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    is_admin: bool
    has_listings: bool
    is_verified: bool = False


class AuthTokenResponse(CamelModel):
    status: str
    token: str
    user: UserSummaryResponse


class AuthRegisterResponse(CamelModel):
    status: str
    message: str
    token: str
    user: UserSummaryResponse
    verification_token: str | None = None


class AuthVerifyEmailResponse(CamelModel):
    status: str
    message: str


class AuthResendVerificationResponse(CamelModel):
    status: str
    message: str


class MeUserResponse(UserSummaryResponse):
    phone: str | None = None
    profile_photo_url: str | None = None
    created_at: str | None = None
    joined_label: str | None = None
    lives: str | None = None
    about: str | None = None
    languages: str | None = None
    work: str | None = None
    is_approved_to_drive: bool
    has_email: bool
    has_phone: bool
    trips_count: int
    average_rating: float | None = None


class MeResponse(CamelModel):
    status: str
    user: MeUserResponse


class PublicUserResponse(CamelModel):
    user_id: int
    full_name: str | None = None
    profile_photo_url: str | None = None
    created_at: str | None = None
    joined_label: str | None = None
    lives: str | None = None
    about: str | None = None
    languages: str | None = None
    work: str | None = None
    trips_count: int
    average_rating: float | None = None
    is_verified: bool = False
    is_host: bool = False


class PublicProfileResponse(CamelModel):
    status: str
    user: PublicUserResponse


class MeUpdateRequest(CamelModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        serialize_by_alias=True,
        extra="forbid",
    )

    full_name: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    profile_photo_url: str | None = Field(default=None)
    lives: str | None = Field(default=None)
    about: str | None = Field(default=None)
    languages: str | None = Field(default=None)
    work: str | None = Field(default=None)
