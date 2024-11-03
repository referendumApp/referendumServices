import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "StorageConfig":
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not access_key or not secret_key:
            raise ValueError("AWS credentials not found in environment variables")

        return cls(
            access_key=access_key,
            secret_key=secret_key,
            region=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        )


class ObjectStorageClient:
    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self.s3_client = self._create_client()

    def _create_client(self) -> Any:
        boto_config = Config(
            connect_timeout=self.config.timeout,
            read_timeout=self.config.timeout,
            retries={"max_attempts": self.config.max_retries},
            s3={"addressing_style": "path"},  # Required for MinIO
        )

        client_kwargs: Dict[str, Any] = {
            "aws_access_key_id": self.config.access_key,
            "aws_secret_access_key": self.config.secret_key,
            "region_name": self.config.region,
            "config": boto_config,
        }

        if self.config.endpoint_url:
            client_kwargs.update({"endpoint_url": self.config.endpoint_url, "verify": False})

        return boto3.client("s3", **client_kwargs)

    def upload_file(
        self, bucket: str, key: str, file_obj: bytes, content_type: Optional[str] = None
    ):
        extra_args = {"ContentType": content_type} if content_type else {}
        self.s3_client.upload_fileobj(BytesIO(file_obj), bucket, key, ExtraArgs=extra_args)

    def download_file(self, bucket: str, key: str) -> bytes:
        buffer = BytesIO()
        self.s3_client.download_fileobj(bucket, key, buffer)
        return buffer.getvalue()

    def delete_file(self, bucket: str, key: str):
        self.s3_client.delete_object(Bucket=bucket, Key=key)


def create_storage_client() -> ObjectStorageClient:
    return ObjectStorageClient(StorageConfig.from_env())
