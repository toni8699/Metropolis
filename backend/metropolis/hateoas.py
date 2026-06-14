"""Hypermedia links for REST responses."""

from __future__ import annotations

from typing import Any


def _link(href: str, method: str = "GET") -> dict[str, str]:
    return {"href": href, "method": method}


def booking_links(booking: dict[str, Any]) -> dict[str, dict[str, str]]:
    booking_id = booking.get("bookingId")
    if not booking_id:
        return {}

    links: dict[str, dict[str, str]] = {
        "self": _link(f"/api/bookings/{booking_id}"),
        "messages": _link(f"/api/bookings/{booking_id}/messages"),
        "listing": _link(f"/api/listings/{booking['listingId']}"),
    }

    if booking.get("canApprove"):
        links["approve"] = _link(f"/api/bookings/{booking_id}", "PATCH")
    if booking.get("canReject"):
        links["reject"] = _link(f"/api/bookings/{booking_id}", "PATCH")
    if booking.get("canCancel"):
        links["cancel"] = _link(f"/api/bookings/{booking_id}", "PATCH")
    if booking.get("canConfirmPickup"):
        links["confirmPickup"] = _link(f"/api/bookings/{booking_id}", "PATCH")
    if booking.get("canCompleteTrip"):
        links["complete"] = _link(f"/api/bookings/{booking_id}", "PATCH")
    if booking.get("status") == "PENDING":
        links["payment"] = _link(f"/api/bookings/{booking_id}/payments", "POST")
    if booking.get("status") == "COMPLETED" and booking.get("needsReview"):
        links["reviews"] = _link(f"/api/bookings/{booking_id}/reviews", "POST")

    return links


def listing_links(listing: dict[str, Any], *, can_edit: bool = False) -> dict[str, dict[str, str]]:
    listing_id = listing.get("listingId")
    if not listing_id:
        return {}

    links: dict[str, dict[str, str]] = {
        "self": _link(f"/api/listings/{listing_id}"),
        "reviews": _link(f"/api/listings/{listing_id}/reviews"),
        "bookedRanges": _link(f"/api/listings/{listing_id}/booked-ranges"),
    }
    if can_edit:
        links["update"] = _link(f"/api/listings/{listing_id}", "PATCH")
        links["delete"] = _link(f"/api/listings/{listing_id}", "DELETE")
        links["location"] = _link(f"/api/listings/{listing_id}/location", "POST")
        links["availability"] = _link(f"/api/listings/{listing_id}/availability", "POST")
    return links


def collection_links(path: str, *, query: str | None = None) -> dict[str, dict[str, str]]:
    href = f"{path}?{query}" if query else path
    return {"self": _link(href)}


def with_booking_links(result: dict[str, Any]) -> dict[str, Any]:
    booking = result.get("booking")
    if booking:
        booking["_links"] = booking_links(booking)
    bookings = result.get("bookings")
    if bookings:
        for item in bookings:
            if isinstance(item, dict) and item.get("bookingId"):
                item["_links"] = booking_links(item)
    if "bookings" in result or "booking" in result:
        scope = result.get("scope")
        query = f"scope={scope}" if scope else None
        result["_links"] = collection_links("/api/bookings", query=query)
    return result


def with_listing_links(
    result: dict[str, Any],
    *,
    can_edit: bool = False,
) -> dict[str, Any]:
    listing = result.get("listing")
    if listing:
        listing["_links"] = listing_links(listing, can_edit=can_edit)
    listings = result.get("listings")
    if listings:
        for item in listings:
            if isinstance(item, dict) and item.get("listingId"):
                item["_links"] = listing_links(item, can_edit=can_edit)
    if "listings" in result or "listing" in result:
        scope = result.get("scope")
        query = f"scope={scope}" if scope else None
        result["_links"] = collection_links("/api/listings", query=query)
    return result
