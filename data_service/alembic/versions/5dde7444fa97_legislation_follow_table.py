"""Legislation Follow Table

Revision ID: 5dde7444fa97
Revises: c2ba66e883d7
Create Date: 2025-05-23 12:39:53.292905

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5dde7444fa97"
down_revision: Union[str, None] = "c2ba66e883d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("actor", "actors", schema="atproto")

    op.create_table(
        "content_votes",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("voter_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_choice",
            sa.Enum("YAY", "NAY", name="votechoice", create_type=False),
            nullable=False,
        ),
        sa.Column("subject_cid", sa.LargeBinary(), nullable=False),
        sa.Column("subject_rkey", sa.String(), nullable=False),
        sa.Column("subject_collection", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["voter_id"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("voter_id", "subject_rkey"),
        schema="atproto",
    )
    op.create_index(
        "idx_content_votes_voter_id_active",
        "content_votes",
        ["voter_id", "deleted_at", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.execute(
        """
        CREATE TRIGGER refresh_content_votes_updated_at
        BEFORE UPDATE ON atproto.content_votes
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.create_table(
        "actor_votes",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("voter_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_choice",
            sa.Enum("YAY", "NAY", name="votechoice", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["voter_id"], ["atproto.actors.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("voter_id", "target_id"),
        schema="atproto",
    )
    op.create_index(
        "idx_actor_votes_voter_id_active",
        "actor_votes",
        ["voter_id", "deleted_at", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.execute(
        """
        CREATE TRIGGER refresh_actor_votes_updated_at
        BEFORE UPDATE ON atproto.actor_votes
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.create_table(
        "content_follows",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("collection", sa.String(), nullable=False),
        sa.Column("subject_cid", sa.LargeBinary(), nullable=False),
        sa.Column("subject_rkey", sa.String(), nullable=False),
        sa.Column("subject_collection", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["follower_id"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("follower_id", "rkey"),
        schema="atproto",
    )
    op.create_index(
        "idx_content_follows_follower_id_active",
        "content_follows",
        ["follower_id", "deleted_at", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.execute(
        """
        CREATE TRIGGER refresh_content_follows_updated_at
        BEFORE UPDATE ON atproto.content_follows
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.rename_table("endorsement_record", "endorsements", schema="atproto")
    op.alter_column(
        "endorsements",
        "endorser",
        new_column_name="endorser_id",
        schema="atproto",
    )

    op.execute(
        "DROP TRIGGER IF EXISTS refresh_user_follow_record_updated_at ON atproto.actor_follow_record"
    )
    op.drop_table("actor_follow_record", schema="atproto")
    op.create_table(
        "actor_follows",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("collection", sa.String(), nullable=False),
        sa.Column("target_collection", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["atproto.actors.id"]),
        sa.ForeignKeyConstraint(["follower_id"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("follower_id", "target_id"),
        schema="atproto",
    )
    op.create_index(
        "idx_actor_follows_target_collection",
        "actor_follows",
        ["target_collection"],
        schema="atproto",
    )
    op.create_index(
        "idx_actor_follows_follower_id_active",
        "actor_follows",
        ["follower_id", "deleted_at", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.execute(
        """
        CREATE TRIGGER refresh_actor_follows_updated_at
        BEFORE UPDATE ON atproto.actor_follows
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.rename_table("user", "users", schema="atproto")
    op.alter_column(
        "users",
        "posts",
        new_column_name="comments",
        schema="atproto",
    )
    op.add_column(
        "users",
        sa.Column("votes", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        schema="atproto",
    )
    op.create_foreign_key(
        "fk_users_aid",
        "users",
        "actors",
        ["aid"],
        ["id"],
        source_schema="atproto",
        referent_schema="atproto",
    )

    op.create_table(
        "public_servants",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("aid", sa.Integer(), nullable=False, unique=True),
        sa.Column("followers", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("yay_count", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("nay_count", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("pds_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["pds_id"], ["atproto.pds.id"]),
        sa.ForeignKeyConstraint(["aid"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.execute(
        """
        CREATE TRIGGER refresh_public_servants_updated_at
        BEFORE UPDATE ON atproto.public_servants
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )

    op.create_table(
        "policy_content",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("collection", sa.String(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("cid", sa.String(), nullable=False),
        sa.Column("yay_count", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("nay_count", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("followers", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("views", sa.BigInteger(), nullable=True, server_default=sa.text("0")),
        sa.Column("deleted", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["author_id"], ["atproto.actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_index(
        "idx_policy_content_collection_rkey",
        "policy_content",
        ["collection", "rkey"],
        schema="atproto",
        unique=True,
    )
    op.execute(
        """
        CREATE TRIGGER refresh_policy_content_updated_at
        BEFORE UPDATE ON atproto.policy_content
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS refresh_policy_content_updated_at ON atproto.policy_content")
    op.drop_table("policy_content", schema="atproto")

    op.execute(
        "DROP TRIGGER IF EXISTS refresh_public_servants_updated_at ON atproto.public_servants"
    )
    op.drop_table("public_servants", schema="atproto")

    op.alter_column(
        "users",
        "comments",
        new_column_name="posts",
        schema="atproto",
    )
    op.drop_column("users", "votes", schema="atproto")
    op.drop_constraint(
        "fk_users_aid",
        "users",
        type_="foreignkey",
        schema="atproto",
    )
    op.rename_table("users", "user", schema="atproto")

    op.execute(
        "DROP TRIGGER IF EXISTS refresh_user_follow_record_updated_at ON atproto.actor_follows"
    )
    op.drop_table("actor_follows", schema="atproto")
    op.create_table(
        "actor_follow_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("follower", sa.Integer(), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.execute(
        "DROP TRIGGER IF EXISTS refresh_content_follows_updated_at ON atproto.content_follows"
    )

    op.rename_table("endorsements", "endorsement_record", schema="atproto")

    op.execute(
        "DROP TRIGGER IF EXISTS refresh_content_follows_updated_at ON atproto.content_follows"
    )
    op.drop_table("content_follows", schema="atproto")

    op.execute("DROP TRIGGER IF EXISTS refresh_actor_votes_updated_at ON atproto.actor_votes")
    op.drop_table("actor_vote", schema="atproto")

    op.execute("DROP TRIGGER IF EXISTS refresh_content_votes_updated_at ON atproto.content_votes")
    op.drop_table("content_votes", schema="atproto")

    op.execute("DROP TYPE IF EXISTS votechoice")

    op.rename_table("actors", "actor", schema="atproto")
