import os
import json
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecretsManagerClient:
    def __init__(self) -> None:
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.secret_key = os.getenv("AWS_SECRET_KEY")

        if not self.access_key or not self.secret_key:
            raise ValueError("AWS credentials not found in environment variables")

        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("SECRETS_MANAGER_ENDPOINT_URL")
        self.timeout = 30
        self.max_retries = 3

        self.secrets_client = self._create_client()

    def _create_client(self) -> Any:
        boto_config = Config(
            connect_timeout=self.timeout,
            read_timeout=self.timeout,
            retries={"max_attempts": self.max_retries},
        )

        client_kwargs: Dict[str, Any] = {
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "region_name": self.region,
            "config": boto_config,
        }

        if self.endpoint_url:
            client_kwargs.update({"endpoint_url": self.endpoint_url, "verify": False})

        return boto3.client("secretsmanager", **client_kwargs)

    def check_connection(self):
        """Test connection by listing secrets (limited to 1 result)"""
        try:
            self.secrets_client.list_secrets(MaxResults=1)
            logger.info("Successfully connected to AWS Secrets Manager")
        except ClientError as e:
            logger.error(f"Failed to connect to AWS Secrets Manager: {e}")
            raise

    def create_secret(self, name: str, secret_value: str, description: Optional[str] = None) -> str:
        """Create a new secret"""
        try:
            kwargs = {
                "Name": name,
                "SecretString": secret_value,
            }
            if description:
                kwargs["Description"] = description

            response = self.secrets_client.create_secret(**kwargs)
            logger.info(f"Successfully created secret: {name}")
            return response["ARN"]
        except ClientError as e:
            logger.error(f"Failed to create secret {name}: {e}")
            raise

    def get_secret(self, secret_name: str) -> str:
        """Retrieve a secret value"""
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def get_secret_json(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret value and parse as JSON"""
        try:
            secret_string = self.get_secret(secret_name)
            return json.loads(secret_string)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret {secret_name} as JSON: {e}")
            raise
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def update_secret(self, secret_name: str, secret_value: str) -> str:
        """Update an existing secret"""
        try:
            response = self.secrets_client.update_secret(
                SecretId=secret_name, SecretString=secret_value
            )
            logger.info(f"Successfully updated secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            logger.error(f"Failed to update secret {secret_name}: {e}")
            raise

    def delete_secret(self, secret_name: str, force_delete: bool = False) -> str:
        """Delete a secret (with optional immediate deletion)"""
        try:
            kwargs = {"SecretId": secret_name}
            if force_delete:
                kwargs["ForceDeleteWithoutRecovery"] = True

            response = self.secrets_client.delete_secret(**kwargs)
            action = "immediately deleted" if force_delete else "scheduled for deletion"
            logger.info(f"Successfully {action} secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            logger.error(f"Failed to delete secret {secret_name}: {e}")
            raise

    def list_secrets(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all secrets, optionally filtered by name prefix"""
        try:
            secrets = []
            paginator = self.secrets_client.get_paginator("list_secrets")

            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    if prefix is None or secret["Name"].startswith(prefix):
                        secrets.append(
                            {
                                "Name": secret["Name"],
                                "ARN": secret["ARN"],
                                "Description": secret.get("Description", ""),
                                "CreatedDate": secret.get("CreatedDate"),
                                "LastChangedDate": secret.get("LastChangedDate"),
                            }
                        )

            return secrets
        except ClientError as e:
            logger.error(f"Failed to list secrets: {e}")
            raise

    def secret_exists(self, secret_name: str) -> bool:
        """Check if a secret exists"""
        try:
            self.secrets_client.describe_secret(SecretId=secret_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            logger.error(f"Error checking if secret {secret_name} exists: {e}")
            raise
