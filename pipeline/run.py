import logging
import pandas as pd
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection

from etl_configs import etl_configs

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


def count_rows(db_session, table_name):
    try:
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = db_session.execute(text(query)).scalar()
        return result
    except SQLAlchemyError as e:
        logger.error(f"Error counting rows in {table_name}: {str(e)}")
        return None


def extract(etl_configs) -> Dict[str, pd.DataFrame]:
    logger.info("EXTRACT: Extracting data")
    legiscan_db = next(get_legiscan_api_db())

    if check_db_connection(legiscan_db):

        with legiscan_db.connection() as conn:
            for config in etl_configs:
                table_name = config["source"]

                try:
                    df = pd.read_sql(table_name, con=conn)

                    for transformation in config.get("transformations", []):
                        if transformation["function"] == "keep_columns":
                            columns_to_keep = transformation["parameters"]["columns"]
                            df = df[columns_to_keep]

                    config["dataframe"] = df

                    # Count rows in the Legiscan database for this table
                    row_count = len(df)
                    config["legiscan_row_count"] = row_count
                    logger.info(f"Extracted {row_count} rows from {table_name}")

                except Exception as e:
                    logger.error(f"Error processing table {table_name}: {e}")
                    config["legiscan_row_count"] = 0

        return etl_configs

    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


def transform(etl_configs) -> Dict[str, pd.DataFrame]:
    logger.info("EXTRACT: Transforming data")
    for config in etl_configs:
        table_name = config["source"]

        try:

            df = config["dataframe"]

            for transformation in config.get("transformations", []):
                if transformation["function"] == "rename":
                    columns_to_rename = transformation["parameters"]["columns"]
                    df = df.rename(columns=columns_to_rename)

                elif transformation["function"] == "set_primary_sponsor":
                    sponsor_type_col = transformation["parameters"][
                        "sponsor_type_column"
                    ]
                    is_primary_col = transformation["parameters"]["is_primary_column"]

                    df[is_primary_col] = df[sponsor_type_col] == 1

                    df = df.drop(columns=[sponsor_type_col])
                elif transformation["function"] == "duplicate":
                    source_name = transformation["parameters"]["source_name"]
                    destination_name = transformation["parameters"]["destination_name"]
                    df[destination_name] = df[source_name]

            config["dataframe"] = df

        except Exception as e:
            logger.error(f"Error transforming data for table {table_name}: {e}")
            raise

    return etl_configs


def load(etl_configs):
    logger.info("EXTRACT: Loading data")
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

        # Process the ETL load
        for config in etl_configs:
            destination_table = config["destination"]
            df = config["dataframe"]

            try:
                df.to_sql(
                    destination_table,
                    referendum_db.bind(),
                    if_exists="append",
                    index=False,
                )

                logger.info(f"Loaded data into {destination_table}")

                # Count rows in the Referendum database for this table
                referendum_row_count = count_rows(referendum_db, destination_table)

                # Compare row counts between Legiscan and Referendum databases
                legiscan_row_count = config["legiscan_row_count"]
                if legiscan_row_count == referendum_row_count:
                    logger.info(
                        f"Row count check passed for {destination_table}: {referendum_row_count} rows."
                    )
                else:
                    logger.error(
                        f"Row count mismatch for {destination_table}: "
                        f"Legiscan DB has {legiscan_row_count}, "
                        f"Referendum DB has {referendum_row_count}."
                    )

            except Exception as e:
                logger.error(f"Error inserting data into '{destination_table}': {e}")
                raise
    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():

    try:
        logger.info("Starting ETL pipeline...")
        etl_configs = extract(etl_configs)
        etl_configs = transform(etl_configs)
        load(etl_configs)
        logger.info("ETL process completed successfully")
    except ConnectionError as e:
        logger.error(f"ETL process failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ETL process: {str(e)}")


if __name__ == "__main__":
    orchestrate_etl()
