from apifairy import other_responses, response
from flask import Blueprint, g

from metropolis.auth import require_auth
from metropolis.schemas.common import ErrorSchema
from metropolis.schemas.messages import MessageThreadCollectionSchema
from metropolis.services import message_service

bp = Blueprint("messages", __name__, url_prefix="/api/messages")


@bp.get("/threads")
@require_auth()
@response(MessageThreadCollectionSchema)
@other_responses({500: (ErrorSchema, "Server error.")})
def list_message_threads():
    """List inbox conversation threads for the authenticated user."""
    result = message_service.list_message_threads(int(g.current_user["userId"]))
    return {"threads": result["threads"]}
