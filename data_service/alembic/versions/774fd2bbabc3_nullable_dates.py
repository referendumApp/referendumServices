"""Allow null dates in bill versions

Revision ID: 774fd2bbabc3
Revises: 43e4bac6f9b5
Create Date: 2025-03-27 07:05:24.443558

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "774fd2bbabc3"
down_revision: Union[str, None] = "43e4bac6f9b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("bill_versions", "date", existing_type=sa.DATE(), nullable=True)


def downgrade() -> None:
    op.alter_column("bill_versions", "date", existing_type=sa.DATE(), nullable=False)
