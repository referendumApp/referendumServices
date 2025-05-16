"""atproto legislator table
Revision ID: 6ce6213e39f6
Revises: 8c120e0c6ace
Create Date: 2025-05-16 10:28:54.554629
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6ce6213e39f6"
down_revision: Union[str, None] = "8c120e0c6ace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legislator",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("did", sa.String(), nullable=False),
        sa.Column("aid", sa.Integer(), nullable=False),
        sa.Column("legislator_id", sa.Integer(), nullable=True),
        sa.Column("pds_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_index(op.f("ix_legislator_aid"), "legislator", ["aid"], schema="atproto", unique=True)
    op.create_index(op.f("ix_legislator_did"), "legislator", ["did"], schema="atproto", unique=True)
    op.create_index(
        op.f("ix_legislator_legislator_id"),
        "legislator",
        ["legislator_id"],
        schema="atproto",
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_legislator_did"), table_name="legislator", schema="atproto")
    op.drop_index(op.f("ix_legislator_aid"), table_name="legislator", schema="atproto")
    op.drop_index(op.f("ix_legislator_legislator_id"), table_name="legislator", schema="atproto")

    op.drop_table("legislator", schema="atproto")
