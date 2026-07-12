from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart AI Incubator V2"
    api_prefix: str = "/api"
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "INCUBATOR_DATABASE_URL"),
    )
    db_host: str | None = Field(default=None, validation_alias=AliasChoices("DB_HOST", "INCUBATOR_DB_HOST"))
    db_port: int = Field(default=3306, validation_alias=AliasChoices("DB_PORT", "INCUBATOR_DB_PORT"))
    db_name: str | None = Field(default=None, validation_alias=AliasChoices("DB_NAME", "INCUBATOR_DB_NAME"))
    db_user: str | None = Field(default=None, validation_alias=AliasChoices("DB_USER", "INCUBATOR_DB_USER"))
    db_password: str | None = Field(default=None, validation_alias=AliasChoices("DB_PASSWORD", "INCUBATOR_DB_PASSWORD"))
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

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env", "../.env"), env_prefix="", extra="ignore")

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if self.database_url:
            return self
        missing = [value for value in (self.db_host, self.db_name, self.db_user) if not value]
        if missing:
            return self
        user = quote_plus(self.db_user or "")
        password = quote_plus(self.db_password or "")
        auth = f"{user}:{password}@" if password else f"{user}@"
        self.database_url = f"mysql+pymysql://{auth}{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
