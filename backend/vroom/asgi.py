"""Combined ASGI entrypoint: Socket.IO mounted on FastAPI (production + dev)."""

from __future__ import annotations

import socketio
from starlette.types import ASGIApp, Receive, Scope, Send

from vroom.main import create_app
from vroom.sockets.booking_chat import sio

fastapi_app = create_app()
_sio_asgi = socketio.ASGIApp(sio, socketio_path="socket.io")


def _is_socketio_path(path: str) -> bool:
    return path == "/socket.io" or path.startswith("/socket.io/")


class CombinedASGI:
    """Route /socket.io/* to Engine.IO before FastAPI (avoids Starlette 404 fallback)."""

    def __init__(self, socketio_app: ASGIApp, api_app: ASGIApp) -> None:
        self._socketio_app = socketio_app
        self._api_app = api_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._api_app(scope, receive, send)
            return
        if scope["type"] in {"http", "websocket"} and _is_socketio_path(scope.get("path", "")):
            await self._socketio_app(scope, receive, send)
            return
        await self._api_app(scope, receive, send)


app = CombinedASGI(_sio_asgi, fastapi_app)
