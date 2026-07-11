from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart AI Incubator V2"
    api_prefix: str = "/api"
    database_url: str = Field(default="sqlite:///./data/incubator.db")
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://netrue-smart-incubator.vercel.app",
    ]
    cors_origin_regex: str | None = r"https://.*\.vercel\.app"
    firmware_version: str = "2.0.0"
    sync_interval_seconds: int = 10
    sensor_timeout_seconds: int = 8
    relay_timeout_seconds: int = 900
    data_dir: Path = Path("data")
    upload_dir: Path = Path("uploads")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INCUBATOR_")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
