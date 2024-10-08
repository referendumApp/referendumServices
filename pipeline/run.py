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


def extract() -> Dict[str, pd.DataFrame]:
    etl_configs = [
        {"source": "ls_bill", "destination": "bills"},
        {"source": "ls_people", "destination": "legislators"},
    ]
    legiscan_dataframes = {}
    logger.info("EXTRACT: Extracting data")
    legiscan_db = next(get_legiscan_api_db())

    if check_db_connection(legiscan_db):
        logger.info("EXTRACT: Successfully connected to Legiscan API database")

        # Get all table names from the public schema
        table_names = [config["source"] for config in etl_configs]

        with legiscan_db.connection() as conn:
            for table_name in table_names:
                # Extract data for each table and store it in the legiscan_dataframes dictionary
                df = pd.read_sql(table_name, con=conn)
                legiscan_dataframes[table_name] = df

        logger.info("EXTRACT: Extract completed")

        return legiscan_dataframes
    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


# def transform(dataframes):
def transform(legiscan_dataframes, desired_tables=None) -> Dict[str, pd.DataFrame]:
    logger.info("TRANSFORM: Transforming data")
    transformed_data = {}

    def rename_columns(df):
        if "bill_id" in df.columns:
            df = df.rename(columns={"bill_id": "legiscan_id"})
            logger.info("TRANSFORM: Renamed 'bill_id' to 'legiscan_id'")
        elif "people_id" in df.columns:
            df = df.rename(columns={"people_id": "legiscan_id"})
            logger.info("TRANSFORM: Renamed 'people_id' to 'legiscan_id'")
        return df

    # Check if a subset of tables is specified; otherwise, process all tables
    if desired_tables is None or len(desired_tables) == 0:
        logger.info(
            "TRANSFORM: No specific tables provided, processing all available tables."
        )
        tables_to_transform = legiscan_dataframes.keys()
        for table_name in tables_to_transform:
            df = legiscan_dataframes[table_name]

            transformed_df = rename_columns(df)

            # Add the transformed table to the final result with the same table name
            transformed_data[table_name] = transformed_df
            logger.info(
                f"TRANSFORM: Table '{table_name}' added to transformed data with {len(transformed_df)} rows"
            )
    else:
        logger.info(f"TRANSFORM: Specific tables provided: {desired_tables}")
        for table_mapping in desired_tables:
            source_table = table_mapping.get("source")
            destination_table = table_mapping.get("destination")

            if source_table in legiscan_dataframes:
                df = legiscan_dataframes[source_table]

                transformed_df = rename_columns(df)

                # Add the transformed table to the final result with the destination table name
                transformed_data[destination_table] = transformed_df
                logger.info(
                    f"TRANSFORM: Table '{source_table}' transformed and renamed to '{destination_table}' with {len(transformed_df)} rows"
                )
            else:
                logger.warning(
                    f"TRANSFORM: Source table '{source_table}' not found in legiscan dataframes"
                )

    logger.info("TRANSFORM: Transform completed")
    return transformed_data


def load(transformed_data):
    logger.info("LOAD: Loading data")
    referendum_db = next(get_referendum_db())
    if check_db_connection(referendum_db):
        logger.info("LOAD: Successfully connected to Referendum database")

        # Insert only the first bill into the Referendum database
        if "bills" in transformed_data:
            bills_df = transformed_data["bills"]

            # Extract the first row
            first_row = bills_df.iloc[0]

            # Convert types for compatibility with PostgreSQL
            bill_data = {
                "legiscan_id": int(
                    first_row["legiscan_id"]
                ),  # Convert numpy.int64 to native Python int
                "title": str(first_row["title"]),
                "status": str(first_row["status"]),
            }

            # Insert the first row into the BILL table in the Referendum database
            referendum_db.execute(
                text(
                    "INSERT INTO bills (legiscan_id, title, status) VALUES (:legiscan_id, :title, :status) ON CONFLICT (id) DO NOTHING;"
                ),
                bill_data,
            )

            # Log all details of the first row
            logger.info(f"LOAD: First bill inserted - ID: {bill_data['legiscan_id']}, ")

        logger.info("LOAD: Load completed")

        result = referendum_db.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        )
        tables = result.fetchall()
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

        # Log the names of all tables in the database
        logger.info(f"LOAD: Tables in referendum_db: {[table[0] for table in tables]}")

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
                    "function": "rename",
                    "parameters": {"columns": {"bill_id": "legiscan_id"}},
                },
                {
                    "function": "keep_columns",
                    "parameters": {"columns": ["legiscan_id"]},
                },
            ],
            "dataframe": None,
        },
        {"source": "ls_people", "destination": "legislators"},
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
