"""create status table

Revision ID: 5fe048772214
Revises: beba4a1ac5e2
Create Date: 2024-12-18 11:19:53.658340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5fe048772214"
down_revision: Union[str, None] = "beba4a1ac5e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_MAPPING = {
    0: "Prefiled",
    1: "Introduced",
    2: "Engrossed",
    3: "Enrolled",
    4: "Passed",
    5: "Vetoed",
    6: "Failed",
    7: "Override",
    8: "Chaptered",
    9: "Refer",
    10: "Report Pass",
    11: "Report DNP",
    12: "Draft",
}


def upgrade() -> None:
    op.create_table(
        "statuses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.bulk_insert(
        sa.table("statuses", sa.Column("id", sa.Integer()), sa.Column("name", sa.String())),
        [{"id": k, "name": v} for k, v in STATUS_MAPPING.items()],
    )

    op.add_column("bills", sa.Column("status_id", sa.Integer(), nullable=True))

    # Map existing status to ID
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE bills 
            SET status_id = statuses.id 
            FROM statuses 
            WHERE bills.status = statuses.name
        """
        )
    )

    # Finalize new column
    op.alter_column("bills", "status_id", nullable=False)
    op.create_index("ix_bills_status_id", "bills", ["status_id"])
    op.create_foreign_key(
        "fk_bills_status_id_statuses",
        "bills",
        "statuses",
        ["status_id"],
        ["id"],
    )

    # Drop the status column
    op.drop_column("bills", "status")


def downgrade() -> None:
    # Add back the status column
    op.add_column("bills", sa.Column("status", sa.String(), nullable=True))

    # Migrate data back
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
        UPDATE bills 
        SET status = statuses.name 
        FROM statuses 
        WHERE bills.status_id = statuses.id
        """
        )
    )

    # Make status not nullable after population
    op.alter_column("bills", "status", nullable=False)

    # Drop foreign key constraint and status_id column
    op.drop_constraint("fk_bills_status_id_statuses", "bills", type_="foreignkey")
    op.drop_index("ix_bills_status_id", "bills")
    op.drop_column("bills", "status_id")

    # Drop statuses table and its index
    op.drop_index("ix_statuses_name", "statuses")
    op.drop_table("statuses")
