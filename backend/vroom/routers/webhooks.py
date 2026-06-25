"""External webhooks (Stripe — no JWT)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from vroom.schemas.booking_models import StripeWebhookResponse
from vroom.services.payment_service import payment_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", response_model=StripeWebhookResponse)
async def stripe_webhook(request: Request) -> dict:
    """Stripe payment webhook (signature verified against raw body)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    result = payment_service.handle_webhook(payload, sig_header)
    if result["status"] == "validation_error":
        raise HTTPException(status_code=400, detail="Invalid webhook.")
    return {"received": True, "status": result["status"]}
