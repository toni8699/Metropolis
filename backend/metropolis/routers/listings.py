"""Listing routes (search, CRUD, location, availability, reviews)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from metropolis.core.errors import raise_for_service_result
from metropolis.dependencies.auth import (
    ListingAccessContext,
    UserContext,
    get_current_user,
    get_optional_user,
    require_listing_access,
)
from metropolis.hateoas import with_listing_links
from metropolis.schemas.listing_models import (
    BookedRangeCollectionResponse,
    ListingAvailabilityRequest,
    ListingAvailabilityResponse,
    ListingCollectionResponse,
    ListingCreateRequest,
    ListingItemResponse,
    ListingListQuery,
    ListingLocationInputRequest,
    ListingUpdateRequest,
    ReviewCollectionResponse,
    StatusResponse,
)
from metropolis.services import fleet_service, listing_service, review_service

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _actor_from_user(user: UserContext) -> dict:
    return {
        "userId": user.user_id,
        "sub": str(user.user_id),
        "email": user.email,
        "role": "admin" if user.is_admin else "user",
        "isAdmin": user.is_admin,
        "hasListings": user.has_listings,
    }


def parse_listing_list_query(request: Request) -> ListingListQuery:
    """Read listing search query params (FastAPI CamelModel only binds camelCase aliases)."""
    qp = request.query_params
    payload: dict = {}
    if scope := qp.get("scope"):
        payload["scope"] = scope
    if bbox := qp.get("bbox"):
        payload["bbox"] = bbox
    if city_zone := qp.get("city_zone") or qp.get("cityZone"):
        payload["city_zone"] = city_zone
    start_s = qp.get("start_at") or qp.get("start") or qp.get("startAt")
    end_s = qp.get("end_at") or qp.get("end") or qp.get("endAt")
    if start_s:
        payload["start_at"] = start_s
    if end_s:
        payload["end_at"] = end_s
    return ListingListQuery.model_validate(payload)


@router.get("", response_model=ListingCollectionResponse)
def list_listings(
    request: Request,
    user: UserContext | None = Depends(get_optional_user),
) -> dict:
    """Search public listings or list scoped collections (mine, fleet, host)."""
    query = parse_listing_list_query(request)
    scope = (query.scope or "").strip().lower()
    if not scope:
        result = listing_service.search_listings(
            query.model_dump(exclude_none=True, by_alias=False),
        )
        raise_for_service_result(result)
        return with_listing_links(result)
    if scope == "mine":
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        result = listing_service.owner_listings(_actor_from_user(user))
        result["scope"] = scope
        return with_listing_links(result, can_edit=True)
    if scope == "fleet":
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required.")
        result = fleet_service.admin_listings()
        result["scope"] = scope
        return with_listing_links(result, can_edit=True)
    if scope == "host":
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required.")
        result = fleet_service.admin_host_listings()
        result["scope"] = scope
        return with_listing_links(result)
    raise HTTPException(
        status_code=400,
        detail="Unsupported scope. Use mine, fleet, or host.",
    )


@router.get("/{listing_id}", response_model=ListingItemResponse)
def get_listing(
    listing_id: int,
    user: UserContext | None = Depends(get_optional_user),
) -> dict:
    """Get listing details by id."""
    try:
        result = listing_service.get_listing(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    raise_for_service_result(result)
    can_edit = bool(
        user and (user.is_admin or result.get("listing", {}).get("ownerUserId") == user.user_id)
    )
    return with_listing_links(result, can_edit=can_edit)


@router.post("", status_code=201, response_model=ListingItemResponse)
def create_listing(
    payload: ListingCreateRequest,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Create listing for authenticated user."""
    try:
        result = listing_service.create_listing(
            _actor_from_user(user),
            payload.model_dump(by_alias=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@router.patch("/{listing_id}", response_model=ListingItemResponse)
def patch_listing(
    payload: ListingUpdateRequest,
    listing_id: int,
    access: ListingAccessContext = Depends(require_listing_access),
) -> dict:
    """Patch listing fields."""
    try:
        result = listing_service.update_listing(
            _actor_from_user(access.user),
            listing_id,
            payload.model_dump(by_alias=True, exclude_unset=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@router.delete("/{listing_id}", response_model=StatusResponse)
def delete_listing(
    listing_id: int,
    access: ListingAccessContext = Depends(require_listing_access),
) -> dict:
    """Delete listing when actor has listing access."""
    try:
        result = listing_service.delete_listing(_actor_from_user(access.user), listing_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.post("/{listing_id}/location", response_model=ListingItemResponse)
def set_location(
    payload: ListingLocationInputRequest,
    listing_id: int,
    access: ListingAccessContext = Depends(require_listing_access),
) -> dict:
    """Upsert parking location for listing."""
    try:
        result = listing_service.upsert_location(
            _actor_from_user(access.user),
            listing_id,
            payload.model_dump(by_alias=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return with_listing_links(result, can_edit=True)


@router.post("/{listing_id}/availability", response_model=ListingAvailabilityResponse)
def add_availability(
    payload: ListingAvailabilityRequest,
    listing_id: int,
    access: ListingAccessContext = Depends(require_listing_access),
) -> dict:
    """Add availability window for listing."""
    try:
        result = listing_service.add_availability(
            _actor_from_user(access.user),
            listing_id,
            payload.model_dump(by_alias=True),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result["availability"]


@router.get("/{listing_id}/booked-ranges", response_model=BookedRangeCollectionResponse)
def list_listing_booked_ranges(listing_id: int) -> dict:
    """List booking windows that block new reservations for this listing."""
    try:
        result = listing_service.list_listing_booked_ranges(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.get("/{listing_id}/reviews", response_model=ReviewCollectionResponse)
def list_listing_reviews(listing_id: int) -> dict:
    """List public listing reviews (renter feedback on the vehicle)."""
    try:
        result = review_service.list_listing_reviews(listing_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result
