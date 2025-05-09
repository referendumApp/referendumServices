"""rename users

Revision ID: d5945315bd6d
Revises: f3584da4c065
Create Date: 2025-05-09 12:50:26.807243

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5945315bd6d"
down_revision: Union[str, None] = "f3584da4c065"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
