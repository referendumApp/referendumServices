"""add followthemoney_eid

Revision ID: 4bc80e18174b
Revises: 774fd2bbabc3
Create Date: 2025-04-01 14:52:25.645100

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4bc80e18174b"
down_revision: Union[str, None] = "774fd2bbabc3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("legislators", sa.Column("followthemoney_eid", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("legislators", "followthemoney_eid")
