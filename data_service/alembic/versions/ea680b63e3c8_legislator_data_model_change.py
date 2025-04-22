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

    # Add legislatures table
    op.create_table(
        "legislatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["state_id"],
            ["states.id"],
        ),
    )

    # Update sessions table
    op.drop_column("sessions", "state_id")
    op.add_column("sessions", sa.Column("legislature_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_legislature_id", "sessions", "legislatures", ["legislature_id"], ["id"]
    )

    # Update legislators table
    op.drop_column("legislators", "role_id")

    op.drop_column("legislators", "state_id")

    op.add_column("legislators", sa.Column("legislative_body_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_legislators_legislative_body_id",
        "legislators",
        "legislative_bodys",
        ["legislative_body_id"],
        ["id"],
    )

    # Update legislative_bodys table
    op.alter_column("legislative_bodys", "role_id", new_column_name="chamber_id")
    op.create_foreign_key(
        "fk_legislative_bodys_chamber_id", "legislative_bodys", "chambers", ["chamber_id"], ["id"]
    )

    op.drop_constraint("legislative_bodys_state_id_fkey", "legislative_bodys", type_="foreignkey")
    op.drop_column("legislative_bodys", "state_id")

    op.add_column("legislative_bodys", sa.Column("legislature_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_legislative_bodys_legislature_id",
        "legislative_bodys",
        "legislatures",
        ["legislature_id"],
        ["id"],
    )


def downgrade():
    # Revert legislative_bodys table
    op.drop_constraint(
        "fk_legislative_bodys_legislature_id", "legislative_bodys", type_="foreignkey"
    )
    op.drop_column("legislative_bodys", "legislature_id")
    op.add_column("legislative_bodys", "state_id")
    op.create_foreign_key(
        "legislative_bodys_state_id_fkey",
        "legislative_bodys",
        "states",
        ["state_id"],
        ["id"],
    )

    op.drop_constraint("fk_legislative_bodys_chamber_id", "legislative_bodys", type_="foreignkey")
    op.rename_column("legislative_bodys", "chamber_id", new_column_name="role_id")

    # Revert legislators Table
    op.drop_constraint("legislators_chamber_id_fkey", "legislators", type_="foreignkey")
    op.rename_column("legislators", "chamber_id", new_column_name="role_id")
    op.add_column("legislators", sa.Column("role_id", sa.Integer(), nullable=True))

    # Revert sessions table
    op.drop_constraint("fk_sessions_legislature_id", "sessions", type_="foreignkey")
    op.drop_column("sessions", "legislature_id")
    op.add_column("sessions", sa.Column("state_id", sa.Integer(), nullable=True))

    # Remove legislatures table
    op.drop_table("legislatures")

    # Revert chambers to roles
    op.execute(
        "UPDATE chambers SET name = 'Representative' WHERE name = 'House of Representatives'"
    )
    op.execute("UPDATE chambers SET name = 'Senator' WHERE name = 'Senate'")
    op.rename_table("chambers", "roles")
