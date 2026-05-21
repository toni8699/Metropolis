from apifairy import other_responses, response
from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from metropolis.auth import require_admin
from metropolis.schemas.admin import (
    AdminAnalyticsSchema,
    AdminBookingsSchema,
    AdminCompanyLocationsSchema,
    AdminListingsSchema,
    AdminUsersSchema,
    FleetSyncSchema,
    RelocationSimulationSchema,
)
from metropolis.schemas.common import ErrorSchema
from metropolis.services import auth_service, marketplace_service, rental_service

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/relocation/simulate")
@require_admin()
@response(RelocationSimulationSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def simulate_relocation():
    """Run the fleet relocation planner simulation (admin)."""
    try:
        body = rental_service.simulate_relocation()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc

    if body["status"] == "error":
        raise InternalServerError(description=body["message"])
    return body


@bp.post("/fleet/sync-listings")
@require_admin()
@response(FleetSyncSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def sync_fleet_listings():
    """Expose fleet as marketplace listings (FLEET source type)."""
    try:
        return marketplace_service.sync_fleet_listings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/bookings")
@require_admin()
@response(AdminBookingsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_bookings():
    """List bookings for company fleet listings only."""
    try:
        return marketplace_service.admin_bookings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/listings")
@require_admin()
@response(AdminListingsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_listings():
    """List company fleet listings for admin."""
    try:
        return marketplace_service.admin_listings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/host-listings")
@require_admin()
@response(AdminListingsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_host_listings():
    """List host-owned (non-fleet) listings for admin moderation."""
    try:
        return marketplace_service.admin_host_listings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/company-locations")
@require_admin()
@response(AdminCompanyLocationsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_company_locations():
    """List canonical company location sources for listing creation."""
    try:
        return marketplace_service.admin_company_locations()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/users")
@require_admin()
@response(AdminUsersSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_users():
    """List users for admin."""
    try:
        return auth_service.admin_list_users()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/analytics")
@require_admin()
@response(AdminAnalyticsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def admin_analytics():
    """Get analytics for company fleet listings only."""
    try:
        return marketplace_service.admin_analytics()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
