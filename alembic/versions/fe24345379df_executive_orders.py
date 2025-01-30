"""executive orders

Revision ID: fe24345379df
Revises: aa2fdd5f0d54
Create Date: 2025-01-29 21:41:54.707776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fe24345379df"
down_revision: Union[str, None] = "aa2fdd5f0d54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "presidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("party_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["partys.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "executive_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status_date", sa.Date(), nullable=True),
        sa.Column("president_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["president_id"],
            ["presidents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_executive_orders_president_id", "executive_orders", ["president_id"])


def downgrade():
    op.drop_index("ix_executive_orders_president_id", "executive_orders")
    op.drop_table("executive_orders")
    op.drop_table("presidents")
