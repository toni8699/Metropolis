"""FastAPI auth dependencies (replaces Flask JWT decorators)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from metropolis.core.config import settings
from metropolis.core.db import RealDictCursor, get_connection

http_bearer = HTTPBearer(auto_error=False)


class UserContext(BaseModel):
    user_id: int
    email: str | None = None
    is_admin: bool = False
    has_listings: bool = False

    def service_role(self) -> str:
        return "admin" if self.is_admin else "user"


class ListingAccessContext(BaseModel):
    """Verified listing ownership (or admin override) for guarded routes."""

    listing_id: int
    owner_user_id: int
    user: UserContext


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def create_access_token(
    user_id: int,
    email: str,
    is_admin: bool,
    *,
    has_listings: bool = False,
) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "admin" if is_admin else "user",
        "isAdmin": bool(is_admin),
        "hasListings": bool(has_listings),
        "exp": datetime.now(UTC) + timedelta(hours=settings.jwt_expires_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _user_context_from_payload(payload: dict) -> UserContext:
    is_admin = bool(payload.get("isAdmin"))
    return UserContext(
        user_id=int(payload["sub"]),
        email=payload.get("email"),
        is_admin=is_admin,
        has_listings=bool(payload.get("hasListings")),
    )


def _resolve_user_from_token(token: str) -> UserContext:
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc
    return _user_context_from_payload(payload)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> UserContext:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing Bearer token.")
    return _resolve_user_from_token(creds.credentials)


def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required.")
    return user


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> UserContext | None:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        return None
    try:
        return _resolve_user_from_token(creds.credentials)
    except HTTPException:
        return None


def require_listing_access(
    listing_id: int,
    user: UserContext = Depends(get_current_user),
) -> ListingAccessContext:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT listing_id, owner_user_id
                FROM vehicle_listing
                WHERE listing_id = %s
                """,
                (listing_id,),
            )
            listing = cur.fetchone()

    if not listing:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if not user.is_admin and listing["owner_user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    return ListingAccessContext(
        listing_id=int(listing["listing_id"]),
        owner_user_id=int(listing["owner_user_id"]),
        user=user,
    )
