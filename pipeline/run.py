import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.referendum import connection as referendum_connection
from database.legiscan_api import connection as legiscan_api_connection

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


def extract():
    logger.info("Starting extraction phase")
    legiscan_db = next(get_legiscan_api_db())
    if check_db_connection(legiscan_db):
        logger.info("Successfully connected to Legiscan API database")
        # Perform extraction logic here
        logger.info("Extraction completed")
    else:
        logger.error("Failed to connect to Legiscan API database. Extraction aborted.")
        raise ConnectionError("Legiscan API database connection failed")


def transform():
    logger.info("Transforming data")
    # Perform transformation logic here


def load():
    logger.info("Starting load phase")
    referendum_db = next(get_referendum_db())
    if check_db_connection(referendum_db):
        logger.info("Successfully connected to Referendum database")
        # Perform load logic here
        logger.info("Load completed")
    else:
        logger.error("Failed to connect to Referendum database. Load aborted.")
        raise ConnectionError("Referendum database connection failed")


def orchestrate_etl():
    try:
        extract()
        transform()
        load()
        logger.info("ETL process completed successfully")
    except ConnectionError as e:
        logger.error(f"ETL process failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ETL process: {str(e)}")


if __name__ == "__main__":
    orchestrate_etl()
