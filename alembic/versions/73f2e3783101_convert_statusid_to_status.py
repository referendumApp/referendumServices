"""convert statusId to status

Revision ID: 73f2e3783101
Revises: 837fed54a80f
Create Date: 2024-11-21 10:14:16.796041

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "73f2e3783101"
down_revision: Union[str, None] = "837fed54a80f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Status mapping from config
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
    # Add new status column
    op.add_column("bills", sa.Column("status", sa.String(), nullable=True))

    # Update data using the mapping
    for status_id, status_name in STATUS_MAPPING.items():
        op.execute(
            f"""
            UPDATE bills 
            SET status = '{status_name}'
            WHERE status_id = {status_id}
            """
        )

    # Drop the old status_id column
    op.drop_column("bills", "status_id")


def downgrade() -> None:
    # Add back status_id column
    op.add_column("bills", sa.Column("status_id", sa.Integer(), nullable=True))

    # Reverse map the data
    for status_id, status_name in STATUS_MAPPING.items():
        op.execute(
            f"""
            UPDATE bills 
            SET status_id = {status_id}
            WHERE status = '{status_name}'
            """
        )

    # Drop the new status column
    op.drop_column("bills", "status")
