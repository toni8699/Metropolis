"""Unit tests for listing search filter SQL builder."""

from __future__ import annotations

from metropolis.services.marketplace_common import build_listing_search_filters


def test_build_filters_price_and_body_type() -> None:
    clauses, params, error = build_listing_search_filters(
        {
            "min_price": 50,
            "max_price": 120,
            "body_type_ids": [1, 3],
        },
        booking_hold_statuses=("CONFIRMED",),
    )
    assert error is None
    assert "l.price_per_day >= %s" in clauses
    assert "l.price_per_day <= %s" in clauses
    assert "va.body_type_id = ANY(%s)" in clauses
    assert params[:3] == [50.0, 120.0, [1, 3]]


def test_build_filters_transmission_and_fuel() -> None:
    clauses, params, error = build_listing_search_filters(
        {
            "transmission": "AUTOMATIC",
            "fuel_types": ["Gasoline", "Hybrid"],
        },
        booking_hold_statuses=("CONFIRMED",),
    )
    assert error is None
    assert "va.transmission = %s::transmission_type" in clauses
    assert "va.fuel_type = ANY(%s::fuel_type_enum[])" in clauses
    assert params[-2:] == ["AUTOMATIC", ["Gasoline", "Hybrid"]]


def test_build_filters_seats_exact_and_seven_plus() -> None:
    clauses, params, error = build_listing_search_filters(
        {"seats": [2, 5, 7]},
        booking_hold_statuses=("CONFIRMED",),
    )
    assert error is None
    assert "(va.seats = ANY(%s) OR va.seats >= %s)" in " ".join(clauses)
    assert [2, 5] in params
    assert 7 in params


def test_build_filters_feature_intersection() -> None:
    clauses, params, error = build_listing_search_filters(
        {"feature_ids": [4, 9]},
        booking_hold_statuses=("CONFIRMED",),
    )
    assert error is None
    sql = " ".join(clauses)
    assert "HAVING COUNT(DISTINCT lf.feature_id) = %s" in sql
    assert params[-2:] == [[4, 9], 2]


def test_build_filters_date_validation_error() -> None:
    _clauses, _params, error = build_listing_search_filters(
        {"start_at": "2099-01-01T00:00:00Z"},
        booking_hold_statuses=("CONFIRMED",),
    )
    assert error is not None
    assert error["status"] == "validation_error"
