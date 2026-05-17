from apifairy import other_responses, response
from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from metropolis.auth import require_auth
from metropolis.schemas.admin import FleetSyncSchema, RelocationSimulationSchema
from metropolis.schemas.common import ErrorSchema
from metropolis.services import marketplace_service, rental_service

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/relocation/simulate")
@require_auth("ADMIN")
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
@require_auth("ADMIN")
@response(FleetSyncSchema)
@other_responses({500: (ErrorSchema, "Database or server error.")})
def sync_fleet_listings():
    """Expose fleet as marketplace listings (FLEET source type)."""
    try:
        return marketplace_service.sync_fleet_listings()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
