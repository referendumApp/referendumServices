"""update bill_actions

Revision ID: b7f235dc8bd5
Revises: 15516b02753d
Create Date: 2024-11-08 13:45:33.327624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7f235dc8bd5"
down_revision: Union[str, None] = "15516b02753d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the type column using BillActionType enum
    op.drop_column("bill_actions", "type")

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS billactiontype")

    # Add new columns
    op.add_column("bill_actions", sa.Column("description", sa.String(), nullable=True))
    op.add_column("bill_actions", sa.Column("legislative_body_id", sa.Integer(), nullable=False))

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_bill_actions_legislative_body",
        "bill_actions",
        "legislative_bodys",
        ["legislative_body_id"],
        ["id"],
    )


def downgrade():
    # Create the enum type
    op.execute("CREATE TYPE billactiontype AS ENUM ('FLOOR_VOTE', 'COMMITTEE_VOTE')")

    # Drop the new columns
    op.drop_constraint("fk_bill_actions_legislative_body", "bill_actions", type_="foreignkey")
    op.drop_column("bill_actions", "legislative_body_id")
    op.drop_column("bill_actions", "description")

    # Add back the type column
    op.add_column(
        "bill_actions",
        sa.Column(
            "type", sa.Enum("FLOOR_VOTE", "COMMITTEE_VOTE", name="billactiontype"), nullable=False
        ),
    )
