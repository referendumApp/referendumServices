import logging
import json
import os
import gc
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from common.database.referendum import connection as referendum_connection
from common.database.legiscan_api import connection as legiscan_api_connection
from common.object_storage.client import ObjectStorageClient
from pipeline.bill_text_extraction import BillTextExtractor
from pipeline.etl_config import ETLConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BILL_TEXT_BUCKET_NAME = os.getenv("BILL_TEXT_BUCKET_NAME")


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


def run_text_extraction(batch_size=20):
    storage_client = ObjectStorageClient()
    referendum_db = next(get_referendum_db())
    extractor = BillTextExtractor(
        storage_client=storage_client, db_session=referendum_db, bucket_name=BILL_TEXT_BUCKET_NAME
    )

    # Get bills to process
    required_text_hash_map = extractor.get_required_bill_text_hash_map()
    logger.info(f"Found {len(required_text_hash_map)} required bill texts in database")

    # Get already processed bills
    existing_hashes = extractor.get_stored_hashes()
    logger.info(f"Found {len(existing_hashes)} existing bill texts")

    # Process missing bills
    missing_text_hash_map = {
        url_hash: url
        for url_hash, url in required_text_hash_map.items()
        if url_hash not in existing_hashes
    }
    logger.info(f"Processing {len(missing_text_hash_map)} missing bills")

    succeeded = 0
    failed = 0
    hash_map_items = list(missing_text_hash_map.items())
    total_items = len(hash_map_items)
    total_batches = (total_items + batch_size - 1) // batch_size
    progress_interval = max(1, total_batches // 10)
    logger.info(
        f"Processing {total_items} missing bills across {total_batches} batches (batch_size={batch_size})"
    )
    for i in range(0, len(hash_map_items), batch_size):
        batch = dict(hash_map_items[i : i + batch_size])
        current_batch = i // batch_size + 1
        logger.info(f"Processing batch {current_batch}/{total_batches}, size: {len(batch)}")
        for url_hash, url in batch.items():
            logger.info(f"Processing url for hash {url_hash}")
            try:
                extractor.process_bill(url_hash, url)
                succeeded += 1
            except Exception as e:
                logger.error(f"Failed to process with error: {str(e)}")
                failed += 1

        gc.collect()
        if current_batch % progress_interval == 0:
            logger.info(
                f"Progress: {current_batch}/{total_batches} batches completed ({(current_batch / total_batches * 100):.1f}%)"
            )

    logger.info(
        f"Text extraction completed. "
        f"Total Succeeded: {succeeded}, "
        f"Total Failed: {failed}, "
        f"Success Rate: {(succeeded / (succeeded + failed) * 100):.1f}%"
    )

    if failed > 0:
        raise Exception(f"Text extraction had {failed} failures")


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
