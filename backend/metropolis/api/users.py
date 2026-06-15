from apifairy import arguments, body, other_responses, response
from flask import Blueprint
from werkzeug.exceptions import BadRequest, InternalServerError

from metropolis.auth import require_admin
from metropolis.errors import raise_for_service_result
from metropolis.schemas.admin import (
    AdminKycQueueSchema,
    AdminKycUpdateSchema,
    AdminUsersSchema,
    KycQueueQuerySchema,
)
from metropolis.schemas.auth import KycPatchSchema
from metropolis.schemas.common import ErrorSchema
from metropolis.services import auth_service, kyc_service

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.get("")
@require_admin()
@response(AdminUsersSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def list_users():
    """List users for admin."""
    try:
        return auth_service.admin_list_users()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/kyc")
@require_admin()
@arguments(KycQueueQuerySchema)
@response(AdminKycQueueSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def list_kyc_queue(query):
    """List host identity verifications awaiting review."""
    status = (query.get("status") or "pending").strip().lower()
    if status != "pending":
        raise BadRequest(description="Only status=pending is supported.")
    try:
        return kyc_service.list_pending()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.patch("/<int:user_id>/kyc")
@require_admin()
@body(KycPatchSchema)
@response(AdminKycUpdateSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found.")})
def patch_user_kyc(payload, user_id: int):
    """Approve or reject a pending host KYC submission."""
    verification_status = payload["verificationStatus"].strip().upper()
    if verification_status not in {"VERIFIED", "REJECTED"}:
        raise BadRequest(description="verificationStatus must be VERIFIED or REJECTED.")
    try:
        result = kyc_service.set_status(user_id, verification_status)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result
