import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

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


def extract(empty_legiscan_dataframes):
    logger.info("EXTRACT: Extracting data")
    legiscan_db = next(get_legiscan_api_db())
    if check_db_connection(legiscan_db):
        logger.info("EXTRACT: Successfully connected to Legiscan API database")
        result = legiscan_db.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        )
        tables = result.fetchall()
        # logger.info(f"EXTRACT: Finished extracting all tables: {tables}")

        with legiscan_db.connection() as conn:
            for table_row in tables:
                table_name = table_row[0]

                if table_name == "ls_bill":
                    df = pd.read_sql(table_name, con=conn)
                    empty_legiscan_dataframes[table_name] = df
                    logger.info(f"EXTRACT: Data extracted from table: {table_name}")
                    logger.info(
                        f"EXTRACT: First row from table {table_name}: {df.head(1).T}"
                    )

                if table_name == "ls_people":
                    df = pd.read_sql(table_name, con=conn)
                    empty_legiscan_dataframes[table_name] = df
                    logger.info(f"EXTRACT: Data extracted from table: {table_name}")

        logger.info("EXTRACT: Extract completed")
        legiscan_dataframes = empty_legiscan_dataframes
        return legiscan_dataframes
    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


# def transform(dataframes):
def transform(legiscan_dataframes):
    logger.info("TRANSFORM: Transforming data")
    transformed_data = {}

    ### bills ###
    if "ls_bill" in legiscan_dataframes:
        ls_bill = legiscan_dataframes["ls_bill"][
            ["bill_id", "title", "created", "status_id"]
        ]
        transformed_bill = ls_bill.rename(
            columns={
                "bill_id": "id",
                "title": "title",
                "created": "introduced_date",
                "status": "status_id",
            }
        )
        transformed_data["bill"] = transformed_bill
        logger.info(
            f"TRANSFORM: Transformed 'ls_bill' into 'bill' table with {len(transformed_bill)} rows"
        )
        logger.info(
            f"TRANSFORM: First row of transformed legislator data:\n{transformed_bill.iloc[0].to_dict()}"
        )

    else:
        logger.warning("'ls_bill' table not found in legiscan dataframes")

    ### legislators ###
    if "ls_people" in legiscan_dataframes:
        ls_people = legiscan_dataframes["ls_people"][
            ["people_id", "name", "state_id", "district", "party_id"]
        ]
        transformed_legislator = ls_people.rename(
            columns={
                "people_id": "legiscan_id",
                "name": "name",
                "state_id": "state_id",  ### WHAT IS 'state_id' ???????
                "district": "district",
                "party_id": "party_id",
                "role_id": "role_id",
            }
        )
        transformed_legislator["state"] = (
            transformed_legislator["district"].str.split("-").str[1]
        )
        transformed_data["legislator"] = transformed_legislator
        logger.info(
            f"TRANSFORM: Transformed 'ls_bill' into 'bill' table with {len(transformed_legislator)} rows"
        )
        # logger.info(f"TRANSFORM: First row of transformed legislator data:\n{transformed_legislator.iloc[0].to_dict()}")
    else:
        logger.warning("'ls_people' table not found in legiscan dataframes")

    logger.info("TRANSFORM: Transform completed")

    return transformed_data


def load(transformed_data):
    logger.info("LOAD: Loading data")
    referendum_db = next(get_referendum_db())
    if check_db_connection(referendum_db):
        logger.info("LOAD: Successfully connected to Referendum database")

        # Insert only the first bill into the Referendum database
        if "bill" in transformed_data:
            bills_df = transformed_data["bill"]

            # Extract the first row
            first_row = bills_df.iloc[0]

            # Convert types for compatibility with PostgreSQL
            bill_data = {
                "id": int(first_row["id"]),  # Convert numpy.int64 to native Python int
                "title": str(first_row["title"]),
                "introduced_date": first_row[
                    "introduced_date"
                ].to_pydatetime(),  # Convert pandas.Timestamp to Python datetime
                "status": str(first_row["status"]),
            }

            # Insert the first row into the BILL table in the Referendum database
            referendum_db.execute(
                text(
                    """
                    INSERT INTO BILL (id, title, introduced_date, status)
                    VALUES (:id, :title, :introduced_date, 'status')
                    ON CONFLICT (id) DO NOTHING;
                    """
                ),
                bill_data,
            )

            # Log all details of the first row
            logger.info(
                f"LOAD: First bill inserted - ID: {bill_data['id']}, "
                f"Title: {bill_data['title']}, "
                f"Introduced Date: {bill_data['introduced_date']}, "
                f"Status: {bill_data['status']}"
            )

        logger.info("LOAD: Load completed")
    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():
    empty_legiscan_dataframes = {}
    try:
        legiscan_dataframes = extract(empty_legiscan_dataframes)
        transformed_data = transform(legiscan_dataframes)
        load(transformed_data)
        logger.info("ETL process completed successfully")
    except ConnectionError as e:
        logger.error(f"ETL process failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ETL process: {str(e)}")


if __name__ == "__main__":
    orchestrate_etl()
