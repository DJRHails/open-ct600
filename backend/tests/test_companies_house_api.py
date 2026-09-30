"""The Companies House routes against a stub of the public data API and Document API."""

import base64
import logging
from datetime import date
from typing import Any, get_args

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

from open_ct600.companies_house.routes import companies_house_http, current_date
from open_ct600.config import Settings
from open_ct600.ct600 import LegalForm
from open_ct600.main import create_app

API_KEY = "placeholder-for-tests"
ENABLED = Settings(companies_house_api_key=API_KEY)
TODAY = date(2027, 5, 1)
"""In the fixture, the period to 31 March 2027 has ended and its accounts aren't filed yet."""


def client_for(
    stub: StubCompaniesHouse, settings: Settings = ENABLED, today: date = TODAY
) -> TestClient:
    app = create_app(settings)

    async def stub_http():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            yield http

    app.dependency_overrides[companies_house_http] = stub_http
    app.dependency_overrides[current_date] = lambda: today
    return TestClient(app)


def lookup(stub: StubCompaniesHouse, path: str, settings: Settings = ENABLED, today: date = TODAY):
    with client_for(stub, settings, today) as client:
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
            "last_made_up_to": "2026-03-31",
            "next_period": {"start": "2026-04-01", "end": "2027-03-31"},
        },
        "suggested_period": {"start": "2026-04-01", "end": "2027-03-31", "note": None},
        "previous_accounts_unavailable": None,
    }
    assert previous["filed_on"] == "2026-09-20"
    assert previous["period"] == {"start": "2025-04-01", "end": "2026-03-31"}
    assert previous["standard"] == "small"
    assert previous["profit_and_loss"]["turnover"] == 162336
    # The frontend copies these into Comparatives.tax_on_profit and average_employees.
    assert previous["profit_and_loss"]["tax"] == 7208
    assert previous["average_employees"] == 0
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


def company(
    *,
    incorporated: str = "2019-05-01",
    last: tuple[str, str] | None,
    next_period: tuple[str, str] | None,
    filings: list[tuple[str, str]],
) -> StubCompaniesHouse:
    """A stub whose profile has these periods and whose accounts filings are ``(made up to,
    document id)``, newest first; the documents all hold the real filing to 31 March 2026."""
    stub = StubCompaniesHouse()
    profile: dict[str, Any] = fixture("company-profile.json")
    profile["date_of_creation"] = incorporated
    accounts = profile["accounts"]
    for key, period in (("last_accounts", last), ("next_accounts", next_period)):
        if period is None:
            del accounts[key]
        else:
            accounts[key] |= {"period_start_on": period[0], "period_end_on": period[1]}
    if last is not None:
        accounts["last_accounts"]["made_up_to"] = last[1]
    history = fixture("filing-history-accounts.json")
    template = history["items"][1]
    history["items"] = [
        template
        | {
            "description_values": {"made_up_date": made_up},
            "links": {"document_metadata": f"https://example/document/{document}"},
        }
        for made_up, document in filings
    ]
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)
    stub.answers[f"/company/{COMPANY}/filing-history"] = json_answer(history)
    for _, document in filings:
        stub.answers[f"/document/{document}"] = stub.answers[f"/document/{DOCUMENT}"]
        stub.answers[f"/document/{document}/content"] = stub.answers[
            f"/document/{DOCUMENT}/content"
        ]
    return stub


NEWER = "bmV3ZXJhY2NvdW50czIwMjc"
OLDER = "b2xkZXJhY2NvdW50czIwMjQ"


def test_accounts_due_but_not_filed_suggests_that_period_with_the_latest_as_comparatives():
    record = lookup(StubCompaniesHouse(), f"/companies/{COMPANY}", today=date(2027, 5, 1)).json()

    assert record["suggested_period"] == {"start": "2026-04-01", "end": "2027-03-31", "note": None}
    assert record["previous_accounts"]["period"] == {"start": "2025-04-01", "end": "2026-03-31"}


def test_accounts_filed_while_the_next_period_runs_suggests_the_filed_period():
    stub = company(
        last=("2026-04-01", "2027-03-31"),
        next_period=("2027-04-01", "2028-03-31"),
        filings=[("2027-03-31", NEWER), ("2026-03-31", DOCUMENT)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2027, 10, 1)).json()

    assert record["suggested_period"] == {"start": "2026-04-01", "end": "2027-03-31", "note": None}
    assert record["previous_accounts"]["period"] == {"start": "2025-04-01", "end": "2026-03-31"}
    assert not any(NEWER in path for path in stub.paths())


def test_the_period_being_returned_is_never_its_own_comparatives():
    stub = company(
        last=("2025-04-01", "2026-03-31"),
        next_period=("2026-04-01", "2027-03-31"),
        filings=[("2026-03-31", DOCUMENT)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2026, 9, 29)).json()

    assert record["suggested_period"] == {"start": "2025-04-01", "end": "2026-03-31", "note": None}
    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == (
        "Companies House has no accounts made up to 31 March 2025, the day before this period "
        "starts."
    )
    assert not any(path.startswith("/document") for path in stub.paths())


def test_a_first_period_still_running_has_nothing_to_suggest():
    stub = company(
        incorporated="2026-05-01", last=None, next_period=("2026-05-01", "2027-10-31"), filings=[]
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2027, 5, 1)).json()

    assert record["suggested_period"] is None
    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == (
        "Companies House has no accounts for this company yet."
    )


def test_a_first_period_of_18_months_filed_is_cut_to_12_without_comparatives():
    stub = company(
        incorporated="2025-05-01",
        last=("2025-05-01", "2026-10-31"),
        next_period=("2026-11-01", "2027-10-31"),
        filings=[("2026-10-31", NEWER)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2027, 5, 1)).json()

    assert record["suggested_period"] == {
        "start": "2025-05-01",
        "end": "2026-04-30",
        "note": (
            "The company's period of account runs from 1 May 2025 to 31 October 2026, which "
            "is longer than 12 months. A Company Tax Return covers at most 12 months, so this "
            "one ends on 30 April 2026; the rest of the period needs a second return."
        ),
    }
    assert record["previous_accounts_unavailable"] == (
        "This is the company's first period of account, so there are no previous figures."
    )


def test_a_first_period_ended_but_not_filed_has_no_comparatives():
    stub = company(
        incorporated="2025-05-01", last=None, next_period=("2025-05-01", "2026-05-31"), filings=[]
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2027, 5, 1)).json()

    assert record["suggested_period"]["start"] == "2025-05-01"
    assert record["suggested_period"]["end"] == "2026-04-30"
    assert record["previous_accounts_unavailable"] == (
        "This is the company's first period of account, so there are no previous figures."
    )


def test_an_extended_period_after_a_change_of_reference_date_is_cut_to_12_months():
    stub = company(
        last=("2025-04-01", "2026-03-31"),
        next_period=("2026-04-01", "2027-09-30"),
        filings=[("2026-03-31", DOCUMENT)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2027, 10, 15)).json()

    assert record["suggested_period"] == {
        "start": "2026-04-01",
        "end": "2027-03-31",
        "note": (
            "The company's period of account runs from 1 April 2026 to 30 September 2027, which "
            "is longer than 12 months. A Company Tax Return covers at most 12 months, so this "
            "one ends on 31 March 2027; the rest of the period needs a second return."
        ),
    }
    assert record["previous_accounts"]["period"]["end"] == "2026-03-31"


def test_a_shortened_period_takes_the_accounts_made_up_to_the_day_before():
    stub = company(
        last=("2025-04-01", "2025-12-31"),
        next_period=("2026-01-01", "2026-12-31"),
        filings=[("2025-12-31", NEWER), ("2025-03-31", OLDER)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2026, 9, 29)).json()

    assert record["suggested_period"] == {"start": "2025-04-01", "end": "2025-12-31", "note": None}
    assert not any(NEWER in path for path in stub.paths())
    assert any(OLDER in path for path in stub.paths())


def test_overdue_accounts_suggest_the_earliest_period_not_filed():
    stub = company(
        last=("2023-04-01", "2024-03-31"),
        next_period=("2024-04-01", "2025-03-31"),
        filings=[("2024-03-31", OLDER)],
    )

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2026, 9, 29)).json()

    assert record["suggested_period"] == {"start": "2024-04-01", "end": "2025-03-31", "note": None}
    # The stub's document is the filing to 31 March 2026, so it can't be these comparatives.
    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == (
        "The previous period's accounts give their period as 1 April 2025 to 31 March 2026, "
        "but Companies House has them made up to 31 March 2024, so their figures can't be used."
    )


def test_the_filed_periods_start_comes_from_the_filing_before_when_not_given():
    stub = company(
        last=("2025-04-01", "2026-03-31"),
        next_period=("2026-04-01", "2027-03-31"),
        filings=[("2026-03-31", NEWER), ("2025-03-31", OLDER)],
    )
    profile = fixture("company-profile.json")
    del profile["accounts"]["last_accounts"]["period_start_on"]
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)

    record = lookup(stub, f"/companies/{COMPANY}", today=date(2026, 9, 29)).json()

    assert record["suggested_period"] == {"start": "2025-04-01", "end": "2026-03-31", "note": None}


def test_a_company_without_periods_has_nothing_to_suggest():
    stub = company(last=None, next_period=None, filings=[("2026-03-31", DOCUMENT)])

    record = lookup(stub, f"/companies/{COMPANY}").json()

    assert record["accounts"]["next_period"] is None
    assert record["suggested_period"] is None
    assert record["previous_accounts_unavailable"] == (
        "Companies House doesn't show a period of account that has ended, so there's no "
        "previous period to take figures from."
    )


@pytest.mark.parametrize(
    "change",
    [{"description_values": {}}, {"date": "unknown"}, {"description_values": "2026-03-31"}],
    ids=["no made-up date", "bad filing date", "malformed values"],
)
def test_accounts_filings_without_usable_dates_are_skipped(change, caplog):
    stub = with_latest_filing(**change)

    with caplog.at_level(logging.WARNING):
        response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    assert response.json()["previous_accounts_unavailable"] == (
        "Companies House has no accounts made up to 31 March 2026, the day before this period "
        "starts."
    )
    assert "Skipped accounts filing" in caplog.text


CIC = "community-interest-company"


@pytest.mark.parametrize(
    ("company_type", "extra", "legal_form"),
    [
        ("ltd", {}, "private-limited-company"),
        ("private-limited-shares-section-30-exemption", {}, "private-limited-company"),
        ("private-limited-guarant-nsc", {}, "private-company-limited-by-guarantee"),
        (
            "private-limited-guarant-nsc-limited-exemption",
            {},
            "private-company-limited-by-guarantee",
        ),
        ("private-unlimited", {}, "private-unlimited-company"),
        ("private-unlimited-nsc", {}, "private-unlimited-company"),
        ("ltd", {"subtype": CIC}, CIC),
        ("private-limited-guarant-nsc", {"subtype": CIC}, CIC),
        ("ltd", {"is_community_interest_company": True}, CIC),
        (CIC, {}, CIC),
        ("plc", {}, None),
        ("llp", {}, None),
        ("plc", {"subtype": CIC}, None),
        ("registered-society-non-jurisdictional", {}, None),
    ],
)
def test_legal_form_uses_the_models_values(company_type, extra, legal_form):
    stub = StubCompaniesHouse()
    profile = fixture("company-profile.json") | {"type": company_type} | extra
    stub.answers[f"/company/{COMPANY}"] = json_answer(profile)

    assert lookup(stub, f"/companies/{COMPANY}").json()["legal_form"] == legal_form
    assert legal_form is None or legal_form in get_args(LegalForm)


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
            "The previous period's accounts were filed on paper, so their figures can't be read.",
        ),
        (
            with_latest_filing(links={"self": "/company/01234567/filing-history/x"}),
            "The previous period's accounts aren't available to download from Companies House yet.",
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
        "The previous period's accounts were filed as a PDF, so their figures can't be read."
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
        "The previous period's accounts couldn't be read: the document is not valid XHTML"
    )


def test_document_api_failure_leaves_the_rest_of_the_record(caplog):
    stub = StubCompaniesHouse()
    stub.answers[f"/document/{DOCUMENT}"] = failing(httpx2.ConnectTimeout("timed out"))

    with caplog.at_level(logging.WARNING):
        response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    assert response.json()["previous_accounts_unavailable"] == (
        "Companies House couldn't provide the previous period's accounts just now. Try again later."
    )
    assert "ConnectTimeout" in caplog.text
    assert API_KEY not in caplog.text


def test_unknown_company_is_a_404():
    response = lookup(StubCompaniesHouse(), "/companies/09999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Companies House has no company with that number"}


NOT_FOUND = json_answer({"errors": [{"error": "not-found"}]}, status=404)


@pytest.mark.parametrize(
    "answer",
    [NOT_FOUND, lambda: httpx2.Response(500), failing(httpx2.ConnectError("refused"))],
    ids=["404", "500", "connect"],
)
def test_officers_failing_still_gives_the_record_without_directors(answer, caplog):
    stub = StubCompaniesHouse()
    stub.answers[f"/company/{COMPANY}/officers"] = answer

    with caplog.at_level(logging.DEBUG):
        response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    record = response.json()
    assert record["name"] == "ACME WIDGETS LTD"
    assert record["directors"] == []
    assert record["previous_accounts"] is not None
    assert "officers" in caplog.text
    assert API_KEY not in caplog.text


@pytest.mark.parametrize(
    "answer",
    [NOT_FOUND, lambda: httpx2.Response(500), failing(httpx2.ConnectError("refused"))],
    ids=["404", "500", "connect"],
)
def test_filing_history_failing_still_gives_the_record_without_previous_accounts(answer):
    stub = StubCompaniesHouse()
    stub.answers[f"/company/{COMPANY}/filing-history"] = answer

    response = lookup(stub, f"/companies/{COMPANY}")

    assert response.status_code == 200
    record = response.json()
    assert record["name"] == "ACME WIDGETS LTD"
    assert len(record["directors"]) == 2
    assert record["previous_accounts"] is None
    assert record["previous_accounts_unavailable"] == (
        "Companies House couldn't provide the previous period's accounts just now. Try again later."
    )


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
