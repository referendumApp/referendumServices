import logging
import json
import os
import boto3
import requests
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Set
import hashlib

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


def run_etl():
    directory = os.path.dirname(os.path.abspath(__file__))
    config_filepath = f"{directory}/etl_configs.json"

    with open(config_filepath, "r") as config_file:
        config_data = json.load(config_file)
        etl_configs = [ETLConfig(**config) for config in config_data]

    try:
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


def get_url_hash(url: str) -> str:
    """Generate a consistent hash for a URL."""
    return hashlib.sha256(url.encode()).hexdigest()


def get_s3_bill_texts() -> Set[str]:
    """Retrieve list of bill text hashes already stored in S3."""
    # TODO - renable this with local storage
    return []
    # try:
    #     s3_client = boto3.client('s3')
    #     bucket_name = os.getenv('BILL_TEXT_BUCKET', 'bill-texts')
    #
    #     # List all objects in the bucket
    #     paginator = s3_client.get_paginator('list_objects_v2')
    #     existing_hashes = set()
    #
    #     for page in paginator.paginate(Bucket=bucket_name):
    #         if 'Contents' in page:
    #             for obj in page['Contents']:
    #                 # Remove .txt extension to get hash
    #                 file_hash = os.path.splitext(obj['Key'])[0]
    #                 existing_hashes.add(file_hash)
    #
    #     return existing_hashes
    # except Exception as e:
    #     logger.error(f"Error getting S3 bill texts: {str(e)}")
    #     return set()


def extract_bill_text(url: str):
    """Extract bill text from URL and store in S3."""
    try:
        url_hash = get_url_hash(url)

        # # TODO implement local storage
        # bucket_name = os.getenv('BILL_TEXT_BUCKET', 'bill-texts')
        # s3_client = boto3.client('s3')
        #
        # # Download bill text
        # response = requests.get(url, timeout=30)
        # response.raise_for_status()
        # bill_text = response.text
        #
        # # Upload to S3
        # s3_client.put_object(
        #     Bucket=bucket_name,
        #     Key=f"{url_hash}.txt",
        #     Body=bill_text.encode('utf-8')
        # )

        logger.info(f"Successfully extracted and stored text for URL {url} at hash {url_hash}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download bill text from URL {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to process bill text for URL {url}: {str(e)}")
        return False


def run_text_extraction():
    """Run the text extraction process for all missing bill texts."""
    logger.info("Starting bill text extraction process")

    # Get all URLs from database
    referendum_db = next(get_referendum_db())
    try:
        result = referendum_db.execute(
            text("SELECT DISTINCT url FROM bill_versions WHERE url IS NOT NULL;")
        )
        urls = [row[0] for row in result]
        logger.info(f"Found {len(urls)} unique bill URLs in database")
    except Exception as e:
        logger.error(f"Failed to retrieve URLs from database: {str(e)}")
        return

    # Get existing hashes from S3
    existing_hashes = get_s3_bill_texts()
    logger.info(f"Found {len(existing_hashes)} existing bill texts in S3")

    # Find missing texts
    missing_texts = [url for url in urls if get_url_hash(url) not in existing_hashes]
    logger.info(f"Found {len(missing_texts)} missing bill texts to process")

    # Extract text from missing bills
    success_count = 0
    for url in missing_texts:
        if extract_bill_text(url):
            success_count += 1

    logger.info(
        f"Text extraction completed. Successfully processed {success_count} out of {len(missing_texts)} bills"
    )


def orchestrate():
    """Orchestrate the complete ETL and text extraction process."""
    try:
        logger.info("ETL process starting")
        run_etl()
        logger.info("Text extraction starting")
        run_text_extraction()
        logger.info("ETL orchestration completed")
    except Exception as e:
        logger.error(f"ETL orchestration failed: {str(e)}")
        raise


if __name__ == "__main__":
    orchestrate()
