from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, g, request
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import Forbidden, Unauthorized

from metropolis.db import get_connection

def _load_user_context(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT user_id, email, full_name, phone, created_at, is_admin
                FROM app_user
                WHERE user_id = %s
                """,
                (user_id,),
            )
            user = cur.fetchone()
            if not user:
                raise Unauthorized(description="User not found.")
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM vehicle_listing
                    WHERE owner_user_id = %s
                ) AS has_listings
                """,
                (user_id,),
            )
            has_listings = bool(cur.fetchone()["has_listings"])

    return {
        "userId": user["user_id"],
        "sub": str(user["user_id"]),
        "email": user["email"],
        "fullName": user.get("full_name"),
        "phone": user.get("phone"),
        "createdAt": user["created_at"].isoformat() if user.get("created_at") else None,
        "role": "admin" if user.get("is_admin") else "user",
        "isAdmin": bool(user.get("is_admin")),
        "hasListings": has_listings,
    }


def create_access_token(user_id: int, email: str, is_admin: bool) -> str:
    expires_hours = int(current_app.config.get("JWT_EXPIRES_HOURS", 24))
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "admin" if is_admin else "user",
        "isAdmin": bool(is_admin),
        "exp": datetime.now(UTC) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
    )


def get_bearer_token() -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized(description="Missing Bearer token.")
    return header.removeprefix("Bearer ").strip()


def _resolve_request_user() -> dict:
    token = get_bearer_token()
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized(description="Token expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized(description="Invalid token.") from exc

    return _load_user_context(int(payload["sub"]))


def require_auth():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            g.current_user = _resolve_request_user()
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_admin():
    def decorator(fn):
        @wraps(fn)
        @require_auth()
        def wrapper(*args, **kwargs):
            if not g.current_user["isAdmin"]:
                raise Forbidden(description="Admin required.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _can_access_listing(user: dict, listing_row: dict) -> bool:
    if user["isAdmin"]:
        return True
    return listing_row["owner_user_id"] == user["userId"]


def require_listing_access(listing_arg: str = "listing_id"):
    def decorator(fn):
        @wraps(fn)
        @require_auth()
        def wrapper(*args, **kwargs):
            listing_id = kwargs.get(listing_arg)
            if listing_id is None:
                raise Unauthorized(description=f"Missing listing identifier: {listing_arg}.")

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
                raise Forbidden(description="Listing not found.")
            if not _can_access_listing(g.current_user, listing):
                raise Forbidden(description="No listing access.")

            g.listing_access = listing
            return fn(*args, **kwargs)

        return wrapper

    return decorator
