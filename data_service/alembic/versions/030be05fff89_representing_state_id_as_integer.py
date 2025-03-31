"""representing_state_iD as integer

Revision ID: 030be05fff89
Revises: fe24345379df
Create Date: 2025-02-06 05:13:55.407545

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "030be05fff89"
down_revision: Union[str, None] = "fe24345379df"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE legislators ALTER COLUMN representing_state_id TYPE integer USING representing_state_id::integer"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE legislators ALTER COLUMN representing_state_id TYPE varchar USING representing_state_id::varchar"
    )
