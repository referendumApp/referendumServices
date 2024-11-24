"""update bill_sponsors

Revision ID: b6b109a8e4ed
Revises: f47d504ae1ff
Create Date: 2024-11-24 11:09:27.240231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6b109a8e4ed"
down_revision: Union[str, None] = "f47d504ae1ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
