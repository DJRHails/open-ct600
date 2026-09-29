from typing import Any

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from open_ct600.config import Settings
from open_ct600.main import create_app

RETURN: dict[str, Any] = {
    "company": {
        "name": "Acme Widgets Ltd",
        "registration_number": "01234567",
        "utr": "1234567890",
        "principal_activity": "Manufacture of widgets",
    },
    "period": {"start": "2024-04-01", "end": "2025-03-31"},
    "profit_and_loss": {"turnover": 100_000},
    "tax_adjustments": {},
    "balance_sheet": {"current_assets": 100, "called_up_share_capital": 100},
    "accounts": {
        "standard": "micro",
        "approval_date": "2025-06-30",
        "directors": ["Ada Lovelace"],
        "signing_director": "Ada Lovelace",
        "average_employees": 1,
        "trading_status": "trading",
    },
}


@pytest.fixture
def client():
    with TestClient(create_app(Settings(static_dir=None))) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("path", "filename", "concept"),
    [
        ("accounts.xhtml", "01234567-accounts-2025-03-31.xhtml", "core:TurnoverRevenue"),
        ("computations.xhtml", "01234567-computations-2025-03-31.xhtml", "ct-comp:TaxPayable"),
    ],
)
def test_downloads_ixbrl(client, path, filename, concept):
    response = client.post(f"/api/returns/{path}", json={"ct600": RETURN})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xhtml+xml"
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'
    root = etree.fromstring(response.content)
    names = {element.get("name") for element in root.iter("{*}nonFraction")}
    assert concept in names


def test_computations_for_periods_without_a_taxonomy_are_unprocessable(client):
    late = {
        **RETURN,
        "period": {"start": "2025-05-01", "end": "2026-04-30"},
        "accounts": {**RETURN["accounts"], "approval_date": "2026-06-30"},
    }

    response = client.post("/api/returns/computations.xhtml", json={"ct600": late})

    assert response.status_code == 422
    assert "31 March 2026" in response.json()["detail"]
    assert client.post("/api/returns/accounts.xhtml", json={"ct600": late}).status_code == 200


def test_invalid_returns_are_rejected(client):
    body = {"ct600": {**RETURN, "accounts": {}}}

    response = client.post("/api/returns/accounts.xhtml", json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("path", ["accounts.xhtml", "computations.xhtml", "ct600.xml", "validate"])
def test_every_return_route_takes_the_same_body(client, path):
    declaration = {"name": "Ada Lovelace", "capacity": "director", "confirmed": True}

    assert client.post(f"/api/returns/{path}", json={"ct600": RETURN}).status_code == 200
    body = {"ct600": RETURN, "declaration": declaration}
    assert client.post(f"/api/returns/{path}", json=body).status_code == 200
    assert client.post(f"/api/returns/{path}", json=RETURN).status_code == 422
