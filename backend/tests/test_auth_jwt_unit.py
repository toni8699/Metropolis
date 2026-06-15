"""JWT auth context — no DB hit per request."""

import os

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.auth import _user_context_from_jwt


def test_user_context_from_jwt_maps_claims():
    ctx = _user_context_from_jwt(
        {
            "sub": "42",
            "email": "host@example.com",
            "isAdmin": True,
            "hasListings": True,
        }
    )
    assert ctx["userId"] == 42
    assert ctx["email"] == "host@example.com"
    assert ctx["isAdmin"] is True
    assert ctx["hasListings"] is True
    assert ctx["role"] == "admin"


def test_user_context_from_jwt_defaults_has_listings_false():
    ctx = _user_context_from_jwt({"sub": "1", "email": "u@example.com", "isAdmin": False})
    assert ctx["hasListings"] is False
    assert ctx["role"] == "user"
