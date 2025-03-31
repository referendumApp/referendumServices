"""fix table naming

Revision ID: 837fed54a80f
Revises: c8af5485204a
Create Date: 2024-11-11 15:28:29.635235

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "837fed54a80f"
down_revision: Union[str, None] = "c8af5485204a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint("fk_legislator_votes_vote_choice", "legislator_votes", type_="foreignkey")
    op.rename_table("vote_choice", "vote_choices")
    op.create_foreign_key(
        "fk_legislator_votes_vote_choices",
        "legislator_votes",
        "vote_choices",
        ["vote_choice_id"],
        ["id"],
    )

    op.add_column("user_votes", sa.Column("vote_choice_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_user_votes_vote_choices",
        "user_votes",
        "vote_choices",
        ["vote_choice_id"],
        ["id"],
    )
    op.drop_column("user_votes", "vote_choice")


def downgrade():
    op.add_column("user_votes", sa.Column("vote_choice", sa.String(), nullable=True))
    op.drop_constraint("fk_user_votes_vote_choices", "user_votes", type_="foreignkey")
    op.drop_column("user_votes", "vote_choice_id")

    op.drop_constraint("fk_legislator_votes_vote_choices", "legislator_votes", type_="foreignkey")
    op.rename_table("vote_choices", "vote_choice")
    op.create_foreign_key(
        "fk_legislator_votes_vote_choice",
        "legislator_votes",
        "vote_choice",
        ["vote_choice_id"],
        ["id"],
    )
