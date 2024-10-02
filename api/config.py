from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    PROJECT_NAME: str = "Referendum App"
    LOG_LEVEL: str = "INFO"

    # AWS
    AWS_REGION: str | None = "us-east-2"
    ALPHA_BUCKET_NAME: str = "referendum-app-alpha"
    FEEDBACK_FILE_NAME: str = "feedback.json"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
