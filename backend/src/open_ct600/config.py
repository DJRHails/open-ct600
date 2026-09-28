"""Runtime configuration, read from environment variables (or a ``.env`` file)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        static_dir: A built frontend to serve alongside the API. Unset in development,
            where Vite serves the frontend and proxies ``/api``.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    static_dir: Path | None = None
