"""The Companies House routes against a stub of the public data API and Document API."""

import base64
import logging

import httpx2
import pytest
from companies_house_stub import (
    COMPANY,
    DOCUMENT,
    StubCompaniesHouse,
    failing,
    fixture,
    json_answer,
)
from fastapi.testclient import TestClient

from open_ct600.companies_house.routes import companies_house_http
from open_ct600.config import Settings
from open_ct600.main import create_app

API_KEY = "placeholder-for-tests"
ENABLED = Settings(companies_house_api_key=API_KEY)


def client_for(stub: StubCompaniesHouse, settings: Settings = ENABLED) -> TestClient:
    app = create_app(settings)

    async def stub_http():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            yield http

    app.dependency_overrides[companies_house_http] = stub_http
    return TestClient(app)


def lookup(stub: StubCompaniesHouse, path: str, settings: Settings = ENABLED):
    with client_for(stub, settings) as client:
        return client.get(f"/api/companies-house{path}")


def test_status_says_whether_lookup_is_on():
    assert lookup(StubCompaniesHouse(), "/status").json() == {"enabled": True}
    assert lookup(StubCompaniesHouse(), "/status", Settings()).json() == {"enabled": False}


@pytest.mark.parametrize("path", ["/search?q=acme", f"/companies/{COMPANY}"])
def test_lookup_is_switched_off_without_a_key(path):
    stub = StubCompaniesHouse()

    response = lookup(stub, path, Settings())

    assert response.status_code == 503
    assert "switched off" in response.json()["detail"]
    assert stub.requests == []


def test_search():
    stub = StubCompaniesHouse()

    response = lookup(stub, "/search?q=acme widgets")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "number": "01234567",
                "name": "ACME WIDGETS LTD",
                "status": "active",
                "address": "1 High Street, Leeds, LS1 1AA",
                "incorporated_on": "2019-05-01",
            },
            {
                "number": "SC123456",
                "name": "ACME WIDGETS (NORTH) LIMITED",
                "status": "dissolved",
                "address": "2 Low Road, Glasgow, G1 1AA",
                "incorporated_on": "2001-02-03",
            },
        ]
    }
    [request] = stub.requests
    assert request.url.params["q"] == "acme widgets"
    assert request.url.params["items_per_page"] == "20"


@pytest.mark.parametrize("query", ["a", "x" * 161])
def test_search_needs_2_to_160_characters(query):
    assert lookup(StubCompaniesHouse(), f"/search?q={query}").status_code == 422


def test_company_record():
    stub = StubCompaniesHouse()

    response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    record = response.json()
    previous = record.pop("previous_accounts")
    assert record == {
        "number": "01234567",
        "name": "ACME WIDGETS LTD",
        "status": "active",
        "incorporated_on": "2019-05-01",
        "legal_form": "private-limited-company",
        "registered_office": {
            "lines": ["1 High Street", "Chapel Allerton", "Leeds", "West Yorkshire"],
            "postcode": "LS1 1AA",
        },
        "sic_codes": [
            {"code": "62020", "description": "Information technology consultancy activities"},
            {"code": "62090", "description": "Other information technology service activities"},
        ],
        "principal_activity": "Information technology consultancy activities",
        "directors": [
            {"name": "Ada Augusta Lovelace", "appointed_on": "2019-05-01"},
            {"name": "Siobhan Mary O'Brien", "appointed_on": "2024-02-01"},
        ],
        "accounts": {
            "reference_date": "03-31",
            "last_made_up_to": "2025-03-31",
            "next_period": {"start": "2025-04-01", "end": "2026-03-31"},
        },
        "suggested_period": {"start": "2025-04-01", "end": "2026-03-31", "note": None},
        "previous_accounts_unavailable": None,
    }
    assert previous["filed_on"] == "2025-11-02"
    assert previous["period"] == {"start": "2025-04-01", "end": "2026-03-31"}
    assert previous["standard"] == "small"
    assert previous["profit_and_loss"]["turnover"] == 162336
    assert previous["balance_sheet"]["net_assets"] == 280310
    assert previous["directors"][0] == "S Durbin-Wood"
    assert set(previous) == {
        "period",
        "filed_on",
        "standard",
        "dormant",
        "profit_and_loss",
        "balance_sheet",
        "average_employees",
        "directors",
        "principal_activity",
    }


def test_latest_accounts_are_the_newest_aa_filing_read_as_xhtml():
    stub = StubCompaniesHouse()

    lookup(stub, f"/companies/{COMPANY}")

    content = next(r for r in stub.requests if r.url.path.endswith("/content"))
    assert content.url.host == "document-api.company-information.service.gov.uk"
    assert content.url.path == f"/document/{DOCUMENT}/content"
    assert content.headers["accept"] == "application/xhtml+xml"
    filings = next(r for r in stub.requests if r.url.path.endswith("/filing-history"))
    assert filings.url.params["category"] == "accounts"


def test_the_api_key_goes_only_to_companies_house():
    stub = StubCompaniesHouse()

    lookup(stub, f"/companies/{COMPANY}")

    expected = "Basic " + base64.b64encode(f"{API_KEY}:".encode()).decode()
    for request in stub.requests:
        if request.url.host.endswith("company-information.service.gov.uk"):
            assert request.headers["authorization"] == expected
        else:
            assert "authorization" not in request.headers


def test_a_period_of_account_over_12_months_is_cut_to_12_with_a_note():
    stub = StubCompaniesHouse()
    profile = fixture("company-profile.json")
    profile["accounts"]["next_accounts"]["period_end_on"] = "2026-09-30"
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)

    suggested = lookup(stub, f"/companies/{COMPANY}").json()["suggested_period"]

    assert suggested["start"] == "2025-04-01"
    assert suggested["end"] == "2026-03-31"
    assert suggested["note"] == (
        "The company's period of account runs from 1 April 2025 to 30 September 2026, which "
        "is longer than 12 months. A Company Tax Return covers at most 12 months, so this one "
        "ends on 31 March 2026; the rest of the period needs a second return."
    )


def test_a_company_without_next_accounts_has_no_suggested_period():
    stub = StubCompaniesHouse()
    profile = fixture("company-profile.json")
    del profile["accounts"]["next_accounts"]
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)

    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["accounts"]["next_period"] is None
    assert record["suggested_period"] is None


@pytest.mark.parametrize(
    ("company_type", "subtype", "legal_form"),
    [
        ("ltd", None, "private-limited-company"),
        ("ltd", "community-interest-company", "community-interest-company"),
        ("private-limited-guarant-nsc", None, "private-company-limited-by-guarantee"),
        ("private-unlimited", None, "private-unlimited-company"),
        ("plc", None, "public-limited-company"),
        ("llp", None, "limited-liability-partnership"),
        ("registered-society-non-jurisdictional", None, None),
    ],
)
def test_legal_form_from_company_type(company_type, subtype, legal_form):
    stub = StubCompaniesHouse()
    profile = fixture("company-profile.json") | {"type": company_type}
    if subtype:
        profile["subtype"] = subtype
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)

    assert lookup(stub, f"/companies/{COMPANY}").json()["legal_form"] == legal_form


def with_latest_filing(**changes) -> StubCompaniesHouse:
    stub = StubCompaniesHouse()
    filings = fixture("filing-history-accounts.json")
    filings["items"][1] |= changes
    stub.answers[f"/company/{COMPANY}/filing-history"] = json_answer(filings)
    return stub


@pytest.mark.parametrize(
    ("stub", "reason"),
    [
        (
            with_latest_filing(paper_filed=True),
            "The latest accounts were filed on paper, so their figures can't be read.",
        ),
        (
            with_latest_filing(links={"self": "/company/01234567/filing-history/x"}),
            "The latest accounts aren't available to download from Companies House yet.",
        ),
    ],
    ids=["paper", "no document"],
)
def test_previous_accounts_unavailable(stub, reason):
    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == reason
    assert not any(path.endswith("/content") for path in stub.paths())


def test_pdf_only_accounts_are_unavailable():
    stub = StubCompaniesHouse()
    metadata = fixture("document-metadata.json")
    del metadata["resources"]["application/xhtml+xml"]
    stub.answers[f"/document/{DOCUMENT}"] = json_answer(metadata)

    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == (
        "The latest accounts were filed as a PDF, so their figures can't be read."
    )


def test_a_company_without_accounts_yet():
    stub = StubCompaniesHouse()
    filings = fixture("filing-history-accounts.json")
    filings["items"] = [item for item in filings["items"] if item["type"] != "AA"]
    stub.answers[f"/company/{COMPANY}/filing-history"] = json_answer(filings)

    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["previous_accounts_unavailable"] == (
        "Companies House has no accounts for this company yet."
    )


def test_unreadable_accounts_are_explained():
    stub = StubCompaniesHouse()
    stub.answers["/docs/sample"] = lambda: httpx2.Response(200, content=b"<html>not ixbrl")

    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"].startswith(
        "The latest accounts couldn't be read: the document is not valid XHTML"
    )


def test_document_api_failure_leaves_the_rest_of_the_record(caplog):
    stub = StubCompaniesHouse()
    stub.answers[f"/document/{DOCUMENT}"] = failing(httpx2.ConnectTimeout("timed out"))

    with caplog.at_level(logging.WARNING):
        response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    assert response.json()["previous_accounts_unavailable"] == (
        "Companies House couldn't provide the latest accounts just now. Try again later."
    )
    assert "ConnectTimeout" in caplog.text
    assert API_KEY not in caplog.text


def test_unknown_company_is_a_404():
    response = lookup(StubCompaniesHouse(), "/companies/09999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Companies House has no company with that number"}


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        (lambda: httpx2.Response(500), "Companies House answered 500"),
        (lambda: httpx2.Response(429), "Companies House answered 429"),
        (lambda: httpx2.Response(401), "refused this service's API key"),
        (failing(httpx2.ConnectError("refused")), "could not be reached (ConnectError"),
        (failing(httpx2.ReadTimeout("slow")), "could not be reached (ReadTimeout"),
    ],
    ids=["500", "429", "401", "connect", "timeout"],
)
def test_companies_house_unavailable_is_a_503_that_never_shows_the_key(answer, message, caplog):
    stub = StubCompaniesHouse()
    stub.answers[f"/company/{COMPANY}"] = answer

    with caplog.at_level(logging.DEBUG):
        response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 503
    assert message in response.json()["detail"]
    assert API_KEY not in response.text
    assert API_KEY not in caplog.text
    assert base64.b64encode(f"{API_KEY}:".encode()).decode() not in response.text


@pytest.mark.parametrize(
    ("number", "requested"),
    [("1234567", "01234567"), ("sc123456", "SC123456"), (" 01234567", "01234567")],
)
def test_company_numbers_are_normalised(number, requested):
    stub = StubCompaniesHouse()

    lookup(stub, f"/companies/{number}")

    assert stub.requests[0].url.path == f"/company/{requested}"


@pytest.mark.parametrize("number", ["ABC!", "12-34", "S1234567"])
def test_malformed_company_numbers_are_refused(number):
    stub = StubCompaniesHouse()

    assert lookup(stub, f"/companies/{number}").status_code == 422
    assert stub.requests == []


def test_repeat_lookups_come_from_the_cache():
    stub = StubCompaniesHouse()

    with client_for(stub) as client:
        first = client.get(f"/api/companies-house/companies/{COMPANY}").json()
        count = len(stub.requests)
        second = client.get(f"/api/companies-house/companies/{COMPANY}").json()

    assert first == second
    assert len(stub.requests) == count
