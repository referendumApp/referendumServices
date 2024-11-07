"""add hash to bill_versions

Revision ID: 15516b02753d
Revises: c8abdc3aa12a
Create Date: 2024-11-07 09:00:43.825952

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15516b02753d"
down_revision: Union[str, None] = "c8abdc3aa12a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bill_versions", sa.Column("hash", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("bill_versions", "hash")
