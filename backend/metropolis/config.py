import os


class Config:
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    PORT = int(os.environ.get("PORT", "8080"))
    DEBUG = os.environ.get("FLASK_DEBUG") == "1"

    APIFAIRY_TITLE = "Metropolis Nexus API"
    APIFAIRY_VERSION = "1.0"
    APIFAIRY_UI = "redoc"

    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-dev-secret")
    JWT_EXPIRES_HOURS = int(os.environ.get("JWT_EXPIRES_HOURS", "24"))
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    AWS_REGION = os.environ.get("AWS_REGION", "").strip()
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "").strip()
    S3_PRESIGN_TTL_SECONDS = int(os.environ.get("S3_PRESIGN_TTL_SECONDS", "300"))
    ALLOW_USER_LISTINGS = os.environ.get("ALLOW_USER_LISTINGS", "1") in {
        "1",
        "true",
        "TRUE",
        "yes",
        "YES",
    }
