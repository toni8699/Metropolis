"""Inbox message thread routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from metropolis.core.errors import raise_for_service_result
from metropolis.dependencies.auth import UserContext, get_current_user
from metropolis.schemas.message_models import MessageThreadCollectionResponse
from metropolis.services import message_service

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("", response_model=MessageThreadCollectionResponse)
@router.get("/threads", response_model=MessageThreadCollectionResponse)
def list_message_threads(user: UserContext = Depends(get_current_user)) -> dict:
    """List inbox conversation threads for the authenticated user."""
    try:
        result = message_service.list_message_threads(user.user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return {"threads": result["threads"]}
