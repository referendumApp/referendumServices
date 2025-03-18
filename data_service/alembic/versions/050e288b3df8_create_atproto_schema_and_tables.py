"""Create atproto schema and tables

Revision ID: 050e288b3df8
Revises: fbaa14d45feb
Create Date: 2025-03-08 11:52:17.228780

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "050e288b3df8"
down_revision: Union[str, None] = "fbaa14d45feb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS atproto;")
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("handle", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("recovery_key", sa.String(), nullable=True),
        sa.Column("did", sa.String(), nullable=True),
        sa.Column("pds_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], schema="atproto", unique=True)
    op.create_index(op.f("ix_user_handle"), "user", ["handle"], schema="atproto", unique=True)
    op.create_index(op.f("ix_user_did"), "user", ["did"], schema="atproto", unique=True)

    op.create_table(
        "pds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("host", sa.String(), nullable=False),
        sa.Column("did", sa.String(), nullable=False),
        sa.Column("ssl", sa.Boolean(), nullable=False),
        sa.Column("cursor", sa.BigInteger(), nullable=False),
        sa.Column("registered", sa.Boolean(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("rate_limit", sa.Float(), nullable=False),
        sa.Column("crawl_rate_limit", sa.Float(), nullable=False),
        sa.Column("repo_count", sa.BigInteger(), nullable=False),
        sa.Column("repo_limit", sa.BigInteger(), nullable=False),
        sa.Column("hourly_event_limit", sa.BigInteger(), nullable=False),
        sa.Column("daily_event_limit", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["did"], ["atproto.user.did"], name="fk_pds_did"),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_foreign_key(
        "fk_user_pds",
        "user",
        "pds",
        ["pds_id"],
        ["id"],
        source_schema="atproto",
        referent_schema="atproto",
    )

    op.create_table(
        "peering",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("host", sa.String(), nullable=False),
        sa.Column("did", sa.String(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["did"], ["atproto.user.did"], name="fk_peering_did"),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )

    op.create_table(
        "citizen",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.Column("handle", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("did", sa.String(), nullable=False),
        sa.Column("following", sa.BigInteger(), nullable=True),
        sa.Column("followers", sa.BigInteger(), nullable=True),
        sa.Column("posts", sa.BigInteger(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("pds_id", sa.Integer(), nullable=True),
        sa.Column("valid_handle", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("settings", JSONB, nullable=True, default={}),
        sa.ForeignKeyConstraint(["did"], ["atproto.user.did"], name="fk_citizen_did"),
        sa.ForeignKeyConstraint(["pds_id"], ["atproto.pds.id"], name="fk_citizen_pds_id"),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_index(op.f("ix_citizen_uid"), "citizen", ["uid"], schema="atproto", unique=True)
    op.create_index(op.f("ix_citizen_did"), "citizen", ["did"], schema="atproto", unique=True)
    op.create_index(
        op.f("ix_citizen_handle"), "citizen", ["handle"], schema="atproto", unique=False
    )

    op.create_table(
        "activity_post",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("author", sa.Integer(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("cid", sa.String(), nullable=False),
        sa.Column("up_count", sa.BigInteger(), nullable=False),
        sa.Column("reply_count", sa.BigInteger(), nullable=False),
        sa.Column("reply_to", sa.Integer(), nullable=True),
        sa.Column("missing", sa.Boolean(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reply_to"], ["atproto.activity_post.id"], name="fk_activity_post_reply_to"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )
    op.create_index(
        "idx_activity_post_rkey", "activity_post", ["author", "rkey"], schema="atproto", unique=True
    )

    op.create_table(
        "endorsement_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("vote_choice_id", sa.Integer(), nullable=False),
        sa.Column("voter", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.String(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("cid", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"], ["atproto.activity_post.id"], name="fk_endorsement_post_id"
        ),
        sa.ForeignKeyConstraint(
            ["vote_choice_id"], ["public.vote_choices.id"], name="fk_endorsement_vote_choice_id"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )

    op.create_table(
        "user_follow_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("follower", sa.Integer(), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("rkey", sa.String(), nullable=False),
        sa.Column("cid", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="atproto",
    )


def downgrade():
    # Drop tables in reverse order to avoid foreign key constraints
    op.drop_table("user_follow_record")
    op.drop_table("endorsement_record")
    op.drop_table("activity_post")
    op.drop_table("citizen")
    op.drop_column("user", "pds_id")
    op.drop_table("pds")
    op.drop_table("user")

    op.execute("DROP SCHEMA IF EXISTS atproto;")
