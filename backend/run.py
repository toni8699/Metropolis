"""Application entry point for Flask CLI and direct execution."""

from metropolis import create_app
from metropolis.config import Config

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
