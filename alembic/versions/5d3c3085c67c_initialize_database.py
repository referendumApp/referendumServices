"""Initialize database

Revision ID: 5d3c3085c67c
Revises:
Create Date: 2024-10-01 09:18:59.007473

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d3c3085c67c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create base tables
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topics_name"), "topics", ["name"], unique=True)

    op.create_table(
        "partys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create tables with foreign key dependencies
    op.create_table(
        "legislative_bodys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["state_id"],
            ["states.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
    )

    op.create_table(
        "committees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("legislative_body_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["legislative_body_id"],
            ["legislative_bodys.id"],
        ),
    )

    op.create_table(
        "bills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("legiscan_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("state_id", sa.Integer(), nullable=True),
        sa.Column("legislative_body_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("briefing", sa.String(), nullable=True),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.Column("status_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["state_id"],
            ["states.id"],
        ),
        sa.ForeignKeyConstraint(
            ["legislative_body_id"],
            ["legislative_bodys.id"],
        ),
    )
    op.create_index(op.f("ix_bills_legiscan_id"), "bills", ["legiscan_id"], unique=True)
    op.create_index(op.f("ix_bills_state_id"), "bills", ["state_id"], unique=False)
    op.create_index(
        op.f("ix_bills_legislative_body_id"),
        "bills",
        ["legislative_body_id"],
        unique=False,
    )
    op.create_index(op.f("ix_bills_session_id"), "bills", ["session_id"], unique=False)

    op.create_table(
        "legislators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("legiscan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("party_id", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("facebook", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("twitter", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["partys.id"],
        ),
    )
    op.create_index(op.f("ix_legislators_name"), "legislators", ["name"], unique=False)
    op.create_index(op.f("ix_legiscan_id"), "legislators", ["legiscan_id"], unique=True)
    op.create_index(
        op.f("ix_legislator_name_district"),
        "legislators",
        ["name", "district"],
        unique=True,
    )

    # Create junction tables
    op.create_table(
        "bill_versions",
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("bill_id", "version"),
        sa.ForeignKeyConstraint(
            ["bill_id"],
            ["bills.id"],
        ),
    )

    op.create_table(
        "user_topic_follows",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )

    op.create_table(
        "user_bill_follows",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bill_id"],
            ["bills.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "bill_id"),
    )

    op.create_table(
        "committee_membership",
        sa.Column("committee_id", sa.Integer(), nullable=False),
        sa.Column("legislator_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["committee_id"],
            ["committees.id"],
        ),
        sa.ForeignKeyConstraint(
            ["legislator_id"],
            ["legislators.id"],
        ),
        sa.PrimaryKeyConstraint("committee_id", "legislator_id"),
    )

    op.create_table(
        "bill_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("FLOOR_VOTE", "COMMITTEE_VOTE", name="billactiontype", create_type=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
    )

    op.create_table(
        "bill_sponsors",
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("legislator_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(
            ["bill_id"],
            ["bills.id"],
        ),
        sa.ForeignKeyConstraint(
            ["legislator_id"],
            ["legislators.id"],
        ),
        sa.PrimaryKeyConstraint("bill_id", "legislator_id"),
    )

    op.create_table(
        "bill_topics",
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bill_id"],
            ["bills.id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("bill_id", "topic_id"),
    )

    op.create_table(
        "user_votes",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_choice",
            sa.Enum("YES", "NO", name="votechoice", create_type=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "bill_id"),
    )

    op.create_table(
        "legislator_votes",
        sa.Column("legislator_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("bill_action_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_choice",
            sa.Enum("YES", "NO", name="votechoice", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
        sa.ForeignKeyConstraint(["bill_action_id"], ["bill_actions.id"]),
        sa.ForeignKeyConstraint(["legislator_id"], ["legislators.id"]),
        sa.PrimaryKeyConstraint("legislator_id", "bill_action_id"),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("comment", sa.String, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "user_comment_likes",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "comment_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"]),
    )

    op.create_table(
        "user_legislator_follows",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("legislator_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["legislator_id"],
            ["legislators.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "legislator_id"),
    )


def downgrade():
    # Drop junction tables
    op.drop_table("user_legislator_follows")
    op.drop_table("user_comment_likes")
    op.drop_table("comments")
    op.drop_table("legislator_votes")
    op.drop_table("user_votes")
    op.drop_table("bill_topics")
    op.drop_table("bill_sponsors")
    op.drop_table("bill_actions")
    op.drop_table("committee_membership")
    op.drop_table("user_bill_follows")
    op.drop_table("user_topic_follows")
    op.drop_table("bill_versions")

    # Drop tables with foreign key dependencies
    op.drop_index(op.f("ix_legislator_name_district"), table_name="legislators")
    op.drop_index(op.f("ix_legiscan_id"), table_name="legislators")
    op.drop_index(op.f("ix_legislators_name"), table_name="legislators")
    op.drop_table("legislators")

    op.drop_index(op.f("ix_bills_session_id"), table_name="bills")
    op.drop_index(op.f("ix_bills_legislative_body_id"), table_name="bills")
    op.drop_index(op.f("ix_bills_state_id"), table_name="bills")
    op.drop_index(op.f("ix_bills_legiscan_id"), table_name="bills")
    op.drop_table("bills")

    op.drop_table("committees")
    op.drop_table("legislative_bodys")

    # Drop base tables
    op.drop_table("roles")
    op.drop_table("states")
    op.drop_table("partys")
    op.drop_index(op.f("ix_topics_name"), table_name="topics")
    op.drop_table("topics")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS billactiontype")
    op.execute("DROP TYPE IF EXISTS votechoice")
