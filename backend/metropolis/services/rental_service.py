"""Rental business logic (service layer)."""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from psycopg2.extras import RealDictCursor

from metropolis.db import get_connection

UTIL_TARGET = 0.75
DONOR_MAX_UTIL = 0.65
UTIL_SAFE_THRESHOLD = 0.45
ALPHA = 100.0
BETA = 10.0

ACTIVE_BOOKING_STATUSES = ("PENDING", "CONFIRMED", "IN_PROGRESS")

BRANCH_STATS_SQL = """
SELECT b.branchid, b.city, b.areaid,
       COUNT(DISTINCT v.vin) AS fleet_size,
       COUNT(DISTINCT bk.booking_id) AS active_reservations,
       SUM(
         CASE
           WHEN v.status = 'Available'
            AND NOT EXISTS (
              SELECT 1
              FROM vehicle_listing vl
              JOIN booking b_now ON b_now.listing_id = vl.listing_id
              WHERE vl.fleet_vehicle_vin = v.vin
                AND vl.source_type = 'FLEET'
                AND b_now.status IN ('PENDING', 'CONFIRMED', 'IN_PROGRESS')
                AND b_now.start_at <= NOW()
                AND b_now.end_at > NOW()
            )
           THEN 1
           ELSE 0
         END
       ) AS available_vehicles
FROM branch b
JOIN vehicle v ON v.branchid = b.branchid
LEFT JOIN vehicle_listing vl
  ON vl.fleet_vehicle_vin = v.vin
 AND vl.source_type = 'FLEET'
LEFT JOIN booking bk
  ON bk.listing_id = vl.listing_id
 AND bk.status IN ('PENDING', 'CONFIRMED', 'IN_PROGRESS')
 AND bk.start_at <= NOW()
 AND bk.end_at > NOW()
GROUP BY b.branchid, b.city, b.areaid
"""

RELOCATION_FEE_SQL = "SELECT sourceareaid, targetareaid, fee FROM relocation"

MARKETPLACE_BOOKINGS_BY_EMAIL_SQL = """
SELECT
  b.booking_id,
  b.created_at AS bookedattime,
  b.start_at AS pickupdate,
  b.end_at AS returndate,
  l.title AS listing_title,
  l.fleet_vehicle_vin AS vin,
  l.make,
  l.model,
  l.source_type,
  b.status,
  b.price_snapshot_json
FROM booking b
JOIN vehicle_listing l ON l.listing_id = b.listing_id
JOIN app_user u ON u.user_id = b.renter_user_id
WHERE lower(trim(u.email)) = lower(trim(%s))
ORDER BY b.created_at DESC, b.booking_id DESC
"""

AVAILABLE_BY_AREA_SQL = """
WITH fleet_vehicles AS (
  SELECT a.areaname, v.vin
  FROM area a
  JOIN branch br ON br.areaid = a.areaid
  JOIN vehicle v ON v.branchid = br.branchid
  WHERE v.status = 'Available'
),
booked_now AS (
  SELECT DISTINCT vl.fleet_vehicle_vin AS vin
  FROM vehicle_listing vl
  JOIN booking b ON b.listing_id = vl.listing_id
  WHERE vl.source_type = 'FLEET'
    AND vl.fleet_vehicle_vin IS NOT NULL
    AND b.status IN ('PENDING', 'CONFIRMED', 'IN_PROGRESS')
    AND b.start_at <= NOW()
    AND b.end_at > NOW()
)
SELECT fv.areaname, COUNT(*) AS number_vehicles
FROM fleet_vehicles fv
LEFT JOIN booked_now bn ON bn.vin = fv.vin
WHERE bn.vin IS NULL
GROUP BY fv.areaname
ORDER BY number_vehicles DESC
"""


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


@dataclass
class BranchStats:
    branch_id: int
    city: str
    area_id: int
    fleet_size: int
    active_reservations: int
    available_vehicles: int
    utilization: float
    need_vehicles: int
    donor_capacity: int


@dataclass
class RelocationMove:
    from_branch_id: int
    from_city: str
    to_branch_id: int
    to_city: str
    quantity: int = 0
    transfer_cost: float = 0.0
    opportunity_cost: float = 0.0
    total_cost: float = 0.0


class RentalService:
    """Coordinates rental operations against the database."""

    def get_reservations_by_email(self, email: str | None) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                return _lookup_customer_reservations(cur, email)

    def list_available_vehicles_by_area(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                return _list_available_vehicles_by_area(cur)

    def simulate_relocation(self) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                return _run_relocation_planner(cur)


def _lookup_customer_reservations(cur, email: str | None) -> dict[str, Any]:
    if not email or not email.strip():
        return {
            "status": "validation_error",
            "message": "Please enter a customer email.",
            "reservations": [],
        }

    trimmed = email.strip()
    cur.execute(
        "SELECT user_id, email, full_name FROM app_user WHERE lower(trim(email)) = lower(trim(%s))",
        (trimmed,),
    )
    user = cur.fetchone()
    if not user:
        return {
            "status": "not_found",
            "message": "No marketplace account found for this email.",
            "reservations": [],
        }

    cur.execute(MARKETPLACE_BOOKINGS_BY_EMAIL_SQL, (trimmed,))
    rows = cur.fetchall()
    if not rows:
        return {
            "status": "not_found",
            "message": "No bookings found for this email.",
            "reservations": [],
        }

    reservations = []
    for row in rows:
        price_snapshot = row.get("price_snapshot_json") or {}
        reservations.append(
            {
                "resId": row["booking_id"],
                "bookedAt": _json_value(row["bookedattime"]),
                "pickupDate": _json_value(row["pickupdate"]),
                "returnDate": _json_value(row["returndate"]),
                "contractId": row["booking_id"],
                "planType": row["status"],
                "totalCost": price_snapshot.get("pricePerDay"),
                "employeeName": None,
                "vehicleClassName": row["listing_title"],
                "make": row["make"],
                "model": row["model"],
                "branchId": None,
                "city": None,
                "areaName": row["source_type"],
            }
        )

    return {"status": "success", "message": None, "reservations": reservations}


def _list_available_vehicles_by_area(cur) -> list[dict[str, Any]]:
    cur.execute(AVAILABLE_BY_AREA_SQL)
    return [
        {"areaName": row["areaname"], "availableCount": row["number_vehicles"]}
        for row in cur.fetchall()
    ]


def _run_relocation_planner(cur) -> dict[str, Any]:
    cur.execute(BRANCH_STATS_SQL)
    branches: list[BranchStats] = []
    for row in cur.fetchall():
        fleet_size = row["fleet_size"]
        active = row["active_reservations"]
        available = row["available_vehicles"]
        utilization = 0.0 if fleet_size == 0 else active / fleet_size
        need = max(0, 2 * active - fleet_size)
        max_give = fleet_size - math.ceil(active / DONOR_MAX_UTIL) if active else fleet_size
        donor_capacity = max(0, min(available, max_give))
        branches.append(
            BranchStats(
                branch_id=row["branchid"],
                city=row["city"],
                area_id=row["areaid"],
                fleet_size=fleet_size,
                active_reservations=active,
                available_vehicles=available,
                utilization=utilization,
                need_vehicles=need,
                donor_capacity=donor_capacity,
            )
        )

    cur.execute(RELOCATION_FEE_SQL)
    fee_map = {
        f"{row['sourceareaid']}->{row['targetareaid']}": float(row["fee"])
        for row in cur.fetchall()
    }

    if not branches:
        return _relocation_error("No branch data found.")

    max_active = max((b.active_reservations for b in branches), default=0)
    denom_active = max(1.0, float(max_active))

    targets = [b for b in branches if b.utilization > UTIL_TARGET and b.need_vehicles > 0]
    donors = [b for b in branches if b.utilization < DONOR_MAX_UTIL and b.donor_capacity > 0]

    if not targets:
        return {
            "status": "success",
            "message": "None. No relocation needed.",
            "relocationNeeded": False,
            "overloadedBranches": [],
            "moves": [],
            "totalVehiclesMoved": 0,
            "totalTransferCost": 0.0,
            "totalOpportunityCost": 0.0,
            "grandTotalCost": 0.0,
        }

    overloaded = [
        {
            "branchId": t.branch_id,
            "city": t.city,
            "areaId": t.area_id,
            "utilizationPercent": t.utilization * 100.0,
            "needVehicles": t.need_vehicles,
        }
        for t in targets
    ]

    move_map: OrderedDict[str, RelocationMove] = OrderedDict()
    total_transfer = 0.0
    total_opportunity = 0.0

    for target in targets:
        remaining_need = target.need_vehicles
        while remaining_need > 0:
            best_donor = None
            best_total = float("inf")
            best_transfer = 0.0
            best_opportunity = 0.0

            for donor in donors:
                if donor.donor_capacity <= 0:
                    continue
                fee_key = f"{donor.area_id}->{target.area_id}"
                transfer_fee = fee_map.get(fee_key)
                if transfer_fee is None:
                    continue

                source_util = (
                    0.0 if donor.fleet_size == 0 else donor.active_reservations / donor.fleet_size
                )
                pressure = max(0.0, source_util - UTIL_SAFE_THRESHOLD)
                demand_norm = donor.active_reservations / denom_active
                opportunity = (ALPHA * pressure) + (BETA * demand_norm)
                total_cost = transfer_fee + opportunity

                if total_cost < best_total:
                    best_total = total_cost
                    best_donor = donor
                    best_transfer = transfer_fee
                    best_opportunity = opportunity

            if best_donor is None:
                break

            best_donor.donor_capacity -= 1
            remaining_need -= 1

            key = f"{best_donor.branch_id}->{target.branch_id}"
            if key not in move_map:
                move_map[key] = RelocationMove(
                    from_branch_id=best_donor.branch_id,
                    from_city=best_donor.city,
                    to_branch_id=target.branch_id,
                    to_city=target.city,
                )
            move = move_map[key]
            move.quantity += 1
            move.transfer_cost += best_transfer
            move.opportunity_cost += best_opportunity
            move.total_cost += best_total
            total_transfer += best_transfer
            total_opportunity += best_opportunity

    if not move_map:
        return {
            "status": "success",
            "message": "No feasible donor/route pairs found from Relocation table.",
            "relocationNeeded": True,
            "overloadedBranches": overloaded,
            "moves": [],
            "totalVehiclesMoved": 0,
            "totalTransferCost": 0.0,
            "totalOpportunityCost": 0.0,
            "grandTotalCost": 0.0,
        }

    moves = []
    total_moved = 0
    for move in move_map.values():
        total_moved += move.quantity
        payload = asdict(move)
        moves.append(
            {
                "fromBranchId": payload["from_branch_id"],
                "fromCity": payload["from_city"],
                "toBranchId": payload["to_branch_id"],
                "toCity": payload["to_city"],
                "quantity": payload["quantity"],
                "transferCost": payload["transfer_cost"],
                "opportunityCost": payload["opportunity_cost"],
                "totalCost": payload["total_cost"],
            }
        )

    return {
        "status": "success",
        "message": None,
        "relocationNeeded": True,
        "overloadedBranches": overloaded,
        "moves": moves,
        "totalVehiclesMoved": total_moved,
        "totalTransferCost": total_transfer,
        "totalOpportunityCost": total_opportunity,
        "grandTotalCost": total_transfer + total_opportunity,
    }


def _relocation_error(message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "relocationNeeded": False,
        "overloadedBranches": [],
        "moves": [],
        "totalVehiclesMoved": 0,
        "totalTransferCost": 0.0,
        "totalOpportunityCost": 0.0,
        "grandTotalCost": 0.0,
    }
