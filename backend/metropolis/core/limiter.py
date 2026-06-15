"""Rate limiting (slowapi — mirrors Flask-Limiter setup)."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_user_or_ip(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        try:
            from metropolis.dependencies.auth import decode_access_token

            payload = decode_access_token(token)
            return f"user:{payload['sub']}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address, default_limits=[])
