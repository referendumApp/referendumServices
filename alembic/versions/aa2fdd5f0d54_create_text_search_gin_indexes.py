"""Create text search gin indexes

Revision ID: aa2fdd5f0d54
Revises: 5fe048772214
Create Date: 2025-01-08 16:02:25.216252

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa2fdd5f0d54"
down_revision: Union[str, None] = "296fffa291c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_legislators_name", "legislators")
    op.drop_index("ix_legislator_name_district", "legislators")

    op.execute(
        """
        CREATE INDEX ix_legislator_name_search ON legislators 
        USING gin(to_tsvector('english', name));
        """
    )
    op.execute(
        "CREATE INDEX ix_bill_identifier_search ON bills USING gin(to_tsvector('simple', COALESCE(identifier, '')));"
    )
    op.execute(
        "CREATE INDEX ix_bill_title_search ON bills USING gin(to_tsvector('english', COALESCE(title, '')));"
    )


def downgrade() -> None:
    op.create_index(op.f("ix_legislators_name"), "legislators", ["name"], unique=False)
    op.create_index(
        op.f("ix_legislator_name_district"),
        "legislators",
        ["name", "district"],
        unique=True,
    )

    op.drop_index("ix_legislator_name_search", "legislators")
    op.drop_index("ix_bill_identifier_search", "bills")
    op.drop_index("ix_bill_title_search", "bills")
