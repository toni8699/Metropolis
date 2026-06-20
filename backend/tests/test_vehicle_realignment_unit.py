"""Unit tests for vehicle asset/listing cache sync and VIN mapping."""

from __future__ import annotations

import json

from metropolis.services.listing_service import (
    ListingService,
    _management_mode,
    _normalize_body_type_other,
)
from metropolis.services.vin_decode_service import (
    BODY_TYPE_DEFAULTS,
    enrich_with_spec_fields,
    map_nhtsa_result,
    normalize_vin,
    spec_value,
)


class _FakeCursor:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def execute(self, *_args, **_kwargs) -> None:
        return None

    def fetchone(self) -> dict | None:
        return self._row


def test_normalize_vin_accepts_valid_value() -> None:
    assert normalize_vin(" 1hgcm82633a004352 ") == "1HGCM82633A004352"


def test_normalize_vin_rejects_short_value() -> None:
    assert normalize_vin("ABC") is None


def test_management_mode_derivation() -> None:
    assert _management_mode(is_company_owned=False) == "SELF"
    assert _management_mode(is_company_owned=True) == "COMPANY_MANAGED"


def test_build_asset_facts_manual_self_allowed() -> None:
    service = ListingService()
    cur = _FakeCursor(None)
    result = service._build_asset_facts(
        cur,
        {"make": "Toyota", "model": "Corolla", "year": 2020},
        is_company_owned=False,
    )
    assert result["status"] == "success"
    assert result["facts"]["vin"] is None
    assert result["facts"]["is_vin_verified"] is False


def test_build_asset_facts_company_requires_vin() -> None:
    service = ListingService()
    cur = _FakeCursor(None)
    result = service._build_asset_facts(
        cur,
        {"make": "Toyota", "model": "Corolla", "year": 2020},
        is_company_owned=True,
    )
    assert result["status"] == "validation_error"
    assert "VIN is required" in result["message"]


def test_map_nhtsa_result_maps_mpv_to_body_type() -> None:
    cur = _FakeCursor(
        {
            "body_type_id": 5,
            "code": "MINIVAN",
            "display_name": "Minivan",
        }
    )
    mapped = map_nhtsa_result(
        cur,
        {
            "Make": "Honda",
            "Model": "Odyssey",
            "ModelYear": "2018",
            "TransmissionStyle": "Automatic",
            "FuelTypePrimary": "Gasoline",
            "BodyClass": "MPV",
            "Seats": "7",
        },
    )
    assert mapped["make"] == "Honda"
    assert mapped["model"] == "Odyssey"
    assert mapped["model_year"] == 2018
    assert mapped["body_type_id"] == 5
    assert mapped["suggested_body_type"]["display_name"] == "Minivan"


def test_map_nhtsa_fixture_shape() -> None:
    fixture = {
        "Results": [
            {
                "Make": "TOYOTA",
                "Model": "RAV4",
                "ModelYear": "2020",
                "BodyClass": "Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)",
            }
        ]
    }
    assert fixture["Results"][0]["Make"] == "TOYOTA"
    assert json.dumps(fixture)


def test_enrich_applies_body_type_defaults_when_nhtsa_null() -> None:
    cur = _FakeCursor({"code": "SUV"})
    mapped = {
        "make": "Toyota",
        "model": "RAV4",
        "model_year": 2020,
        "transmission": None,
        "fuel_type": None,
        "seats": None,
        "doors": None,
        "body_type_id": 2,
        "suggested_body_type": {"body_type_id": 2, "code": "SUV", "display_name": "SUV"},
    }
    enriched = enrich_with_spec_fields(cur, mapped)
    assert enriched["seats"]["value"] == BODY_TYPE_DEFAULTS["SUV"]["seats"]
    assert enriched["seats"]["is_verified"] is False
    assert enriched["seats"]["source"] == "default"
    assert enriched["transmission"]["source"] == "default"
    assert spec_value(enriched["fuel_type"]) is None
    assert enriched["fuel_type"]["source"] == "missing"


def test_normalize_body_type_other_requires_label_for_other_code() -> None:
    cur = _FakeCursor({"code": "OTHER"})
    missing = _normalize_body_type_other(cur, 8, "")
    assert missing["status"] == "validation_error"
    ok = _normalize_body_type_other(cur, 8, "  Limousine ")
    assert ok["status"] == "success"
    assert ok["value"] == "Limousine"


def test_normalize_body_type_other_clears_for_non_other() -> None:
    cur = _FakeCursor({"code": "SEDAN"})
    result = _normalize_body_type_other(cur, 1, "should not store")
    assert result["status"] == "success"
    assert result["value"] is None


def test_enrich_keeps_nhtsa_values_verified() -> None:
    cur = _FakeCursor(None)
    mapped = {
        "seats": 7,
        "doors": 5,
        "transmission": "Automatic",
        "fuel_type": "Gasoline",
        "suggested_body_type": {"code": "MINIVAN"},
    }
    enriched = enrich_with_spec_fields(cur, mapped)
    assert enriched["seats"]["value"] == 7
    assert enriched["seats"]["is_verified"] is True
    assert enriched["seats"]["source"] == "nhtsa"
