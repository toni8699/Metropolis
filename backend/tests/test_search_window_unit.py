from datetime import datetime, timezone

from metropolis.services.marketplace_common import _resolve_search_window


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
