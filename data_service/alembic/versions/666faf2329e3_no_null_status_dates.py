"""no_null_status_dates

Revision ID: 666faf2329e3
Revises: 9546aedcaac4
Create Date: 2025-04-25 13:02:05.191121

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "666faf2329e3"
down_revision: Union[str, None] = "9546aedcaac4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column("bills", "status_date", nullable=False)


def downgrade():
    op.alter_column("bills", "status_date", nullable=True)
