from apifairy import other_responses, response
from flask import Blueprint

from metropolis.auth import require_admin
from metropolis.schemas.admin import (
    AdminCompanyLocationsSchema,
    FleetSyncSchema,
)
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.marketplace import VehicleClassCollectionSchema
from metropolis.services import fleet_service

bp = Blueprint("fleet", __name__, url_prefix="/api")


@bp.get("/vehicle-classes")
@response(VehicleClassCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def list_vehicle_classes():
    """List vehicle classes for listing forms."""
    return {
        "status": "success",
        "vehicleClasses": fleet_service.list_vehicle_classes(),
    }


@bp.get("/company-locations")
@require_admin()
@response(AdminCompanyLocationsSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def list_company_locations():
    """List canonical company location sources for listing creation."""
    return fleet_service.admin_company_locations()


@bp.post("/fleet/sync")
@require_admin()
@response(FleetSyncSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def sync_fleet_listings():
    """Expose fleet as marketplace listings (FLEET source type)."""
    return fleet_service.sync_fleet_listings()
