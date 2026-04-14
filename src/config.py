"""Application configuration."""

import logging
import sys
from importlib.metadata import version as _pkg_version

from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_VERSION = _pkg_version("fosdem-atlas")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FOSDEM_",
    )

    # App settings
    debug: bool = False

    @property
    def version(self) -> str:
        return _APP_VERSION

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


def configure_logging() -> None:
    """Configure stdlib logging with a level derived from settings.debug."""
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
