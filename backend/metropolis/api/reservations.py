from apifairy import arguments, other_responses, response
from flask import Blueprint
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.reservations import (
    ReservationLookupResponseSchema,
    ReservationQuerySchema,
)
from metropolis.services import rental_service

bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")


@bp.get("")
@arguments(ReservationQuerySchema)
@response(ReservationLookupResponseSchema)
@other_responses(
    {
        400: (ErrorSchema, "Invalid or missing email."),
        404: (ErrorSchema, "Customer or reservations not found."),
        500: (ErrorSchema, "Database or server error."),
    }
)
def list_reservations(query):
    """Look up reservations for a customer by email."""
    try:
        body = rental_service.get_reservations_by_email(query["email"])
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    status = body["status"]
    if status == "validation_error":
        raise BadRequest(description=body["message"])
    if status == "not_found":
        raise NotFound(description=body["message"])
    if status == "error":
        raise InternalServerError(description=body["message"])
    return body
