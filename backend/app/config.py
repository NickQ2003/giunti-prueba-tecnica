from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    rate_limit_requests: int = Field(default=20, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=86400)


@lru_cache
def get_settings() -> Settings:
    return Settings()
