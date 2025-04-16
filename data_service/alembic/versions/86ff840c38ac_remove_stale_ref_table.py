"""Remove stale ref table

Revision ID: 86ff840c38ac
Revises: 297f99638c3f
Create Date: 2025-04-12 11:43:52.457737

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "86ff840c38ac"
down_revision: Union[str, None] = "297f99638c3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("stale_refs", schema="carstore")


def downgrade() -> None:
    op.create_table(
        "stale_refs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=True),
        sa.Column("cids", sa.LargeBinary(), nullable=True),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="carstore",
    )

    op.create_index("idx_stale_refs_uid", "stale_refs", ["uid"], schema="carstore", unique=False)
    op.create_index("idx_stale_refs_cid", "stale_refs", ["cid"], schema="carstore", unique=False)
