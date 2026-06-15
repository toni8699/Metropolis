from apifairy import arguments, body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError

from metropolis.auth import current_user_id, require_auth
from metropolis.errors import raise_for_service_result
from metropolis.extensions import limiter, rate_limit_user_or_ip
from metropolis.hateoas import with_booking_links
from metropolis.schemas.bookings import (
    BookingCollectionSchema,
    BookingCreateSchema,
    BookingItemSchema,
    BookingListSchema,
    BookingPatchSchema,
)
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.messages import (
    BookingMessageCollectionSchema,
    BookingMessageCreateSchema,
    BookingMessageItemSchema,
)
from metropolis.schemas.payments import PaymentIntentResponseSchema
from metropolis.schemas.reviews import ReviewItemSchema, ReviewSubmitSchema
from metropolis.services import (
    booking_service,
    fleet_service,
    message_service,
    payment_service,
    review_service,
)
from metropolis.sockets import emit_booking_message

bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")


@bp.get("")
@require_auth()
@arguments(BookingListSchema)
@response(BookingCollectionSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        500: (ErrorSchema, "Server error."),
    }
)
def list_bookings(query):
    """List bookings for renter (mine), host (owner), or admin fleet (fleet)."""
    scope = (query.get("scope") or "").strip().lower()
    try:
        if scope == "mine":
            result = booking_service.list_renter_bookings(current_user_id())
        elif scope == "owner":
            result = booking_service.owner_bookings(current_user_id())
        elif scope == "fleet":
            if not g.current_user.get("isAdmin"):
                raise Forbidden(description="Admin access required.")
            result = fleet_service.admin_bookings()
        else:
            raise BadRequest(description="Unsupported scope. Use mine, owner, or fleet.")
        result["scope"] = scope
        return with_booking_links(result)
    except (BadRequest, Forbidden):
        raise
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.post("")
@require_auth()
@limiter.limit("20 per minute", key_func=rate_limit_user_or_ip)
@body(BookingCreateSchema)
@response(BookingItemSchema, 201)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def create_booking(payload):
    """Create booking (status PENDING until payment succeeds)."""
    try:
        result = booking_service.create_booking(current_user_id(), payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return with_booking_links(result)


@bp.get("/<int:booking_id>")
@require_auth()
@response(BookingItemSchema)
@other_responses(
    {
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def get_booking(booking_id: int):
    """Get booking details for renter, owner, or admin."""
    try:
        result = booking_service.get_booking(
            booking_id,
            current_user_id(),
            g.current_user["isAdmin"],
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    raise_for_service_result(result)
    return with_booking_links(result)


@bp.patch("/<int:booking_id>")
@require_auth()
@body(BookingPatchSchema)
@response(BookingItemSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def patch_booking(payload, booking_id: int):
    """Update booking status."""
    try:
        result = booking_service.patch_booking(
            booking_id,
            current_user_id(),
            g.current_user["isAdmin"],
            payload,
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return with_booking_links(result)


@bp.post("/<int:booking_id>/payments")
@require_auth()
@response(PaymentIntentResponseSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def create_booking_payment(booking_id: int):
    """Create Stripe PaymentIntent for a pending booking (dev auto-completes without keys)."""
    try:
        result = payment_service.create_payment_intent(booking_id, current_user_id())
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result


@bp.get("/<int:booking_id>/messages")
@require_auth()
@response(BookingMessageCollectionSchema)
@other_responses(
    {
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def list_booking_messages(booking_id: int):
    """Return the complete booking chat thread (created_at ASC, no pagination)."""
    try:
        result = message_service.list_booking_messages(
            booking_id,
            current_user_id(),
            g.current_user["isAdmin"],
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    raise_for_service_result(result)
    return {"messages": result["messages"]}


@bp.post("/<int:booking_id>/messages")
@require_auth()
@body(BookingMessageCreateSchema)
@response(BookingMessageItemSchema, 201)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def create_booking_message(payload, booking_id: int):
    """Send a chat message for a booking (renter or host only)."""
    try:
        result = message_service.create_booking_message(
            booking_id,
            current_user_id(),
            payload["messageText"],
            g.current_user["isAdmin"],
        )
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    raise_for_service_result(result)

    message = result["message"]
    emit_booking_message(booking_id, message)
    return {"message": message}


@bp.post("/<int:booking_id>/reviews")
@require_auth()
@body(ReviewSubmitSchema)
@response(ReviewItemSchema, 201)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def submit_review(payload, booking_id: int):
    """Submit listing or renter feedback for a completed booking."""
    try:
        result = review_service.submit_review(
            booking_id,
            current_user_id(),
            payload["targetType"],
            payload["rating"],
            payload.get("comment"),
            payload.get("cleanliness"),
            payload.get("accuracy"),
            payload.get("communication"),
        )
    except ValueError as exc:
        raise BadRequest(description=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result
