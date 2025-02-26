"""comment timestamps

Revision ID: fbaa14d45feb
Revises: 895ad8c038a1
Create Date: 2025-01-27 14:13:05.495914

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fbaa14d45feb"
down_revision: Union[str, None] = "895ad8c038a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "comments",
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("comments", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("comments", "updated_at")
    op.drop_column("comments", "created_at")
