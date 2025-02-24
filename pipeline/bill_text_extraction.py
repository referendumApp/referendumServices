import io
from typing import Set, Dict
import logging
import requests
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

from common.object_storage.schemas import StructuredBillText
from pipeline.bill_pdf_parser import BillPDFParser

logger = logging.getLogger(__name__)


class BillTextExtractor:
    CHUNK_SIZE = 32768

    def __init__(self, storage_client, db_session, bucket_name: str):
        self.storage_client = storage_client
        self.db_session = db_session
        self.bucket_name = bucket_name
        self.session = requests.Session()

    def get_required_bill_text_hash_map(self) -> Dict:
        query = """
            SELECT hash, url
            FROM bill_versions
            WHERE url IS NOT NULL
            AND hash IS NOT NULL
        """
        result = self.db_session.execute(text(query))
        return {row[0]: row[1] for row in result}

    def get_stored_hashes(self) -> Set[str]:
        """Get set of bill text hashes already stored"""
        existing_files = self.storage_client.list_filenames(self.bucket_name)
        return {Path(filename).stem for filename in existing_files}

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True
    )
    def download_pdf(self, url: str) -> bytes:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    def store_text(self, structured_text: StructuredBillText, file_hash: str) -> None:
        """Store extracted text in object storage"""
        json_string = structured_text.model_dump_json()
        self.storage_client.upload_file(
            bucket=self.bucket_name,
            key=f"{file_hash}.json",
            file_obj=json_string.encode("utf-8"),
        )

        plain_text = structured_text.get_plain_text()
        self.storage_client.upload_file(
            bucket=self.bucket_name,
            key=f"{file_hash}.txt",
            file_obj=plain_text.encode("utf-8"),
        )

    def process_bill(self, url_hash: str, url: str):
        logger.info(f"Processing bill text for url {url}")

        pdf_bytes = self.download_pdf(url)

        parser = BillPDFParser(io.BytesIO(pdf_bytes))
        structured_text = parser.parse()

        self.store_text(structured_text, url_hash)

        logger.info(f"Saved bill text for url {url} as {url_hash}")
