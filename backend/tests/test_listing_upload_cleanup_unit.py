"""Unit tests for listing upload S3 cleanup and orphan sweeper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from metropolis.services.uploads_service import UploadsService


@pytest.fixture
def uploads_service():
    service = UploadsService()
    service.bucket = "my-bucket"
    service.region = "us-east-1"
    service.client = MagicMock()
    return service


def _s3_page(keys: list[str], *, age_hours: int = 48) -> dict:
    modified = datetime.now(UTC) - timedelta(hours=age_hours)
    return {
        "Contents": [{"Key": key, "LastModified": modified} for key in keys],
    }


def test_delete_listing_s3_files_deletes_all_keys_under_listing_prefix(uploads_service):
    listing_id = 42
    keys = [
        f"owner/7/listing/{listing_id}/photo-a.jpg",
        f"owner/7/listing/{listing_id}/photo-b.jpg",
        "owner/7/listing/99/other.jpg",
        "owner/8/listing/421/other-listing.jpg",
    ]
    uploads_service.client.get_paginator.return_value.paginate.return_value = [
        _s3_page(keys),
    ]

    result = uploads_service.delete_listing_s3_files(listing_id)

    assert result == {"status": "success", "deleted": 2, "attempted": 2}
    delete_calls = uploads_service.client.delete_object.call_args_list
    assert len(delete_calls) == 2
    deleted_keys = {call.kwargs["Key"] for call in delete_calls}
    assert deleted_keys == {
        f"owner/7/listing/{listing_id}/photo-a.jpg",
        f"owner/7/listing/{listing_id}/photo-b.jpg",
    }


def test_sweep_orphan_listing_uploads_deletes_old_untracked_keys(uploads_service):
    old_orphan = "owner/3/listing/10/abandoned.jpg"
    recent_orphan = "owner/3/listing/11/recent.jpg"
    tracked = "owner/3/listing/12/tracked.jpg"
    uploads_service.client.get_paginator.return_value.paginate.return_value = [
        _s3_page([old_orphan], age_hours=48),
        _s3_page([recent_orphan], age_hours=1),
        _s3_page([tracked], age_hours=48),
    ]
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = [
        [(tracked,)],
        [(11,), (12,)],
    ]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn

    with (
        patch("metropolis.services.uploads_service.get_connection", return_value=mock_conn),
        patch("metropolis.services.uploads_service.settings") as mock_settings,
    ):
        mock_settings.upload_sweep_orphan_grace_hours = 24
        result = uploads_service.sweep_orphan_listing_uploads()

    assert result["status"] == "success"
    assert result["deleted"] == 1
    uploads_service.client.delete_object.assert_called_once_with(
        Bucket="my-bucket",
        Key=old_orphan,
    )


def test_sweep_deletes_recent_orphans_when_listing_gone(uploads_service):
    deleted_listing_orphan = "owner/3/listing/151/fresh.jpg"
    uploads_service.client.get_paginator.return_value.paginate.return_value = [
        _s3_page([deleted_listing_orphan], age_hours=1),
    ]
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = [[], []]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn

    with (
        patch("metropolis.services.uploads_service.get_connection", return_value=mock_conn),
        patch("metropolis.services.uploads_service.settings") as mock_settings,
    ):
        mock_settings.upload_sweep_orphan_grace_hours = 24
        result = uploads_service.sweep_orphan_listing_uploads()

    assert result["deleted"] == 1
    uploads_service.client.delete_object.assert_called_once_with(
        Bucket="my-bucket",
        Key=deleted_listing_orphan,
    )


def test_delete_listing_calls_s3_cleanup_before_db_delete():
    from metropolis.services import uploads_service as uploads_svc
    from metropolis.services.listing_service import ListingService

    service = ListingService()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn
    call_order: list[str] = []
    mock_cur.execute.side_effect = lambda sql, params=None: call_order.append("db")

    with (
        patch("metropolis.services.listing_service.get_connection", return_value=mock_conn),
        patch.object(service, "_fetch_listing_ownership", return_value={"owner_user_id": 5}),
        patch.object(service, "_can_manage_listing", return_value=True),
        patch.object(
            uploads_svc,
            "delete_listing_s3_files",
            side_effect=lambda listing_id: call_order.append("s3") or {"deleted": 1},
        ),
    ):
        result = service.delete_listing({"user_id": 5, "role": "USER"}, 42)

    assert result == {"status": "success"}
    assert call_order == ["s3", "db"]
