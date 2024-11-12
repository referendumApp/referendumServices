from typing import Set, Dict
import logging
import requests
import re
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

    @staticmethod
    def _is_single_token(line: str) -> bool:
        tokens = [t for t in line.split() if t]
        return len(tokens) == 1

    def _is_artifact(self, line: str) -> bool:
        if self._is_single_token(line):
            return True
        artifacts = [
            r"Fmt \d+",  # Format markers
            r"Frm \d+",  # Frame markers
            r"Sfmt \d+",  # Section format markers
            r"VerDate.*",  # Version date lines
            r"HR \d+ .*",  # House resolution marker
        ]
        return any(re.search(pattern, line) for pattern in artifacts)

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing artifacts and normalizing whitespace"""
        lines = text.split("\n")
        cleaned_lines = [
            line.strip() for line in lines if line.strip() and not self._is_artifact(line)
        ]

        # Remove line numbers at the start of any remaining lines
        cleaned_lines = [re.sub(r"^\d+ ", "", line) for line in cleaned_lines]

        # Rejoin with single newlines
        return "\n".join(cleaned_lines)

    def extract_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                # Clean the text before adding
                cleaned_text = self.clean_text(text)

                # Add to text parts if not empty
                if text.strip():
                    text_parts.append(cleaned_text)

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
