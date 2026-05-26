from apifairy import arguments, other_responses, response
from flask import Blueprint
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.marketplace import (
    BookedRangeCollectionSchema,
    ListingCollectionSchema,
    ListingItemSchema,
    ListingSearchSchema,
)
from metropolis.schemas.reviews import ReviewCollectionSchema
from metropolis.services import marketplace_service, review_service

bp = Blueprint("market", __name__, url_prefix="/api/market")


@bp.get("/listings")
@arguments(ListingSearchSchema)
@response(ListingCollectionSchema)
@other_responses({400: (ErrorSchema, "Validation error."), 500: (ErrorSchema, "Server error.")})
def search_listings(query):
    """Search visible listings for map viewport; optional start_at/end_at availability filter."""
    try:
        return marketplace_service.search_listings(query)
    except BadRequest:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/listings/<int:listing_id>")
@response(ListingItemSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def get_listing(listing_id: int):
    """Get listing details by id."""
    try:
        result = marketplace_service.get_listing(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.get("/listings/<int:listing_id>/booked-ranges")
@response(BookedRangeCollectionSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def list_listing_booked_ranges(listing_id: int):
    """List booking windows that block new reservations for this listing."""
    try:
        result = marketplace_service.list_listing_booked_ranges(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result


@bp.get("/listings/<int:listing_id>/reviews")
@response(ReviewCollectionSchema)
@other_responses({404: (ErrorSchema, "Listing not found."), 500: (ErrorSchema, "Server error.")})
def list_listing_reviews(listing_id: int):
    """List public listing reviews (renter feedback on the vehicle)."""
    try:
        result = review_service.list_listing_reviews(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
    if result["status"] == "not_found":
        raise NotFound(description=result["message"])
    return result
