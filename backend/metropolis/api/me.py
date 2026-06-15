from apifairy import body, other_responses, response
from flask import Blueprint

from metropolis.auth import current_user_id, require_auth
from metropolis.errors import raise_for_service_result
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
    result = auth_service.me(current_user_id())
    raise_for_service_result(result)
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
    result = auth_service.update_me(current_user_id(), payload)
    raise_for_service_result(result)
    return result
