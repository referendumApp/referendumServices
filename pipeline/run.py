import logging
import pandas as pd
import sqlalchemy
import json
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection
from pipeline.etl_config import ETLConfig, TransformationFunction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_legiscan_api_db():
    db = legiscan_api_connection.SessionLocal()
    if not check_db_connection(db):
        logger.error("Failed to connect to legiscan_api database")
        raise ConnectionError("legiscan_api database connection failed")
    try:
        yield db
    finally:
        db.close()


def get_referendum_db():
    db = referendum_connection.SessionLocal()
    if not check_db_connection(db):
        logger.error("Failed to connect to referendum database")
        raise ConnectionError("referendum database connection failed")
    try:
        yield db
    finally:
        db.close()


def check_db_connection(db_session):
    try:
        db_session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database connection check: {str(e)}")
        db_session.invalidate()
        raise


def extract_all(etl_configs: List[ETLConfig]):
    legiscan_db = next(get_legiscan_api_db())

    with legiscan_db.connection() as conn:
        for config in etl_configs:
            config.extract(conn)


def transform_all(etl_configs: List[ETLConfig]):
    for config in etl_configs:
        config.transform()


def load_all(etl_configs: List[ETLConfig]):
    referendum_db = next(get_referendum_db())

    with referendum_db.connection() as conn:
        for config in etl_configs:
            config.load(conn)


def orchestrate_etl():
    directory = os.path.dirname(os.path.abspath(__file__))
    config_filepath = f"{directory}/etl_configs.json"

    with open(config_filepath, "r") as config_file:
        config_data = json.load(config_file)
        etl_configs = [ETLConfig(**config) for config in config_data]

    try:
        logger.info("ETL process starting")
        logger.info("Beginning extraction")
        extract_all(etl_configs)
        logger.info("Beginning transformation")
        transform_all(etl_configs)
        logger.info("Beginning load")
        load_all(etl_configs)
        logger.info("ETL process completed successfully")
    except ConnectionError as e:
        logger.error(f"ETL process failed: {str(e)}")
    except Exception as e:
        logger.error(f"ETL process failed with unexpected error: {str(e)}")


if __name__ == "__main__":
    orchestrate_etl()
