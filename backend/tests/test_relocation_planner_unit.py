"""Unit tests for the fleet relocation planner algorithm.

Tests use a mock cursor — no database or Flask context required.
The planner logic lives in rental_service._run_relocation_planner.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.services.rental_service import _relocation_error, _run_relocation_planner


def _make_branch_row(branchid, city, areaid, fleet_size, active_reservations, available_vehicles):
    return {
        "branchid": branchid,
        "city": city,
        "areaid": areaid,
        "fleet_size": fleet_size,
        "active_reservations": active_reservations,
        "available_vehicles": available_vehicles,
    }


def _make_cursor(branch_rows, fee_rows):
    """Return a mock cursor that yields branch_rows then fee_rows on successive fetchall calls."""
    cur = MagicMock()
    cur.fetchall.side_effect = [branch_rows, fee_rows]
    return cur


# ---------------------------------------------------------------------------
# _relocation_error helper
# ---------------------------------------------------------------------------


def test_relocation_error_structure():
    result = _relocation_error("test message")
    assert result["status"] == "error"
    assert result["message"] == "test message"
    assert result["relocationNeeded"] is False
    assert result["moves"] == []
    assert result["totalVehiclesMoved"] == 0
    assert result["grandTotalCost"] == 0.0


# ---------------------------------------------------------------------------
# No branches → error path
# ---------------------------------------------------------------------------


def test_no_branches_returns_error():
    cur = _make_cursor([], [])
    result = _run_relocation_planner(cur)
    assert result["status"] == "error"
    assert "No branch data" in result["message"]


# ---------------------------------------------------------------------------
# All branches below utilisation target → no relocation needed
# ---------------------------------------------------------------------------


def test_no_overloaded_branches_no_relocation():
    # utilization = active / fleet_size; UTIL_TARGET = 0.75
    # Use low utilization (0 active out of 10 fleet = 0.0) → below threshold
    cur = _make_cursor(
        [
            _make_branch_row(1, "Montreal", 1, 10, 0, 10),
            _make_branch_row(2, "Toronto", 2, 10, 0, 10),
        ],
        [],
    )
    result = _run_relocation_planner(cur)
    assert result["status"] == "success"
    assert result["relocationNeeded"] is False
    assert result["moves"] == []
    assert result["totalVehiclesMoved"] == 0


# ---------------------------------------------------------------------------
# Overloaded target but no feasible donor route → moves empty
# ---------------------------------------------------------------------------


def test_overloaded_no_donor_route():
    # Branch 1: overloaded (utilization > 0.75, high need)
    # Branch 2: potential donor but no fee entry between their areas
    cur = _make_cursor(
        [
            _make_branch_row(1, "Montreal", 1, 4, 4, 0),  # util = 1.0, need = 4
            _make_branch_row(2, "Toronto", 2, 10, 0, 10),  # util = 0, donor_capacity > 0
        ],
        [],  # no relocation fees in table
    )
    result = _run_relocation_planner(cur)
    assert result["status"] == "success"
    assert result["relocationNeeded"] is True
    assert result["moves"] == []
    assert len(result["overloadedBranches"]) == 1
    assert result["overloadedBranches"][0]["branchId"] == 1


# ---------------------------------------------------------------------------
# Happy path: overloaded target with donor + fee route
# ---------------------------------------------------------------------------


def test_relocation_move_generated():
    # Branch 1 (area 1): overloaded — 8 active out of 8 fleet = 1.0 util > 0.75
    # Branch 2 (area 2): donor — 0 active, 8 available (capacity > 0)
    # Fee: area 2 → area 1 = 50.0
    cur = _make_cursor(
        [
            _make_branch_row(1, "Montreal", 1, 8, 8, 0),
            _make_branch_row(2, "Toronto", 2, 8, 0, 8),
        ],
        [{"sourceareaid": 2, "targetareaid": 1, "fee": 50.0}],
    )
    result = _run_relocation_planner(cur)
    assert result["status"] == "success"
    assert result["relocationNeeded"] is True
    assert len(result["moves"]) >= 1
    assert result["totalVehiclesMoved"] > 0
    assert result["totalTransferCost"] > 0

    move = result["moves"][0]
    assert move["fromBranchId"] == 2
    assert move["toBranchId"] == 1
    assert move["quantity"] > 0
    assert move["transferCost"] > 0


# ---------------------------------------------------------------------------
# Cost aggregation
# ---------------------------------------------------------------------------


def test_grand_total_equals_transfer_plus_opportunity():
    cur = _make_cursor(
        [
            _make_branch_row(1, "A", 1, 4, 4, 0),
            _make_branch_row(2, "B", 2, 10, 1, 5),
        ],
        [{"sourceareaid": 2, "targetareaid": 1, "fee": 25.0}],
    )
    result = _run_relocation_planner(cur)
    if result["relocationNeeded"] and result["moves"]:
        assert (
            abs(
                result["grandTotalCost"]
                - (result["totalTransferCost"] + result["totalOpportunityCost"])
            )
            < 1e-6
        )
