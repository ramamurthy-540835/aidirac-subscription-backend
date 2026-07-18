from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIDIRAC Subscription Backend"
    app_env: str = "local"
    database_backend: str = "sqlalchemy"
    database_url: str = "sqlite:///./aidirac_subscription.db"
    gcp_project_id: str | None = None
    bigquery_dataset: str = "aidirac_subscription"
    bigquery_location: str = "US"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
