"""require state_id for legislators

Revision ID: ba4e2efa2c76
Revises: f645dde3ae91
Create Date: 2024-11-01 06:38:25.112751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ba4e2efa2c76"
down_revision: Union[str, None] = "f645dde3ae91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column("legislators", "state_id", existing_type=sa.Integer(), nullable=False)


def downgrade():
    op.alter_column("legislators", "state_id", existing_type=sa.Integer(), nullable=True)
