"""Unit checks for service-result → HTTP error mapping."""

import os

import pytest
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

os.environ.setdefault("FLASK_DEBUG", "1")

from metropolis.errors import raise_for_service_result


def test_raise_for_service_result_ok_statuses():
    raise_for_service_result({"status": "success"})
    raise_for_service_result({"status": "ok"})


def test_raise_for_service_result_maps_errors():
    with pytest.raises(NotFound):
        raise_for_service_result({"status": "not_found", "message": "gone"})
    with pytest.raises(Forbidden):
        raise_for_service_result({"status": "forbidden", "message": "nope"})
    with pytest.raises(BadRequest):
        raise_for_service_result({"status": "validation_error", "message": "bad"})
