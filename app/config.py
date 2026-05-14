from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    APP_NAME: str = "Events API"
    APP_VERSION: str = "1.0.0"
    EVENTS_FILE: str = "data/events.jsonl"
    RETENTION_DAYS: int = 500
    CLEANUP_INTERVAL_HOURS: int = 24
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()

config = get_config()