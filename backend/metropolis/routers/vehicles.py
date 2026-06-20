"""Vehicle decode and reference catalog routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from psycopg2.extras import RealDictCursor

from metropolis.core.db import get_connection
from metropolis.core.errors import raise_for_service_result
from metropolis.core.limiter import limiter
from metropolis.dependencies.auth import UserContext, verified_user_required
from metropolis.schemas.vehicle_models import (
    BodyTypeCollectionResponse,
    FeatureCollectionResponse,
    VinDecodeRequest,
    VinDecodeResponse,
)
from metropolis.services.marketplace_common import list_body_types, list_features
from metropolis.services.vin_decode_service import decode_vin

router = APIRouter(prefix="/api", tags=["vehicles"])


@router.post("/vehicles/vin/decode", response_model=VinDecodeResponse)
@limiter.limit("30/minute")
def decode_vehicle_vin(
    request: Request,
    body: VinDecodeRequest,
    _user: UserContext = Depends(verified_user_required),
) -> VinDecodeResponse:
    result = decode_vin(body.vin)
    if result.get("status") in {"validation_error", "error"}:
        raise_for_service_result(result)
    return VinDecodeResponse.model_validate(result)


@router.get("/body-types", response_model=BodyTypeCollectionResponse)
def get_body_types() -> BodyTypeCollectionResponse:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            body_types = list_body_types(cur)
    return BodyTypeCollectionResponse(status="success", body_types=body_types)


@router.get("/features", response_model=FeatureCollectionResponse)
def get_features(
    category: str | None = Query(default=None),
) -> FeatureCollectionResponse:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            features = list_features(cur, category=category)
    return FeatureCollectionResponse(status="success", features=features)
