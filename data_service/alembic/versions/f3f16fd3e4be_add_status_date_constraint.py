"""add status date constraint

Revision ID: f3f16fd3e4be
Revises: 4bc80e18174b
Create Date: 2025-04-09 09:23:20.763042

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3f16fd3e4be"
down_revision: Union[str, None] = "4bc80e18174b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("bills", "status_date", nullable=False)


def downgrade() -> None:
    op.alter_column("bills", "status_date", nullable=True)
