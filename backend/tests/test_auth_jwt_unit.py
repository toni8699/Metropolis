"""JWT auth context — no DB hit per request."""

from vroom.dependencies.auth import _user_context_from_payload


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


def test_require_listing_access_allows_admin_on_fleet_listing():
    from unittest.mock import MagicMock, patch

    from vroom.dependencies.auth import UserContext, require_listing_access

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"listing_id": 99, "owner_user_id": None}
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn
    admin = UserContext(user_id=1, email="admin@example.com", is_admin=True)

    with patch("vroom.dependencies.auth.get_connection", return_value=mock_conn):
        access = require_listing_access(99, admin)

    assert access.listing_id == 99
    assert access.owner_user_id is None
