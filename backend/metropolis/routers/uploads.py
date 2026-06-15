"""S3 presigned upload routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from metropolis.core.errors import raise_werkzeug_as_http
from metropolis.dependencies.auth import UserContext, get_current_user
from metropolis.schemas.upload_models import (
    UploadCompleteRequest,
    UploadCompleteResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from metropolis.services import uploads_service

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/presign", response_model=UploadPresignResponse)
def presign_upload(
    payload: UploadPresignRequest,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Create a presigned S3 upload URL."""
    try:
        return uploads_service.presign_upload(
            user.user_id,
            user.service_role(),
            payload.model_dump(by_alias=True),
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise_werkzeug_as_http(exc)


@router.post("/complete", response_model=UploadCompleteResponse)
def complete_upload(
    payload: UploadCompleteRequest,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Persist uploaded file metadata in database."""
    try:
        return uploads_service.complete_upload(
            user.user_id,
            user.service_role(),
            payload.model_dump(by_alias=True),
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise_werkzeug_as_http(exc)
