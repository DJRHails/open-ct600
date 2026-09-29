import asyncio

import httpx2
import pytest
from companies_house_stub import COMPANY, DOCUMENT, StubCompaniesHouse, failing
from pydantic import SecretStr

from open_ct600.companies_house import client as client_module
from open_ct600.companies_house.client import (
    CACHE_SECONDS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_SECONDS,
    CompaniesHouseClient,
    CompaniesHouseUnavailableError,
    RequestLimiter,
    ResponseCache,
)

API_KEY = "placeholder-for-tests"


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def run(stub, call, cache=None, limiter=None):
    async def go():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            client = CompaniesHouseClient(
                SecretStr(API_KEY), http, cache or ResponseCache(), limiter or RequestLimiter()
            )
            return await call(client)

    return asyncio.run(go())


def test_cache_keeps_responses_for_ten_minutes():
    clock = Clock()
    cache = ResponseCache(clock)
    cache.put(("url", "json"), b"body")

    clock.now += CACHE_SECONDS
    assert cache.get(("url", "json")) == b"body"
    clock.now += 1
    assert cache.get(("url", "json")) is None


def test_cache_is_bounded(monkeypatch):
    monkeypatch.setattr(client_module, "CACHE_ENTRIES", 2)
    cache = ResponseCache()
    for name in ("a", "b", "c"):
        cache.put((name, "json"), name.encode())

    assert [cache.get((name, "json")) for name in ("a", "b", "c")] == [None, b"b", b"c"]


def test_limiter_allows_the_limit_per_window_then_refuses():
    clock = Clock()
    limiter = RequestLimiter(clock)
    for _ in range(RATE_LIMIT_REQUESTS):
        limiter.acquire()

    with pytest.raises(CompaniesHouseUnavailableError, match="Try again in a few minutes"):
        limiter.acquire()

    clock.now += RATE_LIMIT_SECONDS
    limiter.acquire()


def test_limit_stays_under_companies_houses_600_per_5_minutes():
    assert RATE_LIMIT_REQUESTS < 600
    assert RATE_LIMIT_SECONDS == 300


def test_cached_responses_do_not_count_against_the_limit():
    stub = StubCompaniesHouse()
    cache, limiter = ResponseCache(), RequestLimiter()

    for _ in range(3):
        run(stub, lambda client: client.company(COMPANY), cache, limiter)

    assert len(stub.requests) == 1


def test_transport_errors_carry_no_request():
    stub = StubCompaniesHouse()
    stub.answers[f"/company/{COMPANY}"] = failing(httpx2.ConnectError("refused"))

    with pytest.raises(CompaniesHouseUnavailableError) as raised:
        run(stub, lambda client: client.company(COMPANY))

    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None
    assert API_KEY not in str(raised.value)


def test_document_redirects_must_be_https():
    stub = StubCompaniesHouse()
    stub.answers[f"/document/{DOCUMENT}/content"] = lambda: httpx2.Response(
        302, headers={"Location": "http://example.com/doc"}
    )

    with pytest.raises(CompaniesHouseUnavailableError, match="non-HTTPS"):
        run(stub, lambda client: client.document_content(DOCUMENT, "application/xhtml+xml"))


def test_oversized_documents_are_refused(monkeypatch):
    monkeypatch.setattr(client_module, "MAX_DOCUMENT_BYTES", 1000)
    stub = StubCompaniesHouse()

    with pytest.raises(CompaniesHouseUnavailableError, match="larger than 1000 bytes"):
        run(stub, lambda client: client.document_content(DOCUMENT, "application/xhtml+xml"))
