"""Unit tests for profile field helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from vroom.services.auth_service import AuthService, _joined_label


def test_joined_label_formats_month_and_year():
    created_at = datetime(2026, 5, 15, tzinfo=timezone.utc)
    assert _joined_label(created_at) == "Joined May 2026"


def test_joined_label_returns_none_without_date():
    assert _joined_label(None) is None


def test_public_user_never_exposes_private_fields():
    row = {
        "user_id": 7,
        "email": "secret@example.com",
        "phone": "+15145550100",
        "password_hash": "hash",
        "full_name": "Pat Host",
        "profile_photo_url": None,
        "lives": "Toronto, ON",
        "about": "Hi",
        "languages": "English",
        "work": "Driver",
        "created_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "is_verified": True,
        "is_admin": True,
    }
    public = AuthService()._format_public_user(
        row, has_listings=True, trips_count=3, average_rating=4.5
    )
    assert {"email", "phone", "password_hash", "isAdmin"}.isdisjoint(public)
    assert public["userId"] == 7
    assert public["fullName"] == "Pat Host"
    assert public["isHost"] is True
    assert public["joinedLabel"] == "Joined June 2026"
