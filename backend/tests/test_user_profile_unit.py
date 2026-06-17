"""Unit tests for profile field helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from metropolis.services.auth_service import _joined_label


def test_joined_label_formats_month_and_year():
    created_at = datetime(2026, 5, 15, tzinfo=timezone.utc)
    assert _joined_label(created_at) == "Joined May 2026"


def test_joined_label_returns_none_without_date():
    assert _joined_label(None) is None
