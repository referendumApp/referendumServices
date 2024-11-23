from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import boto3
import logging
import watchtower
from typing import Optional


class Settings(BaseSettings):
    # API
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Security
    API_ACCESS_TOKEN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SECRET_KEY: str

    # AWS
    AWS_REGION: Optional[str] = "us-east-2"
    ALPHA_BUCKET_NAME: str = "referendum-app-alpha"
    BILL_TEXT_BUCKET_NAME: str
    FEEDBACK_FILE_NAME: str = "feedback.json"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


def setup_logging() -> None:
    try:
        logs_client = boto3.client("logs", region_name=settings.AWS_REGION)
        log_group_name = "referendum-api-logs"

        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group_name=log_group_name,
            log_stream_name=f"{settings.ENVIRONMENT}-logs",
            create_log_group=True,
            boto3_client=logs_client,
        )

        # Configure root logger
        logging.basicConfig(level=settings.LOG_LEVEL)
        root_logger = logging.getLogger()
        root_logger.addHandler(cloudwatch_handler)

        # Shutdown hook to flush the handler
        import atexit

        atexit.register(cloudwatch_handler.close)

        logging.info("CloudWatch logging has been set up successfully.")

    except Exception as e:
        logging.error(f"Failed to set up CloudWatch logging: {e}")
        logging.warning("Falling back to basic logging")
        logging.basicConfig(level=settings.LOG_LEVEL)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
setup_logging()
