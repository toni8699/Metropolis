"""ASGI Socket.IO booking chat (replaces Flask-SocketIO in sockets.py)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import jwt
import socketio

from metropolis.core.config import settings
from metropolis.dependencies.auth import decode_access_token
from metropolis.services import message_service

logger = logging.getLogger(__name__)

_socket_users: dict[str, dict[str, Any]] = {}
_emit_loop: asyncio.AbstractEventLoop | None = None

if settings.redis_url:
    _client_manager: socketio.AsyncRedisManager | None = socketio.AsyncRedisManager(
        settings.redis_url
    )
else:
    # ponytail: in-process manager only — single uvicorn worker; set REDIS_URL for multi-worker
    _client_manager = None

sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=_client_manager,
    cors_allowed_origins=settings.cors_origins,
    logger=settings.debug,
    engineio_logger=settings.debug,
)


def _booking_room(booking_id: int) -> str:
    return f"booking_{booking_id}"


def _token_from_auth(auth: dict | None) -> str | None:
    if not auth:
        return None
    return auth.get("token")


def bind_emit_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _emit_loop
    _emit_loop = loop


def clear_emit_loop() -> None:
    global _emit_loop
    _emit_loop = None


def emit_booking_message(booking_id: int, message: dict) -> None:
    """Broadcast a chat message to everyone in the booking room (sync REST callers)."""
    if _emit_loop is None:
        return
    room = _booking_room(booking_id)
    asyncio.run_coroutine_threadsafe(
        sio.emit("new_message", message, room=room),
        _emit_loop,
    )


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None) -> bool:
    token = _token_from_auth(auth)
    if not token:
        return False
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except jwt.InvalidTokenError:
        return False
    except Exception:  # noqa: BLE001
        logger.exception("Socket connect failed")
        return False

    _socket_users[sid] = {
        "userId": user_id,
        "isAdmin": bool(payload.get("isAdmin")),
    }
    return True


@sio.event
async def disconnect(sid: str) -> None:
    _socket_users.pop(sid, None)


@sio.event
async def join_room(sid: str, data: dict | None) -> None:
    user = _socket_users.get(sid)
    if not user:
        await sio.emit("chat_error", {"message": "Not authenticated."}, to=sid)
        return

    booking_id = (data or {}).get("bookingId")
    if booking_id is None:
        await sio.emit("chat_error", {"message": "bookingId is required."}, to=sid)
        return

    try:
        access = await asyncio.to_thread(
            message_service.assert_booking_participant,
            int(booking_id),
            int(user["userId"]),
            bool(user.get("isAdmin")),
        )
    except Exception:  # noqa: BLE001
        logger.exception("join_room failed booking_id=%s", booking_id)
        await sio.emit("chat_error", {"message": "Could not join chat room."}, to=sid)
        return

    if access["status"] != "ok":
        await sio.emit(
            "chat_error",
            {"message": access.get("message", "Forbidden.")},
            to=sid,
        )
        return

    await sio.enter_room(sid, _booking_room(int(booking_id)))
    await sio.emit("joined", {"bookingId": int(booking_id)}, to=sid)


@sio.event
async def leave_room(sid: str, data: dict | None) -> None:
    booking_id = (data or {}).get("bookingId")
    if booking_id is None:
        return
    await sio.leave_room(sid, _booking_room(int(booking_id)))
