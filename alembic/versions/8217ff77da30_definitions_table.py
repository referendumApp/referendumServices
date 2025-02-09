"""definitions table

Revision ID: 8217ff77da30
Revises: fbaa14d45feb
Create Date: 2025-02-09 08:55:33.918639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import yaml
from pathlib import Path


# revision identifiers, used by Alembic.
revision: str = "8217ff77da30"
down_revision: Union[str, None] = "fbaa14d45feb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

definitions_version = 1


def load_definitions(version: int) -> dict:
    """Load specific version of definitions from YAML file."""
    definitions_dir = Path(__file__).parent.parent / "data"

    # Find the file for this version
    version_file = next(definitions_dir.glob(f"definitions_v{version}.yaml"))

    with open(version_file) as f:
        data = yaml.safe_load(f)
        assert data["version"] == version, f"Version mismatch in {version_file}"
        return data["definitions"]


def upgrade():
    op.create_table(
        "definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    definitions = load_definitions(version=definitions_version)

    values = []
    for name, data in definitions.items():
        description = data["description"].replace("'", "''")
        values.append(f"('{name}', '{description}')")

    values_str = ",\n    ".join(values)

    op.execute(
        f"""
    INSERT INTO definitions (name, description) VALUES
    {values_str}
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;
    """
    )


def downgrade():
    definitions = load_definitions(version=1)
    names = ", ".join(f"'{name}'" for name in definitions.keys())

    op.execute(
        f"""
    DELETE FROM definitions 
    WHERE name IN ({names});
    """
    )
