"""Dashboard analytics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from vroom.core.errors import raise_for_service_result
from vroom.dependencies.auth import UserContext, get_current_user
from vroom.schemas.admin_models import AdminAnalyticsResponse
from vroom.services import fleet_service, listing_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AdminAnalyticsResponse)
def get_analytics(
    scope: str = Query(..., description="owner (host) or fleet (admin)."),
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Dashboard metrics for host (owner) or admin fleet (fleet)."""
    normalized = scope.strip().lower()
    try:
        if normalized == "owner":
            result = listing_service.owner_analytics(user.user_id)
        elif normalized == "fleet":
            if not user.is_admin:
                raise HTTPException(status_code=403, detail="Admin access required.")
            result = fleet_service.admin_analytics()
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported scope. Use owner or fleet.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result
