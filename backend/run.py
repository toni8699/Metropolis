"""Application entry point for Flask CLI and direct execution."""

import eventlet

eventlet.monkey_patch()

from metropolis import create_app
from metropolis.config import Config
from metropolis.extensions import socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
