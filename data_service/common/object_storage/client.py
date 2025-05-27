import os
import logging
from typing import Optional, Dict, Any, List
from io import BytesIO
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self) -> None:
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")

        if not self.access_key or not self.secret_key:
            raise ValueError("AWS credentials not found in environment variables")

        self.region = os.getenv("AWS_REGION", "us-east-2")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")
        self.timeout = 30
        self.max_retries = 3

        self.s3_client = self._create_client()

    def _create_client(self) -> Any:
        boto_config = Config(
            connect_timeout=self.timeout,
            read_timeout=self.timeout,
            retries={"max_attempts": self.max_retries},
        )

        if self.endpoint_url and "localstack" in self.endpoint_url:
            boto_config.s3 = {"addressing_style": "path"}

        client_kwargs: Dict[str, Any] = {
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "region_name": self.region,
            "config": boto_config,
        }

        if self.endpoint_url:
            client_kwargs.update({"endpoint_url": self.endpoint_url, "verify": False})

        return boto3.client("s3", **client_kwargs)

    def check_connection(self, bucket: str):
        self.s3_client.head_bucket(Bucket=bucket)

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

    def list_filenames(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        params = {"Bucket": bucket}
        if prefix:
            params["Prefix"] = prefix

        filenames = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(**params):
            if "Contents" in page:
                filenames.extend(obj["Key"] for obj in page["Contents"])

        return filenames
