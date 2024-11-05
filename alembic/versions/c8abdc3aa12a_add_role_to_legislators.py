"""add legislative body to legislators

Revision ID: c8abdc3aa12a
Revises: a8b4f2c91d3e
Create Date: 2024-11-05 13:30:58.132430

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8abdc3aa12a"
down_revision: Union[str, None] = "a8b4f2c91d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("legislators", sa.Column("role_id", sa.Integer(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key("fk_legislators_role_id", "legislators", "roles", ["role_id"], ["id"])

    # Create index
    op.create_index(op.f("ix_legislators_role_id"), "legislators", ["role_id"], unique=False)


def downgrade():
    # Remove index
    op.drop_index(op.f("ix_legislators_role_id"), table_name="legislators")

    # Remove foreign key constraint
    op.drop_constraint("fk_legislators_role_id", "legislators", type="foreignkey")

    # Remove column
    op.drop_column("legislators", "role_id")
