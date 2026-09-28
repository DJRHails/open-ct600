"""Runtime configuration, read from environment variables (or a ``.env`` file)."""

from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        signup_webhook_url: Where sign-up registrations are delivered, for example a
            https://webhook.site/<token> URL. Required: the app will not start without it.
        webhook_timeout_seconds: How long to wait for the webhook to accept a sign-up.
        static_dir: A built frontend to serve alongside the API. Unset in development,
            where Vite serves the frontend and proxies ``/api``.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    signup_webhook_url: HttpUrl
    webhook_timeout_seconds: float = 10.0
    static_dir: Path | None = None
