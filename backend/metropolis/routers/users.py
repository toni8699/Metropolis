"""Admin user and KYC routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from metropolis.core.errors import raise_for_service_result
from metropolis.dependencies.auth import UserContext, require_admin
from metropolis.schemas.admin_models import (
    AdminKycQueueResponse,
    AdminKycUpdateResponse,
    AdminUsersResponse,
    KycPatchRequest,
)
from metropolis.services import auth_service, kyc_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=AdminUsersResponse)
def list_users(_admin: UserContext = Depends(require_admin)) -> dict:
    """List users for admin."""
    try:
        result = auth_service.admin_list_users()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.get("/kyc", response_model=AdminKycQueueResponse)
def list_kyc_queue(
    status: str | None = Query(None),
    _admin: UserContext = Depends(require_admin),
) -> dict:
    """List host identity verifications awaiting review."""
    normalized = (status or "pending").strip().lower()
    if normalized != "pending":
        raise HTTPException(status_code=400, detail="Only status=pending is supported.")
    try:
        result = kyc_service.list_pending()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.patch("/{user_id}/kyc", response_model=AdminKycUpdateResponse)
def patch_user_kyc(
    payload: KycPatchRequest,
    user_id: int,
    _admin: UserContext = Depends(require_admin),
) -> dict:
    """Approve or reject a pending host KYC submission."""
    verification_status = payload.verification_status.strip().upper()
    if verification_status not in {"VERIFIED", "REJECTED"}:
        raise HTTPException(
            status_code=400,
            detail="verificationStatus must be VERIFIED or REJECTED.",
        )
    try:
        result = kyc_service.set_status(user_id, verification_status)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result
