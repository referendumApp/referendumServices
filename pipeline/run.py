import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection

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
        # Attempt to execute a simple query
        db_session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def extract(etl_configs) -> Dict[str, pd.DataFrame]:
    logger.info("EXTRACT: Extracting data")
    legiscan_db = next(get_legiscan_api_db())

    if check_db_connection(legiscan_db):
        logger.info("EXTRACT: Successfully connected to Legiscan API database")

        with legiscan_db.connection() as conn:
            for config in etl_configs:
                table_name = config["source"]

                try:
                    # Extract data for each table
                    df = pd.read_sql(table_name, con=conn)

                    # Perform the "keep_columns" transformation
                    for transformation in config.get("transformations", []):
                        if transformation["function"] == "keep_columns":
                            columns_to_keep = transformation["parameters"]["columns"]
                            df = df[columns_to_keep]

                    # Save the extracted dataframe (without renaming) into the config
                    config["dataframe"] = df

                    logger.info(
                        f"EXTRACT: Successfully extracted data for table {table_name}"
                    )

                except Exception as e:
                    logger.error(f"Error processing table {table_name}: {e}")
                    raise

        logger.info("EXTRACT: Extraction completed")
        # Return the modified etl_configs with the extracted data
        return etl_configs

    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


# def transform(dataframes):
def transform(etl_configs) -> Dict[str, pd.DataFrame]:
    logger.info("TRANSFORM: Performing transformations")

    for config in etl_configs:
        table_name = config["source"]

        try:
            # Check if the dataframe exists in the config
            if "dataframe" not in config:
                logger.warning(
                    f"TRANSFORM: No dataframe found for table {table_name}. Skipping transformation."
                )
                continue

            df = config["dataframe"]

            # Perform the "rename" transformation
            for transformation in config.get("transformations", []):
                if transformation["function"] == "rename":
                    columns_to_rename = transformation["parameters"]["columns"]
                    df = df.rename(columns=columns_to_rename)

                # Check if sponsor_type_id is 1 and set is_primary_sponsor to True
                elif transformation["function"] == "set_primary_sponsor":
                    sponsor_type_col = transformation["parameters"][
                        "sponsor_type_column"
                    ]
                    is_primary_col = transformation["parameters"]["is_primary_column"]

                    # Set the new boolean column based on the condition
                    df[is_primary_col] = df[sponsor_type_col] == 1

            # Save the transformed dataframe back into the config
            config["dataframe"] = df

            logger.info(
                f"TRANSFORM: Successfully transformed data for table {table_name}"
            )

        except Exception as e:
            logger.error(f"Error transforming data for table {table_name}: {e}")
            raise

    logger.info("TRANSFORM: Transformations completed")
    # Return the modified etl_configs with transformed data
    return etl_configs


def load(etl_configs):
    referendum_db = next(get_referendum_db())

    if check_db_connection(referendum_db):
        logger.info("LOAD: Successfully connected to Referendum database")
        logger.info("LOAD: Loading data")

        for config in etl_configs:
            destination_table = config["destination"]

            # Check if the dataframe exists in the config
            if "dataframe" not in config:
                logger.warning(
                    f"LOAD: No dataframe found for table {destination_table}. Skipping load."
                )
                continue

            df = config["dataframe"]

            # Log the number of rows to be inserted
            logger.info(
                f"LOAD: Preparing to insert {len(df)} rows into '{destination_table}' table"
            )

            # Build the insertion query for bulk inserts
            try:
                # Use Pandas to insert the dataframe into the destination table
                df.to_sql(
                    destination_table,
                    referendum_db.connection(),
                    if_exists="append",
                    index=False,
                )
            except Exception as e:
                logger.error("Error inserting data")
                # logger.error(f"Error inserting data into '{destination_table}': {e}")
                raise

            # Log that the insert was successful
            logger.info(
                f"LOAD: Successfully inserted data into '{destination_table}' table"
            )

            # After insertion, fetch and print the first row from the corresponding table to ensure it worked
            try:
                first_row_query = referendum_db.execute(
                    text(f"SELECT * FROM {destination_table} LIMIT 1")
                )
                first_row_result = first_row_query.fetchone()

                if first_row_result:
                    logger.info(
                        f"LOAD: First row of the '{destination_table}' table in referendum_db: {first_row_result}"
                    )
                else:
                    logger.warning(
                        f"LOAD: No rows found in '{destination_table}' table after insertion"
                    )
            except Exception as e:
                logger.error(
                    f"Error fetching first row from '{destination_table}': {e}"
                )

        # At the end, fetch and print all table names in the referendum_db
        try:
            result = referendum_db.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            tables = result.fetchall()

            if tables:
                table_names = [table[0] for table in tables]
                logger.info(f"LOAD: All tables in referendum_db: {table_names}")

                # For each table, fetch and log the column names
                for table_name in table_names:
                    try:
                        column_result = referendum_db.execute(
                            text(
                                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                            )
                        )
                        columns = column_result.fetchall()
                        column_names = [col[0] for col in columns]
                        logger.info(
                            f"LOAD: Columns in '{table_name}' table: {column_names}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Error fetching columns for table '{table_name}': {e}"
                        )
            else:
                logger.warning("LOAD: No tables found in the referendum_db")

        except Exception as e:
            logger.error(f"Error fetching table names from referendum_db: {e}")

    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():
    etl_configs = [
        {
            "source": "ls_state",
            "destination": "states",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {"columns": ["state_id", "state_name"]},
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"state_id": "id", "state_name": "name"}},
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_role",
            "destination": "roles",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {"columns": ["role_id", "role_name"]},
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"role_id": "id", "role_name": "name"}},
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_body",
            "destination": "legislative_bodys",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {"columns": ["body_id", "state_id", "role_id"]},
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"body_id": "id"}},
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_party",
            "destination": "partys",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {"columns": ["party_id", "party_name"]},
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"party_id": "id", "party_name": "name"}},
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_bill",
            "destination": "bills",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {
                        "columns": [
                            "bill_id",
                            "title",
                            "description",
                            "state_id",
                            "body_id",
                            "bill_number",
                            "session_id",
                            "status_id",
                            "status_date",
                        ]
                    },
                },
                {
                    "function": "rename",
                    "parameters": {
                        "columns": {
                            "bill_id": "legiscan_id",
                            "bill_number": "identifier",
                            "body_id": "legislative_body_id",
                        }
                    },
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_people",
            "destination": "legislators",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {
                        "columns": ["people_id", "name", "party_id", "district"]
                    },
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"people_id": "legiscan_id"}},
                },
            ],
            "dataframe": None,
        },
    ]
    try:
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
