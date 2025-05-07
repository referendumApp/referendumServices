"""add did & uid

Revision ID: f3584da4c065
Revises: 9546aedcaac4
Create Date: 2025-05-07 07:08:43.206700

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3584da4c065"
down_revision: Union[str, None] = "9546aedcaac4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("legislators", sa.Column("uid", sa.String(), nullable=True))
    op.add_column("legislators", sa.Column("did", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("legislators", "uid")
    op.drop_column("legislators", "did")
