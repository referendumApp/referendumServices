from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    API_ACCESS_TOKEN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    PROJECT_NAME: str = "Referendum App"
    LOG_LEVEL: str = "INFO"

    # AWS
    AWS_REGION: str | None = "us-east-2"
    ALPHA_BUCKET_NAME: str = "referendum-app-alpha"
    FEEDBACK_FILE_NAME: str = "feedback.json"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
