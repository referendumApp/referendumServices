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
                    # logger.info(
                    #     f"EXTRACT: First row from table {table_name}: {df.head(1).T}"
                    # )

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
    state_abbreviation_map = {
        1: "AL",
        2: "AK",
        4: "AZ",
        5: "AR",
        6: "CA",
        8: "CO",
        9: "CT",
        10: "DE",
        11: "DC",
        12: "FL",
        13: "GA",
        15: "HI",
        16: "ID",
        17: "IL",
        18: "IN",
        19: "IA",
        20: "KS",
        21: "KY",
        22: "LA",
        23: "ME",
        24: "MD",
        25: "MA",
        26: "MI",
        27: "MN",
        28: "MS",
        29: "MO",
        30: "MT",
        31: "NE",
        32: "NV",
        33: "NH",
        34: "NJ",
        35: "NM",
        36: "NY",
        37: "NC",
        38: "ND",
        39: "OH",
        40: "OK",
        41: "OR",
        42: "PA",
        44: "RI",
        45: "SC",
        46: "SD",
        47: "TN",
        48: "TX",
        49: "UT",
        50: "VT",
        51: "VA",
        52: "FL",
        53: "WA",
        54: "WV",
        55: "WI",
        56: "WY",
    }

    ### bills ###
    if "ls_bill" in legiscan_dataframes:
        ls_bill = legiscan_dataframes["ls_bill"][["bill_id", "title", "created"]]
        transformed_bill = ls_bill.rename(
            columns={"bill_id": "id", "title": "title", "created": "introduced_date"}
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

        for table in transformed_data:

            logger.info(f"LOAD: table loaded: {table}")
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
