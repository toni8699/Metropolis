from __future__ import annotations

from metropolis.services.booking_support import booking_day_count


def _listing_photo_from_row(row: dict) -> str | None:
    urls = row.get("listing_image_urls") or []
    if isinstance(urls, list) and urls:
        first = urls[0]
        return str(first) if first else None
    return None


def _host_is_verified(verification_status: str | None) -> bool:
    return str(verification_status or "").upper() == "VERIFIED"


def build_price_breakdown(row: dict) -> dict:
    snapshot = row.get("price_snapshot_json") or {}
    if isinstance(snapshot, str):
        snapshot = {}
    start_at = row["start_at"]
    end_at = row["end_at"]
    fallback_price = float(row.get("listing_price_per_day") or 0)
    day_count = int(snapshot.get("dayCount") or booking_day_count(start_at, end_at))
    price_per_day = float(snapshot.get("pricePerDay") or fallback_price)
    subtotal = float(snapshot.get("subtotal") or round(price_per_day * day_count, 2))
    cleaning_fee = float(snapshot.get("cleaningFee", 50))
    service_fee = float(snapshot.get("serviceFee") or round(subtotal * 0.1, 2))
    security_deposit = float(snapshot.get("securityDeposit", 0))
    total = float(
        snapshot.get("total") or round(subtotal + cleaning_fee + service_fee + security_deposit, 2)
    )
    return {
        "pricePerDay": price_per_day,
        "dayCount": day_count,
        "subtotal": subtotal,
        "serviceFee": service_fee,
        "cleaningFee": cleaning_fee,
        "securityDeposit": security_deposit,
        "total": total,
        "currency": snapshot.get("currency") or "CAD",
    }


def build_host_earnings(pricing: dict) -> dict:
    subtotal = float(pricing.get("subtotal") or 0)
    cleaning_fee = float(pricing.get("cleaningFee") or 0)
    return {
        "pricePerDay": pricing.get("pricePerDay"),
        "dayCount": pricing.get("dayCount"),
        "subtotal": subtotal,
        "cleaningFee": cleaning_fee,
        "grossPayout": round(subtotal + cleaning_fee, 2),
        "currency": pricing.get("currency") or "CAD",
    }


def to_booking_row(row: dict, *, include_detail: bool = False) -> dict:
    payload = {
        "bookingId": row["booking_id"],
        "listingId": row["listing_id"],
        "listingTitle": row["listing_title"],
        "sourceType": row["source_type"],
        "ownerUserId": row["owner_user_id"],
        "renterUserId": row["renter_user_id"],
        "renterEmail": row.get("renter_email"),
        "cityZone": row.get("city_zone"),
        "startAt": row["start_at"].isoformat(),
        "endAt": row["end_at"].isoformat(),
        "status": row["status"],
        "priceSnapshot": row["price_snapshot_json"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
        "needsReview": bool(row.get("needs_review")),
    }
    if not include_detail:
        return payload

    lat = row.get("lat")
    lng = row.get("lng")
    payload.update(
        {
            "listingPhoto": _listing_photo_from_row(row),
            "pickupNotes": row.get("pickup_notes_template"),
            "listingLocation": {
                "lat": float(lat) if lat is not None else None,
                "lng": float(lng) if lng is not None else None,
                "cityZone": row.get("city_zone"),
                "pickupAddress": row.get("pickup_address"),
                "geohash": row.get("geohash"),
            },
            "host": {
                "userId": row.get("host_user_id") or row.get("owner_user_id"),
                "name": row.get("host_name") or row.get("owner_name"),
                "email": row.get("host_email"),
                "verified": _host_is_verified(row.get("host_verification_status")),
            },
            "pricing": build_price_breakdown(row),
            "tripEvents": row.get("trip_events") or [],
            "canCancel": bool(row.get("can_cancel")),
            "canConfirmPickup": bool(row.get("can_confirm_pickup")),
            "canCompleteTrip": bool(row.get("can_complete_trip")),
        }
    )
    return payload
