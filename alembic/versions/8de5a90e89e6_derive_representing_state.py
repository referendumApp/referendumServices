"""derive representing state

Revision ID: 8de5a90e89e6
Revises: aa2fdd5f0d54
Create Date: 2025-01-16 13:18:28.797300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8de5a90e89e6"
down_revision: Union[str, None] = "aa2fdd5f0d54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add column to legislators table
    op.add_column("legislators", sa.Column("representing_state_abbr", sa.String(), nullable=True))

    # Create index
    op.create_index(
        op.f("ix_legislators_representing_state_abbr"),
        "legislators",
        ["representing_state_abbr"],
        unique=False,
    )


def downgrade():
    # Remove index
    op.drop_index(op.f("ix_legislators_representing_state_abbr"), table_name="legislators")

    # Remove column
    op.drop_column("legislators", "representing_state_abbr")
