"""add pds data to legislators

Revision ID: 3adfde5f33f0
Revises: 5dde7444fa97
Create Date: 2025-06-02 07:31:05.489956

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3adfde5f33f0"
down_revision: Union[str, None] = "5dde7444fa97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "legislators",
        "uid",
        new_column_name="aid",
    )
    op.add_column("legislators", sa.Column("pds_handle", sa.String(length=255), nullable=True))
    op.add_column("legislators", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("legislators", sa.Column("pds_synced_at", sa.DateTime(), nullable=True))

    op.create_index("ix_legislators_pds_synced_at", "legislators", ["pds_synced_at"])
    op.create_index("ix_legislators_updated_at", "legislators", ["updated_at"])
    op.create_index("ix_legislators_did", "legislators", ["did"])
    op.create_index("ix_legislators_aid", "legislators", ["aid"])

    # Create trigger for updated_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )
    op.execute(
        """
        CREATE TRIGGER update_legislators_updated_at
            BEFORE UPDATE ON legislators
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_legislators_updated_at ON legislators;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    op.drop_index("ix_legislators_aid", table_name="legislators")
    op.drop_index("ix_legislators_did", table_name="legislators")
    op.drop_index("ix_legislators_updated_at", table_name="legislators")
    op.drop_index("ix_legislators_pds_synced_at", table_name="legislators")

    op.drop_column("legislators", "pds_synced_at")
    op.drop_column("legislators", "updated_at")
    op.drop_column("legislators", "pds_handle")
    op.alter_column(
        "legislators",
        "aid",
        new_column_name="uid",
    )
