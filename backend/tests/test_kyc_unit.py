"""Unit tests for KycService — no database required."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vroom.services.kyc_service import KycService


def test_set_status_rejects_invalid_status():
    svc = KycService()
    result = svc.set_status(user_id=1, status="UNKNOWN")
    assert result["status"] == "validation_error"
    assert "VERIFIED or REJECTED" in result["message"]


def test_set_status_rejects_empty_status():
    svc = KycService()
    result = svc.set_status(user_id=1, status="")
    assert result["status"] == "validation_error"


def test_set_status_rejects_lowercase_invalid():
    svc = KycService()
    result = svc.set_status(user_id=1, status="pending")
    assert result["status"] == "validation_error"


def _mock_conn(fetchone_return=None):
    """Return a context-manager-compatible mock connection."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_return
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


def test_set_status_not_found_when_no_profile():
    svc = KycService()
    conn, cur = _mock_conn(fetchone_return=None)
    with patch("vroom.services.kyc_service.get_connection", return_value=conn):
        result = svc.set_status(user_id=999, status="VERIFIED")
    assert result["status"] == "not_found"
    assert "not found" in result["message"].lower()


def test_set_status_verified_success():
    svc = KycService()
    conn, cur = _mock_conn(fetchone_return={"user_id": 42, "verification_status": "VERIFIED"})
    with patch("vroom.services.kyc_service.get_connection", return_value=conn):
        result = svc.set_status(user_id=42, status="VERIFIED")
    assert result["status"] == "success"
    assert result["verificationStatus"] == "VERIFIED"
    assert result["userId"] == 42


def test_set_status_rejected_success():
    svc = KycService()
    conn, cur = _mock_conn(fetchone_return={"user_id": 7, "verification_status": "REJECTED"})
    with patch("vroom.services.kyc_service.get_connection", return_value=conn):
        result = svc.set_status(user_id=7, status="rejected")
    assert result["status"] == "success"
    assert result["verificationStatus"] == "REJECTED"


def test_list_pending_empty():
    svc = KycService()
    conn, cur = _mock_conn()
    cur.fetchall.return_value = []
    with patch("vroom.services.kyc_service.get_connection", return_value=conn):
        result = svc.list_pending()
    assert result["status"] == "success"
    assert result["queue"] == []
