from apifairy import body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from metropolis.auth import require_auth
from metropolis.schemas.auth import MeSchema, MeUpdateSchema
from metropolis.schemas.common import ErrorSchema
from metropolis.services import auth_service

bp = Blueprint("me", __name__, url_prefix="/api")


@bp.get("/me")
@require_auth()
@response(MeSchema)
@other_responses({404: (ErrorSchema, "User not found."), 500: (ErrorSchema, "Server error.")})
def me():
    """Current authenticated user."""
    try:
        result = auth_service.me(int(g.current_user["sub"]))
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.patch("/me")
@require_auth()
@body(MeUpdateSchema)
@response(MeSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        404: (ErrorSchema, "User not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def update_me(payload):
    """Update current authenticated user's profile."""
    try:
        result = auth_service.update_me(
            int(g.current_user["sub"]),
            payload,
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    if result["status"] != "success":
        raise BadRequest(description=result["message"])
    return result
