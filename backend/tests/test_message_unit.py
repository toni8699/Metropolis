"""Unit tests for MessageService unread/read-state helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vroom.services.message_service import MessageService


def _mock_conn(*, fetchall=None, fetchone=None):
    cur = MagicMock()
    cur.fetchall.return_value = fetchall if fetchall is not None else []
    cur.fetchone.return_value = fetchone
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


def test_list_booking_messages_loads_full_thread_without_pagination():
    svc = MessageService()
    conn, cur = _mock_conn(fetchall=[])
    with patch.object(svc, "assert_booking_participant", return_value={"status": "ok"}):
        with patch("vroom.services.message_service.get_connection", return_value=conn):
            svc.list_booking_messages(1, 3, False)

    select_sql = cur.execute.call_args_list[0].args[0].upper()
    assert "ORDER BY M.CREATED_AT ASC" in select_sql
    assert "LIMIT" not in select_sql
    assert "OFFSET" not in select_sql


def test_list_booking_messages_marks_latest_as_read():
    svc = MessageService()
    rows = [
        {
            "message_id": 10,
            "booking_id": 1,
            "sender_id": 2,
            "message_text": "Hi",
            "created_at": MagicMock(isoformat=lambda: "2026-06-01T10:00:00"),
            "sender_name": "Host",
        },
        {
            "message_id": 11,
            "booking_id": 1,
            "sender_id": 3,
            "message_text": "Hello",
            "created_at": MagicMock(isoformat=lambda: "2026-06-01T10:01:00"),
            "sender_name": "Renter",
        },
    ]
    conn, cur = _mock_conn(fetchall=rows)
    with patch.object(svc, "assert_booking_participant", return_value={"status": "ok"}):
        with patch("vroom.services.message_service.get_connection", return_value=conn):
            result = svc.list_booking_messages(1, 3, False)

    assert result["status"] == "ok"
    assert len(result["messages"]) == 2
    upsert_calls = [
        call
        for call in cur.execute.call_args_list
        if "INSERT INTO booking_chat_state" in str(call.args[0])
    ]
    assert len(upsert_calls) == 1
    assert upsert_calls[0].args[1] == (1, 3, 11)


def test_list_booking_messages_skips_read_state_when_empty():
    svc = MessageService()
    conn, cur = _mock_conn(fetchall=[])
    with patch.object(svc, "assert_booking_participant", return_value={"status": "ok"}):
        with patch("vroom.services.message_service.get_connection", return_value=conn):
            result = svc.list_booking_messages(1, 3, False)

    assert result["status"] == "ok"
    assert result["messages"] == []
    upsert_calls = [
        call
        for call in cur.execute.call_args_list
        if "INSERT INTO booking_chat_state" in str(call.args[0])
    ]
    assert upsert_calls == []


def test_list_message_threads_includes_unread_count():
    svc = MessageService()
    row = {
        "booking_id": 5,
        "listing_id": 9,
        "renter_user_id": 3,
        "status": "CONFIRMED",
        "start_at": MagicMock(isoformat=lambda: "2026-06-01T10:00:00"),
        "end_at": MagicMock(isoformat=lambda: "2026-06-03T10:00:00"),
        "price_snapshot_json": {"pricePerDay": 50, "total": 100, "currency": "CAD"},
        "listing_title": "Test Car",
        "price_per_day": 50,
        "owner_user_id": 2,
        "city_zone": "montreal",
        "host_name": "Host",
        "host_email": "host@example.com",
        "renter_name": "Renter",
        "renter_email": "renter@example.com",
        "latest_message_text": "New msg",
        "latest_message_at": MagicMock(isoformat=lambda: "2026-06-01T12:00:00"),
        "unread_count": 2,
    }
    conn, cur = _mock_conn(fetchall=[row])
    with patch("vroom.services.message_service.get_connection", return_value=conn):
        with patch(
            "vroom.services.message_service.fetch_listing_images_map",
            return_value={9: []},
        ):
            result = svc.list_message_threads(3)

    assert result["status"] == "ok"
    assert len(result["threads"]) == 1
    assert result["threads"][0]["unreadCount"] == 2
    select_sql = cur.execute.call_args.args[0]
    assert "booking_chat_state" in select_sql
    assert "unread_count" in select_sql
