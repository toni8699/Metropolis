"""Auth routes (register, login, Google OAuth, email verification)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from vroom.core.config import settings
from vroom.core.errors import raise_for_service_result
from vroom.core.limiter import limiter
from vroom.dependencies.auth import UserContext, get_current_user
from vroom.schemas.auth_models import (
    AuthGoogleRequest,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthRegisterResponse,
    AuthResendVerificationResponse,
    AuthTokenResponse,
    AuthVerifyEmailResponse,
)
from vroom.services import auth_service, mail_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=AuthRegisterResponse)
@limiter.limit("5/minute")
def register(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: AuthRegisterRequest,
) -> dict:
    """Register account; issues JWT and sends verification email."""
    result = auth_service.register(
        email=str(payload.email),
        password=payload.password,
        full_name=payload.full_name,
    )
    raise_for_service_result(result)
    verification_token = result.pop("verification_token", None)
    if verification_token:
        background_tasks.add_task(
            mail_service.send_verification_email,
            str(payload.email),
            verification_token,
        )
        if settings.debug:
            result["verificationToken"] = verification_token
    return result


@router.post("/resend-verification", response_model=AuthResendVerificationResponse)
@limiter.limit("3/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Resend verification email for logged-in unverified user."""
    result = auth_service.resend_verification(user.user_id)
    raise_for_service_result(result)
    verification_token = result.pop("verification_token", None)
    email = result.pop("email", None)
    if verification_token and email:
        background_tasks.add_task(
            mail_service.send_verification_email,
            str(email),
            verification_token,
        )
    return result


@router.get("/verify-email", response_model=AuthVerifyEmailResponse)
@limiter.limit("20/minute")
def verify_email(request: Request, token: str = Query(min_length=1)) -> dict:
    """Mark email verified from link token."""
    result = auth_service.verify_email(token)
    raise_for_service_result(result)
    return result


@router.post("/login", response_model=AuthTokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: AuthLoginRequest) -> dict:
    """Login with email/password and get JWT."""
    result = auth_service.login(email=str(payload.email), password=payload.password)
    raise_for_service_result(result)
    return result


@router.post("/google", response_model=AuthTokenResponse)
def google_login(payload: AuthGoogleRequest) -> dict:
    """Login or register via Google ID token; issues same JWT as password login."""
    data = payload.model_dump(by_alias=True)
    result = auth_service.google_login(data["idToken"])
    raise_for_service_result(result)
    return result
