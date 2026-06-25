"""Stripe Connect Accounts v2 HTTP client (preview API)."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from vroom.core.config import settings

_logger = logging.getLogger("vroom.stripe_connect_v2")

_STRIPE_API_BASE = "https://api.stripe.com"
_DEFAULT_INCLUDES = ("configuration.recipient", "identity", "requirements")


class StripeConnectV2Error(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _api_key() -> str:
    return settings.stripe_secret_key.strip() or os.environ.get("STRIPE_SECRET_KEY", "").strip()


def _api_version() -> str:
    return settings.stripe_connect_api_version.strip() or "2026-05-27.preview"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Stripe-Version": _api_version(),
        "Content-Type": "application/json",
    }


def _request(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    params: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    key = _api_key()
    if not key:
        raise StripeConnectV2Error("Stripe secret key not configured.")
    url = f"{_STRIPE_API_BASE}{path}"
    headers = _headers()
    if method == "GET":
        headers = {k: v for k, v in headers.items() if k != "Content-Type"}
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=json_body if method != "GET" else None,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        _logger.exception("Stripe v2 request failed: %s %s", method, path)
        raise StripeConnectV2Error(str(exc)) from exc
    if response.status_code >= 400:
        try:
            body = response.json()
            err = body.get("error") or {}
            message = err.get("message") or response.text or "Stripe v2 request failed."
        except ValueError:
            message = response.text or "Stripe v2 request failed."
        raise StripeConnectV2Error(message, status_code=response.status_code)
    if not response.content:
        return {}
    return response.json()


def create_account(payload: dict[str, Any]) -> dict[str, Any]:
    return _request("POST", "/v2/core/accounts", json_body=payload)


def retrieve_account(
    account_id: str,
    *,
    include: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    includes = include or _DEFAULT_INCLUDES
    return _request(
        "GET",
        f"/v2/core/accounts/{account_id}",
        params=[("include", part) for part in includes],
    )


def update_account(account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = {**payload, "include": list(payload.get("include") or _DEFAULT_INCLUDES)}
    return _request("POST", f"/v2/core/accounts/{account_id}", json_body=body)
