"""Unit checks for FastAPI service-result → HTTPException mapping."""

import pytest
from fastapi import HTTPException

from vroom.core.errors import raise_for_service_result


def test_raise_for_service_result_ok_statuses() -> None:
    raise_for_service_result({"status": "success"})
    raise_for_service_result({"status": "ok"})
    raise_for_service_result({"status": "pending_verification"})


def test_raise_for_service_result_maps_errors() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_for_service_result({"status": "not_found", "message": "gone"})
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        raise_for_service_result({"status": "forbidden", "message": "nope"})
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        raise_for_service_result({"status": "validation_error", "message": "bad"})
    assert exc_info.value.status_code == 400
