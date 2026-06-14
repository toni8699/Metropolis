"""Unit tests for relocation planner placeholder response."""

from __future__ import annotations

import os

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.services.rental_service import RentalService


def test_relocation_placeholder_response_shape():
    service = RentalService()
    result = service.simulate_relocation()
    assert result["status"] == "success"
    assert "deferred" in result["message"].lower()
    assert result["relocationNeeded"] is False
    assert result["moves"] == []
    assert result["totalVehiclesMoved"] == 0
    assert result["grandTotalCost"] == 0.0
