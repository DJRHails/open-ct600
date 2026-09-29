"""Live checks against the real Companies House API. Opt in with ``-m companies_house_live``
and ``COMPANIES_HOUSE_API_KEY`` set; they read public records only."""

import os

import pytest
from fastapi.testclient import TestClient

from open_ct600.config import Settings
from open_ct600.main import create_app

pytestmark = pytest.mark.companies_house_live

API_KEY = os.environ.get("COMPANIES_HOUSE_API_KEY")
# Ashday (1986) Limited: its accounts to 31 March 2026 are in the bulk-file fixtures.
ASHDAY = "02014751"


@pytest.fixture
def client():
    if not API_KEY:
        pytest.skip("COMPANIES_HOUSE_API_KEY is not set")
    with TestClient(create_app(Settings(companies_house_api_key=API_KEY))) as client:
        yield client


def test_live_search(client):
    response = client.get("/api/companies-house/search", params={"q": "ashday"})

    assert response.status_code == 200
    assert ASHDAY in [item["number"] for item in response.json()["items"]]


def test_live_company_record(client):
    response = client.get(f"/api/companies-house/companies/{ASHDAY}")

    assert response.status_code == 200
    record = response.json()
    assert record["name"].startswith("ASHDAY")
    assert record["legal_form"] == "private-limited-company"
    assert record["directors"]
    assert record["accounts"]["reference_date"] == "03-31"
    previous = record["previous_accounts"]
    assert previous is not None, record["previous_accounts_unavailable"]
    assert previous["standard"] == "small"


def test_live_unknown_company(client):
    assert client.get("/api/companies-house/companies/99999998").status_code == 404
