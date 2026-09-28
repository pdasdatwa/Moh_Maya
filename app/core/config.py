from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_db: str = "mohmaya"
    postgres_user: str = "mohmaya"
    postgres_password: str = "mohmaya_dev_password"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+psycopg://mohmaya:mohmaya_dev_password@localhost:5432/mohmaya"
    )
    test_database_url: str = (
        "postgresql+psycopg://mohmaya:mohmaya_dev_password@localhost:5432/mohmaya_test"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
