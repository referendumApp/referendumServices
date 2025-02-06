"""Create State abbr column

Revision ID: 895ad8c038a1
Revises: 030be05fff89
Create Date: 2025-02-06 05:54:58.773213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '895ad8c038a1'
down_revision: Union[str, None] = '030be05fff89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("states", sa.Column("abbr", sa.String(), nullable=False))

    op.create_foreign_key(
        "fk_representing_state_id",
        "legislators",
        "states",
        ["representing_state_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_column("states", "abbr")

    op.drop_constraint("fk_representing_state_id", "legislators", type_="foreignkey")
