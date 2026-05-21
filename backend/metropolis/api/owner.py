from apifairy import body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError, NotFound

from metropolis.auth import require_auth, require_listing_access
from metropolis.schemas.common import ErrorSchema, StatusSchema
from metropolis.schemas.marketplace import (
    ListingAvailabilitySchema,
    ListingCollectionSchema,
    ListingCreateSchema,
    ListingItemSchema,
    ListingLocationSchema,
    ListingUpdateSchema,
    OwnerBookingsSchema,
    VehicleClassCollectionSchema,
)
from metropolis.services import marketplace_service

bp = Blueprint("owner", __name__, url_prefix="/api/owner")


@bp.get("/vehicle-classes")
@require_auth()
@response(VehicleClassCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def owner_vehicle_classes():
    """List vehicle classes for owner listing forms."""
    try:
        return {
            "status": "success",
            "vehicleClasses": marketplace_service.list_vehicle_classes(),
        }
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/bookings")
@require_auth()
@response(OwnerBookingsSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def owner_bookings():
    """List bookings for listings owned by the authenticated user."""
    try:
        return marketplace_service.owner_bookings(g.current_user["userId"])
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/listings")
@require_auth()
@response(ListingCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def owner_listings():
    """List owner-managed listings."""
    try:
        return marketplace_service.owner_listings(g.current_user)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.post("/listings")
@require_auth()
@body(ListingCreateSchema)
@response(ListingItemSchema, 201)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def create_listing(payload):
    """Create listing for authenticated user."""
    try:
        result = marketplace_service.create_listing(g.current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "forbidden":
        raise Forbidden(description=result["message"])
    return result


@bp.patch("/listings/<int:listing_id>")
@require_listing_access("listing_id")
@body(ListingUpdateSchema)
@response(ListingItemSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def patch_listing(payload, listing_id: int):
    """Patch owner listing fields."""
    try:
        result = marketplace_service.update_listing(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.post("/listings/<int:listing_id>/location")
@require_listing_access("listing_id")
@body(ListingLocationSchema)
@response(ListingItemSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def set_location(payload, listing_id: int):
    """Upsert parking location for listing."""
    try:
        result = marketplace_service.upsert_location(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.post("/listings/<int:listing_id>/availability")
@require_listing_access("listing_id")
@body(ListingAvailabilitySchema)
@response(ListingAvailabilitySchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def add_availability(payload, listing_id: int):
    """Add availability window for listing."""
    try:
        result = marketplace_service.add_availability(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result["availability"]


@bp.delete("/listings/<int:listing_id>")
@require_listing_access("listing_id")
@response(StatusSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def delete_listing(listing_id: int):
    """Delete listing when actor has listing access."""
    try:
        result = marketplace_service.delete_listing(g.current_user, listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result
