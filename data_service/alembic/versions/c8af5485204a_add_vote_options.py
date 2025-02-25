"""add vote options

Revision ID: c8af5485204a
Revises: b7f235dc8bd5
Create Date: 2024-11-11 13:41:28.005354

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8af5485204a"
down_revision: Union[str, None] = "b7f235dc8bd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "vote_choice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column("legislator_votes", sa.Column("vote_choice_id", sa.Integer(), nullable=False))

    op.create_foreign_key(
        "fk_legislator_votes_vote_choice",
        "legislator_votes",
        "vote_choice",
        ["vote_choice_id"],
        ["id"],
    )
    op.drop_column("legislator_votes", "vote_choice")


def downgrade():
    op.add_column("legislator_votes", sa.Column("vote_choice", sa.String(), nullable=True))

    op.drop_constraint("fk_legislator_votes_vote_choice", "legislator_votes", type_="foreignkey")

    op.drop_column("legislator_votes", "vote_choice_id")

    op.drop_table("vote_choice")
