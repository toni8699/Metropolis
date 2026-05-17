from apifairy import other_responses, response
from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.vehicles import AreaAvailabilitySchema
from metropolis.services import rental_service

bp = Blueprint("vehicles", __name__, url_prefix="/api/vehicles")


@bp.get("/available")
@response(AreaAvailabilitySchema(many=True))
@other_responses({500: (ErrorSchema, "Database or server error.")})
def available_by_area():
    """List available vehicle counts grouped by area."""
    try:
        return rental_service.list_available_vehicles_by_area()
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
