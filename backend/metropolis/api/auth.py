from apifairy import body, other_responses, response
from flask import Blueprint
from werkzeug.exceptions import BadRequest, InternalServerError

from metropolis.schemas.auth import AuthLoginSchema, AuthRegisterSchema, AuthTokenSchema
from metropolis.schemas.common import ErrorSchema
from metropolis.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
@body(AuthRegisterSchema)
@response(AuthTokenSchema, 201)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def register(payload):
    """Register account with shared auth system."""
    try:
        result = auth_service.register(
            email=payload["email"],
            password=payload["password"],
            full_name=payload.get("fullName"),
            role=payload.get("role", "user"),
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] != "success":
        raise BadRequest(description=result["message"])
    return result


@bp.post("/login")
@body(AuthLoginSchema)
@response(AuthTokenSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def login(payload):
    """Login with email/password and get JWT."""
    try:
        result = auth_service.login(email=payload["email"], password=payload["password"])
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] != "success":
        raise BadRequest(description=result["message"])
    return result
