"""Create CAR tables

Revision ID: 297f99638c3f
Revises: 721daf5ae461
Create Date: 2025-04-10 14:08:46.253791

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "297f99638c3f"
down_revision: Union[str, None] = "721daf5ae461"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS carstore;")
    op.create_table(
        "car_shards",
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("root", sa.LargeBinary(), nullable=False, unique=True),
        sa.Column("data_start", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.Column("rev", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="carstore",
    )
    op.create_index("idx_car_shards_uid", "car_shards", ["uid"], schema="carstore", unique=False)
    op.create_index(
        "idx_car_shards_uid_rev", "car_shards", ["uid", "rev"], schema="carstore", unique=False
    )
    op.create_index(
        "idx_car_shards_uid_seq", "car_shards", ["uid", "seq"], schema="carstore", unique=False
    )

    op.create_table(
        "block_refs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=False),
        sa.Column("shard", sa.BigInteger(), nullable=False),
        sa.Column("byte_offset", sa.BigInteger(), nullable=False),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["shard"],
            ["carstore.car_shards.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="carstore",
    )
    op.create_index("idx_block_refs_cid", "block_refs", ["cid"], schema="carstore", unique=False)
    op.create_index(
        "idx_block_refs_shard", "block_refs", ["shard"], schema="carstore", unique=False
    )
    op.create_index("idx_block_refs_uid", "block_refs", ["uid"], schema="carstore", unique=False)

    op.create_table(
        "stale_refs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cid", sa.LargeBinary(), nullable=True),
        sa.Column("cids", sa.LargeBinary(), nullable=True),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="carstore",
    )
    op.create_index("idx_stale_refs_uid", "stale_refs", ["uid"], schema="carstore", unique=False)
    op.create_index("idx_stale_refs_cid", "stale_refs", ["cid"], schema="carstore", unique=False)


def downgrade():
    op.drop_table("stale_refs")
    op.drop_table("block_refs")
    op.drop_table("car_shards")
