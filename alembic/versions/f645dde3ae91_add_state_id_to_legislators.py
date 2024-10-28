"""Add state_id to legislators

Revision ID: f645dde3ae91
Revises: 5d3c3085c67c
Create Date: 2024-10-28 08:40:32.676267

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f645dde3ae91"
down_revision: Union[str, None] = "5d3c3085c67c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add state_id column to legislators table
    op.add_column("legislators", sa.Column("state_id", sa.Integer(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key("fk_legislators_state_id", "legislators", "states", ["state_id"], ["id"])

    # Create index for state_id
    op.create_index(op.f("ix_legislators_state_id"), "legislators", ["state_id"], unique=False)


def downgrade():
    # Remove index
    op.drop_index(op.f("ix_legislators_state_id"), table_name="legislators")

    # Remove foreign key constraint
    op.drop_constraint("fk_legislators_state_id", "legislators", type_="foreignkey")

    # Remove column
    op.drop_column("legislators", "state_id")
