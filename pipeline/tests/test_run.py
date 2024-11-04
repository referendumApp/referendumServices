import pytest
import subprocess
import os

from pipeline import run
from sqlalchemy import text

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection


def test_pipeline_execution():
    run.orchestrate()

    referendum_db = referendum_connection.SessionLocal()
    legiscan_db = legiscan_api_connection.SessionLocal()

    table_pairs = {
        "ls_state": "states",
        "ls_body": "legislative_bodys",
        "ls_role": "roles",
        "ls_committee": "committees",
        "ls_bill": "bills",
        "ls_party": "partys",
        "ls_people": "legislators",
        # "legiscan_table": "bill_versions",
        # "legiscan_table": "topics",
        # "legiscan_table": "user_topic_follows",
        # "legiscan_table": "users",
        # "legiscan_table": "user_bill_follows",
        # "legiscan_table": "committee_membership",
        # "legiscan_table": "bill_actions",
        # "legiscan_table": "bill_sponsors",
        # "legiscan_table": "bill_topics",
        # "legiscan_table": "user_votes",
        # "legiscan_table": "legislator_votes",
        # "legiscan_table": "comments",
        # "legiscan_table": "user_legislator_follows"
    }

    for legiscan_table, referendum_table in table_pairs.items():
        # Query to count rows in each table
        legiscan_count = legiscan_db.execute(
            text(f"SELECT COUNT(*) FROM {legiscan_table}")
        ).scalar()
        referendum_count = referendum_db.execute(
            text(f"SELECT COUNT(*) FROM {referendum_table}")
        ).scalar()

        # Assert that the row counts are the same
        assert legiscan_count == referendum_count, (
            f"Row count mismatch for tables {legiscan_table} and {referendum_table}: "
            f"{legiscan_count} vs {referendum_count}\n"
        )

    referendum_db.close()
    legiscan_db.close()
