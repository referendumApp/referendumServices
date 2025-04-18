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
    BILL_TEXT_BUCKET_NAME: str
    FEEDBACK_FILE_NAME: str = "feedback.json"
    FEEDBACK_BUCKET_NAME: str = "referendumapp-beta"

    # AI
    OPENAI_API_KEY: str = None
    MAX_BILL_LENGTH_WORDS: int = 10000
    MAX_MESSAGES_PER_MONTH: int = 100
    CHAT_SESSION_TIMEOUT_SECONDS: int = 3600

    # User Limits
    COMMENT_CHAR_LIMIT: int = 500

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

        # Uvicorn loggers
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_access_logger.handlers = []  # Clear existing handlers
        uvicorn_access_logger.addHandler(cloudwatch_handler)
        uvicorn_access_logger.propagate = False  # Prevent duplicate logs

        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        uvicorn_error_logger.handlers = []
        uvicorn_error_logger.addHandler(cloudwatch_handler)
        uvicorn_error_logger.propagate = False

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
