from flask import Flask

from metropolis.api.analytics import bp as analytics_bp
from metropolis.api.auth import bp as auth_bp
from metropolis.api.bookings import bp as bookings_bp
from metropolis.api.fleet import bp as fleet_bp
from metropolis.api.health import bp as health_bp
from metropolis.api.listings import bp as listings_bp
from metropolis.api.me import bp as me_bp
from metropolis.api.messages import bp as messages_bp
from metropolis.api.uploads import bp as uploads_bp
from metropolis.api.users import bp as users_bp
from metropolis.api.webhooks import bp as webhooks_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(webhooks_bp)
