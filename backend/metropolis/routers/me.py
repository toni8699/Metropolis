"""Current user profile routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from metropolis.core.errors import raise_for_service_result
from metropolis.dependencies.auth import UserContext, get_current_user
from metropolis.schemas.auth_models import MeResponse, MeUpdateRequest
from metropolis.schemas.listing_models import SavedListingsResponse, SavedListingToggleResponse
from metropolis.services import auth_service, saved_listing_service

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me", response_model=MeResponse)
def me(user: UserContext = Depends(get_current_user)) -> dict:
    """Current authenticated user."""
    result = auth_service.me(user.user_id)
    raise_for_service_result(result)
    return result


@router.patch("/me", response_model=MeResponse)
def update_me(
    payload: MeUpdateRequest,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Update current authenticated user's profile."""
    result = auth_service.update_me(user.user_id, payload.model_dump(by_alias=True))
    raise_for_service_result(result)
    return result


@router.get("/me/saved-listings", response_model=SavedListingsResponse)
def list_saved_listings(user: UserContext = Depends(get_current_user)) -> dict:
    """List listings saved by the current user."""
    result = saved_listing_service.list_saved(user.user_id)
    raise_for_service_result(result)
    return result


@router.post(
    "/me/saved-listings/{listing_id}",
    status_code=201,
    response_model=SavedListingToggleResponse,
)
def save_listing(
    listing_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Save a listing to the current user's favorites."""
    result = saved_listing_service.save_listing(user.user_id, listing_id)
    raise_for_service_result(result)
    return result


@router.delete(
    "/me/saved-listings/{listing_id}",
    response_model=SavedListingToggleResponse,
)
def unsave_listing(
    listing_id: int,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Remove a listing from the current user's favorites."""
    result = saved_listing_service.unsave_listing(user.user_id, listing_id)
    raise_for_service_result(result)
    return result
