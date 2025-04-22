"""legislator data model change

Revision ID: ea680b63e3c8
Revises: 86ff840c38ac
Create Date: 2025-04-22 07:10:03.436956

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea680b63e3c8"
down_revision: Union[str, None] = "86ff840c38ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Migrate roles to chambers
    op.rename_table("roles", "chambers")
    op.execute(
        "UPDATE chambers SET name = 'House of Representatives' WHERE name = 'Representative'"
    )
    op.execute("UPDATE chambers SET name = 'Senate' WHERE name = 'Senator'")

    # Update legislators table
    op.alter_column("legislators", "role_id", new_column_name="chamber_id")
    op.create_foreign_key(
        "legislators_chamber_id_fkey", "legislators", "chambers", ["chamber_id"], ["id"]
    )

    # Update legislative_bodys table
    op.alter_column("legislative_bodys", "role_id", new_column_name="chamber_id")
    op.create_foreign_key(
        "legislative_bodys_chamber_id_fkey", "legislative_bodys", "chambers", ["chamber_id"], ["id"]
    )


def downgrade():
    # Revert legislative_bodys table
    op.drop_constraint("legislative_bodys_chamber_id_fkey", "legislative_bodys", type_="foreignkey")
    op.rename_column("legislative_bodys", "chamber_id", new_column_name="role_id")

    # Revert legislators Table
    op.drop_constraint("legislators_chamber_id_fkey", "legislators", type_="foreignkey")
    op.rename_column("legislators", "chamber_id", new_column_name="role_id")

    # Revert chambers to roles
    op.execute(
        "UPDATE chambers SET name = 'Representative' WHERE name = 'House of Representatives'"
    )
    op.execute("UPDATE chambers SET name = 'Senator' WHERE name = 'Senate'")
    op.rename_table("chambers", "roles")
