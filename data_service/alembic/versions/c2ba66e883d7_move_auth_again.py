"""move_auth_again

Revision ID: c2ba66e883d7
Revises: 01793d9ea433
Create Date: 2025-05-21 15:42:53.758097

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "c2ba66e883d7"
down_revision: Union[str, None] = "01793d9ea433"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("actor", "display_name", schema="atproto")
    op.drop_column("actor", "settings", schema="atproto")

    op.drop_column("user", "did", schema="atproto")
    op.add_column("user", sa.Column("display_name", sa.String), schema="atproto")
    op.add_column("user", sa.Column("settings", JSONB, nullable=True, default={}), schema="atproto")

    op.drop_column("legislator", "did", schema="atproto")
    op.add_column("legislator", sa.Column("display_name", sa.String), schema="atproto")


def downgrade() -> None:
    op.drop_column("legislator", "display_name", schema="atproto")
    op.add_column("legislator", sa.Column("did", sa.String), schema="atproto")

    op.drop_column("user", "settings", schema="atproto")
    op.drop_column("user", "display_name", schema="atproto")
    op.add_column("user", sa.Column("did", sa.String), schema="atproto")

    op.add_column(
        "actor", sa.Column("settings", JSONB, nullable=True, default={}), schema="atproto"
    )
    op.add_column("actor", sa.Column("display_name", sa.String), schema="atproto")
