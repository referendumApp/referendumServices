from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import boto3
import logging
import watchtower
import time
from typing import Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler
import structlog
from fastapi import FastAPI, Request
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


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

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_ROTATION_MAX_BYTES: int = 10_000_000  # 10MB
    LOG_BACKUP_COUNT: int = 5

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


def setup_structured_logging(settings: Settings) -> structlog.BoundLogger:
    """Set up structured logging with proper processors and formatters"""

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Add JSON formatting for production
    if settings.ENVIRONMENT != "local":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def setup_cloudwatch_logging(settings: Settings) -> None:
    """Set up CloudWatch logging with proper error handling and configuration"""
    try:
        logs_client = boto3.client("logs", region_name=settings.AWS_REGION)
        log_group_name = f"referendum-api-{settings.ENVIRONMENT}"

        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group_name=log_group_name,
            log_stream_name=f"{settings.ENVIRONMENT}-{datetime.now().strftime('%Y-%m-%d')}",
            create_log_group=True,
            boto3_client=logs_client,
            use_queues=True,  # Use async queue for better performance
            send_interval=10,  # Send logs every 10 seconds
            max_batch_count=10,  # Max number of messages per batch
        )

        cloudwatch_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
            )
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(cloudwatch_handler)

        # Configure specific loggers
        for logger_name in ["uvicorn.access", "uvicorn.error", "fastapi"]:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.addHandler(cloudwatch_handler)
            logger.propagate = False

        # Set global log level
        logging.getLogger().setLevel(settings.LOG_LEVEL)

        # Shutdown hook to flush the handler
        import atexit

        atexit.register(cloudwatch_handler.close)

        logging.info("CloudWatch logging has been set up successfully.")

    except Exception as e:
        logging.error(f"Failed to set up CloudWatch logging: {e}")
        logging.warning("Falling back to file-based logging")
        setup_file_logging(settings)


def setup_file_logging(settings: Settings) -> None:
    """Set up file-based logging as fallback"""

    # Create logs directory if it doesn't exist
    import os

    os.makedirs("logs", exist_ok=True)

    # Set up rotating file handler
    file_handler = RotatingFileHandler(
        f"logs/referendum-api-{settings.ENVIRONMENT}.log",
        maxBytes=settings.LOG_ROTATION_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(settings.LOG_LEVEL)


def setup_sentry(settings: Settings) -> None:
    """Set up Sentry for error tracking"""
    if settings.SENTRY_DSN:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above
            event_level=logging.ERROR,  # Send errors and above to Sentry
        )

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                sentry_logging,
            ],
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1 if settings.ENVIRONMENT != "production" else 0.01,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT != "production" else 0.01,
            send_default_pii=False,
        )

        logging.info("Sentry error tracking initialized successfully")


class RequestLoggingMiddleware:
    """Middleware to log all requests and responses"""

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.logger = logger

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        start_time = time.time()

        # Extract request metadata
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        user_agent = request.headers.get("User-Agent", "Unknown")

        # Bind request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_agent=user_agent,
            path=request.url.path,
            method=request.method,
        )

        # Log request
        self.logger.info(
            "request_started",
            client_ip=request.client.host if request.client else None,
            query_params=dict(request.query_params),
        )

        status_code = 500
        response_headers = {}

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers.update(message.get("headers", {}))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            self.logger.exception("unhandled_exception")
            raise
        finally:
            # Log response
            process_time = time.time() - start_time
            self.logger.info(
                "request_completed",
                status_code=status_code,
                process_time=process_time,
            )

            # Clear context
            structlog.contextvars.clear_contextvars()


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
logger = setup_structured_logging(settings)
setup_cloudwatch_logging(settings)
setup_sentry(settings)
