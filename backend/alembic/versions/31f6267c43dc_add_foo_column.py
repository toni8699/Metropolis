"""add foo column

Revision ID: 31f6267c43dc
Revises: 000001_sql_baseline
Create Date: 2026-05-21 13:17:23.966278

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31f6267c43dc'
down_revision: Union[str, None] = '000001_sql_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
