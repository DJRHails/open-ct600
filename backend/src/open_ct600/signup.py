"""Sign-up: validate a registration and deliver it to the configured webhook.

Open CT600 keeps no user database. A registration is posted as JSON to a webhook
(https://webhook.site in the reference deployment), where the operator can read it.
Anyone holding a webhook.site URL can read what is sent to it, so the form deliberately
collects no password or other secret.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal

import httpx2 as httpx
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from open_ct600.ids import new_id

logger = logging.getLogger(__name__)


class SignupRequest(BaseModel):
    """What a person gives us when they register."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: Annotated[str, Field(min_length=1, max_length=120)]
    email: EmailStr
    company_name: Annotated[str, Field(min_length=1, max_length=160)]
    accept_terms: Literal[True]


class SignupReceipt(BaseModel):
    """Acknowledgement returned to the person who registered."""

    reference: str
    email: EmailStr


class WebhookDeliveryError(RuntimeError):
    """Raised when the sign-up webhook does not accept a registration."""


async def deliver_signup(
    request: SignupRequest, client: httpx.AsyncClient, webhook_url: str
) -> SignupReceipt:
    """Post a registration to the sign-up webhook.

    Args:
        request: The validated registration.
        client: HTTP client used to reach the webhook.
        webhook_url: Where to post the registration.

    Returns:
        A receipt carrying the registration reference.

    Raises:
        WebhookDeliveryError: If the webhook is unreachable or answers with an error.
    """
    reference = new_id("sgn")
    payload = {
        "event": "signup",
        "reference": reference,
        "received_at": datetime.now(UTC).isoformat(),
        "full_name": request.full_name,
        "email": request.email,
        "company_name": request.company_name,
    }
    try:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
    except httpx.HTTPError as error:
        # Never log the error text: it contains the webhook URL, which grants read access
        # to every sign-up.
        reason = (
            f"HTTP {error.response.status_code}"
            if isinstance(error, httpx.HTTPStatusError)
            else type(error).__name__
        )
        logger.warning("Sign-up %s was not accepted by the webhook: %s", reference, reason)
        raise WebhookDeliveryError(f"Sign-up webhook rejected {reference}: {reason}") from None
    logger.info("Sign-up %s delivered to the webhook", reference)
    return SignupReceipt(reference=reference, email=request.email)
