from datetime import datetime, timezone

from metropolis.services.marketplace_common import (
    _BOOKING_HOLD_STATUSES,
    _resolve_search_window,
    listing_available_for_window_sql,
)


def test_resolve_search_window_accepts_snake_case_keys():
    start = datetime(2099, 6, 1, 10, tzinfo=timezone.utc)
    end = datetime(2099, 6, 5, 10, tzinfo=timezone.utc)
    assert _resolve_search_window({"start_at": start, "end_at": end}) == (start, end)


def test_resolve_search_window_requires_both_dates():
    result = _resolve_search_window({"start_at": datetime(2099, 6, 1, tzinfo=timezone.utc)})
    assert result == {
        "status": "validation_error",
        "message": "Both start_at and end_at are required for date-aware search.",
    }


def test_listing_available_sql_uses_hold_statuses():
    sql = listing_available_for_window_sql(_BOOKING_HOLD_STATUSES)
    assert sql.count("%s::booking_status") == len(_BOOKING_HOLD_STATUSES)
    assert "listing_availability" in sql


def test_parse_listing_list_query_accepts_start_end_aliases():
    from unittest.mock import Mock

    from starlette.datastructures import QueryParams

    from metropolis.routers.listings import parse_listing_list_query

    request = Mock()
    request.query_params = QueryParams("start=2099-06-02T10:00:00Z&end=2099-06-04T10:00:00Z")
    query = parse_listing_list_query(request)
    assert query.start_at is not None
    assert query.end_at is not None
