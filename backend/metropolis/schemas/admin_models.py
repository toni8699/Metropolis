"""Pydantic admin/fleet schemas (FastAPI — mirrors Marshmallow admin.py)."""

from __future__ import annotations

from typing import Any

from metropolis.schemas.camel import CamelModel


class AnalyticsScopeQuery(CamelModel):
    scope: str


class KycQueueQuery(CamelModel):
    status: str | None = None


class KycPatchRequest(CamelModel):
    verification_status: str


class FleetSyncResponse(CamelModel):
    status: str
    created: int
    existing: int


class AdminUsersResponse(CamelModel):
    status: str
    users: list[dict[str, Any]]


class AdminCompanyLocationsResponse(CamelModel):
    status: str
    areas: list[dict[str, Any]]
    branches: list[dict[str, Any]]
    parking_spots: list[dict[str, Any]]
    vehicle_classes: list[dict[str, Any]]


class AdminAnalyticsResponse(CamelModel):
    status: str
    analytics: dict[str, Any]


class AdminKycQueueResponse(CamelModel):
    status: str
    queue: list[dict[str, Any]]


class AdminKycUpdateResponse(CamelModel):
    status: str
    user_id: int
    verification_status: str


class VehicleClassCollectionResponse(CamelModel):
    status: str
    vehicle_classes: list[dict[str, Any]]
