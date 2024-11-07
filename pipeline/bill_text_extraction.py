from typing import Optional, Set, List, Dict
import logging
import requests
import io
import pdfplumber
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

logger = logging.getLogger(__name__)


class BillTextExtractor:
    def __init__(self, storage_client, db_session, bucket_name: str):
        self.storage_client = storage_client
        self.db_session = db_session
        self.bucket_name = bucket_name

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

    def extract_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        if not text_parts:
            logger.error("No text extracted from pdf content")

        return "\n\n".join(text_parts)

    def store_text(self, text: str, file_hash: str) -> None:
        """Store extracted text in object storage"""
        text_bytes = text.encode("utf-8")
        self.storage_client.upload_file(
            bucket=self.bucket_name,
            key=f"{file_hash}.txt",
            file_obj=text_bytes,
        )

    def process_bill(self, url_hash: str, url: str):
        logger.info(f"Processing bill text for url {url}")

        pdf_content = self.download_pdf(url)
        text_content = self.extract_text(pdf_content)

        self.store_text(text_content, url_hash)
        logger.info(f"Saved bill text for url {url} at {url_hash}.txt")
