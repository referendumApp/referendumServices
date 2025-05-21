"""actor authentication

Revision ID: 01793d9ea433
Revises: 6ce6213e39f6
Create Date: 2025-05-20 14:27:07.473099

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "01793d9ea433"
down_revision: Union[str, None] = "6ce6213e39f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user", "email", schema="atproto")
    op.drop_column("user", "hashed_password", schema="atproto")

    op.add_column("actor", sa.Column("email", sa.String(), nullable=True), schema="atproto")
    op.add_column(
        "actor", sa.Column("hashed_password", sa.String(), nullable=True), schema="atproto"
    )


def downgrade() -> None:
    op.drop_column("actor", "email", schema="atproto")
    op.drop_column("actor", "hashed_password", schema="atproto")

    op.add_column("user", sa.Column("email", sa.String(), nullable=True), schema="atproto")
    op.add_column(
        "user", sa.Column("hashed_password", sa.String(), nullable=True), schema="atproto"
    )
