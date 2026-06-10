import os

from flask import Flask
from flask_cors import CORS

from metropolis.api import register_blueprints
from metropolis.config import Config
from metropolis.errors import register_error_handlers
from metropolis.extensions import apifairy, limiter, ma, socketio, sqldb
from metropolis.models import sqlalchemy_models  # noqa: F401
from metropolis.observability import register_observability
from metropolis.security import validate_security_config


def create_app(config: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    settings = config or Config

    app.config.from_object(settings)
    validate_security_config(
        jwt_secret=settings.JWT_SECRET,
        debug=settings.DEBUG,
        cors_origins=settings.CORS_ORIGINS,
    )

    CORS(
        app,
        resources={r"/api/*": {"origins": settings.CORS_ORIGINS}},
    )

    redis_url = os.environ.get("REDIS_URL", "").strip() or None
    socketio.init_app(
        app,
        cors_allowed_origins=settings.CORS_ORIGINS,
        async_mode=os.environ.get("SOCKETIO_ASYNC_MODE", "eventlet"),
        message_queue=redis_url,
        logger=settings.DEBUG,
        engineio_logger=settings.DEBUG,
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    ma.init_app(app)
    sqldb.init_app(app)
    limiter.init_app(app)
    apifairy.init_app(app)
    register_error_handlers(app)
    register_observability(app)
    register_blueprints(app)
    import metropolis.sockets  # noqa: F401

    return app


app = create_app()
