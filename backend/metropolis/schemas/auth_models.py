"""Pydantic auth / profile schemas (FastAPI — mirrors Marshmallow auth.py)."""

from __future__ import annotations

from pydantic import ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from metropolis.schemas.camel import CamelModel


class AuthRegisterRequest(CamelModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "user"


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


class AuthTokenResponse(CamelModel):
    status: str
    token: str
    user: UserSummaryResponse


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
