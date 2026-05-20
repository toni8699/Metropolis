from apifairy import body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import InternalServerError

from metropolis.auth import require_auth
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.uploads import (
    UploadCompleteRequestSchema,
    UploadCompleteResponseSchema,
    UploadPresignRequestSchema,
    UploadPresignResponseSchema,
)
from metropolis.services import uploads_service

bp = Blueprint("uploads", __name__, url_prefix="/api/uploads")


@bp.post("/presign")
@require_auth()
@body(UploadPresignRequestSchema)
@response(UploadPresignResponseSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def presign_upload(payload):
    """Create a presigned S3 upload URL."""
    try:
        return uploads_service.presign_upload(
            int(g.current_user["sub"]),
            str(g.current_user.get("role", "user")),
            payload,
        )
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "code", None):
            raise
        raise InternalServerError(description=str(exc)) from exc


@bp.post("/complete")
@require_auth()
@body(UploadCompleteRequestSchema)
@response(UploadCompleteResponseSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def complete_upload(payload):
    """Persist uploaded file metadata in database."""
    try:
        return uploads_service.complete_upload(
            int(g.current_user["sub"]),
            str(g.current_user.get("role", "user")),
            payload,
        )
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "code", None):
            raise
        raise InternalServerError(description=str(exc)) from exc
