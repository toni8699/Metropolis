from apifairy import APIFairy
from flask import g, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO

ma = Marshmallow()
apifairy = APIFairy()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
socketio = SocketIO()


def rate_limit_user_or_ip() -> str:
    user = getattr(g, "current_user", None)
    if user and user.get("userId") is not None:
        return f"user:{user['userId']}"
    return get_remote_address()


def rate_limit_bearer_or_ip() -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token = header.removeprefix("Bearer ").strip()
        if token:
            return f"token:{token[:32]}"
    return get_remote_address()
