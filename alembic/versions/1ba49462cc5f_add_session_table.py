"""add session table

Revision ID: 1ba49462cc5f
Revises: 73f2e3783101
Create Date: 2024-11-21 21:00:39.966488

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "1ba49462cc5f"
down_revision: Union[str, None] = "73f2e3783101"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if "sessions" not in tables:
        op.create_table(
            "sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("state_id", sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["state_id"],
                ["states.id"],
            ),
        )


def downgrade():
    op.drop_table("sessions")
