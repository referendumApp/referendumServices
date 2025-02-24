from typing import Set, Dict
import logging
import requests
import re
import gc
import tempfile
import PyPDF2
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

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

    @staticmethod
    def _is_single_token_no_punctuation(line: str) -> bool:
        """Check if line is a single token without any punctuation"""
        punctuation = ".,:;?!-()[]{}'/\"$%"
        tokens = [t for t in line.split() if t]

        return len(tokens) == 1 and not any(p in tokens[0] for p in punctuation)

    def _is_artifact(self, line: str) -> bool:
        if self._is_single_token_no_punctuation(line):
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

    def download_pdf_streaming(self, url: str, temp_file) -> None:
        with self.session.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    temp_file.write(chunk)
        temp_file.flush()

    def extract_text_streaming(self, pdf_path: str) -> str:
        text_parts = []

        with open(pdf_path, "rb") as file:
            pdf = PyPDF2.PdfReader(file)

            batch_size = 5
            for i in range(0, len(pdf.pages), batch_size):
                batch = pdf.pages[i : i + batch_size]
                for page in batch:
                    try:
                        page_text = page.extract_text()
                        cleaned_text = self.clean_text(page_text)
                        if cleaned_text:
                            cleaned_text.strip()
                            text_parts.append(cleaned_text)
                    except Exception as e:
                        logger.error(f"Error on page {i}: {e}")
                        continue

                gc.collect()

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

        with tempfile.NamedTemporaryFile() as temp_pdf:
            self.download_pdf_streaming(url, temp_pdf)
            text_content = self.extract_text_streaming(temp_pdf.name)

        self.store_text(text_content, url_hash)
        logger.info(f"Saved bill text for url {url} at {url_hash}.txt")
