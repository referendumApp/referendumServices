"""create_forgot_password_token_table

Revision ID: bde3976872b8
Revises: 43e4bac6f9b5
Create Date: 2025-03-26 11:48:20.585437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bde3976872b8'
down_revision: Union[str, None] = '43e4bac6f9b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forgot_password_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_forgot_password_tokens",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("forgot_password_token_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"]
        ),
        sa.ForeignKeyConstraint(
            ["forgot_password_token_id"],
            ["forgot_password_tokens.id"]
        ),
        sa.PrimaryKeyConstraint("user_id", "forgot_password_token_id"),
    )


def downgrade() -> None:
    # Drop junction table
    op.drop_table("user_forgot_password_tokens")

    # Drop bas table
    op.drop_table("forgot_password_tokens")
