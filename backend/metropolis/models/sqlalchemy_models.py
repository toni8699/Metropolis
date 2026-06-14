"""Frozen SQLAlchemy stubs for Flask-SQLAlchemy init only.

Services use psycopg2 raw SQL — do not add ORM queries here.
See CONTRIBUTING.md for the database access pattern.
"""

from metropolis.extensions import sqldb


class UserModel(sqldb.Model):
    """Minimal model so SQLAlchemy metadata loads; not used in query path."""

    __tablename__ = "app_user"

    user_id = sqldb.Column(sqldb.BigInteger, primary_key=True)
    email = sqldb.Column(sqldb.String(255), nullable=False, unique=True)


class BookingChatStateModel(sqldb.Model):
    """Per-user read cursor for booking chat; queries use raw SQL in MessageService."""

    __tablename__ = "booking_chat_state"

    booking_id = sqldb.Column(
        sqldb.BigInteger, sqldb.ForeignKey("booking.booking_id"), primary_key=True
    )

    user_id = sqldb.Column(sqldb.BigInteger, sqldb.ForeignKey("app_user.user_id"), primary_key=True)

    last_read_message_id = sqldb.Column(
        sqldb.BigInteger, sqldb.ForeignKey("booking_message.message_id")
    )
    last_read_at = sqldb.Column(sqldb.DateTime(timezone=True), nullable=False)
