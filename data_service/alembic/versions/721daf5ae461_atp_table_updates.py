"""ATP table updates

Revision ID: 721daf5ae461
Revises: 4bc80e18174b
Create Date: 2025-04-06 19:18:36.243684

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "721daf5ae461"
down_revision: Union[str, None] = "4bc80e18174b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS refresh_citizen_updated_at ON atproto.citizen")
    op.rename_table("citizen", "person", schema="atproto")
    op.alter_column("person", "following", server_default=sa.text("0"), schema="atproto")
    op.alter_column("person", "followers", server_default=sa.text("0"), schema="atproto")
    op.alter_column("person", "posts", server_default=sa.text("0"), schema="atproto")
    op.execute(
        """
        CREATE TRIGGER refresh_person_updated_at
        BEFORE UPDATE ON atproto.person
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.drop_column("user_follow_record", "cid", schema="atproto")
    op.add_column(
        "user_follow_record",
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        schema="atproto",
    )

    op.drop_column("user", "name", schema="atproto")
    op.alter_column("user", "did", schema="atproto", nullable=False)

    op.drop_column("endorsement_record", "cid", schema="atproto")
    op.add_column(
        "endorsement_record",
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        schema="atproto",
    )
    op.drop_column("endorsement_record", "vote_choice_id", schema="atproto")
    op.alter_column(
        "endorsement_record", "voter", new_column_name="endorser", schema="atproto", nullable=False
    )

    op.drop_column("activity_post", "cid", schema="atproto")
    op.add_column(
        "activity_post",
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        schema="atproto",
    )
    op.alter_column(
        "activity_post",
        "up_count",
        new_column_name="endorsements",
        schema="atproto",
        nullable=False,
    )


def downgrade() -> None:
    op.add_column(
        "user",
        sa.Column("name", sa.String(), nullable=True),
        schema="atproto",
    )
    op.alter_column("user", "did", schema="atproto", nullable=True)

    op.add_column(
        "endorsement_record",
        sa.Column("vote_choice_id", sa.Integer(), nullable=False),
        schema="atproto",
    )
    op.alter_column(
        "endorsement_record", "endorser", new_column_name="voter", schema="atproto", nullable=False
    )
    op.drop_column("endorsement_record", "cid", schema="atproto")
    op.add_column(
        "endorsement_record",
        sa.Column("cid", sa.String(), nullable=False),
        schema="atproto",
    )

    op.alter_column(
        "activity_post",
        "up_count",
        new_column_name="endorsements",
        schema="atproto",
        nullable=False,
    )
    op.drop_column("activity_post", "cid", schema="atproto")
    op.add_column(
        "activity_post",
        sa.Column("cid", sa.String(), nullable=False),
        schema="atproto",
    )

    op.drop_column("user_follow_record", "cid", schema="atproto")
    op.add_column(
        "user_follow_record",
        sa.Column("cid", sa.String(), nullable=False),
        schema="atproto",
    )

    op.execute("DROP TRIGGER IF EXISTS refresh_person_updated_at ON atproto.person")
    op.rename_table("person", "citizen", schema="atproto")
    op.execute(
        """
        CREATE TRIGGER refresh_citizen_updated_at
        BEFORE UPDATE ON atproto.citizen
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.alter_column("citizen", "following", server_default=None, schema="atproto")
    op.alter_column("citizen", "followers", server_default=None, schema="atproto")
    op.alter_column("citizen", "posts", server_default=None, schema="atproto")
