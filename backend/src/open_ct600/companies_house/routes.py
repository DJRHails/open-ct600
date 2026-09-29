"""Companies House lookup: ``/api/companies-house/status``, ``/search`` and ``/companies/{number}``.

Switched off (``status`` says so, the others answer 503) unless ``COMPANIES_HOUSE_API_KEY`` is
set. Responses follow ``docs/design/companies-house-prefill.md``; a missing company is a 404
and Companies House being unavailable (or this service's rate limit reached) a 503, with a
message in ``detail``.
"""

import re
from collections.abc import AsyncIterator, Coroutine
from typing import Annotated, Any

import httpx2
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel

from open_ct600.companies_house.client import (
    TIMEOUT,
    CompaniesHouseClient,
    CompaniesHouseUnavailableError,
    CompanyNotFoundError,
    RequestLimiter,
    ResponseCache,
)
from open_ct600.companies_house.records import (
    CompanyRecord,
    SearchResults,
    company_record,
    search,
)
from open_ct600.config import Settings

_COMPANY_NUMBER = re.compile(
    r"""(?x)
    ^ (?: [0-9]{1,8}           # English and Welsh companies: digits, zero-padded to eight
        | [A-Z]{2} [0-9]{6}    # prefixed numbers: SC, NI, OC, SO, ...
      ) $
    """
)


class Status(BaseModel):
    """Whether company lookup is available."""

    enabled: bool


async def companies_house_http() -> AsyncIterator[httpx2.AsyncClient]:
    """Dependency: an HTTP client for one lookup."""
    async with httpx2.AsyncClient(timeout=TIMEOUT) as client:
        yield client


def companies_house_router(settings: Settings) -> APIRouter:
    """The lookup routes, sharing one cache and one rate limiter per process."""
    router = APIRouter(prefix="/api/companies-house", tags=["companies-house"])
    cache, limiter = ResponseCache(), RequestLimiter()

    def client(
        http: Annotated[httpx2.AsyncClient, Depends(companies_house_http)],
    ) -> CompaniesHouseClient:
        if settings.companies_house_api_key is None:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Looking companies up at Companies House is switched off on this service. "
                "Enter the company's details yourself.",
            )
        return CompaniesHouseClient(settings.companies_house_api_key, http, cache, limiter)

    lookup_client = Annotated[CompaniesHouseClient, Depends(client)]

    @router.get("/status")
    def lookup_status() -> Status:
        """Say whether company lookup is available on this service."""
        return Status(enabled=settings.companies_house_api_key is not None)

    @router.get("/search")
    async def search_companies(
        companies_house: lookup_client, q: Annotated[str, Query(min_length=2, max_length=160)]
    ) -> SearchResults:
        """Find companies by name or number (at most 20)."""
        return await _answer(search(companies_house, q.strip()))

    @router.get("/companies/{number}")
    async def company(
        companies_house: lookup_client, number: Annotated[str, Path(min_length=1, max_length=16)]
    ) -> CompanyRecord:
        """A company's record: details, current directors and its latest filed accounts."""
        return await _answer(company_record(companies_house, _company_number(number)))

    return router


def _company_number(number: str) -> str:
    normalised = number.strip().upper()
    if not _COMPANY_NUMBER.fullmatch(normalised):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Enter a company number in the correct format, like 01234567 or SC123456",
        )
    return normalised.zfill(8)


async def _answer[T](lookup: Coroutine[Any, Any, T]) -> T:
    failure: HTTPException | None = None
    try:
        return await lookup
    except CompanyNotFoundError:
        failure = HTTPException(
            status.HTTP_404_NOT_FOUND, "Companies House has no company with that number"
        )
    except CompaniesHouseUnavailableError as error:
        failure = HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error))
    # Raised outside the except block, so the exception chain holds no request (or API key).
    raise failure
