"""S3 presigned upload routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from metropolis.core.errors import raise_for_service_result
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
    result = uploads_service.presign_upload(
        user.user_id,
        user.service_role(),
        payload.model_dump(by_alias=True),
    )
    raise_for_service_result(result)
    return result


@router.post("/complete", response_model=UploadCompleteResponse)
def complete_upload(
    payload: UploadCompleteRequest,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Persist uploaded file metadata in database."""
    result = uploads_service.complete_upload(
        user.user_id,
        user.service_role(),
        payload.model_dump(by_alias=True),
    )
    raise_for_service_result(result)
    return result
