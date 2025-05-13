import json
import os

from pipeline import run
from sqlalchemy import text

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection
from pipeline.etl_config import ETLConfig


def test_pipeline_execution():
    # We skip pulling & processing PDF data
    run.orchestrate(stage="etl")

    referendum_db = referendum_connection.SessionLocal()
    legiscan_db = legiscan_api_connection.SessionLocal()

    directory = os.path.dirname(os.path.abspath(__file__))
    config_filepath = f"{directory}/../etl_configs.json"
    with open(config_filepath, "r") as config_file:
        config_data = json.load(config_file)
        etl_configs = [ETLConfig(**config) for config in config_data]

    table_pairs = {config.source: config.destination for config in etl_configs}

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
