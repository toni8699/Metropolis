"""NHTSA VPIC VIN decode + metadata persistence."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from vroom.core.db import get_connection

_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{11,17}$")
_NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"

# ponytail: static map by ref_body_type.code; upgrade path = admin-editable ref table
BODY_TYPE_DEFAULTS: dict[str, dict[str, str | int]] = {
    "SUV": {"seats": 5, "doors": 5, "transmission": "AUTOMATIC"},
    "MINIVAN": {"seats": 7, "doors": 5, "transmission": "AUTOMATIC"},
    "COUPE": {"seats": 4, "doors": 2, "transmission": "AUTOMATIC"},
    "SEDAN": {"seats": 5, "doors": 4, "transmission": "AUTOMATIC"},
    "TRUCK": {"seats": 5, "doors": 4, "transmission": "AUTOMATIC"},
    "WAGON": {"seats": 5, "doors": 4, "transmission": "AUTOMATIC"},
    "EV": {"seats": 5, "doors": 4, "transmission": "AUTOMATIC"},
    "OTHER": {"seats": 5, "doors": 4, "transmission": "AUTOMATIC"},
}


def normalize_transmission(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if "manual" in lowered:
        return "MANUAL"
    if "auto" in lowered or "cvt" in lowered:
        return "AUTOMATIC"
    if text in {"AUTOMATIC", "MANUAL"}:
        return text
    return None


def normalize_fuel_type(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if "electric" in lowered or lowered == "ev":
        return "Electric"
    if "hybrid" in lowered:
        return "Hybrid"
    if "diesel" in lowered:
        return "Diesel"
    if "gas" in lowered or "petrol" in lowered:
        return "Gasoline"
    if text in {"Gasoline", "Electric", "Hybrid", "Diesel"}:
        return text
    return None


def normalize_vin(vin: str | None) -> str | None:
    if vin is None:
        return None
    cleaned = str(vin).strip().upper()
    if not cleaned:
        return None
    if not _VIN_RE.match(cleaned):
        return None
    return cleaned


def _clean_nhtsa_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"Not Applicable", "0", "null"}:
        return None
    return text


def _parse_model_year(value: object) -> int | None:
    text = _clean_nhtsa_value(value)
    if not text or not text.isdigit():
        return None
    year = int(text)
    if year < 1900 or year > 2100:
        return None
    return year


def _parse_positive_int(value: object) -> int | None:
    text = _clean_nhtsa_value(value)
    if not text or not text.isdigit():
        return None
    parsed = int(text)
    return parsed if parsed > 0 else None


def _spec_field(value: Any, *, is_verified: bool, source: str) -> dict[str, Any]:
    return {"value": value, "is_verified": is_verified, "source": source}


def _resolve_spec(nhtsa_value: Any, default_value: Any) -> dict[str, Any]:
    if nhtsa_value is not None:
        return _spec_field(nhtsa_value, is_verified=True, source="nhtsa")
    if default_value is not None:
        return _spec_field(default_value, is_verified=False, source="default")
    return _spec_field(None, is_verified=False, source="missing")


def spec_value(spec: dict[str, Any] | None) -> Any:
    if not spec:
        return None
    return spec.get("value")


def _body_type_code_for_mapped(cur, mapped: dict) -> str | None:
    suggested = mapped.get("suggested_body_type") or {}
    code = suggested.get("code")
    if code:
        return str(code)
    body_type_id = mapped.get("body_type_id")
    if body_type_id is None:
        return None
    cur.execute(
        "SELECT code FROM ref_body_type WHERE body_type_id = %s",
        (body_type_id,),
    )
    row = cur.fetchone()
    return str(row["code"]) if row and row.get("code") else None


def enrich_with_spec_fields(cur, mapped: dict) -> dict:
    """Replace flat spec columns with {value, is_verified, source} objects."""
    body_code = _body_type_code_for_mapped(cur, mapped)
    defaults = BODY_TYPE_DEFAULTS.get(body_code or "", {})
    enriched = dict(mapped)
    enriched["seats"] = _resolve_spec(mapped.get("seats"), defaults.get("seats"))
    enriched["doors"] = _resolve_spec(mapped.get("doors"), defaults.get("doors"))
    enriched["transmission"] = _resolve_spec(
        mapped.get("transmission"), defaults.get("transmission")
    )
    enriched["fuel_type"] = _resolve_spec(mapped.get("fuel_type"), defaults.get("fuel_type"))
    return enriched


def fetch_nhtsa_decode(vin: str) -> dict[str, Any]:
    url = _NHTSA_URL.format(vin=vin)
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "status": "error",
            "message": f"NHTSA decode failed: {exc}",
        }
    results = payload.get("Results") or []
    if not results:
        return {"status": "partial", "message": "No decode results returned."}
    return {"status": "success", "raw": payload, "result": results[0]}


def map_nhtsa_result(cur, result: dict) -> dict:
    make = _clean_nhtsa_value(result.get("Make"))
    model = _clean_nhtsa_value(result.get("Model"))
    model_year = _parse_model_year(result.get("ModelYear"))
    transmission = normalize_transmission(
        _clean_nhtsa_value(result.get("TransmissionStyle"))
        or _clean_nhtsa_value(result.get("TransmissionSpeeds"))
    )
    fuel_type = normalize_fuel_type(_clean_nhtsa_value(result.get("FuelTypePrimary")))
    seats = _parse_positive_int(result.get("Seats"))
    doors = _parse_positive_int(result.get("Doors"))
    body_class = _clean_nhtsa_value(result.get("BodyClass"))
    body_type_id = None
    suggested_body_type = None
    if body_class:
        normalized = body_class.upper()
        cur.execute(
            """
            SELECT m.body_type_id, bt.code, bt.display_name
            FROM ref_nhtsa_body_class_map m
            JOIN ref_body_type bt ON bt.body_type_id = m.body_type_id
            WHERE m.nhtsa_body_class = %s
            """,
            (normalized,),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                """
                SELECT m.body_type_id, bt.code, bt.display_name
                FROM ref_nhtsa_body_class_map m
                JOIN ref_body_type bt ON bt.body_type_id = m.body_type_id
                WHERE %s LIKE '%%' || m.nhtsa_body_class || '%%'
                ORDER BY char_length(m.nhtsa_body_class) DESC
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
        if row:
            body_type_id = row["body_type_id"]
            suggested_body_type = {
                "body_type_id": row["body_type_id"],
                "code": row["code"],
                "display_name": row["display_name"],
            }
    return {
        "make": make,
        "model": model,
        "model_year": model_year,
        "transmission": transmission,
        "fuel_type": fuel_type,
        "seats": seats,
        "doors": doors,
        "body_class": body_class,
        "body_type_id": body_type_id,
        "suggested_body_type": suggested_body_type,
    }


def decode_vin(vin: str) -> dict:
    normalized = normalize_vin(vin)
    if not normalized:
        return {"status": "validation_error", "message": "VIN must be 11-17 valid characters."}
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            fetched = fetch_nhtsa_decode(normalized)
            if fetched["status"] == "error":
                return fetched
            mapped = map_nhtsa_result(cur, fetched.get("result") or {})
            decoded = enrich_with_spec_fields(cur, mapped)
            partial = fetched["status"] == "partial" or not decoded.get("make")
            return {
                "status": "partial" if partial else "success",
                "vin": normalized,
                "decoded": decoded,
                "raw_stored": False,
            }


def upsert_vin_metadata(cur, vehicle_id: int, vin: str, raw_payload: dict) -> None:
    cur.execute(
        """
        INSERT INTO vehicle_vin_metadata (vehicle_id, vin, nhtsa_response, decoded_at)
        VALUES (%s, %s, %s::jsonb, NOW())
        ON CONFLICT (vehicle_id) DO UPDATE
        SET vin = EXCLUDED.vin,
            nhtsa_response = EXCLUDED.nhtsa_response,
            decoded_at = NOW()
        """,
        (vehicle_id, vin, Json(raw_payload)),
    )


def decode_and_map_for_asset(cur, vin: str) -> dict:
    """Decode VIN and return metal facts for vehicle_asset insert/update."""
    normalized = normalize_vin(vin)
    if not normalized:
        return {"status": "validation_error", "message": "VIN must be 11-17 valid characters."}
    fetched = fetch_nhtsa_decode(normalized)
    if fetched["status"] == "error":
        return fetched
    mapped = map_nhtsa_result(cur, fetched.get("result") or {})
    decoded = enrich_with_spec_fields(cur, mapped)
    return {
        "status": "success",
        "vin": normalized,
        "raw": fetched.get("raw"),
        "facts": {
            "vin": normalized,
            "make": decoded.get("make"),
            "model": decoded.get("model"),
            "model_year": decoded.get("model_year"),
            "transmission": spec_value(decoded.get("transmission")),
            "fuel_type": spec_value(decoded.get("fuel_type")),
            "seats": spec_value(decoded.get("seats")),
            "body_type_id": decoded.get("body_type_id"),
        },
    }


vin_decode_service = type(
    "VinDecodeService",
    (),
    {
        "normalize_vin": staticmethod(normalize_vin),
        "decode_vin": staticmethod(decode_vin),
        "decode_and_map_for_asset": staticmethod(decode_and_map_for_asset),
        "upsert_vin_metadata": staticmethod(upsert_vin_metadata),
        "enrich_with_spec_fields": staticmethod(enrich_with_spec_fields),
        "spec_value": staticmethod(spec_value),
    },
)()
