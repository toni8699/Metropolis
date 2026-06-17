"""Booking routes (trips, payments, messages, reviews)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from metropolis.core.errors import raise_for_service_result
from metropolis.core.limiter import limiter, rate_limit_user_or_ip
from metropolis.dependencies.auth import UserContext, get_current_user, verified_user_required
from metropolis.hateoas import with_booking_links
from metropolis.schemas.booking_models import (
    BookingCollectionResponse,
    BookingCreateRequest,
    BookingItemResponse,
    BookingListQuery,
    BookingMessageCollectionResponse,
    BookingMessageCreateRequest,
    BookingMessageItemResponse,
    BookingPatchRequest,
    PaymentIntentResponse,
    ReviewItemResponse,
    ReviewSubmitRequest,
)
from metropolis.services import (
    booking_service,
    fleet_service,
    message_service,
    payment_service,
    review_service,
)
from metropolis.sockets.booking_chat import emit_booking_message

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _emit_booking_message_safe(booking_id: int, message: dict) -> None:
    try:
        emit_booking_message(booking_id, message)
    except Exception:
        pass


def _booking_list_query(scope: str = Query(...)) -> BookingListQuery:
    return BookingListQuery(scope=scope)


@router.get("", response_model=BookingCollectionResponse)
def list_bookings(
    query: BookingListQuery = Depends(_booking_list_query),
    user: UserContext = Depends(get_current_user),
) -> dict:
    """List bookings for renter (mine), host (owner), or admin fleet (fleet)."""
    scope = query.scope.strip().lower()
    try:
        if scope == "mine":
            result = booking_service.list_renter_bookings(user.user_id)
        elif scope == "owner":
            result = booking_service.owner_bookings(user.user_id)
        elif scope == "fleet":
            if not user.is_admin:
                raise HTTPException(status_code=403, detail="Admin access required.")
            result = fleet_service.admin_bookings()
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported scope. Use mine, owner, or fleet.",
            )
        result["scope"] = scope
        return with_booking_links(result)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("", status_code=201, response_model=BookingItemResponse)
@limiter.limit("20/minute", key_func=rate_limit_user_or_ip)
def create_booking(
    request: Request,
    payload: BookingCreateRequest,
    user: UserContext = Depends(verified_user_required),
) -> dict:
    """Create booking (status PENDING until payment succeeds). Requires verified email."""
    try:
        result = booking_service.create_booking(
            user.user_id,
            payload.model_dump(by_alias=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_booking_links(result)


@router.get("/{booking_id}", response_model=BookingItemResponse)
def get_booking(
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Get booking details for renter, owner, or admin."""
    try:
        result = booking_service.get_booking(
            booking_id,
            user.user_id,
            user.is_admin,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_booking_links(result)


@router.patch("/{booking_id}", response_model=BookingItemResponse)
def patch_booking(
    payload: BookingPatchRequest,
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Update booking status (approve, reject, cancel, pickup, complete)."""
    try:
        result = booking_service.patch_booking(
            booking_id,
            user.user_id,
            user.is_admin,
            payload.model_dump(by_alias=True, exclude_unset=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_booking_links(result)


@router.post("/{booking_id}/payments", response_model=PaymentIntentResponse)
def create_booking_payment(
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Create Stripe PaymentIntent for a pending booking."""
    try:
        result = payment_service.create_payment_intent(booking_id, user.user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.get("/{booking_id}/messages", response_model=BookingMessageCollectionResponse)
def list_booking_messages(
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Return the complete booking chat thread (created_at ASC)."""
    try:
        result = message_service.list_booking_messages(
            booking_id,
            user.user_id,
            user.is_admin,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return {"messages": result["messages"]}


@router.post("/{booking_id}/messages", status_code=201, response_model=BookingMessageItemResponse)
def create_booking_message(
    payload: BookingMessageCreateRequest,
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Send a chat message for a booking (renter or host only)."""
    try:
        result = message_service.create_booking_message(
            booking_id,
            user.user_id,
            payload.message_text,
            user.is_admin,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    message = result["message"]
    _emit_booking_message_safe(booking_id, message)
    return {"message": message}


@router.post("/{booking_id}/reviews", status_code=201, response_model=ReviewItemResponse)
def submit_review(
    payload: ReviewSubmitRequest,
    booking_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Submit listing or renter feedback for a completed booking."""
    data = payload.model_dump(by_alias=True)
    try:
        result = review_service.submit_review(
            booking_id,
            user.user_id,
            data["targetType"],
            data["rating"],
            data.get("comment"),
            data.get("cleanliness"),
            data.get("accuracy"),
            data.get("communication"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result
