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
CLIENT_REQUESTS = 60
"""Per client per window: about ten company lookups (each up to six requests) and searches."""
RESERVE_REQUESTS = 110
RESERVE_SHARE = 15
"""When the budget is down to its reserve, clients that have sent fewer than this still get
enough for a lookup or two."""
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
TIMEOUT = httpx2.Timeout(10.0, connect=5.0)
_REDIRECTS = frozenset({301, 302, 303, 307, 308})


class CompaniesHouseError(Exception):
    """Companies House could not answer a request."""


class CompanyNotFoundError(CompaniesHouseError):
    """Companies House has no such company (or document)."""


class CompaniesHouseUnavailableError(CompaniesHouseError):
    """Companies House is unreachable, failing, refusing our key, or we are rate limited."""


_CACHED_STATUSES = frozenset({httpx2.codes.OK, httpx2.codes.NOT_FOUND})
_BUSY = (
    "Company lookup is busy: this service has made as many requests to Companies House as it "
    "may for now. Try again in a few minutes, or enter the company's details yourself."
)
_TOO_MANY_FROM_YOU = (
    "You've looked up a lot of companies in a short time. Wait a few minutes, or enter the "
    "company's details yourself."
)


class ResponseCache:
    """Public answers (found or not found) for ``CACHE_SECONDS``, in memory, least recent evicted.

    Not-found answers are kept too, so looking up unknown numbers again costs no requests.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Create an empty cache reading time from ``clock``."""
        self._clock = clock
        self._entries: OrderedDict[tuple[str, str], tuple[float, int, bytes]] = OrderedDict()

    def get(self, key: tuple[str, str]) -> tuple[int, bytes] | None:
        """The cached status and body for ``key``, if still fresh."""
        entry = self._entries.get(key)
        if entry is None or self._clock() - entry[0] > CACHE_SECONDS:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry[1], entry[2]

    def put(self, key: tuple[str, str], status_code: int, body: bytes) -> None:
        """Keep the answer ``status_code`` with ``body`` for ``key``."""
        self._entries[key] = (self._clock(), status_code, body)
        self._entries.move_to_end(key)
        while len(self._entries) > CACHE_ENTRIES:
            self._entries.popitem(last=False)


class RequestLimiter:
    """Shares Companies House's request budget fairly between the people using this service.

    - The service sends at most ``RATE_LIMIT_REQUESTS`` per ``RATE_LIMIT_SECONDS``.
    - Each client (by IP address) may send at most ``CLIENT_REQUESTS`` of those, so one client
      can't use up the budget for everyone else.
    - Once fewer than ``RESERVE_REQUESTS`` remain, only clients that have sent fewer than
      ``RESERVE_SHARE`` get more, so the last of the budget goes to newcomers rather than to a
      few busy clients.

    Only requests actually sent count: cached answers are free. Requests over a limit fail at
    once rather than queue, so nobody waits minutes.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Create a limiter reading time from ``clock``."""
        self._clock = clock
        self._sent: deque[tuple[float, str]] = deque()
        self._sent_by: dict[str, deque[float]] = {}

    def acquire(self, requester: str) -> None:
        """Count one request sent on behalf of ``requester``.

        Raises:
            CompaniesHouseUnavailableError: If the service, or this requester, is over a limit.
        """
        now = self._clock()
        self._forget_before(now - RATE_LIMIT_SECONDS)
        mine = len(self._sent_by.get(requester, ()))
        short = len(self._sent) >= RATE_LIMIT_REQUESTS - RESERVE_REQUESTS
        if len(self._sent) >= RATE_LIMIT_REQUESTS or (short and mine >= RESERVE_SHARE):
            raise CompaniesHouseUnavailableError(_BUSY)
        if mine >= CLIENT_REQUESTS:
            raise CompaniesHouseUnavailableError(_TOO_MANY_FROM_YOU)
        self._sent.append((now, requester))
        self._sent_by.setdefault(requester, deque()).append(now)

    def _forget_before(self, cutoff: float) -> None:
        while self._sent and self._sent[0][0] <= cutoff:
            _, requester = self._sent.popleft()
            theirs = self._sent_by[requester]
            theirs.popleft()
            if not theirs:
                del self._sent_by[requester]


@dataclass(frozen=True)
class CompaniesHouseClient:
    """Reads public records from Companies House.

    Attributes:
        api_key: The Companies House API key.
        http: The HTTP client.
        cache: Shared response cache.
        limiter: Shared request limiter.
        requester: Who the requests are for (their IP address), for the limiter.
    """

    api_key: SecretStr
    http: httpx2.AsyncClient
    cache: ResponseCache
    limiter: RequestLimiter
    requester: str

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
        answer = self.cache.get((url, content_type))
        if answer is None:
            response = await self._send(url, None, content_type)
            if response.status_code in _REDIRECTS:
                response = await self._stored_document(response.headers.get("location", ""))
            answer = response.status_code, response.content
            if len(answer[1]) > MAX_DOCUMENT_BYTES:
                raise CompaniesHouseUnavailableError(
                    f"{url} is larger than {MAX_DOCUMENT_BYTES} bytes"
                )
            self._remember((url, content_type), answer)
        return self._checked(url, *answer)

    async def _json(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        key = (str(httpx2.URL(url, params=params)), "application/json")
        answer = self.cache.get(key)
        if answer is None:
            response = await self._send(url, params, "application/json")
            answer = response.status_code, response.content
            self._remember(key, answer)
        return self._parsed(url, self._checked(url, *answer))

    @staticmethod
    def _parsed(url: str, body: bytes) -> dict[str, Any]:
        """A JSON object, or unavailable (a maintenance page, say) if the body isn't one."""
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        if not isinstance(parsed, dict):
            raise CompaniesHouseUnavailableError(
                f"Companies House gave an unexpected answer for {httpx2.URL(url).path}"
            )
        return parsed

    def _remember(self, key: tuple[str, str], answer: tuple[int, bytes]) -> None:
        if answer[0] in _CACHED_STATUSES:
            self.cache.put(key, *answer)

    async def _send(self, url: str, params: dict[str, str] | None, accept: str) -> httpx2.Response:
        self.limiter.acquire(self.requester)
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
    def _checked(url: str, status_code: int, body: bytes) -> bytes:
        path = httpx2.URL(url).path
        if status_code == httpx2.codes.OK:
            return body
        if status_code == httpx2.codes.NOT_FOUND:
            raise CompanyNotFoundError(f"Companies House has nothing at {path}")
        if status_code == httpx2.codes.UNAUTHORIZED:
            raise CompaniesHouseUnavailableError(
                f"Companies House refused this service's API key ({path}): check "
                "COMPANIES_HOUSE_API_KEY"
            )
        raise CompaniesHouseUnavailableError(f"Companies House answered {status_code} for {path}")
