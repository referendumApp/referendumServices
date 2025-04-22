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
    # Rename tables
    op.rename_table("roles", "chambers")
    op.rename_table("states", "jurisdictions")

    # Update chamber names
    op.execute(
        "UPDATE chambers SET name = 'House of Representatives' WHERE name = 'Representative'"
    )
    op.execute("UPDATE chambers SET name = 'Senate' WHERE name = 'Senator'")

    # Add level column to legislators
    op.add_column("legislators", sa.Column("level", sa.String(), nullable=True))
    op.execute(
        "UPDATE legislators SET level = CASE WHEN state_id = 52 THEN 'Federal' ELSE 'State' END"
    )

    # Update level column with a default value (you may want to customize this)
    op.execute("UPDATE legislators SET level = 'state' WHERE level IS NULL")

    # Make level column not nullable after populating it
    op.alter_column("legislators", "level", nullable=False)

    # Rename columns
    op.alter_column("legislators", "role_id", new_column_name="chamber_id")
    op.alter_column("legislators", "state_id", new_column_name="jurisdiction_id")

    # Create new foreign key constraints
    op.create_foreign_key(
        "legislators_chamber_id_fkey", "legislators", "chambers", ["chamber_id"], ["id"]
    )
    op.create_foreign_key(
        "legislators_jurisdiction_id_fkey",
        "legislators",
        "jurisdictions",
        ["jurisdiction_id"],
        ["id"],
    )

    # Drop the representing_state_id column
    op.drop_column("legislators", "representing_state_id")


def downgrade():
    # Rename tables back
    op.rename_table("chambers", "roles")
    op.rename_table("jurisdictions", "states")

    # Restore original chamber names
    op.execute("UPDATE roles SET name = 'Representative' WHERE name = 'House of Representatives'")
    op.execute("UPDATE roles SET name = 'Senator' WHERE name = 'Senate'")

    # Add the representing_state_id column back
    op.add_column("legislators", sa.Column("representing_state_id", sa.Integer(), nullable=True))

    # Drop new foreign key constraints
    op.drop_constraint("legislators_jurisdiction_id_fkey", "legislators", type_="foreignkey")

    # Rename columns back
    op.rename_column("legislators", "chamber_id", new_column_name="role_id")
    op.rename_column("legislators", "jurisdiction_id", new_column_name="state_id")

    # Drop the level column
    op.drop_column("legislators", "level")
