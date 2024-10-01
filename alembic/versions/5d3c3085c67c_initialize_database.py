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
        sa.Column("latestAction", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bills_legiscan_id"), "bills", ["legiscan_id"], unique=False)
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


def downgrade():
    op.drop_table("legislators")
    op.drop_index(op.f("ix_bills_session"), table_name="bills")
    op.drop_index(op.f("ix_bills_body"), table_name="bills")
    op.drop_index(op.f("ix_bills_state"), table_name="bills")
    op.drop_index(op.f("ix_bills_legiscan_id"), table_name="bills")
    op.drop_table("bills")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
