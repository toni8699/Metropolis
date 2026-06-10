from apifairy import other_responses
from flask import Blueprint, request
from werkzeug.exceptions import BadRequest

from metropolis.schemas.common import ErrorSchema
from metropolis.services.payment_service import payment_service

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.post("/stripe")
@other_responses({400: (ErrorSchema, "Invalid webhook.")})
def stripe_webhook():
    """Stripe payment webhook (no JWT; signature verified)."""
    result = payment_service.handle_webhook(
        request.get_data(),
        request.headers.get("Stripe-Signature"),
    )
    if result["status"] == "validation_error":
        raise BadRequest(description=result["message"])
    return {"received": True, "status": result["status"]}
