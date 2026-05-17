from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, g, request
from werkzeug.exceptions import Forbidden, Unauthorized


def create_access_token(user_id: int, email: str, role: str) -> str:
    expires_hours = int(current_app.config.get("JWT_EXPIRES_HOURS", 24))
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
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


def require_auth(*roles: str):
    normalized = {r.upper() for r in roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = get_bearer_token()
            try:
                payload = decode_access_token(token)
            except jwt.ExpiredSignatureError as exc:
                raise Unauthorized(description="Token expired.") from exc
            except jwt.InvalidTokenError as exc:
                raise Unauthorized(description="Invalid token.") from exc

            role = str(payload.get("role", "")).upper()
            if normalized and role not in normalized:
                raise Forbidden(description="Insufficient role.")
            g.current_user = payload
            return fn(*args, **kwargs)

        return wrapper

    return decorator
