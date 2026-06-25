"""Payout service unit tests (mock Stripe + DB)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vroom.services.payout_service import (
    PayoutService,
    _account_onboarding_required,
    _account_pending_verification,
    _connect_ready_from_account,
    _platform_business_profile,
    _public_business_url,
)


def _v2_account(*, transfers_status: str = "pending", requirements: dict | None = None) -> dict:
    return {
        "id": "acct_test",
        "configuration": {
            "recipient": {
                "capabilities": {
                    "stripe_balance": {
                        "stripe_transfers": {"status": transfers_status},
                    },
                },
            },
        },
        "requirements": requirements
        or {"currently_due": [], "past_due": [], "pending_verification": []},
    }


def test_platform_business_profile_prefills_brand():
    with patch("vroom.services.payout_service.settings") as mock_settings:
        mock_settings.stripe_connect_business_name = "Vroom"
        mock_settings.stripe_connect_business_url = "https://vroom.example"
        mock_settings.stripe_connect_support_email = "help@vroom.example"
        mock_settings.mail_from = ""
        profile = _platform_business_profile()
    assert profile["name"] == "Vroom"
    assert profile["url"] == "https://vroom.example"
    assert profile["support_email"] == "help@vroom.example"
    assert profile["mcc"] == "7512"
    assert "Vroom" in profile["product_description"]


def test_public_business_url_skips_localhost():
    with patch("vroom.services.payout_service.settings") as mock_settings:
        mock_settings.stripe_connect_business_url = ""
        mock_settings.frontend_base_url = "http://localhost:3000"
        assert _public_business_url() is None


def _mock_conn(fetchone=None, fetchall=None):
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = fetchone or [None]
    cur.fetchall.return_value = fetchall or []
    conn.cursor.return_value.__enter__.return_value = cur
    conn.__enter__.return_value = conn
    return conn, cur


SNAPSHOT = {"subtotal": 100, "cleaningFee": 50, "dayCount": 1, "pricePerDay": 100}


def test_v2_account_pending_verification_when_submitted_not_ready():
    account = _v2_account(
        transfers_status="pending",
        requirements={"entries": [], "summary": {"minimum_deadline": {"status": "eventually_due"}}},
    )
    assert not _connect_ready_from_account(account)
    assert not _account_onboarding_required(account)
    assert _account_pending_verification(account)


def test_v2_account_pending_verification_only_when_stripe_reviewing():
    account = _v2_account(
        transfers_status="pending",
        requirements={
            "entries": [
                {"minimum_deadline": {"status": "pending_verification"}},
            ],
        },
    )
    assert not _account_onboarding_required(account)
    assert _account_pending_verification(account)


def test_v2_account_onboarding_required_until_ready():
    assert _account_onboarding_required(_v2_account(transfers_status="pending"))
    assert not _account_onboarding_required(_v2_account(transfers_status="active"))
    assert _account_onboarding_required(
        _v2_account(
            transfers_status="pending",
            requirements={
                "entries": [{"minimum_deadline": {"status": "currently_due"}}],
            },
        )
    )


def test_transfer_uses_source_transaction_from_payment_intent():
    svc = PayoutService()
    booking_row = {
        "booking_id": 7,
        "status": "COMPLETED",
        "source_type": "OWNER",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
        "stripe_payment_intent_id": "pi_test",
    }
    profile = {"payout_ref": "acct_test"}
    conn, _cur = _mock_conn(fetchone=[booking_row, None, profile])
    mock_transfer = MagicMock(id="tr_test")
    with (
        patch("vroom.services.payout_service.get_connection", return_value=conn),
        patch("vroom.services.payout_service._connect_enabled", return_value=True),
        patch(
            "vroom.services.payout_service._retrieve_connect_account",
            return_value=_v2_account(transfers_status="active"),
        ),
        patch("vroom.services.payout_service._resolve_charge_id", return_value="ch_test"),
        patch(
            "vroom.services.payout_service.stripe.Transfer.create",
            return_value=mock_transfer,
        ) as create,
        patch("vroom.services.payout_service.mail_service.send_host_payout_sent"),
    ):
        result = svc.transfer_for_booking(7)
    assert result["payoutStatus"] == "succeeded"
    create.assert_called_once()
    assert create.call_args.kwargs["source_transaction"] == "ch_test"


def test_create_account_session_returns_onboarding_secret():
    svc = PayoutService()
    session = MagicMock(client_secret="acs_test_secret")
    with (
        patch.object(svc, "ensure_connect_account", return_value=("acct_test", None)),
        patch(
            "vroom.services.payout_service._retrieve_connect_account",
            return_value=_v2_account(transfers_status="pending"),
        ),
        patch(
            "vroom.services.payout_service.stripe.AccountSession.create",
            return_value=session,
        ) as create,
        patch("vroom.services.payout_service._connect_enabled", return_value=True),
    ):
        result = svc.create_account_session(1, "host@vroom.ca", component="onboarding")
    assert result["status"] == "success"
    assert result["clientSecret"] == "acs_test_secret"
    assert result["accountId"] == "acct_test"
    assert result["component"] == "onboarding"
    assert "account_onboarding" in create.call_args.kwargs["components"]


def test_create_account_session_returns_management_secret():
    svc = PayoutService()
    session = MagicMock(client_secret="acs_mgmt_secret")
    with (
        patch.object(svc, "ensure_connect_account", return_value=("acct_test", None)),
        patch(
            "vroom.services.payout_service._retrieve_connect_account",
            return_value=_v2_account(transfers_status="active"),
        ),
        patch(
            "vroom.services.payout_service.stripe.AccountSession.create",
            return_value=session,
        ) as create,
        patch("vroom.services.payout_service._connect_enabled", return_value=True),
    ):
        result = svc.create_account_session(1, "host@vroom.ca", component="management")
    assert result["status"] == "success"
    assert result["clientSecret"] == "acs_mgmt_secret"
    assert result["component"] == "management"
    assert "account_management" in create.call_args.kwargs["components"]


def test_create_express_dashboard_link_returns_url():
    svc = PayoutService()
    login = MagicMock(url="https://connect.stripe.com/express/login/test")
    with (
        patch("vroom.services.payout_service.get_connection") as mock_get_conn,
        patch("vroom.services.payout_service._connect_enabled", return_value=True),
        patch.object(svc, "_account_ready", return_value=True),
        patch("vroom.services.payout_service.stripe.Account.create_login_link", return_value=login),
    ):
        conn, cur = _mock_conn(fetchone=[{"payout_ref": "acct_test"}])
        mock_get_conn.return_value = conn
        result = svc.create_express_dashboard_link(1)
    assert result["status"] == "success"
    assert result["dashboardUrl"] == "https://connect.stripe.com/express/login/test"


def test_transfer_skipped_for_fleet_listing():
    svc = PayoutService()
    row = {
        "booking_id": 1,
        "status": "COMPLETED",
        "source_type": "FLEET",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[row, None])
    with patch("vroom.services.payout_service.get_connection", return_value=conn):
        result = svc.transfer_for_booking(1)
    assert result["status"] == "skipped"


def test_gross_payout_amount_from_snapshot():
    from vroom.services.booking_rows import build_host_earnings, build_price_breakdown

    row = {
        "price_snapshot_json": {
            "pricePerDay": 100,
            "dayCount": 2,
            "subtotal": 200,
            "cleaningFee": 50,
            "serviceFee": 20,
            "total": 270,
            "currency": "CAD",
        },
        "start_at": MagicMock(),
        "end_at": MagicMock(),
    }
    pricing = build_price_breakdown(row)
    earnings = build_host_earnings(pricing)
    assert earnings["grossPayout"] == 250.0


def test_transfer_idempotent_when_already_succeeded():
    svc = PayoutService()
    payout_row = {"payout_id": 1, "status": "succeeded", "stripe_transfer_id": "tr_123"}
    booking_row = {
        "booking_id": 5,
        "status": "COMPLETED",
        "source_type": "OWNER",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[booking_row, payout_row])
    with patch("vroom.services.payout_service.get_connection", return_value=conn):
        result = svc.transfer_for_booking(5)
    assert result["status"] == "success"
    assert result["payoutStatus"] == "succeeded"


def test_connect_disabled_marks_skipped():
    svc = PayoutService()
    booking_row = {
        "booking_id": 3,
        "status": "COMPLETED",
        "source_type": "OWNER",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[booking_row, None])
    with (
        patch("vroom.services.payout_service.get_connection", return_value=conn),
        patch("vroom.services.payout_service._connect_enabled", return_value=False),
    ):
        result = svc.transfer_for_booking(3)
    assert result["payoutStatus"] == "skipped"
