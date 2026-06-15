import logging

from flask import jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden, HTTPException, NotFound

_logger = logging.getLogger("metropolis")
_GENERIC_500_MESSAGE = "Internal server error."
_OK_STATUSES = frozenset({"success", "ok"})
_ERROR_STATUS_EXC = {
    "validation_error": BadRequest,
    "not_found": NotFound,
    "forbidden": Forbidden,
}


def raise_for_service_result(result: dict) -> None:
    """Map service-layer status dicts to HTTP exceptions."""
    status = result.get("status")
    if status in _OK_STATUSES or status is None:
        return
    exc_cls = _ERROR_STATUS_EXC.get(status)
    if exc_cls is not None:
        raise exc_cls(description=result.get("message") or status)
    raise BadRequest(description=result.get("message") or str(status))


def register_error_handlers(app) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        if exc.code and exc.code >= 500:
            # ponytail: never echo exc.description on 5xx — it may carry SQL/internal
            # details. Log the full chain server-side and return a generic message.
            _logger.error("%s on %s", exc.code, request.path, exc_info=exc)
            payload = {"status": "error", "message": _GENERIC_500_MESSAGE}
        elif exc.code == 400:
            payload = {"status": "validation_error", "message": exc.description}
        elif exc.code == 404:
            payload = {"status": "not_found", "message": exc.description}
        else:
            payload = {"status": "error", "message": exc.description}
        return jsonify(payload), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        _logger.error("Unhandled exception on %s", request.path, exc_info=exc)
        return jsonify({"status": "error", "message": _GENERIC_500_MESSAGE}), 500
