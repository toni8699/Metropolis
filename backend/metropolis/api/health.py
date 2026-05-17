from apifairy import response
from flask import Blueprint

from metropolis.schemas.common import HealthSchema

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
@response(HealthSchema)
def health():
    """Health check."""
    return {"status": "ok"}
