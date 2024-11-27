"""update bill_sponsors

Revision ID: f47d504ae1ff
Revises: 1ba49462cc5f
Create Date: 2024-11-24 09:33:11.548760

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f47d504ae1ff"
down_revision: Union[str, None] = "1ba49462cc5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bill_sponsors", sa.Column("rank", sa.Integer(), nullable=False))
    op.add_column("bill_sponsors", sa.Column("type", sa.String(), nullable=False))

    op.drop_column("bill_sponsors", "is_primary")


def downgrade() -> None:
    op.add_column("bill_sponsors", sa.Column("is_primary", sa.Boolean(), nullable=False))

    op.drop_column("bill_sponsors", "rank")
    op.drop_column("bill_sponsors", "type")
