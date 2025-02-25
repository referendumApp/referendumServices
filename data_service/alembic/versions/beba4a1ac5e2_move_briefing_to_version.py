"""move briefing to version

Revision ID: beba4a1ac5e2
Revises: c207c6eca245
Create Date: 2024-12-06 11:30:35.867206

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "beba4a1ac5e2"
down_revision: Union[str, None] = "c207c6eca245"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("bill_versions", sa.Column("briefing", sa.String(), nullable=True))
    op.drop_column("bills", "briefing")


def downgrade():
    op.add_column("bills", sa.Column("briefing", sa.String(), nullable=True))
    op.drop_column("bill_versions", "briefing")
