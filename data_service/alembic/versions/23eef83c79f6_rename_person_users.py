"""rename person users

Revision ID: 23eef83c79f6
Revises: d5945315bd6d
Create Date: 2025-05-13 07:10:28.528065

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "23eef83c79f6"
down_revision: Union[str, None] = "d5945315bd6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("person", "user", schema="atproto")


def downgrade() -> None:
    op.rename_table("user", "person", schema="atproto")
