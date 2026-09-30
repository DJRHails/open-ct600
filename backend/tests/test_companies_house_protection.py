"""No client can use up the shared Companies House budget or the service's memory.

Review round 2: 550 lookups of unknown company numbers from one address used to lock every user
out for five minutes; documents were read whole before their size was checked; and the cache
was bounded only by its number of entries.
"""

import asyncio

import httpx2
import pytest
from companies_house_stub import ACCOUNTS_XHTML, COMPANY, DOCUMENT, StubCompaniesHouse
from fastapi.testclient import TestClient
from pydantic import SecretStr

from open_ct600.companies_house import client as client_module
from open_ct600.companies_house.client import (
    CACHE_SECONDS,
    CLIENT_REQUESTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_SECONDS,
    RESERVE_REQUESTS,
    RESERVE_SHARE,
    CompaniesHouseClient,
    CompaniesHouseUnavailableError,
    CompanyNotFoundError,
    RequestLimiter,
    ResponseCache,
)
from open_ct600.companies_house.routes import companies_house_http
from open_ct600.config import Settings
from open_ct600.main import create_app

API_KEY = "placeholder-for-tests"


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_each_client_has_a_budget_well_below_the_shared_one():
    assert CLIENT_REQUESTS * 5 <= RATE_LIMIT_REQUESTS
    limiter = RequestLimiter(Clock())
    for _ in range(CLIENT_REQUESTS):
        limiter.acquire("203.0.113.1")

    with pytest.raises(CompaniesHouseUnavailableError, match="You've looked up a lot"):
        limiter.acquire("203.0.113.1")
    limiter.acquire("203.0.113.2")


def test_a_clients_budget_comes_back_after_the_window():
    clock = Clock()
    limiter = RequestLimiter(clock)
    for _ in range(CLIENT_REQUESTS):
        limiter.acquire("203.0.113.1")

    clock.now += RATE_LIMIT_SECONDS
    limiter.acquire("203.0.113.1")


def test_the_reserve_keeps_the_last_of_the_shared_budget_for_newcomers():
    limiter = RequestLimiter(Clock())
    busy = RATE_LIMIT_REQUESTS - RESERVE_REQUESTS
    clients = [f"198.51.100.{n}" for n in range(busy // CLIENT_REQUESTS + 1)]
    used = 0
    for client in clients:
        for _ in range(min(CLIENT_REQUESTS, busy - used)):
            limiter.acquire(client)
            used += 1

    with pytest.raises(CompaniesHouseUnavailableError, match="busy"):
        limiter.acquire(clients[0])  # has used its share and more, and the budget is short
    for _ in range(RESERVE_SHARE):
        limiter.acquire("192.0.2.7")  # a newcomer still gets a lookup's worth
    with pytest.raises(CompaniesHouseUnavailableError, match="busy"):
        limiter.acquire("192.0.2.7")


def test_the_shared_budget_is_never_exceeded():
    limiter = RequestLimiter(Clock())
    served = 0
    for n in range(RATE_LIMIT_REQUESTS * 2):
        try:
            limiter.acquire(f"client-{n}")
            served += 1
        except CompaniesHouseUnavailableError:
            pass

    assert served == RATE_LIMIT_REQUESTS


def run(stub, call, cache=None, limiter=None):
    async def go():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            client = CompaniesHouseClient(
                SecretStr(API_KEY),
                http,
                cache or ResponseCache(),
                limiter or RequestLimiter(),
                requester="203.0.113.1",
            )
            return await call(client)

    return asyncio.run(go())


def test_not_found_answers_are_cached_too():
    stub = StubCompaniesHouse()
    cache = ResponseCache()

    for _ in range(3):
        with pytest.raises(CompanyNotFoundError):
            run(stub, lambda client: client.company("09999999"), cache)

    assert len(stub.requests) == 1


def app_for(stub: StubCompaniesHouse, settings: Settings):
    app = create_app(settings)

    async def stub_http():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            yield http

    app.dependency_overrides[companies_house_http] = stub_http
    return app


def test_one_address_looking_up_unknown_numbers_cannot_lock_others_out():
    stub = StubCompaniesHouse()
    app = app_for(stub, Settings(companies_house_api_key=API_KEY))
    attacker = TestClient(app, client=("203.0.113.9", 5000))
    user = TestClient(app, client=("192.0.2.10", 5000))

    statuses = [
        attacker.get(f"/api/companies-house/companies/{n:08d}").status_code
        for n in range(90000000, 90000000 + RATE_LIMIT_REQUESTS)
    ]

    assert statuses.count(404) == CLIENT_REQUESTS
    refused = attacker.get("/api/companies-house/companies/90999999")
    assert refused.status_code == 503
    assert "You've looked up a lot of companies" in refused.json()["detail"]
    assert user.get(f"/api/companies-house/companies/{COMPANY}").status_code == 200
    assert user.get("/api/companies-house/search", params={"q": "acme"}).status_code == 200


def test_forwarded_for_is_ignored_unless_a_proxy_is_trusted():
    stub = StubCompaniesHouse()
    app = app_for(stub, Settings(companies_house_api_key=API_KEY))
    client = TestClient(app, client=("203.0.113.9", 5000))

    for n in range(CLIENT_REQUESTS):
        headers = {"X-Forwarded-For": f"10.0.0.{n}"}  # spoofed: each claims a new address
        client.get(f"/api/companies-house/companies/{90000000 + n:08d}", headers=headers)

    assert client.get("/api/companies-house/companies/90999999").status_code == 503


def test_a_trusted_proxys_forwarded_for_names_the_client():
    stub = StubCompaniesHouse()
    app = app_for(stub, Settings(companies_house_api_key=API_KEY, trusted_proxies=1))
    proxy = TestClient(app, client=("10.0.0.1", 5000))

    for n in range(CLIENT_REQUESTS):
        proxy.get(
            f"/api/companies-house/companies/{90000000 + n:08d}",
            headers={"X-Forwarded-For": "spoofed, 203.0.113.9"},
        )

    blocked = proxy.get(
        "/api/companies-house/companies/90999999", headers={"X-Forwarded-For": "203.0.113.9"}
    )
    other = proxy.get(
        f"/api/companies-house/companies/{COMPANY}", headers={"X-Forwarded-For": "192.0.2.10"}
    )
    assert blocked.status_code == 503
    assert other.status_code == 200


def test_documents_are_refused_as_soon_as_they_pass_the_cap(monkeypatch):
    monkeypatch.setattr(client_module, "MAX_DOCUMENT_BYTES", 10_000)
    chunks_sent = 0

    async def endless():
        nonlocal chunks_sent
        while True:
            chunks_sent += 1
            yield b"x" * 1_000

    stub = StubCompaniesHouse()
    stub.answers["/docs/sample"] = lambda: httpx2.Response(200, content=endless())

    with pytest.raises(CompaniesHouseUnavailableError, match="larger than 10000 bytes"):
        run(stub, lambda client: client.document_content(DOCUMENT, "application/xhtml+xml"))
    assert chunks_sent <= 12


def test_answers_from_companies_house_are_capped_too(monkeypatch):
    monkeypatch.setattr(client_module, "MAX_DOCUMENT_BYTES", 10_000)
    stub = StubCompaniesHouse()
    stub.answers[f"/company/{COMPANY}"] = lambda: httpx2.Response(200, content=b"x" * 20_000)

    with pytest.raises(CompaniesHouseUnavailableError, match="larger than 10000 bytes"):
        run(stub, lambda client: client.company(COMPANY))


def test_documents_under_the_cap_are_read_whole():
    stub = StubCompaniesHouse()

    body = run(stub, lambda client: client.document_content(DOCUMENT, "application/xhtml+xml"))

    assert body == ACCOUNTS_XHTML


def test_cache_is_bounded_by_bytes(monkeypatch):
    monkeypatch.setattr(client_module, "CACHE_BYTES", 2_500)
    cache = ResponseCache()
    for name in ("a", "b", "c"):
        cache.put((name, "doc"), 200, name.encode() * 1_000)

    assert cache.get(("a", "doc")) is None
    assert cache.get(("b", "doc")) == (200, b"b" * 1_000)
    assert cache.get(("c", "doc")) == (200, b"c" * 1_000)
    assert cache.size_in_bytes() == 2_000


def test_an_answer_bigger_than_the_cache_is_not_kept(monkeypatch):
    monkeypatch.setattr(client_module, "CACHE_BYTES", 2_500)
    cache = ResponseCache()
    cache.put(("small", "doc"), 200, b"s" * 100)
    cache.put(("big", "doc"), 200, b"b" * 3_000)

    assert cache.get(("big", "doc")) is None
    assert cache.get(("small", "doc")) == (200, b"s" * 100)
    assert cache.size_in_bytes() == 100


def test_the_cache_frees_expired_answers_before_evicting_fresh_ones(monkeypatch):
    monkeypatch.setattr(client_module, "CACHE_BYTES", 2_500)
    clock = Clock()
    cache = ResponseCache(clock)
    cache.put(("old", "doc"), 200, b"o" * 1_000)
    clock.now += CACHE_SECONDS + 1
    cache.put(("fresh", "doc"), 200, b"f" * 1_000)

    assert cache.size_in_bytes() == 1_000


def test_replacing_an_entry_counts_its_bytes_once():
    cache = ResponseCache()
    cache.put(("a", "doc"), 200, b"a" * 1_000)
    cache.put(("a", "doc"), 200, b"a" * 500)

    assert cache.size_in_bytes() == 500
