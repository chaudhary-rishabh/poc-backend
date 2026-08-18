"""add model and effort columns to sessions

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("model", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("effort", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "effort")
    op.drop_column("sessions", "model")
