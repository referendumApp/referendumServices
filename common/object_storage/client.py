import os
import logging
from typing import Optional, Union, BinaryIO
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObjectStorageClient:
    def __init__(self) -> None:
        """Initialize storage client"""
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        endpoint_url = os.getenv("S3_ENDPOINT_URL")

        if not aws_access_key:
            raise ValueError("AWS_ACCESS_KEY_ID environment variable is not set")
        if not aws_secret_key:
            raise ValueError("AWS_SECRET_ACCESS_KEY environment variable is not set")

        # Configure S3 client
        config = Config(
            connect_timeout=30,
            read_timeout=30,
            retries={"max_attempts": 3},
            # Required for MinIO compatibility
            s3={"addressing_style": "path"},
        )

        client_kwargs = {
            "aws_access_key_id": aws_access_key,
            "aws_secret_access_key": aws_secret_key,
            "region_name": aws_region,
            "config": config,
        }

        # Add endpoint_url for MinIO
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            client_kwargs["verify"] = False

        self.s3_client = boto3.client("s3", **client_kwargs)

        storage_type = "MinIO" if endpoint_url else "S3"
        logger.info(f"Successfully initialized {storage_type} client")
        if endpoint_url:
            logger.info(f"Using endpoint: {endpoint_url}")

    def upload_file(
        self,
        bucket: str,
        key: str,
        file_obj: bytes,
        content_type: Optional[str] = None,
    ):
        """Upload a file to storage.

        Args:
            bucket: Bucket name
            key: Object key/path
            file_obj: Bytes to upload
            content_type: Optional MIME type of the file
        """
        try:
            extra_args = {"ContentType": content_type} if content_type else {}
            buffer = BytesIO(file_obj)
            self.s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs=extra_args)
            logger.info(f"Successfully uploaded {key} to {bucket}")
        except (ClientError, IOError) as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise

    def download_file(self, bucket: str, key: str) -> Optional[bytes]:
        """Download a file from storage.

        Args:
            bucket: Bucket name
            key: Object key/path

        Returns:
            bytes containing the file content
        """
        try:
            buffer = BytesIO()
            self.s3_client.download_fileobj(bucket, key, buffer)
            return buffer.getvalue()
        except (ClientError, IOError) as e:
            logger.error(f"Failed to download file: {str(e)}")
            return None

    def delete_file(self, bucket: str, key: str) -> bool:
        """Delete a file from storage.

        Args:
            bucket: Bucket name
            key: Object key/path

        Returns:
            bool: True if deletion was successful
        """
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Successfully deleted {key} from {bucket}")
            return True
        except (ClientError, IOError) as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False


def create_storage_client() -> ObjectStorageClient:
    """Factory function to create a storage client.

    Returns:
        ObjectStorageClient instance
    """
    try:
        client = ObjectStorageClient()
        logger.info(f"Successfully created storage client")
        return client
    except Exception as e:
        logger.error(f"Failed to create storage client: {str(e)}")
        raise
