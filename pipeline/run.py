import logging
import pandas as pd
import sqlalchemy
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
        db_session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database connection check: {str(e)}")
        db_session.invalidate()
        raise


def extract(etl_configs) -> Dict[str, pd.DataFrame]:
    legiscan_db = next(get_legiscan_api_db())

    if check_db_connection(legiscan_db):

        with legiscan_db.connection() as conn:
            for config in etl_configs:
                table_name = config["source"]
                logger.info(f"Extracting table {table_name}")

                try:
                    df = pd.read_sql(table_name, con=conn)

                    for transformation in config.get("transformations", []):
                        if transformation["function"] == "keep_columns":
                            columns_to_keep = transformation["parameters"]["columns"]
                            df = df[columns_to_keep]

                    config["dataframe"] = df

                except Exception as e:
                    logger.error(f"Error processing table {table_name}: {e}")

        return etl_configs

    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


def transform(etl_configs) -> Dict[str, pd.DataFrame]:
    for config in etl_configs:
        table_name = config["source"]
        logger.info(f"Transforming table {table_name}")

        try:

            df = config["dataframe"]

            for transformation in config.get("transformations", []):
                if transformation["function"] == "rename":
                    columns_to_rename = transformation["parameters"]["columns"]
                    df = df.rename(columns=columns_to_rename)

                elif transformation["function"] == "set_primary_sponsor":
                    sponsor_type_col = transformation["parameters"]["sponsor_type_column"]
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
            logger.info(f"Loading table {destination_table}")
            df = config["dataframe"]
            try:
                df.to_sql(
                    destination_table,
                    referendum_db.bind,
                    if_exists="append",
                    index=False,
                )
            except Exception as e:
                logger.error(f"Error inserting data into '{destination_table}': {e}")
                raise
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
                            "bill_id": "id",
                            "bill_number": "identifier",
                            "body_id": "legislative_body_id",
                        }
                    },
                },
                {
                    "function": "duplicate",
                    "parameters": {
                        "source_name": "id",
                        "destination_name": "legiscan_id",
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
                        "columns": [
                            "people_id",
                            "name",
                            "party_id",
                            "district",
                        ]
                    },
                },
                {
                    "function": "rename",
                    "parameters": {"columns": {"people_id": "id"}},
                },
                {
                    "function": "duplicate",
                    "parameters": {
                        "source_name": "id",
                        "destination_name": "legiscan_id",
                    },
                },
            ],
            "dataframe": None,
        },
        {
            "source": "ls_committee",
            "destination": "committees",
            "transformations": [
                {
                    "function": "keep_columns",
                    "parameters": {
                        "columns": [
                            "committee_id",
                            "committee_body_id",
                            "committee_name",
                        ]
                    },
                },
                {
                    "function": "rename",
                    "parameters": {
                        "columns": {
                            "committee_id": "id",
                            "committee_body_id": "legislative_body_id",
                            "committee_name": "name",
                        }
                    },
                },
            ],
            "dataframe": None,
        },
        # {
        #     "source": "ls_bill_vote",
        #     "destination": "bill_actions",
        #     "transformations": [
        #         {
        #             "function": "keep_columns",
        #             "parameters": {
        #                 "columns": [
        #                     "bill_id",
        #                     "created",
        #                     "passed",
        #                 ]
        #             },
        #         },
        #         {
        #             "function": "rename",
        #             "parameters": {
        #                 "columns": {
        #                     "created": "date",
        #                     "passed": "type",
        #                 }
        #             },
        #         },
        #     ],
        #     "dataframe": None,
        # },
        # {
        #     "source": "ls_bill_sponsor",
        #     "destination": "bill_sponsors",
        #     "transformations": [
        #         {
        #             "function": "keep_columns",
        #             "parameters": {
        #                 "columns": ["bill_id", "people_id", "sponsor_type_id"]
        #                 ### bill_id has relationship with bill.id, which we create ??? ###
        #             },
        #         },
        #         {
        #             "function": "rename",
        #             "parameters": {"columns": {"people_id": "legislator_id"}},
        #         },
        #         {
        #             "function": "set_primary_sponsor",
        #             "parameters": {
        #                 "sponsor_type_column": "sponsor_type_id",
        #                 "is_primary_column": "is_primary"
        #             }
        #         }
        #     ],
        #     "dataframe": None,
        # },
    ]
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
