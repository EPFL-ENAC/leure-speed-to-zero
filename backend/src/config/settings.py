from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PATH_PREFIX: str = "/api"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    # Default to True for production safety, explicitly disabled via Makefile in dev
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"


settings = Settings()
