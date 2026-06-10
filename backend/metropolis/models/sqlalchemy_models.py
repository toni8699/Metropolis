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
