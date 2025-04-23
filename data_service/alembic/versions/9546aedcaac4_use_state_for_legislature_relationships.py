"""use state for legislature relationships

Revision ID: 9546aedcaac4
Revises: 86ff840c38ac
Create Date: 2025-04-23 07:59:53.039285

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9546aedcaac4"
down_revision: Union[str, None] = "86ff840c38ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename where we are specifically referring to a legislature
    op.alter_column("legislative_bodys", "state_id", new_column_name="legislature_id")
    op.alter_column("sessions", "state_id", new_column_name="legislature_id")
    op.alter_column("bills", "state_id", new_column_name="legislature_id")

    # Rename legislators columns
    op.alter_column("legislators", "state_id", new_column_name="legislature_id")
    op.alter_column("legislators", "representing_state_id", new_column_name="state_id")

    # Add level to states
    op.add_column("states", sa.Column("level", sa.String))


def downgrade():
    op.drop_column("states", "level")

    op.alter_column("legislators", "state_id", new_column_name="representing_state_id")
    op.alter_column("legislators", "legislature_id", new_column_name="state_id")

    op.alter_column("bills", "legislature_id", new_column_name="state_id")
    op.alter_column("sessions", "legislature_id", new_column_name="state_id")
    op.alter_column("legislative_bodys", "legislature_id", new_column_name="state_id")
