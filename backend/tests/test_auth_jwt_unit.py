"""JWT auth context — no DB hit per request."""

import os

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.dependencies.auth import _user_context_from_payload


def test_user_context_from_payload_maps_claims():
    ctx = _user_context_from_payload(
        {
            "sub": "42",
            "email": "host@example.com",
            "isAdmin": True,
            "hasListings": True,
        }
    )
    assert ctx.user_id == 42
    assert ctx.email == "host@example.com"
    assert ctx.is_admin is True
    assert ctx.has_listings is True
    assert ctx.service_role() == "admin"


def test_user_context_from_payload_defaults_has_listings_false():
    ctx = _user_context_from_payload({"sub": "1", "email": "u@example.com", "isAdmin": False})
    assert ctx.has_listings is False
    assert ctx.service_role() == "user"
