"""Application settings (Pydantic Settings)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]
_TRUTHY = frozenset({"1", "true", "yes"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    port: int = Field(default=8080, validation_alias="PORT")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        validation_alias="CORS_ORIGINS",
    )

    # OpenAPI
    api_title: str = "Metropolis Nexus API"
    api_version: str = "1.0"

    # Auth
    jwt_secret: str = Field(default="change-me-dev-secret", validation_alias="JWT_SECRET")
    jwt_expires_hours: int = Field(default=24, validation_alias="JWT_EXPIRES_HOURS")

    # Database
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    db_pool_min: int = Field(default=1, validation_alias="DB_POOL_MIN")
    db_pool_max: int = Field(default=10, validation_alias="DB_POOL_MAX")

    # AWS / S3
    aws_region: str = Field(default="", validation_alias="AWS_REGION")
    s3_bucket_name: str = Field(default="", validation_alias="S3_BUCKET_NAME")
    s3_presign_ttl_seconds: int = Field(default=300, validation_alias="S3_PRESIGN_TTL_SECONDS")

    # Marketplace
    allow_user_listings: bool = Field(default=True, validation_alias="ALLOW_USER_LISTINGS")
    require_vin_for_p2p: bool = Field(default=True, validation_alias="REQUIRE_VIN_FOR_P2P")

    # Stripe
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_WEBHOOK_SECRET")

    # OAuth
    google_oauth_client_id: str = Field(default="", validation_alias="GOOGLE_OAUTH_CLIENT_ID")

    # Email (Resend)
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")
    mail_from: str = Field(default="", validation_alias="MAIL_FROM")
    frontend_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias="FRONTEND_BASE_URL",
    )

    # Redis (Socket.IO message queue, ARQ worker)
    redis_url: str = Field(default="", validation_alias="REDIS_URL")

    # Rate limiting
    ratelimit_enabled: bool = Field(default=True, validation_alias="RATELIMIT_ENABLED")

    # Booking sweep
    booking_sweep_enabled: bool | None = Field(
        default=None, validation_alias="BOOKING_SWEEP_ENABLED"
    )
    booking_sweep_interval_sec: int = Field(
        default=900, validation_alias="BOOKING_SWEEP_INTERVAL_SEC"
    )

    # Orphan listing-upload sweeper (S3 keys with no file_asset row)
    upload_sweep_enabled: bool | None = Field(default=None, validation_alias="UPLOAD_SWEEP_ENABLED")
    upload_sweep_orphan_grace_hours: int = Field(
        default=24, validation_alias="UPLOAD_SWEEP_ORPHAN_GRACE_HOURS"
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip() == "1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return []

    @field_validator(
        "allow_user_listings", "ratelimit_enabled", "require_vin_for_p2p", mode="before"
    )
    @classmethod
    def parse_bool_env(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in _TRUTHY

    @field_validator(
        "aws_region",
        "s3_bucket_name",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "google_oauth_client_id",
        "redis_url",
        "database_url",
        "resend_api_key",
        "mail_from",
        "frontend_base_url",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()


settings = Settings()
