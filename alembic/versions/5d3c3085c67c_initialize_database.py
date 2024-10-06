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

    # Create bills table
    op.create_table(
        "bills",
        sa.Column("legiscan_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("identifier", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("session", sa.String(), nullable=True),
        sa.Column("briefing", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("latest_action", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bills_legiscan_id"), "bills", ["legiscan_id"], unique=True)
    op.create_index(op.f("ix_bills_state"), "bills", ["state"], unique=False)
    op.create_index(op.f("ix_bills_body"), "bills", ["body"], unique=False)
    op.create_index(op.f("ix_bills_session"), "bills", ["session"], unique=False)

    # Create legislators table
    op.create_table(
        "legislators",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("chamber", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("facebook", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("office", sa.String(), nullable=True),
        sa.Column("party", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("twitter", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "parties",
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
        "legislative_bodies",
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

    # Create legislative_body_membership table
    op.create_table(
        "legislative_body_membership",
        sa.Column("legislative_body_id", sa.Integer()),
        sa.Column("legislator_id", sa.Integer()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.ForeignKeyConstraint(
            ["legislative_body_id"],
            ["legislative_bodies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["legislator_id"],
            ["legislators.id"],
        ),
    )


def downgrade():
    op.drop_table("legislative_body_membership")
    op.drop_table("user_bill_follows")
    op.drop_table("user_topic_follows")
    op.drop_table("legislators")
    op.drop_index(op.f("ix_bills_session"), table_name="bills")
    op.drop_index(op.f("ix_bills_body"), table_name="bills")
    op.drop_index(op.f("ix_bills_state"), table_name="bills")
    op.drop_index(op.f("ix_bills_legiscan_id"), table_name="bills")
    op.drop_table("bills")
    op.drop_index(op.f("ix_topics_name"), table_name="topics")
    op.drop_table("topics")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
