"""Add url to bill versions

Revision ID: a8b4f2c91d3e
Revises: f645dde3ae91
Create Date: 2024-10-30 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8b4f2c91d3e"
down_revision: Union[str, None] = "f645dde3ae91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "bill_version_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_constraint('bill_versions_pkey', 'bill_versions')

    op.add_column("bill_versions", sa.Column("id", sa.Integer(), nullable=False))
    op.add_column("bill_versions", sa.Column("bill_version_type_id", sa.Integer(), nullable=True))
    op.add_column("bill_versions", sa.Column("url", sa.String(), nullable=True))

    op.create_primary_key('bill_versions_pkey', 'bill_versions', ['id'])

    op.drop_column('bill_versions', 'version')


def downgrade():
    op.add_column('bill_versions', sa.Column('version', sa.Integer(), nullable=False))

    op.drop_constraint('bill_versions_pkey', 'bill_versions')

    op.drop_column("bill_versions", "url")
    op.drop_column("bill_versions", "bill_version_type_id")
    op.drop_column("bill_versions", "id")

    op.create_primary_key('bill_versions_pkey', 'bill_versions', ['bill_id', 'version'])

    op.drop_table("bill_version_types")
