from apifairy import arguments, other_responses, response
from flask import Blueprint, g
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError

from metropolis.auth import require_auth
from metropolis.schemas.admin import AdminAnalyticsSchema, AnalyticsScopeSchema
from metropolis.schemas.common import ErrorSchema
from metropolis.services import marketplace_service

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("")
@require_auth()
@arguments(AnalyticsScopeSchema)
@response(AdminAnalyticsSchema)
@other_responses(
    {
        400: (ErrorSchema, "Validation error."),
        403: (ErrorSchema, "Forbidden."),
        500: (ErrorSchema, "Server error."),
    }
)
def get_analytics(query):
    """Dashboard metrics for host (owner) or admin fleet (fleet)."""
    scope = (query.get("scope") or "").strip().lower()
    try:
        if scope == "owner":
            return marketplace_service.owner_analytics(g.current_user["userId"])
        if scope == "fleet":
            if not g.current_user.get("isAdmin"):
                raise Forbidden(description="Admin access required.")
            return marketplace_service.admin_analytics()
        raise BadRequest(description="Unsupported scope. Use owner or fleet.")
    except (BadRequest, Forbidden):
        raise
    except Exception as exc:  # noqa: BLE001
        raise InternalServerError(description=str(exc)) from exc
