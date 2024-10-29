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
    try:
        yield db
    finally:
        db.close()


def get_referendum_db():
    db = referendum_connection.SessionLocal()
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


def extract(etl_configs: List[ETLConfig]) -> List[ETLConfig]:
    legiscan_db = next(get_legiscan_api_db())

    if check_db_connection(legiscan_db):
        with legiscan_db.connection() as conn:
            for config in etl_configs:
                logger.info(f"extracting table {config.source}")
                try:
                    df = pd.read_sql(config.source, con=conn)

                    for transformation in config.transformations:
                        if transformation.function == TransformationFunction.KEEP_COLUMNS:
                            columns_to_keep = transformation.parameters.columns
                            df = df[columns_to_keep]

                    config.dataframe = df

                except Exception as e:
                    logger.error(f"Error processing table {config.source}: {e}")

        return etl_configs
    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


def transform(etl_configs: List[ETLConfig]) -> List[ETLConfig]:
    for config in etl_configs:
        logger.info(f"Transforming table from {config.source} to {config.destination}")
        try:
            df = config.dataframe

            for transformation in config.transformations:
                match transformation.function:
                    case TransformationFunction.RENAME:
                        column_mapping = transformation.parameters.columns
                        df = df.rename(columns=column_mapping)

                    # TODO - generalize to conditional operation
                    case TransformationFunction.SET_PRIMARY_SPONSOR:
                        df[transformation.parameters.is_primary_column] = df[transformation.parameters.sponsor_type_column] == 1
                        df = df.drop(columns=[transformation.parameters.sponsor_type_column])

                    case TransformationFunction.DUPLICATE:
                        df[transformation.parameters.destination_name] = df[transformation.parameters.source_name]

            config.dataframe = df

        except Exception as e:
            logger.error(f"Error transforming data for source table {config.source}: {e}")

    return etl_configs


def load(etl_configs: List[ETLConfig]):
    referendum_db = next(get_referendum_db())

    if check_db_connection(referendum_db):
        try:
            inspector = sqlalchemy.inspect(referendum_db.connection())
            tables = inspector.get_table_names()

            logger.info(f"Tables in Referendum database: {tables}")
            for table in tables:
                columns = inspector.get_columns(table)
                column_names = [column["name"] for column in columns]
                logger.info(f"Columns in '{table}' table: {column_names}")
        except Exception as e:
            logger.error(f"Error fetching table metadata: {e}")
            raise

        for config in etl_configs:
            try:
                logger.info(f"Loading data into {config.destination}")
                config.dataframe.to_sql(
                    config.destination,
                    referendum_db.bind,
                    if_exists="append",
                    index=False,
                )

            except Exception as e:
                logger.error(f"Error inserting data into '{config.destination}': {e}")
                raise
    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():
    directory = os.path.dirname(os.path.abspath(__file__))
    config_filepath = f"{directory}/etl_configs.json"

    with open(config_filepath, "r") as config_file:
        config_data = json.load(config_file)
        etl_configs = [ETLConfig(**config) for config in config_data]

    try:
        logger.info("ETL process starting")
        logger.info("Beginning extraction")
        etl_configs = extract(etl_configs)
        logger.info("Beginning transformation")
        etl_configs = transform(etl_configs)
        logger.info("Beginning load")
        load(etl_configs)
        logger.info("ETL process completed successfully")
    except ConnectionError as e:
        logger.error(f"ETL process failed: {str(e)}")
    except Exception as e:
        logger.error(f"ETL process failed with unexpected error: {str(e)}")


if __name__ == "__main__":
    orchestrate_etl()
