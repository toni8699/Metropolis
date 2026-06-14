"""Fleet relocation service (expansion placeholder)."""

from __future__ import annotations

from typing import Any


class RentalService:
    """Coordinates fleet relocation simulation responses."""

    def simulate_relocation(self) -> dict[str, Any]:
        return {
            "status": "success",
            "message": "Relocation planner deferred for next expansion phase.",
            "relocationNeeded": False,
            "overloadedBranches": [],
            "moves": [],
            "totalVehiclesMoved": 0,
            "totalTransferCost": 0.0,
            "totalOpportunityCost": 0.0,
            "grandTotalCost": 0.0,
        }
