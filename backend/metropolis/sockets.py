from __future__ import annotations

import logging

import jwt
from flask import request
from flask_socketio import emit, join_room, leave_room

from metropolis.auth import decode_access_token
from metropolis.extensions import socketio
from metropolis.services import message_service

logger = logging.getLogger(__name__)

_socket_users: dict[str, dict] = {}


def _booking_room(booking_id: int) -> str:
    return f"booking_{booking_id}"


def emit_booking_message(booking_id: int, message: dict) -> None:
    """Broadcast a chat message to everyone in the booking room."""
    socketio.emit("new_message", message, room=_booking_room(booking_id))


def _token_from_auth(auth: dict | None) -> str | None:
    if not auth:
        return None
    return auth.get("token")


@socketio.on("connect")
def on_connect(auth=None):
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

    _socket_users[request.sid] = {
        "userId": user_id,
        "isAdmin": bool(payload.get("isAdmin")),
    }
    return True


@socketio.on("disconnect")
def on_disconnect():
    _socket_users.pop(request.sid, None)


@socketio.on("join_room")
def on_join_room(data):
    user = _socket_users.get(request.sid)
    if not user:
        emit("chat_error", {"message": "Not authenticated."})
        return

    booking_id = (data or {}).get("bookingId")
    if booking_id is None:
        emit("chat_error", {"message": "bookingId is required."})
        return

    try:
        access = message_service.assert_booking_participant(
            int(booking_id),
            int(user["userId"]),
            bool(user.get("isAdmin")),
        )
    except Exception:  # noqa: BLE001
        logger.exception("join_room failed booking_id=%s", booking_id)
        emit("chat_error", {"message": "Could not join chat room."})
        return

    if access["status"] != "ok":
        emit("chat_error", {"message": access.get("message", "Forbidden.")})
        return

    join_room(_booking_room(int(booking_id)))
    emit("joined", {"bookingId": int(booking_id)})


@socketio.on("leave_room")
def on_leave_room(data):
    booking_id = (data or {}).get("bookingId")
    if booking_id is None:
        return
    leave_room(_booking_room(int(booking_id)))
