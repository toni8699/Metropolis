"""Unit tests for profile photo URL validation."""

from __future__ import annotations

from vroom.services.auth_service import _normalize_profile_photo_url


def test_normalize_profile_photo_url_accepts_null():
    assert _normalize_profile_photo_url(None) is None
    assert _normalize_profile_photo_url("") is None
    assert _normalize_profile_photo_url("   ") is None


def test_normalize_profile_photo_url_rejects_invalid():
    assert _normalize_profile_photo_url("not-a-url") is False
    assert _normalize_profile_photo_url("https://evil.example/avatar/x") is False
