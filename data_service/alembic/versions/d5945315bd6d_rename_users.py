"""rename users

Revision ID: d5945315bd6d
Revises: f3584da4c065
Create Date: 2025-05-09 12:50:26.807243

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5945315bd6d"
down_revision: Union[str, None] = "f3584da4c065"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("user", "actor")
    op.rename_table("user_follow_record", "actor_follow_record")

    op.alter_column("person", "uid", new_column_name="aid")
    op.alter_column("block_refs", "uid", new_column_name="aid")
    op.alter_column("car_shards", "uid", new_column_name="aid")


def downgrade() -> None:
    op.alter_column("car_shards", "aid", new_column_name="uid")
    op.alter_column("block_refs", "aid", new_column_name="uid")
    op.alter_column("person", "aid", new_column_name="uid")

    op.rename_table("actor_follow_record", "user_follow_record")
    op.rename_table("actor", "user")
