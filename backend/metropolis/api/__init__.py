from flask import Flask

from metropolis.api.admin import bp as admin_bp
from metropolis.api.auth import bp as auth_bp
from metropolis.api.bookings import bp as bookings_bp
from metropolis.api.health import bp as health_bp
from metropolis.api.market import bp as market_bp
from metropolis.api.me import bp as me_bp
from metropolis.api.owner import bp as owner_bp
from metropolis.api.reservations import bp as reservations_bp
from metropolis.api.uploads import bp as uploads_bp
from metropolis.api.vehicles import bp as vehicles_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(admin_bp)
