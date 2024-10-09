"""Initialize database

Revision ID: 5d3c3085c67c
Revises:
Create Date: 2024-10-01 09:18:59.007473

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "5d3c3085c67c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Create topics table
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topics_name"), "topics", ["name"], unique=True)

    op.create_table(
        "partys",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "legislative_bodys",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
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

    # Create bills table
    op.create_table(
        "bills",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
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

    # Create legislators table
    op.create_table(
        "legislators",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("facebook", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("twitter", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legislators_name"), "legislators", ["name"], unique=False)
    op.create_index(
        op.f("ix_legislator_name_district"),
        "legislators",
        ["name", "district"],
        unique=True,
    )

    # Create user_topic_follows table
    op.create_table(
        "user_topic_follows",
        sa.Column("user_id", sa.Integer()),
        sa.Column("topic_id", sa.Integer()),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    # Create user_bill_follows table
    op.create_table(
        "user_bill_follows",
        sa.Column("user_id", sa.Integer()),
        sa.Column("bill_id", sa.Integer()),
        sa.ForeignKeyConstraint(
            ["bill_id"],
            ["bills.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    op.create_table(
        "votes",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_choice", sa.Enum("YES", "NO", name="votechoice"), nullable=False
        ),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "bill_id"),
    )


def downgrade():
    op.drop_table("votes")
    op.execute("DROP TYPE votechoice")
    op.drop_table("user_bill_follows")
    op.drop_table("user_topic_follows")
    op.drop_table("legislators")
    op.drop_index(op.f("ix_bills_session"), table_name="bills")
    op.drop_index(op.f("ix_bills_body"), table_name="bills")
    op.drop_index(op.f("ix_bills_state"), table_name="bills")
    op.drop_index(op.f("ix_bills_legiscan_id"), table_name="bills")
    op.drop_table("bills")
    op.drop_table("legislative_bodys")
    op.drop_table("roles")
    op.drop_table("states")
    op.drop_table("partys")
    op.drop_index(op.f("ix_topics_name"), table_name="topics")
    op.drop_table("topics")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
