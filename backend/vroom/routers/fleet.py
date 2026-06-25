"""Fleet sync and marketplace reference data routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from vroom.dependencies.auth import UserContext, require_admin
from vroom.schemas.admin_models import (
    AdminCompanyLocationsResponse,
    FleetSyncResponse,
    VehicleClassCollectionResponse,
)
from vroom.services import fleet_service

router = APIRouter(prefix="/api", tags=["fleet"])


@router.get("/vehicle-classes", response_model=VehicleClassCollectionResponse)
def list_vehicle_classes() -> dict:
    """List vehicle classes for listing forms."""
    return {
        "status": "success",
        "vehicleClasses": fleet_service.list_vehicle_classes(),
    }


@router.get("/company-locations", response_model=AdminCompanyLocationsResponse)
def list_company_locations(_admin: UserContext = Depends(require_admin)) -> dict:
    """List canonical company location sources for listing creation."""
    try:
        return fleet_service.admin_company_locations()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/fleet/sync", response_model=FleetSyncResponse)
def sync_fleet_listings(_admin: UserContext = Depends(require_admin)) -> dict:
    """Expose fleet as marketplace listings (FLEET source type)."""
    try:
        return fleet_service.sync_fleet_listings()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
