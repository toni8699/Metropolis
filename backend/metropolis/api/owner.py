from apifairy import body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from metropolis.auth import require_auth
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.marketplace import (
    ListingAvailabilitySchema,
    ListingCollectionSchema,
    ListingCreateSchema,
    ListingItemSchema,
    ListingLocationSchema,
    ListingUpdateSchema,
)
from metropolis.services import marketplace_service

bp = Blueprint("owner", __name__, url_prefix="/api/owner")


@bp.get("/listings")
@require_auth("OWNER", "ADMIN")
@response(ListingCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def owner_listings():
    """List owner-managed listings."""
    try:
        return marketplace_service.owner_listings(int(g.current_user["sub"]))
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.post("/listings")
@require_auth("OWNER", "ADMIN")
@body(ListingCreateSchema)
@response(ListingItemSchema, 201)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def create_listing(payload):
    """Create a new owner listing."""
    try:
        result = marketplace_service.create_owner_listing(int(g.current_user["sub"]), payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    return result


@bp.patch("/listings/<int:listing_id>")
@require_auth("OWNER", "ADMIN")
@body(ListingUpdateSchema)
@response(ListingItemSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def patch_listing(payload, listing_id: int):
    """Patch owner listing fields."""
    try:
        result = marketplace_service.update_listing(int(g.current_user["sub"]), listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.post("/listings/<int:listing_id>/location")
@require_auth("OWNER", "ADMIN")
@body(ListingLocationSchema)
@response(ListingItemSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def set_location(payload, listing_id: int):
    """Upsert parking location for listing."""
    try:
        result = marketplace_service.upsert_location(int(g.current_user["sub"]), listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.post("/listings/<int:listing_id>/availability")
@require_auth("OWNER", "ADMIN")
@body(ListingAvailabilitySchema)
@response(ListingAvailabilitySchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def add_availability(payload, listing_id: int):
    """Add availability window for listing."""
    try:
        result = marketplace_service.add_availability(int(g.current_user["sub"]), listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result["availability"]
