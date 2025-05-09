from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PATH_PREFIX: str = "/api"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))


settings = Settings()
