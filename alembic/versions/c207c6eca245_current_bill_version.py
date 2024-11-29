"""current bill version

Revision ID: c207c6eca245
Revises: 0c742e81f876
Create Date: 2024-11-29 09:36:45.386613
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c207c6eca245"
down_revision: Union[str, None] = "0c742e81f876"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add current_version_id to bills table
    op.add_column("bills", sa.Column("current_version_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_bills_current_version",
        "bills",
        "bill_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add date column to bill_versions with default value
    op.add_column(
        "bill_versions",
        sa.Column("date", sa.Date(), nullable=False, server_default=sa.text("'1970-01-01'")),
    )

    # Create trigger function
    op.execute(
        """
        CREATE FUNCTION update_bill_current_version() RETURNS trigger AS $$
        BEGIN
          IF (TG_OP = 'DELETE') THEN
            -- On delete, set current_version to the next most recent version
            UPDATE bills 
            SET current_version_id = (
              SELECT id FROM bill_versions 
              WHERE bill_id = OLD.bill_id 
              AND id != OLD.id
              ORDER BY date DESC LIMIT 1
            )
            WHERE id = OLD.bill_id;
            RETURN OLD;
          ELSE
            -- On insert/update, set to most recent version
            UPDATE bills 
            SET current_version_id = (
              SELECT id FROM bill_versions 
              WHERE bill_id = NEW.bill_id 
              ORDER BY date DESC LIMIT 1
            )
            WHERE id = NEW.bill_id;
            RETURN NEW;
          END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Create trigger
    op.execute(
        """
        CREATE TRIGGER bill_version_changes
        AFTER INSERT OR UPDATE OR DELETE ON bill_versions
        FOR EACH ROW
        EXECUTE FUNCTION update_bill_current_version();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS bill_version_changes ON bill_versions")
    op.execute("DROP FUNCTION IF EXISTS update_bill_current_version")

    op.drop_constraint("fk_bills_current_version", "bills", type_="foreignkey")

    op.drop_column("bills", "current_version_id")
    op.drop_column("bill_versions", "date")
