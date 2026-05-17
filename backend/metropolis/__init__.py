from flask import Flask
from flask_cors import CORS

from metropolis.api import register_blueprints
from metropolis.config import Config
from metropolis.errors import register_error_handlers
from metropolis.extensions import apifairy, limiter, ma, sqldb
from metropolis.models import sqlalchemy_models  # noqa: F401


def create_app(config: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    settings = config or Config

    app.config.from_object(settings)

    CORS(
        app,
        resources={r"/api/*": {"origins": settings.CORS_ORIGINS}},
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    ma.init_app(app)
    sqldb.init_app(app)
    limiter.init_app(app)
    apifairy.init_app(app)
    register_error_handlers(app)
    register_blueprints(app)
    return app


app = create_app()
