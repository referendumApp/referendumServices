import json
import os

from pipeline import run
from sqlalchemy import text
from unittest.mock import Mock, patch

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection
from pipeline.etl_config import ETLConfig


def test_etl():
    run.orchestrate(stage="etl")

    referendum_db = referendum_connection.SessionLocal()
    legiscan_db = legiscan_api_connection.SessionLocal()

    directory = os.path.dirname(os.path.abspath(__file__))
    config_filepath = f"{directory}/../legiscan_etl_configs.json"
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


@patch("pipeline.etl_config.UserServiceClient")
def test_pds(mock_user_service_client):
    # Mock the UserServiceClient
    mock_client = Mock()
    created_legislators = {}

    def mock_get_legislator(legislator_id):
        return created_legislators.get(legislator_id)

    def mock_create_legislator(legislator_data):
        legislator_id = legislator_data.get("legislatorId")
        if legislator_id in created_legislators:
            raise Exception(f"Legislator already exists: {legislator_id}")
        response = {
            "did": f"did:plc:{legislator_id}",
            "aid": legislator_id,
            "handle": f"legislator-{legislator_id}.referendum.app",
        }
        created_legislators[legislator_id] = {**legislator_data, **response, "action": "created"}
        return response

    def mock_update_legislator(legislator_data):
        legislator_id = legislator_data.get("legislatorId")
        if legislator_id not in created_legislators:
            raise Exception(f"Legislator not found: {legislator_id}")
        existing = created_legislators[legislator_id]
        updated_data = {**existing, **legislator_data, "action": "updated"}
        created_legislators[legislator_id] = updated_data
        return {"did": existing["did"], "aid": existing["aid"], "handle": existing["handle"]}

    mock_client.get_legislator.side_effect = mock_get_legislator
    mock_client.create_legislator.side_effect = mock_create_legislator
    mock_client.update_legislator.side_effect = mock_update_legislator
    mock_user_service_client.return_value = mock_client

    # Run the PDS processing
    run.orchestrate(stage="pds_processing")
