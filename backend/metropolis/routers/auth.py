"""Auth routes (register, login, Google OAuth)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from metropolis.core.errors import raise_for_service_result
from metropolis.core.limiter import limiter
from metropolis.schemas.auth_models import (
    AuthGoogleRequest,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
)
from metropolis.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=AuthTokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: AuthRegisterRequest) -> dict:
    """Register account with shared auth system."""
    data = payload.model_dump(by_alias=True)
    try:
        result = auth_service.register(
            email=str(payload.email),
            password=payload.password,
            full_name=data.get("fullName"),
            role=data.get("role", "user"),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.post("/login", response_model=AuthTokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: AuthLoginRequest) -> dict:
    """Login with email/password and get JWT."""
    try:
        result = auth_service.login(email=str(payload.email), password=payload.password)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result


@router.post("/google", response_model=AuthTokenResponse)
def google_login(payload: AuthGoogleRequest) -> dict:
    """Login or register via Google ID token; issues same JWT as password login."""
    data = payload.model_dump(by_alias=True)
    try:
        result = auth_service.google_login(data["idToken"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise_for_service_result(result)
    return result
