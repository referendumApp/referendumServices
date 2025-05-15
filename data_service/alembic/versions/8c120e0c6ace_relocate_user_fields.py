"""relocate user fields

Revision ID: 8c120e0c6ace
Revises: 23eef83c79f6
Create Date: 2025-05-14 10:20:22.268806

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c120e0c6ace"
down_revision: Union[str, None] = "23eef83c79f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("actor", "email", schema="atproto")
    op.drop_column("actor", "hashed_password", schema="atproto")

    op.drop_column("user", "display_name", schema="atproto")
    op.drop_column("user", "handle", schema="atproto")

    op.add_column("actor", sa.Column("display_name", sa.String(), nullable=True), schema="atproto")

    op.add_column("user", sa.Column("email", sa.String(), nullable=True), schema="atproto")
    op.add_column(
        "user", sa.Column("hashed_password", sa.String(), nullable=True), schema="atproto"
    )


def downgrade() -> None:
    op.drop_column("user", "email", schema="atproto")
    op.drop_column("user", "hashed_password", schema="atproto")

    op.drop_column("actor", "display_name", schema="atproto")

    op.add_column("user", sa.Column("handle", sa.String(), nullable=True), schema="atproto")
    op.add_column("user", sa.Column("display_name", sa.String(), nullable=True), schema="atproto")

    op.add_column("actor", sa.Column("email", sa.String(), nullable=True), schema="atproto")
    op.add_column(
        "actor", sa.Column("hashed_password", sa.String(), nullable=True), schema="atproto"
    )
