"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FOSDEM_",
    )

    # App settings
    version: str = "0.1.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_path: str = "data/fosdem.duckdb"

    # Scraper
    scrape_interval_minutes: int = 15
    fosdem_schedule_url: str = "https://fosdem.org/2026/schedule/xml"

    # FOSDEM year
    fosdem_year: int = 2026


settings = Settings()
