"""Companies House public data API and Document API client, with a cache and a rate limit.

The API key is sent as HTTP basic auth and nowhere else: errors name the path and status only,
are raised outside ``except`` blocks (so no exception context holds the request and its
``Authorization`` header), and the document redirect to storage is followed without it.
"""

import json
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx2
from pydantic import SecretStr

PUBLIC_DATA_API = "https://api.company-information.service.gov.uk"
DOCUMENT_API = "https://document-api.company-information.service.gov.uk"
CACHE_SECONDS = 600.0
CACHE_ENTRIES = 2_000
RATE_LIMIT_REQUESTS = 550
RATE_LIMIT_SECONDS = 300.0
"""Stay under Companies House's 600 requests per 5 minutes per key, with room to spare."""
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
TIMEOUT = httpx2.Timeout(10.0, connect=5.0)
_REDIRECTS = frozenset({301, 302, 303, 307, 308})


class CompaniesHouseError(Exception):
    """Companies House could not answer a request."""


class CompanyNotFoundError(CompaniesHouseError):
    """Companies House has no such company (or document)."""


class CompaniesHouseUnavailableError(CompaniesHouseError):
    """Companies House is unreachable, failing, refusing our key, or we are rate limited."""


class ResponseCache:
    """Successful public responses for ``CACHE_SECONDS``, in memory only, least recent evicted."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Create an empty cache reading time from ``clock``."""
        self._clock = clock
        self._entries: OrderedDict[tuple[str, str], tuple[float, bytes]] = OrderedDict()

    def get(self, key: tuple[str, str]) -> bytes | None:
        """The cached body for ``key``, if still fresh."""
        entry = self._entries.get(key)
        if entry is None or self._clock() - entry[0] > CACHE_SECONDS:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry[1]

    def put(self, key: tuple[str, str], body: bytes) -> None:
        """Keep ``body`` for ``key``."""
        self._entries[key] = (self._clock(), body)
        self._entries.move_to_end(key)
        while len(self._entries) > CACHE_ENTRIES:
            self._entries.popitem(last=False)


class RequestLimiter:
    """At most ``RATE_LIMIT_REQUESTS`` requests to Companies House per ``RATE_LIMIT_SECONDS``.

    Requests over the limit fail at once rather than queue, so nobody waits minutes.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Create a limiter reading time from ``clock``."""
        self._clock = clock
        self._sent: deque[float] = deque()

    def acquire(self) -> None:
        """Count one request.

        Raises:
            CompaniesHouseUnavailableError: If the limit has been reached.
        """
        now = self._clock()
        while self._sent and now - self._sent[0] >= RATE_LIMIT_SECONDS:
            self._sent.popleft()
        if len(self._sent) >= RATE_LIMIT_REQUESTS:
            raise CompaniesHouseUnavailableError(
                "This service has made as many requests to Companies House as it may for now. "
                "Try again in a few minutes, or enter the company's details yourself."
            )
        self._sent.append(now)


@dataclass(frozen=True)
class CompaniesHouseClient:
    """Reads public records from Companies House.

    Attributes:
        api_key: The Companies House API key.
        http: The HTTP client.
        cache: Shared response cache.
        limiter: Shared request limiter.
    """

    api_key: SecretStr
    http: httpx2.AsyncClient
    cache: ResponseCache
    limiter: RequestLimiter

    async def search(self, query: str, limit: int) -> dict[str, Any]:
        """Search companies by name or number (``GET /search/companies``)."""
        return await self._json(
            f"{PUBLIC_DATA_API}/search/companies", {"q": query, "items_per_page": str(limit)}
        )

    async def company(self, number: str) -> dict[str, Any]:
        """The company profile (``GET /company/{number}``)."""
        return await self._json(f"{PUBLIC_DATA_API}/company/{number}")

    async def officers(self, number: str) -> dict[str, Any]:
        """The company's officers, current first (``GET /company/{number}/officers``)."""
        return await self._json(
            f"{PUBLIC_DATA_API}/company/{number}/officers",
            {"items_per_page": "100", "order_by": "appointed_on"},
        )

    async def accounts_filings(self, number: str) -> dict[str, Any]:
        """Accounts filings, newest first (``GET /company/{number}/filing-history``)."""
        return await self._json(
            f"{PUBLIC_DATA_API}/company/{number}/filing-history",
            {"category": "accounts", "items_per_page": "25"},
        )

    async def document_metadata(self, document_id: str) -> dict[str, Any]:
        """A filed document's metadata (``GET /document/{id}``)."""
        return await self._json(f"{DOCUMENT_API}/document/{document_id}")

    async def document_content(self, document_id: str, content_type: str) -> bytes:
        """A filed document in ``content_type`` (``GET /document/{id}/content``).

        Companies House answers with a redirect to its storage, which is fetched without the
        API key.
        """
        url = f"{DOCUMENT_API}/document/{document_id}/content"
        cached = self.cache.get((url, content_type))
        if cached is not None:
            return cached
        response = await self._send(url, None, content_type)
        if response.status_code in _REDIRECTS:
            response = await self._stored_document(response.headers.get("location", ""))
        body = self._checked(url, response).content
        if len(body) > MAX_DOCUMENT_BYTES:
            raise CompaniesHouseUnavailableError(f"{url} is larger than {MAX_DOCUMENT_BYTES} bytes")
        self.cache.put((url, content_type), body)
        return body

    async def _json(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        key = (str(httpx2.URL(url, params=params)), "application/json")
        body = self.cache.get(key)
        if body is None:
            body = self._checked(url, await self._send(url, params, "application/json")).content
            self.cache.put(key, body)
        return json.loads(body)

    async def _send(self, url: str, params: dict[str, str] | None, accept: str) -> httpx2.Response:
        self.limiter.acquire()
        failure: str | None = None
        try:
            return await self.http.get(
                url,
                params=params,
                headers={"Accept": accept},
                auth=httpx2.BasicAuth(self.api_key.get_secret_value(), ""),
                timeout=TIMEOUT,
            )
        except httpx2.HTTPError as error:
            failure = f"{type(error).__name__} reaching {httpx2.URL(url).path}"
        raise CompaniesHouseUnavailableError(f"Companies House could not be reached ({failure})")

    async def _stored_document(self, location: str) -> httpx2.Response:
        if not location.startswith("https://"):
            raise CompaniesHouseUnavailableError("Companies House redirected to a non-HTTPS URL")
        failure: str | None = None
        try:
            return await self.http.get(location, timeout=TIMEOUT)
        except httpx2.HTTPError as error:
            failure = type(error).__name__
        raise CompaniesHouseUnavailableError(f"The document store could not be reached ({failure})")

    @staticmethod
    def _checked(url: str, response: httpx2.Response) -> httpx2.Response:
        path = httpx2.URL(url).path
        if response.status_code == httpx2.codes.OK:
            return response
        if response.status_code == httpx2.codes.NOT_FOUND:
            raise CompanyNotFoundError(f"Companies House has nothing at {path}")
        if response.status_code == httpx2.codes.UNAUTHORIZED:
            raise CompaniesHouseUnavailableError(
                f"Companies House refused this service's API key ({path}): check "
                "COMPANIES_HOUSE_API_KEY"
            )
        raise CompaniesHouseUnavailableError(
            f"Companies House answered {response.status_code} for {path}"
        )
