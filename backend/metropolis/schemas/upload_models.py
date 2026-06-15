"""Pydantic upload schemas (FastAPI — mirrors Marshmallow uploads.py)."""

from __future__ import annotations

from metropolis.schemas.camel import CamelModel


class UploadPresignRequest(CamelModel):
    file_name: str
    content_type: str
    scope: str
    listing_id: int | None = None


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


class UploadCompleteResponse(CamelModel):
    status: str
    file_id: int
    object_key: str
    file_url: str
