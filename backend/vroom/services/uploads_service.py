from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from urllib.parse import quote, unquote
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from psycopg2.extras import RealDictCursor

from vroom.core.config import settings
from vroom.core.db import get_connection

ALLOWED_SCOPES = {"FLEET", "OWNER_LISTING", "USER_DOC", "USER_AVATAR", "TRIP_INSPECTION"}
LISTING_UPLOAD_KEY_RE = re.compile(r"^owner/\d+/listing/(\d+)/.+")
INSPECTION_UPLOAD_KEY_RE = re.compile(r"^uploads/inspection/(\d+)/.+")


def _safe_filename(file_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", file_name.strip())
    return cleaned or "upload.bin"


def _public_file_url(bucket: str, region: str, object_key: str) -> str:
    encoded_key = quote(object_key, safe="/")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{encoded_key}"


def object_key_from_file_url(bucket: str, region: str, file_url: str) -> str | None:
    if not bucket or not region:
        return None
    prefix = f"https://{bucket}.s3.{region}.amazonaws.com/"
    if not file_url.startswith(prefix):
        return None
    return unquote(file_url[len(prefix) :])


class UploadsService:
    def __init__(self) -> None:
        self.bucket = settings.s3_bucket_name
        self.region = settings.aws_region
        self.expires_in = settings.s3_presign_ttl_seconds
        if self.bucket and self.region:
            self.client = boto3.client("s3", region_name=self.region)
        else:
            self.client = None

    def _ensure_ready(self) -> dict | None:
        if not self.bucket or not self.region or self.client is None:
            return {
                "status": "error",
                "message": "S3 is not configured. Set S3_BUCKET_NAME and AWS_REGION.",
            }
        return None

    def _scope_prefix(
        self,
        scope: str,
        user_id: int,
        listing_id: int | None,
        booking_id: int | None,
    ) -> str | dict:
        if scope == "FLEET":
            return "fleet"
        if scope == "OWNER_LISTING":
            if not listing_id:
                return {
                    "status": "validation_error",
                    "message": "listingId required for OWNER_LISTING uploads.",
                }
            return f"owner/{user_id}/listing/{listing_id}"
        if scope == "TRIP_INSPECTION":
            if not booking_id:
                return {
                    "status": "validation_error",
                    "message": "bookingId required for TRIP_INSPECTION uploads.",
                }
            return f"uploads/inspection/{booking_id}"
        if scope == "USER_AVATAR":
            return f"user/{user_id}/avatar"
        return f"user/{user_id}/documents"

    def _assert_listing_access(
        self, cur, scope: str, listing_id: int | None, user_id: int, role: str
    ) -> dict | None:
        role_upper = role.upper()
        if scope == "FLEET":
            if role_upper != "ADMIN":
                return {"status": "forbidden", "message": "Only admins can upload fleet assets."}
            return None
        if scope != "OWNER_LISTING":
            return None
        if not listing_id:
            return {
                "status": "validation_error",
                "message": "listingId required for OWNER_LISTING uploads.",
            }
        cur.execute(
            "SELECT owner_user_id FROM vehicle_listing WHERE listing_id = %s",
            (listing_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"status": "not_found", "message": "Listing not found."}
        if role_upper != "ADMIN" and row["owner_user_id"] != user_id:
            return {"status": "forbidden", "message": "You do not manage this listing."}
        return None

    def presign_upload(self, user_id: int, role: str, payload: dict) -> dict:
        if err := self._ensure_ready():
            return err
        scope = str(payload.get("scope", "")).upper()
        if scope not in ALLOWED_SCOPES:
            return {"status": "validation_error", "message": "Invalid upload scope."}
        file_name = str(payload.get("fileName", "")).strip()
        content_type = str(payload.get("contentType", "")).strip()
        if not file_name or not content_type:
            return {
                "status": "validation_error",
                "message": "fileName and contentType are required.",
            }
        if scope == "USER_AVATAR" and not content_type.startswith("image/"):
            return {"status": "validation_error", "message": "Avatar must be an image."}
        if scope == "TRIP_INSPECTION" and not content_type.startswith("image/"):
            return {"status": "validation_error", "message": "Inspection photos must be images."}
        listing_id = payload.get("listingId")
        if listing_id is not None:
            listing_id = int(listing_id)
        booking_id = payload.get("bookingId")
        if booking_id is not None:
            booking_id = int(booking_id)
        phase = str(payload.get("phase") or "").upper()
        is_extra = bool(payload.get("isExtra"))

        prefix = self._scope_prefix(scope, user_id, listing_id, booking_id)
        if isinstance(prefix, dict):
            return prefix

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if err := self._assert_listing_access(cur, scope, listing_id, user_id, role):
                    return err
                if scope == "TRIP_INSPECTION":
                    from vroom.services.trip_inspection_service import (
                        trip_inspection_service,
                    )

                    if err := trip_inspection_service.assert_renter_upload_access(
                        cur, booking_id, user_id, phase, is_extra
                    ):
                        return err

        object_key = f"{prefix}/{uuid4()}-{_safe_filename(file_name)}"
        try:
            presigned_url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=self.expires_in,
            )
        except (ClientError, BotoCoreError):
            return {"status": "error", "message": "Failed to generate upload URL."}

        return {
            "status": "success",
            "presignedUrl": presigned_url,
            "objectKey": object_key,
            "fileUrl": _public_file_url(self.bucket, self.region, object_key),
            "expiresIn": self.expires_in,
        }

    def complete_upload(self, user_id: int, role: str, payload: dict) -> dict:
        if err := self._ensure_ready():
            return err
        scope = str(payload.get("scope", "")).upper()
        if scope not in ALLOWED_SCOPES:
            return {"status": "validation_error", "message": "Invalid upload scope."}
        object_key = str(payload.get("objectKey", "")).strip()
        if not object_key:
            return {"status": "validation_error", "message": "objectKey is required."}
        listing_id = payload.get("listingId")
        if listing_id is not None:
            listing_id = int(listing_id)
        booking_id = payload.get("bookingId")
        if booking_id is not None:
            booking_id = int(booking_id)
        phase = str(payload.get("phase") or "").upper()
        angle_key = str(payload.get("angleKey") or "").strip()
        is_extra = bool(payload.get("isExtra"))

        file_url = _public_file_url(self.bucket, self.region, object_key)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if err := self._assert_listing_access(cur, scope, listing_id, user_id, role):
                    return err
                if scope == "TRIP_INSPECTION":
                    from vroom.services.trip_inspection_service import (
                        trip_inspection_service,
                    )

                    if err := trip_inspection_service.assert_renter_upload_access(
                        cur, booking_id, user_id, phase, is_extra
                    ):
                        return err
                cur.execute(
                    """
                    INSERT INTO file_asset
                    (
                        owner_user_id, listing_id, booking_id, bucket, object_key, file_url,
                        content_type, size_bytes, scope
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (object_key)
                    DO UPDATE
                    SET file_url = EXCLUDED.file_url,
                        content_type = COALESCE(EXCLUDED.content_type, file_asset.content_type),
                        size_bytes = COALESCE(EXCLUDED.size_bytes, file_asset.size_bytes),
                        listing_id = COALESCE(EXCLUDED.listing_id, file_asset.listing_id),
                        booking_id = COALESCE(EXCLUDED.booking_id, file_asset.booking_id),
                        scope = EXCLUDED.scope
                    RETURNING file_id
                    """,
                    (
                        user_id if scope != "FLEET" else None,
                        listing_id,
                        booking_id if scope == "TRIP_INSPECTION" else None,
                        self.bucket,
                        object_key,
                        file_url,
                        payload.get("contentType"),
                        payload.get("sizeBytes"),
                        scope,
                    ),
                )
                row = cur.fetchone()
                if scope == "TRIP_INSPECTION":
                    from vroom.services.trip_inspection_service import (
                        trip_inspection_service,
                    )

                    trip_inspection_service.link_photo(
                        cur,
                        booking_id=booking_id,
                        file_id=int(row["file_id"]),
                        phase=phase,
                        angle_key=angle_key,
                        is_extra=is_extra,
                        user_id=user_id,
                    )
                if listing_id:
                    cur.execute(
                        """
                        SELECT COALESCE(MAX(display_order), -1) + 1 AS next_order
                        FROM listing_image
                        WHERE listing_id = %s
                        """,
                        (listing_id,),
                    )
                    next_order = int(cur.fetchone()["next_order"])
                    cur.execute(
                        """
                        INSERT INTO listing_image (listing_id, file_id, display_order)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (listing_id, file_id) DO NOTHING
                        """,
                        (listing_id, row["file_id"], next_order),
                    )
                    cur.execute(
                        """
                        UPDATE vehicle_listing
                        SET updated_at = NOW()
                        WHERE listing_id = %s
                        """,
                        (listing_id,),
                    )
                conn.commit()

        return {
            "status": "success",
            "fileId": row["file_id"],
            "objectKey": object_key,
            "fileUrl": file_url,
        }

    def _delete_s3_object_best_effort(self, object_key: str) -> bool:
        if not self.client or not self.bucket:
            return False
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except (ClientError, BotoCoreError):
            return False

    def _listing_upload_marker(self, listing_id: int) -> str:
        return f"/listing/{listing_id}/"

    def _iter_listing_upload_keys(self, listing_id: int):
        if not self.client or not self.bucket:
            return
        marker = self._listing_upload_marker(listing_id)
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix="owner/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if marker in key and LISTING_UPLOAD_KEY_RE.match(key):
                    yield key

    def delete_listing_s3_files(self, listing_id: int) -> dict:
        """Best-effort S3 purge for a listing. DB rows cascade separately."""
        if not self.client or not self.bucket:
            return {"status": "skipped", "deleted": 0, "attempted": 0}
        try:
            keys = list(dict.fromkeys(self._iter_listing_upload_keys(listing_id)))
        except (ClientError, BotoCoreError):
            return {"status": "skipped", "deleted": 0, "attempted": 0}
        deleted = sum(1 for key in keys if self._delete_s3_object_best_effort(key))
        return {"status": "success", "deleted": deleted, "attempted": len(keys)}

    def _listing_id_from_upload_key(self, key: str) -> int | None:
        match = LISTING_UPLOAD_KEY_RE.match(key)
        if not match:
            return None
        return int(match.group(1))

    def purge_file_assets(self, file_ids: list[int]) -> dict:
        """Delete file_asset rows; booking_inspection_photo cascades via FK."""
        if not file_ids:
            return {"status": "success", "deleted": 0}
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM file_asset WHERE file_id = ANY(%s)",
                    (file_ids,),
                )
                deleted = cur.rowcount
                conn.commit()
        return {"status": "success", "deleted": deleted}

    def _sweep_orphan_keys_for_prefix(
        self,
        *,
        prefix: str,
        key_pattern: re.Pattern[str],
        known_keys: set[str],
        live_marker_check,
        cutoff: datetime,
    ) -> tuple[int, int]:
        scanned = 0
        deleted = 0
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key_pattern.match(key):
                    continue
                scanned += 1
                if key in known_keys:
                    continue
                if live_marker_check(key):
                    continue
                last_modified = obj["LastModified"]
                if last_modified.tzinfo is None:
                    last_modified = last_modified.replace(tzinfo=UTC)
                else:
                    last_modified = last_modified.astimezone(UTC)
                if last_modified > cutoff:
                    continue
                if self._delete_s3_object_best_effort(key):
                    deleted += 1
        return scanned, deleted

    def sweep_orphan_listing_uploads(self) -> dict:
        """Delete owner listing S3 objects absent from file_asset past grace window."""
        if err := self._ensure_ready():
            return {"status": "skipped", "deleted": 0, "scanned": 0, **err}
        cutoff = datetime.now(UTC) - timedelta(hours=settings.upload_sweep_orphan_grace_hours)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT object_key FROM file_asset WHERE bucket = %s",
                    (self.bucket,),
                )
                known_keys = {row[0] for row in cur.fetchall()}
                cur.execute("SELECT listing_id FROM vehicle_listing")
                live_listing_ids = {row[0] for row in cur.fetchall()}

        scanned = 0
        deleted = 0
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix="owner/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not LISTING_UPLOAD_KEY_RE.match(key):
                    continue
                scanned += 1
                if key in known_keys:
                    continue
                listing_id = self._listing_id_from_upload_key(key)
                listing_gone = listing_id is not None and listing_id not in live_listing_ids
                if not listing_gone:
                    last_modified = obj["LastModified"]
                    if last_modified.tzinfo is None:
                        last_modified = last_modified.replace(tzinfo=UTC)
                    else:
                        last_modified = last_modified.astimezone(UTC)
                    if last_modified > cutoff:
                        continue
                if self._delete_s3_object_best_effort(key):
                    deleted += 1

        def _inspection_live(_key: str) -> bool:
            return False

        inspection_scanned, inspection_deleted = self._sweep_orphan_keys_for_prefix(
            prefix="uploads/inspection/",
            key_pattern=INSPECTION_UPLOAD_KEY_RE,
            known_keys=known_keys,
            live_marker_check=_inspection_live,
            cutoff=cutoff,
        )
        scanned += inspection_scanned
        deleted += inspection_deleted
        return {"status": "success", "scanned": scanned, "deleted": deleted}

    def delete_user_avatar_file(self, user_id: int, file_url: str | None) -> None:
        """Remove a superseded avatar from S3 and file_asset. Best-effort when S3 is unavailable."""
        if not file_url:
            return
        object_key = object_key_from_file_url(self.bucket, self.region, file_url)
        if not object_key:
            return
        if not object_key.startswith(f"user/{user_id}/avatar/"):
            return
        self._delete_s3_object_best_effort(object_key)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM file_asset WHERE object_key = %s", (object_key,))
                conn.commit()
