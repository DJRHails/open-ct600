"""Runtime configuration, read from environment variables (or a ``.env`` file)."""

from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        static_dir: A built frontend to serve alongside the API. Unset in development,
            where Vite serves the frontend and proxies ``/api``.
        hmrc_submission_enabled: Whether this deployment relays returns (and the company's
            Government Gateway credentials) to HMRC. Off by default so a public demo never
            handles Gateway passwords.
        hmrc_vendor_id: The 4-digit vendor ID HMRC's Software Developers Support Team issued
            to whoever runs this deployment; submission stays off without it.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    static_dir: Path | None = None
    hmrc_submission_enabled: bool = False
    hmrc_vendor_id: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
