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
    logger.info("TRANSFORM: Performing column renaming")

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

            # Save the renamed dataframe back into the config
            config["dataframe"] = df

            logger.info(
                f"TRANSFORM: Successfully renamed columns for table {table_name}"
            )

        except Exception as e:
            logger.error(f"Error renaming columns for table {table_name}: {e}")
            raise

    logger.info("TRANSFORM: Column renaming completed")
    # Return the modified etl_configs with renamed columns
    return etl_configs


def load(etl_configs):
    logger.info("LOAD: Loading data")
    referendum_db = next(get_referendum_db())

    if check_db_connection(referendum_db):
        logger.info("LOAD: Successfully connected to Referendum database")

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

            for index, row in df.iterrows():
                # Convert row to a dictionary
                row_data = row.to_dict()

                # Build the column placeholders for SQL insertion
                columns = ", ".join(row_data.keys())
                placeholders = ", ".join([f":{key}" for key in row_data.keys()])

                # SQL query for inserting rows with ON CONFLICT handling
                sql_query = f"""
                    INSERT INTO {destination_table} ({columns}) 
                    VALUES ({placeholders}) 
                    ON CONFLICT (id) DO NOTHING;
                """

                # Convert the row data for insertion
                row_data = {
                    k: (
                        v.item()
                        if isinstance(v, (pd.Int64Dtype, pd.Float64Dtype))
                        else v
                    )
                    for k, v in row_data.items()
                }

                try:
                    # Execute the insertion query
                    referendum_db.execute(text(sql_query), row_data)
                except Exception as e:
                    logger.error(
                        f"Error inserting row {index + 1} into '{destination_table}': {e}"
                    )
                    break

        # Fetch the list of tables in the database
        result = referendum_db.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        )
        tables = result.fetchall()
        # Log the names of all tables in the database
        logger.info(f"LOAD: Tables in referendum_db: {[table[0] for table in tables]}")

        # Log the columns of the 'bills' table if it exists
        if "bills" in [table[0] for table in tables]:
            logger.info("LOAD: Fetching column names for the 'bills' table")
            result = referendum_db.execute(
                text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'bills'"
                )
            )
            columns = result.fetchall()
            logger.info(
                f"LOAD: Columns in the 'bills' table: {[col[0] for col in columns]}"
            )
        else:
            logger.warning("LOAD: 'bills' table not found in the Referendum database")

        # Fetch and log the first row from the 'bills' table to confirm the insertion
        first_row_query = referendum_db.execute(text("SELECT * FROM bills LIMIT 1"))
        first_row_result = first_row_query.fetchone()
        if first_row_result:
            logger.info(
                f"LOAD: First row of the 'bills' table in referendum_db to verify insertion: {first_row_result}"
            )
        else:
            logger.warning("LOAD: No rows found in 'bills' table after insertion")

    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():
    etl_configs = [
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
        # {
        #     "source": "ls_people",
        #     "destination": "legislators",
        #     "transformations": [
        #         {
        #             "function": "keep_columns",
        #             "parameters": {
        #                 "columns": [
        #                     "legiscan_id"
        #                     ]
        #                 },
        #         },
        #         {
        #             "function": "rename",
        #             "parameters": {
        #                 "columns": {
        #                     "people_id": "legiscan_id"
        #                     }
        #                 },
        #         }
        #     ],
        # },
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
