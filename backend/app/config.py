from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Biodiversity Backend"
    environment: str = "local"
    database_url: str = "sqlite+pysqlite:///./work/biodiversity_dev.db"
    upload_dir: str = "work/uploads"
    birdnet_command: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
