"""materialized view for vote totals

Revision ID: d45d8a97e784
Revises: 296fffa291c7
Create Date: 2025-01-12 06:49:04.095959

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d45d8a97e784"
down_revision: Union[str, None] = "296fffa291c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        CREATE MATERIALIZED VIEW vote_counts_by_party AS
            SELECT 
                bill_action_id,
                l.party_id,
                vote_choice_id,
                COUNT(*) as vote_count
            FROM legislator_votes lv
            JOIN legislators l ON l.id = lv.legislator_id
            GROUP BY bill_action_id, l.party_id, vote_choice_id
    """
    )

    # Create indices
    op.execute(
        """
        CREATE UNIQUE INDEX vote_counts_by_party_unique_idx ON vote_counts_by_party 
            (bill_action_id, party_id, vote_choice_id)
    """
    )

    op.execute(
        """
        CREATE INDEX vote_counts_by_party_party_vote_idx ON vote_counts_by_party
            (party_id, vote_choice_id)
    """
    )

    op.execute(
        """
        CREATE INDEX vote_counts_by_party_bill_action_idx ON vote_counts_by_party
            (bill_action_id)
    """
    )

    # Create function to refresh materialized view
    op.execute(
        """
            CREATE OR REPLACE FUNCTION refresh_vote_counts_by_party()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY vote_counts_by_party;
                RETURN NULL;
            END;
            $$;
        """
    )

    # Create trigger
    op.execute(
        """
            CREATE TRIGGER refresh_vote_counts_by_party_trigger
                AFTER INSERT OR UPDATE OR DELETE
                ON legislator_votes
                FOR EACH STATEMENT
                EXECUTE PROCEDURE refresh_vote_counts_by_party();
        """
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS refresh_vote_counts_by_party_trigger ON legislator_votes;")
    op.execute("DROP FUNCTION IF EXISTS refresh_vote_counts_by_party();")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vote_counts_by_party")
