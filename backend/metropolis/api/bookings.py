from apifairy import body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError, NotFound

from metropolis.auth import require_auth
from metropolis.schemas.bookings import (
    BookingCreateSchema,
    BookingInstructionCreateSchema,
    BookingItemSchema,
)
from metropolis.schemas.common import ErrorSchema
from metropolis.services import marketplace_service

bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")


@bp.post("")
@require_auth("RENTER", "OWNER", "ADMIN")
@body(BookingCreateSchema)
@response(BookingItemSchema, 201)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def create_booking(payload):
    """Create booking for a listing (auto-confirm for MVP)."""
    try:
        result = marketplace_service.create_booking(int(g.current_user["sub"]), payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.get("/<int:booking_id>")
@require_auth("RENTER", "OWNER", "ADMIN")
@response(BookingItemSchema)
@other_responses({403: (ErrorSchema, "Forbidden."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def get_booking(booking_id: int):
    """Get booking details for renter, owner, or admin."""
    try:
        result = marketplace_service.get_booking(
            booking_id,
            int(g.current_user["sub"]),
            g.current_user["role"],
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    if result["status"] == "forbidden":
        raise Forbidden(description=result["message"])
    return result


@bp.post("/<int:booking_id>/instructions")
@require_auth("OWNER", "ADMIN")
@body(BookingInstructionCreateSchema)
@response(BookingItemSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def send_instruction(payload, booking_id: int):
    """Owner sends pickup/retrieval instructions."""
    try:
        instruction = marketplace_service.send_instruction(
            booking_id,
            int(g.current_user["sub"]),
            payload["message"],
        )
        if instruction["status"] == "not_found":
            raise NotFound(description=instruction["message"])
        result = marketplace_service.get_booking(
            booking_id,
            int(g.current_user["sub"]),
            g.current_user["role"],
        )
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, NotFound):
            raise
        raise InternalServerError(description=str(exc)) from exc
    return result


@bp.post("/<int:booking_id>/confirm-pickup")
@require_auth("RENTER", "OWNER", "ADMIN")
@response(BookingItemSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def confirm_pickup(booking_id: int):
    """Transition booking to IN_PROGRESS."""
    try:
        result = marketplace_service.transition_booking_status(
            booking_id,
            int(g.current_user["sub"]),
            g.current_user["role"],
            "IN_PROGRESS",
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    if result["status"] == "forbidden":
        raise Forbidden(description=result["message"])
    return result


@bp.post("/<int:booking_id>/complete")
@require_auth("RENTER", "OWNER", "ADMIN")
@response(BookingItemSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def complete_booking(booking_id: int):
    """Transition booking to COMPLETED."""
    try:
        result = marketplace_service.transition_booking_status(
            booking_id,
            int(g.current_user["sub"]),
            g.current_user["role"],
            "COMPLETED",
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    if result["status"] == "forbidden":
        raise Forbidden(description=result["message"])
    return result
