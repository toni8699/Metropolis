"""FastAPI exception handlers and service result mapping."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_logger = logging.getLogger("metropolis")
_GENERIC_500_MESSAGE = "Internal server error."
_OK_STATUSES = frozenset({"success", "ok"})


def _detail_message(detail: object) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts: list[str] = []
        for item in detail:
            if isinstance(item, dict):
                loc = ".".join(str(part) for part in item.get("loc", ()))
                msg = item.get("msg", "")
                parts.append(f"{loc}: {msg}" if loc else str(msg))
            else:
                parts.append(str(item))
        return "; ".join(parts)
    return str(detail)


def _validation_error_message(exc: RequestValidationError) -> str:
    return _detail_message(exc.errors())


def raise_for_service_result(result: dict) -> None:
    """Map service-layer status dicts to HTTPException."""
    status = result.get("status")
    if status in _OK_STATUSES or status is None:
        return
    message = result.get("message") or str(status)
    if status == "validation_error":
        raise HTTPException(status_code=400, detail=message)
    if status == "not_found":
        raise HTTPException(status_code=404, detail=message)
    if status == "forbidden":
        raise HTTPException(status_code=403, detail=message)
    if status == "error":
        raise HTTPException(status_code=500, detail=message)
    raise HTTPException(status_code=400, detail=message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            _logger.error("%s on %s", exc.status_code, request.url.path, exc_info=exc)
            payload = {"status": "error", "message": _GENERIC_500_MESSAGE}
        elif exc.status_code == 400:
            payload = {"status": "validation_error", "message": _detail_message(exc.detail)}
        elif exc.status_code == 404:
            payload = {"status": "not_found", "message": _detail_message(exc.detail)}
        else:
            payload = {"status": "error", "message": _detail_message(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "status": "validation_error",
                "message": _validation_error_message(exc),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        _logger.error("Unhandled exception on %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": _GENERIC_500_MESSAGE},
        )
