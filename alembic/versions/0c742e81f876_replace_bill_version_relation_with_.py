"""replace bill_version relation with string

Revision ID: 0c742e81f876
Revises: f47d504ae1ff
Create Date: 2024-11-24 13:32:43.472517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0c742e81f876"
down_revision: Union[str, None] = "f47d504ae1ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bill_versions", sa.Column("version_type", sa.String(), nullable=True))
    op.drop_column("bill_versions", "bill_version_type_id")


def downgrade() -> None:
    op.drop_column("bill_versions", "version_type")
    op.add_column("bill_versions", sa.Column("bill_version_type_id", sa.Integer(), nullable=True))
