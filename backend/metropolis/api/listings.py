from apifairy import arguments, body, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError, Unauthorized

from metropolis.auth import optional_auth, require_auth, require_listing_access
from metropolis.errors import raise_for_service_result
from metropolis.hateoas import with_listing_links
from metropolis.schemas.common import ErrorSchema, StatusSchema
from metropolis.schemas.marketplace import (
    BookedRangeCollectionSchema,
    ListingAvailabilitySchema,
    ListingCollectionSchema,
    ListingCreateSchema,
    ListingItemSchema,
    ListingListSchema,
    ListingLocationInputSchema,
    ListingUpdateSchema,
)
from metropolis.schemas.reviews import ReviewCollectionSchema
from metropolis.services import fleet_service, listing_service, review_service

bp = Blueprint("listings", __name__, url_prefix="/api/listings")


@bp.get("")
@optional_auth()
@arguments(ListingListSchema)
@response(ListingCollectionSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        401: (ErrorSchema, "Authentication required."),
        403: (ErrorSchema, "Forbidden."),
        500: (ErrorSchema, "Server error."),
    }
)
def list_listings(query):
    """Search public listings or list scoped collections (mine, fleet, host)."""
    scope = (query.get("scope") or "").strip().lower()
    try:
        if not scope:
            result = listing_service.search_listings(query)
            return with_listing_links(result)
        if scope == "mine":
            if not g.get("current_user"):
                raise Unauthorized(description="Authentication required.")
            result = listing_service.owner_listings(g.current_user)
            result["scope"] = scope
            return with_listing_links(result, can_edit=True)
        if scope == "fleet":
            if not g.get("current_user"):
                raise Unauthorized(description="Authentication required.")
            if not g.current_user.get("isAdmin"):
                raise Forbidden(description="Admin access required.")
            result = fleet_service.admin_listings()
            result["scope"] = scope
            return with_listing_links(result, can_edit=True)
        if scope == "host":
            if not g.get("current_user"):
                raise Unauthorized(description="Authentication required.")
            if not g.current_user.get("isAdmin"):
                raise Forbidden(description="Admin access required.")
            result = fleet_service.admin_host_listings()
            result["scope"] = scope
            return with_listing_links(result)
        raise BadRequest(description="Unsupported scope. Use mine, fleet, or host.")
    except (BadRequest, Forbidden, Unauthorized):
        raise
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/<int:listing_id>")
@optional_auth()
@response(ListingItemSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def get_listing(listing_id: int):
    """Get listing details by id."""
    try:
        result = listing_service.get_listing(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    raise_for_service_result(result)
    can_edit = bool(
        g.get("current_user")
        and (
            g.current_user.get("isAdmin")
            or result.get("listing", {}).get("ownerUserId") == g.current_user.get("userId")
        )
    )
    return with_listing_links(result, can_edit=can_edit)


@bp.post("")
@require_auth()
@body(ListingCreateSchema)
@response(ListingItemSchema, 201)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def create_listing(payload):
    """Create listing for authenticated user."""
    try:
        result = listing_service.create_listing(g.current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@bp.patch("/<int:listing_id>")
@require_listing_access("listing_id")
@body(ListingUpdateSchema)
@response(ListingItemSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        404: (ErrorSchema, "Not found."),
        500: (ErrorSchema, "Server error."),
    }
)
def patch_listing(payload, listing_id: int):
    """Patch listing fields."""
    try:
        result = listing_service.update_listing(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@bp.delete("/<int:listing_id>")
@require_listing_access("listing_id")
@response(StatusSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def delete_listing(listing_id: int):
    """Delete listing when actor has listing access."""
    try:
        result = listing_service.delete_listing(g.current_user, listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result


@bp.post("/<int:listing_id>/location")
@require_listing_access("listing_id")
@body(ListingLocationInputSchema)
@response(ListingItemSchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def set_location(payload, listing_id: int):
    """Upsert parking location for listing."""
    try:
        result = listing_service.upsert_location(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@bp.post("/<int:listing_id>/availability")
@require_listing_access("listing_id")
@body(ListingAvailabilitySchema)
@response(ListingAvailabilitySchema)
@other_responses({404: (ErrorSchema, "Not found."), 500: (ErrorSchema, "Server error.")})
def add_availability(payload, listing_id: int):
    """Add availability window for listing."""
    try:
        result = listing_service.add_availability(g.current_user, listing_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result["availability"]


@bp.get("/<int:listing_id>/booked-ranges")
@response(BookedRangeCollectionSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def list_listing_booked_ranges(listing_id: int):
    """List booking windows that block new reservations for this listing."""
    try:
        result = listing_service.list_listing_booked_ranges(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result


@bp.get("/<int:listing_id>/reviews")
@response(ReviewCollectionSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def list_listing_reviews(listing_id: int):
    """List public listing reviews (renter feedback on the vehicle)."""
    try:
        result = review_service.list_listing_reviews(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    raise_for_service_result(result)
    return result
