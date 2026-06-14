from apifairy import other_responses, response
from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from metropolis.auth import require_admin
from metropolis.schemas.admin import (
    AdminCompanyLocationsSchema,
    FleetSyncSchema,
    RelocationSimulationSchema,
)
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.marketplace import VehicleClassCollectionSchema
from metropolis.services import marketplace_service, rental_service

bp = Blueprint("fleet", __name__, url_prefix="/api")


@bp.get("/vehicle-classes")
@response(VehicleClassCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def list_vehicle_classes():
    """List vehicle classes for listing forms."""
    try:
        return {
            "status": "success",
            "vehicleClasses": marketplace_service.list_vehicle_classes(),
        }
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/company-locations")
@require_admin()
@response(AdminCompanyLocationsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def list_company_locations():
    """List canonical company location sources for listing creation."""
    try:
        return marketplace_service.admin_company_locations()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.post("/fleet/sync")
@require_admin()
@response(FleetSyncSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def sync_fleet_listings():
    """Expose fleet as marketplace listings (FLEET source type)."""
    try:
        return marketplace_service.sync_fleet_listings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc


@bp.get("/simulations/relocation")
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
