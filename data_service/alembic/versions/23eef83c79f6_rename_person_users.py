"""rename person users

Revision ID: 23eef83c79f6
Revises: d5945315bd6d
Create Date: 2025-05-13 07:10:28.528065

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "23eef83c79f6"
down_revision: Union[str, None] = "d5945315bd6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("person", "user", schema="atproto")
    op.drop_column("user", "settings", schema="atproto")
    op.drop_column("user", "type", schema="atproto")

    op.add_column(
        "actor", sa.Column("settings", JSONB, nullable=True, default={}), schema="atproto"
    )


def downgrade() -> None:
    op.drop_column("actor", "settings", schema="atproto")
    op.add_column("user", sa.Column("type", sa.String), schema="atproto")
    op.add_column("user", sa.Column("settings", JSONB, nullable=True, default={}), schema="atproto")

    op.rename_table("user", "person", schema="atproto")
