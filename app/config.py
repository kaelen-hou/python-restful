from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "sqlite:///./tasks.db"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # Server
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit: str = "100/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
