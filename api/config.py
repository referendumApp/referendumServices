from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import boto3
import logging
import watchtower


class Settings(BaseSettings):
    # API
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Security
    API_ACCESS_TOKEN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str

    # AWS
    AWS_REGION: str | None = "us-east-2"
    ALPHA_BUCKET_NAME: str = "referendum-app-alpha"
    FEEDBACK_FILE_NAME: str = "feedback.json"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


def setup_logging():
    try:
        # Create the CloudWatch handler
        logs_client = boto3.client("logs", region_name=settings.AWS_REGION)
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=f"{settings.PROJECT_NAME}-logs",
            stream_name=f"{settings.ENVIRONMENT}-logs",
            use_queues=False,
            create_log_group=False,
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
        print(f"Failed to set up CloudWatch logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=settings.LOG_LEVEL)
        logging.warning(
            "Falling back to basic logging due to CloudWatch setup failure."
        )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
setup_logging()
