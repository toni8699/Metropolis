from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError, NotFound

from metropolis.config import Config
from metropolis.db import get_connection

ALLOWED_SCOPES = {"FLEET", "OWNER_LISTING", "USER_DOC"}


def _safe_filename(file_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", file_name.strip())
    return cleaned or "upload.bin"


def _public_file_url(bucket: str, region: str, object_key: str) -> str:
    encoded_key = quote(object_key, safe="/")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{encoded_key}"


class UploadsService:
    def __init__(self) -> None:
        self.bucket = Config.S3_BUCKET_NAME
        self.region = Config.AWS_REGION
        self.expires_in = Config.S3_PRESIGN_TTL_SECONDS
        if self.bucket and self.region:
            self.client = boto3.client("s3", region_name=self.region)
        else:
            self.client = None

    def _ensure_ready(self) -> None:
        if not self.bucket or not self.region or self.client is None:
            raise InternalServerError(
                description="S3 is not configured. Set S3_BUCKET_NAME and AWS_REGION."
            )

    def _scope_prefix(self, scope: str, user_id: int, listing_id: int | None) -> str:
        if scope == "FLEET":
            return "fleet"
        if scope == "OWNER_LISTING":
            if not listing_id:
                raise BadRequest(description="listingId required for OWNER_LISTING uploads.")
            return f"owner/{user_id}/listing/{listing_id}"
        return f"user/{user_id}/documents"

    def _assert_listing_access(
        self, cur, scope: str, listing_id: int | None, user_id: int, role: str
    ) -> None:
        role_upper = role.upper()
        if scope == "FLEET":
            if role_upper != "ADMIN":
                raise Forbidden(description="Only admins can upload fleet assets.")
            return
        if scope != "OWNER_LISTING":
            return
        if not listing_id:
            raise BadRequest(description="listingId required for OWNER_LISTING uploads.")
        cur.execute(
            "SELECT owner_user_id FROM vehicle_listing WHERE listing_id = %s",
            (listing_id,),
        )
        row = cur.fetchone()
        if not row:
            raise NotFound(description="Listing not found.")
        if role_upper != "ADMIN" and row["owner_user_id"] != user_id:
            raise Forbidden(description="You do not manage this listing.")

    def presign_upload(self, user_id: int, role: str, payload: dict) -> dict:
        self._ensure_ready()
        scope = str(payload.get("scope", "")).upper()
        if scope not in ALLOWED_SCOPES:
            raise BadRequest(description="Invalid upload scope.")
        file_name = str(payload.get("fileName", "")).strip()
        content_type = str(payload.get("contentType", "")).strip()
        if not file_name or not content_type:
            raise BadRequest(description="fileName and contentType are required.")
        listing_id = payload.get("listingId")
        if listing_id is not None:
            listing_id = int(listing_id)

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                self._assert_listing_access(cur, scope, listing_id, user_id, role)

        object_key = (
            f"{self._scope_prefix(scope, user_id, listing_id)}/"
            f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4()}-{_safe_filename(file_name)}"
        )
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
        except (ClientError, BotoCoreError) as exc:
            raise InternalServerError(description="Failed to generate upload URL.") from exc

        return {
            "status": "success",
            "presignedUrl": presigned_url,
            "objectKey": object_key,
            "fileUrl": _public_file_url(self.bucket, self.region, object_key),
            "expiresIn": self.expires_in,
        }

    def complete_upload(self, user_id: int, role: str, payload: dict) -> dict:
        self._ensure_ready()
        scope = str(payload.get("scope", "")).upper()
        if scope not in ALLOWED_SCOPES:
            raise BadRequest(description="Invalid upload scope.")
        object_key = str(payload.get("objectKey", "")).strip()
        if not object_key:
            raise BadRequest(description="objectKey is required.")
        listing_id = payload.get("listingId")
        if listing_id is not None:
            listing_id = int(listing_id)

        file_url = _public_file_url(self.bucket, self.region, object_key)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                self._assert_listing_access(cur, scope, listing_id, user_id, role)
                cur.execute(
                    """
                    INSERT INTO file_asset
                    (owner_user_id, listing_id, bucket, object_key, file_url, content_type, size_bytes, scope)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (object_key)
                    DO UPDATE
                    SET file_url = EXCLUDED.file_url,
                        content_type = COALESCE(EXCLUDED.content_type, file_asset.content_type),
                        size_bytes = COALESCE(EXCLUDED.size_bytes, file_asset.size_bytes),
                        listing_id = COALESCE(EXCLUDED.listing_id, file_asset.listing_id),
                        scope = EXCLUDED.scope
                    RETURNING file_id
                    """,
                    (
                        user_id if scope != "FLEET" else None,
                        listing_id,
                        self.bucket,
                        object_key,
                        file_url,
                        payload.get("contentType"),
                        payload.get("sizeBytes"),
                        scope,
                    ),
                )
                row = cur.fetchone()
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
