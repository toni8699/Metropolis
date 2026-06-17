"""Unit tests for profile text sanitization."""

from __future__ import annotations

from metropolis.text_sanitize import sanitize_display_text


def test_sanitize_display_text_strips_html_tags():
    assert sanitize_display_text("<script>alert(1)</script>Jane Doe") == "Jane Doe"


def test_sanitize_display_text_strips_encoded_tags():
    assert sanitize_display_text("&lt;img src=x onerror=alert(1)&gt;Sam") == "Sam"


def test_sanitize_display_text_removes_control_characters():
    assert sanitize_display_text("Jane\x00Doe") == "JaneDoe"


def test_sanitize_display_text_preserves_normal_names():
    assert sanitize_display_text("  Marie-Claire O'Brien  ") == "Marie-Claire O'Brien"
