"""add user settings

Revision ID: 296fffa291c7
Revises: 5fe048772214
Create Date: 2024-12-19 07:56:55.387200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "296fffa291c7"
down_revision: Union[str, None] = "5fe048772214"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("settings", JSONB, nullable=False, default={}))


def downgrade() -> None:
    op.drop_column("users", "settings")
