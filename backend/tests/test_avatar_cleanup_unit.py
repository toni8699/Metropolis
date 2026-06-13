"""Unit tests for avatar cleanup helpers."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.services.uploads_service import UploadsService, object_key_from_file_url


def test_object_key_from_file_url_decodes_key():
    bucket = "my-bucket"
    region = "us-east-1"
    url = "https://my-bucket.s3.us-east-1.amazonaws.com/user/5/avatar/photo.jpg"
    assert object_key_from_file_url(bucket, region, url) == "user/5/avatar/photo.jpg"


def test_object_key_from_file_url_rejects_foreign_bucket():
    assert object_key_from_file_url("my-bucket",
     "us-east-1", "https://other.s3.us-east-1.amazonaws.com/x") is None


@pytest.fixture
def uploads_service():
    service = UploadsService()
    service.bucket = "my-bucket"
    service.region = "us-east-1"
    service.client = MagicMock()
    return service


def test_delete_user_avatar_file_removes_s3_and_db_row(uploads_service):
    file_url = "https://my-bucket.s3.us-east-1.amazonaws.com/user/7/avatar/old.jpg"
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn

    with patch("metropolis.services.uploads_service.get_connection", return_value=mock_conn):
        uploads_service.delete_user_avatar_file(7, file_url)

    uploads_service.client.delete_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="user/7/avatar/old.jpg",
    )
    mock_cur.execute.assert_called_once_with(
        "DELETE FROM file_asset WHERE object_key = %s",
        ("user/7/avatar/old.jpg",),
    )
    mock_conn.commit.assert_called_once()


def test_delete_user_avatar_file_skips_other_users_key(uploads_service):
    file_url = "https://my-bucket.s3.us-east-1.amazonaws.com/user/99/avatar/old.jpg"

    with patch("metropolis.services.uploads_service.get_connection") as mock_get_conn:
        uploads_service.delete_user_avatar_file(7, file_url)

    uploads_service.client.delete_object.assert_not_called()
    mock_get_conn.assert_not_called()
