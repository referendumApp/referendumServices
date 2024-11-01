import os
import logging
from typing import Optional, Union, BinaryIO
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObjectStorageClient:
    def __init__(self, storage_type: str = "local"):
        """Initialize storage client

        Args:
            storage_type: Either "s3" or "local"
        """
        self.storage_type = storage_type.lower()
        if self.storage_type == "s3":
            self._init_s3_client()
        elif self.storage_type == "local":
            self._init_local_storage()
        else:
            raise ValueError("Storage type must be either 's3' or 'local'")

    def _init_s3_client(self):
        """Initialize S3 client with credentials from environment variables."""
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not aws_access_key:
            raise ValueError("AWS_ACCESS_KEY_ID environment variable is not set")
        if not aws_secret_key:
            raise ValueError("AWS_SECRET_ACCESS_KEY environment variable is not set")

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            config=Config(connect_timeout=30, read_timeout=30, retries={"max_attempts": 3}),
        )
        logger.info(f"Successfully initialized S3 client in region {aws_region}")

    def _init_local_storage(self):
        """Initialize local storage with base directory from environment variable."""
        self.base_dir = os.getenv("LOCAL_STORAGE_PATH", "storage")
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Initialized local storage at {self.base_dir}")

    def upload_file(
        self,
        bucket: str,
        key: str,
        file_obj: Union[str, bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a file to storage.

        Args:
            bucket: Bucket name for S3 or subdirectory for local storage
            key: Object key/path
            file_obj: File object, path, or bytes to upload
            content_type: Optional MIME type of the file

        Returns:
            bool: True if upload was successful
        """
        try:
            if self.storage_type == "s3":
                extra_args = {"ContentType": content_type} if content_type else {}

                if isinstance(file_obj, (str, Path)):
                    self.s3_client.upload_file(file_obj, bucket, key, ExtraArgs=extra_args)
                else:
                    self.s3_client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)
            else:
                # For local storage, create bucket (directory) if it doesn't exist
                bucket_path = Path(self.base_dir) / bucket
                os.makedirs(bucket_path, exist_ok=True)

                file_path = bucket_path / key
                os.makedirs(file_path.parent, exist_ok=True)

                if isinstance(file_obj, (str, Path)):
                    if isinstance(file_obj, str) and not os.path.exists(file_obj):
                        # Treat as content if it's a string and not a file path
                        with open(file_path, "w") as f:
                            f.write(file_obj)
                    else:
                        # Copy file if it's a path
                        with open(file_obj, "rb") as source, open(file_path, "wb") as dest:
                            dest.write(source.read())
                elif isinstance(file_obj, bytes):
                    with open(file_path, "wb") as f:
                        f.write(file_obj)
                else:
                    with open(file_path, "wb") as f:
                        f.write(file_obj.read())

            logger.info(f"Successfully uploaded {key} to {bucket}")
            return True

        except (ClientError, IOError) as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return False

    def download_file(
        self, bucket: str, key: str, destination: Optional[str] = None
    ) -> Optional[bytes]:
        """Download a file from storage.

        Args:
            bucket: Bucket name for S3 or subdirectory for local storage
            key: Object key/path
            destination: Optional file path to save the downloaded file

        Returns:
            bytes if destination is None, else None (file is saved to destination)
        """
        try:
            if self.storage_type == "s3":
                if destination:
                    self.s3_client.download_file(bucket, key, destination)
                    return None
                else:
                    import io

                    buffer = io.BytesIO()
                    self.s3_client.download_fileobj(bucket, key, buffer)
                    return buffer.getvalue()
            else:
                file_path = Path(self.base_dir) / bucket / key
                if not file_path.exists():
                    logger.error(f"File not found: {file_path}")
                    return None

                if destination:
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    with open(file_path, "rb") as source, open(destination, "wb") as dest:
                        dest.write(source.read())
                    return None
                else:
                    with open(file_path, "rb") as f:
                        return f.read()

            logger.info(f"Successfully downloaded {key} from {bucket}")

        except (ClientError, IOError) as e:
            logger.error(f"Failed to download file: {str(e)}")
            return None

    def delete_file(self, bucket: str, key: str) -> bool:
        """Delete a file from storage.

        Args:
            bucket: Bucket name for S3 or subdirectory for local storage
            key: Object key/path

        Returns:
            bool: True if deletion was successful
        """
        try:
            if self.storage_type == "s3":
                self.s3_client.delete_object(Bucket=bucket, Key=key)
            else:
                file_path = Path(self.base_dir) / bucket / key
                if file_path.exists():
                    os.remove(file_path)

            logger.info(f"Successfully deleted {key} from {bucket}")
            return True

        except (ClientError, IOError) as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False


def create_storage_client(storage_type: str = "local") -> ObjectStorageClient:
    """Factory function to create a storage client.

    Args:
        storage_type: Either "s3" or "local"

    Returns:
        ObjectStorageClient instance
    """
    try:
        client = ObjectStorageClient(storage_type)
        logger.info(f"Successfully created {storage_type} storage client")
        return client
    except Exception as e:
        logger.error(f"Failed to create storage client: {str(e)}")
        raise
