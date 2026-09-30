"""Runtime configuration, read from environment variables (or a ``.env`` file)."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr
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
        companies_house_api_key: A Companies House public data API key. Looking companies
            up is switched off without it.
        trusted_proxies: How many reverse proxies in front of this service append to
            ``X-Forwarded-For``. Per-client limits (on Companies House lookups) then take the
            client's address from that header, as the last proxy's peer; with 0 (the
            default) the header is ignored, since anyone can send it, and the connection's
            address is used. If uvicorn already rewrites the client address
            (``FORWARDED_ALLOW_IPS``), leave this at 0.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    static_dir: Path | None = None
    hmrc_submission_enabled: bool = False
    hmrc_vendor_id: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    companies_house_api_key: Annotated[SecretStr, Field(min_length=1)] | None = None
    trusted_proxies: Annotated[int, Field(ge=0, le=10)] = 0
