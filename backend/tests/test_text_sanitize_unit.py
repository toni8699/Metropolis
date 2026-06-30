"""Unit tests for profile text sanitization."""

from __future__ import annotations

from vroom.services.marketplace_common import sanitize_listing_text_payload
from vroom.text_sanitize import sanitize_display_text


def test_sanitize_listing_text_payload_strips_script_from_fields():
    cleaned = sanitize_listing_text_payload(
        {
            "title": "<script>alert(1)</script>My Car",
            "description": "Great ride <img src=x onerror=alert(1)>",
            "pricePerDay": 49.0,
        }
    )
    assert cleaned["title"] == "My Car"
    assert "<" not in cleaned["description"] and ">" not in cleaned["description"]
    # Non-text fields pass through untouched.
    assert cleaned["pricePerDay"] == 49.0


def test_sanitize_display_text_strips_html_tags():
    assert sanitize_display_text("<script>alert(1)</script>Jane Doe") == "Jane Doe"


def test_sanitize_display_text_strips_encoded_tags():
    assert sanitize_display_text("&lt;img src=x onerror=alert(1)&gt;Sam") == "Sam"


def test_sanitize_display_text_removes_control_characters():
    assert sanitize_display_text("Jane\x00Doe") == "JaneDoe"


def test_sanitize_display_text_preserves_normal_names():
    assert sanitize_display_text("  Marie-Claire O'Brien  ") == "Marie-Claire O'Brien"
