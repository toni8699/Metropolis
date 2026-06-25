"""Unit tests for trip inspection photos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from vroom.schemas.upload_models import UploadPresignRequest
from vroom.services.trip_inspection_service import TripInspectionService
from vroom.trip_inspection_angles import MAX_EXTRA_PHOTOS_PER_PHASE, STANDARD_ANGLE_KEYS


def test_upload_presign_rejects_unknown_angle_key():
    with pytest.raises(ValidationError) as exc:
        UploadPresignRequest(
            fileName="photo.jpg",
            contentType="image/jpeg",
            scope="TRIP_INSPECTION",
            bookingId=1,
            phase="CHECK_IN",
            angleKey="not_a_real_angle",
            isExtra=False,
        )
    assert "unknown angle_key" in str(exc.value)


def test_upload_presign_allows_extra_without_angle_key():
    payload = UploadPresignRequest(
        fileName="photo.jpg",
        contentType="image/jpeg",
        scope="TRIP_INSPECTION",
        bookingId=1,
        phase="CHECK_IN",
        isExtra=True,
    )
    assert payload.is_extra is True


def test_renter_can_upload_check_in_only_when_confirmed_in_window():
    service = TripInspectionService()
    now = datetime.now(UTC)
    booking = {
        "is_renter": True,
        "status": "CONFIRMED",
        "start_at": now - timedelta(hours=1),
        "end_at": now + timedelta(days=2),
    }
    assert service.renter_can_upload_phase(booking, "CHECK_IN") is True
    booking["status"] = "IN_PROGRESS"
    assert service.renter_can_upload_phase(booking, "CHECK_IN") is False


def test_renter_can_upload_check_out_only_in_progress():
    service = TripInspectionService()
    booking = {"is_renter": True, "status": "IN_PROGRESS", "start_at": None, "end_at": None}
    assert service.renter_can_upload_phase(booking, "CHECK_OUT") is True
    booking["status"] = "CONFIRMED"
    assert service.renter_can_upload_phase(booking, "CHECK_OUT") is False


@patch("vroom.services.trip_inspection_service.get_connection")
def test_assert_renter_upload_access_blocks_extra_cap(mock_get_connection):
    service = TripInspectionService()
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value

    start = datetime.now(UTC) - timedelta(hours=1)
    end = datetime.now(UTC) + timedelta(days=1)
    mock_cur.fetchone.side_effect = [
        {
            "booking_id": 9,
            "renter_user_id": 1,
            "status": "IN_PROGRESS",
            "start_at": start,
            "end_at": end,
            "completed_at": None,
            "owner_user_id": 2,
        },
        {"extra_count": MAX_EXTRA_PHOTOS_PER_PHASE},
    ]

    err = service.assert_renter_upload_access(mock_cur, 9, 1, "CHECK_OUT", True)
    assert err is not None
    assert err["status"] == "validation_error"
    assert "Maximum" in err["message"]


@patch("vroom.services.trip_inspection_service.get_connection")
def test_sweep_expired_trip_inspection_deletes_file_assets_only(mock_get_connection):
    service = TripInspectionService()
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchall.return_value = [(10,), (11,)]
    mock_cur.rowcount = 2

    with patch("vroom.services.trip_inspection_service.settings") as mock_settings:
        mock_settings.trip_inspection_retention_days = 30
        result = service.sweep_expired_trip_inspection_photos()

    assert result["deleted"] == 2
    mock_cur.execute.assert_any_call(
        "DELETE FROM file_asset WHERE file_id = ANY(%s)",
        ([10, 11],),
    )


def test_standard_angle_keys_match_manifest_count():
    assert len(STANDARD_ANGLE_KEYS) == 16


def test_angle_manifest_entries_include_group():
    from vroom.trip_inspection_angles import ANGLE_MANIFEST

    assert all(entry.get("group") in {"exterior", "interior", "detail"} for entry in ANGLE_MANIFEST)


@patch("vroom.services.trip_inspection_service.get_connection")
def test_delete_inspection_photo_renter_deletes_file_asset(mock_get_connection):
    service = TripInspectionService()
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value

    start = datetime.now(UTC) - timedelta(hours=1)
    end = datetime.now(UTC) + timedelta(days=1)
    mock_cur.fetchone.side_effect = [
        {
            "booking_id": 9,
            "renter_user_id": 1,
            "status": "IN_PROGRESS",
            "start_at": start,
            "end_at": end,
            "completed_at": None,
            "owner_user_id": 2,
        },
        {
            "photo_id": 5,
            "file_id": 99,
            "phase": "CHECK_OUT",
            "booking_id": 9,
        },
    ]

    result = service.delete_inspection_photo(9, 5, 1, False)
    assert result["status"] == "success"
    mock_cur.execute.assert_any_call(
        "DELETE FROM file_asset WHERE file_id = %s",
        (99,),
    )


@patch("vroom.services.trip_inspection_service.get_connection")
def test_delete_inspection_photo_host_forbidden(mock_get_connection):
    service = TripInspectionService()
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value

    start = datetime.now(UTC) - timedelta(hours=1)
    end = datetime.now(UTC) + timedelta(days=1)
    mock_cur.fetchone.return_value = {
        "booking_id": 9,
        "renter_user_id": 1,
        "status": "IN_PROGRESS",
        "start_at": start,
        "end_at": end,
        "completed_at": None,
        "owner_user_id": 2,
        "is_renter": False,
        "is_host": True,
    }

    result = service.delete_inspection_photo(9, 5, 2, False)
    assert result["status"] == "forbidden"


@patch("vroom.services.trip_inspection_service.get_connection")
def test_delete_inspection_photo_wrong_phase(mock_get_connection):
    service = TripInspectionService()
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value

    start = datetime.now(UTC) - timedelta(hours=1)
    end = datetime.now(UTC) + timedelta(days=1)
    mock_cur.fetchone.side_effect = [
        {
            "booking_id": 9,
            "renter_user_id": 1,
            "status": "IN_PROGRESS",
            "start_at": start,
            "end_at": end,
            "completed_at": None,
            "owner_user_id": 2,
        },
        {
            "photo_id": 5,
            "file_id": 99,
            "phase": "CHECK_IN",
            "booking_id": 9,
        },
    ]

    result = service.delete_inspection_photo(9, 5, 1, False)
    assert result["status"] == "validation_error"
