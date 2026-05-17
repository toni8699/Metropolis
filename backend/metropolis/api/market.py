from apifairy import arguments, other_responses, response
from flask import Blueprint
from werkzeug.exceptions import InternalServerError, NotFound

from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.marketplace import (
    ListingCollectionSchema,
    ListingItemSchema,
    ListingSearchSchema,
)
from metropolis.services import marketplace_service

bp = Blueprint("market", __name__, url_prefix="/api/market")


@bp.get("/listings")
@arguments(ListingSearchSchema)
@response(ListingCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def search_listings(query):
    """Search visible listings for map viewport."""
    try:
        return marketplace_service.search_listings(query)
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
