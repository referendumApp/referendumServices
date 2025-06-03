"""Actor auth indexes

Revision ID: 7e50042a4e42
Revises: 5dde7444fa97
Create Date: 2025-05-29 12:24:46.133531

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e50042a4e42"
down_revision: Union[str, None] = "5dde7444fa97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("idx_actor_deleted_at_not_null", table_name="actors", schema="atproto")
    op.drop_index("idx_actor_deleted_at_null", table_name="actors", schema="atproto")
    op.drop_index("idx_content_votes_voter_id_active", table_name="content_votes", schema="atproto")
    op.drop_index("idx_actor_votes_voter_id_active", table_name="actor_votes", schema="atproto")
    op.drop_index(
        "idx_content_follows_follower_id_active", table_name="content_follows", schema="atproto"
    )
    op.drop_index(
        "idx_actor_follows_follower_id_active", table_name="actor_follows", schema="atproto"
    )

    op.create_index(
        "idx_actors_email_not_deleted",
        "actors",
        ["email", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_actors_handle_not_deleted",
        "actors",
        ["handle", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_content_votes_voter_id_active",
        "content_votes",
        ["voter_id", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_actor_votes_voter_id_active",
        "actor_votes",
        ["voter_id", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_content_follows_follower_id_active",
        "content_follows",
        ["follower_id", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_actor_follows_follower_id_active",
        "actor_follows",
        ["follower_id", "created_at"],
        schema="atproto",
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_ops={"created_at": "DESC"},
    )

    op.add_column(
        "users",
        sa.Column("did", sa.String(), nullable=False),
        schema="atproto",
    )
    op.create_index(op.f("idx_users_did"), "users", ["did"], schema="atproto", unique=True)

    op.add_column(
        "public_servants",
        sa.Column("did", sa.String(), nullable=False),
        schema="atproto",
    )
    op.create_index(
        op.f("idx_public_servants_did"), "public_servants", ["did"], schema="atproto", unique=True
    )


def downgrade() -> None:
    op.drop_column("users", "did", schema="atproto")
    op.drop_index("idx_users_did", table_name="users", schema="atproto")

    op.drop_column("public_servants", "did", schema="atproto")
    op.drop_index("idx_public_servants_did", table_name="public_servants", schema="atproto")

    op.drop_index(
        "idx_actor_follows_follower_id_active", table_name="actor_follows", schema="atproto"
    )
    op.drop_index(
        "idx_content_follows_follower_id_active", table_name="content_follows", schema="atproto"
    )
    op.drop_index("idx_actor_votes_voter_id_active", table_name="actor_votes", schema="atproto")
    op.drop_index("idx_content_votes_voter_id_active", table_name="content_votes", schema="atproto")
    op.drop_index("idx_actors_handle_not_deleted", table_name="actors", schema="atproto")
    op.drop_index("idx_actors_email_not_deleted", table_name="actors", schema="atproto")
