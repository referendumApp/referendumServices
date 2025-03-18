"""Create and use updated_at trigger function

Revision ID: 43e4bac6f9b5
Revises: 050e288b3df8
Create Date: 2025-03-17 13:22:29.031648

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43e4bac6f9b5"
down_revision: Union[str, None] = "050e288b3df8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION public.refresh_updated_at_col()
        RETURNS TRIGGER
        LANGUAGE plpgsql AS
        $func$
        BEGIN
        NEW.updated_at := now();
        RETURN NEW;
        END
        $func$
        """
    )

    op.execute(
        """
        CREATE TRIGGER refresh_user_updated_at
        BEFORE UPDATE ON atproto.user
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_pds_updated_at
        BEFORE UPDATE ON atproto.pds
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_peering_updated_at
        BEFORE UPDATE ON atproto.peering
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_citizen_updated_at
        BEFORE UPDATE ON atproto.citizen
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_activity_post_updated_at
        BEFORE UPDATE ON atproto.activity_post
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_endorsement_record_updated_at
        BEFORE UPDATE ON atproto.endorsement_record
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )
    op.execute(
        """
        CREATE TRIGGER refresh_user_follow_record_updated_at
        BEFORE UPDATE ON atproto.user_follow_record
        FOR EACH ROW EXECUTE FUNCTION public.refresh_updated_at_col();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS refresh_user_follow_record_updated_at ON atproto.user_follow_record"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS refresh_endorsement_record_updated_at ON atproto.endorsement_record"
    )
    op.execute("DROP TRIGGER IF EXISTS refresh_activity_post_updated_at ON atproto.activity_post")
    op.execute("DROP TRIGGER IF EXISTS refresh_citizen_updated_at ON atproto.citizen")
    op.execute("DROP TRIGGER IF EXISTS refresh_peering_updated_at ON atproto.peering")
    op.execute("DROP TRIGGER IF EXISTS refresh_pds_updated_at ON atproto.pds")
    op.execute("DROP TRIGGER IF EXISTS refresh_user_updated_at ON atproto.user")
    op.execute("DROP FUNCTION IF EXISTS public.refresh_updated_at_col()")
