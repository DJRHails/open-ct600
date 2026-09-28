from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from open_ct600.config import Settings
from open_ct600.main import create_app

SUBMISSION = {
    "ct600": {
        "company": {
            "name": "Acme Widgets Ltd",
            "registration_number": "01234567",
            "utr": "1234567890",
        },
        "period": {"start": "2024-04-01", "end": "2025-03-31"},
        "profit_and_loss": {"turnover": 100_000},
        "tax_adjustments": {},
        "balance_sheet": {},
    },
    "declaration": {"name": "Ada Lovelace", "capacity": "director", "confirmed": True},
}


def client_for(static_dir: Path | None = None) -> TestClient:
    return TestClient(create_app(Settings(static_dir=static_dir)))


def test_health():
    with client_for() as client:
        assert client.get("/api/health").json() == {"status": "ok"}


def test_calculator():
    with client_for() as client:
        response = client.post(
            "/api/calculator",
            json={
                "period_start": "2024-04-01",
                "period_end": "2025-03-31",
                "taxable_profits": 100_000,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["tax_chargeable"] == "22750.00"
    assert body["slices"][0]["band"] == "marginal"
    assert body["payment_due"] == "2026-01-01"


def test_calculator_explains_an_invalid_period():
    with client_for() as client:
        response = client.post(
            "/api/calculator",
            json={"period_start": "2024-04-01", "period_end": "2025-12-31", "taxable_profits": 1},
        )

    assert response.status_code == 422
    assert "cannot be longer than 12 months" in response.json()["detail"][0]["msg"]


def test_compute_return():
    with client_for() as client:
        response = client.post("/api/returns/compute", json=SUBMISSION["ct600"])

    assert response.status_code == 200
    boxes = {box["number"]: box["value"] for box in response.json()["boxes"]}
    assert boxes[315] == "100000"
    assert boxes[440] == "22750.00"


def test_submit_issues_a_receipt_with_a_stable_fingerprint():
    with client_for() as client:
        first = client.post("/api/returns/submit", json=SUBMISSION)
        second = client.post("/api/returns/submit", json=SUBMISSION)

    assert first.status_code == 201
    receipt = first.json()
    assert receipt["reference"].startswith("sub_")
    assert receipt["reference"] != second.json()["reference"]
    assert receipt["fingerprint"] == second.json()["fingerprint"]
    assert receipt["signatory"] == "Ada Lovelace"
    assert receipt["computation"]["tax"]["tax_chargeable"] == "22750.00"


def test_submit_requires_the_declaration_to_be_confirmed():
    unconfirmed = {**SUBMISSION, "declaration": {**SUBMISSION["declaration"], "confirmed": False}}
    with client_for() as client:
        response = client.post("/api/returns/submit", json=unconfirmed)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "declaration", "confirmed"]


def test_serves_the_frontend_with_a_client_side_route_fallback(tmp_path: Path):
    (tmp_path / "index.html").write_text("<div id=root></div>")
    (tmp_path / "app.js").write_text("console.log(1)")

    with client_for(static_dir=tmp_path) as client:
        assert client.get("/app.js").text == "console.log(1)"
        assert client.get("/file/check-your-answers").text == "<div id=root></div>"
        assert client.get("/api/no-such-endpoint").status_code == 404
        assert client.get("/assets/missing-chunk.js").status_code == 404
        assert client.get("/api/health").json() == {"status": "ok"}


def test_refuses_to_start_without_a_built_frontend(tmp_path: Path):
    settings = Settings(static_dir=tmp_path)

    with pytest.raises(RuntimeError, match=r"no index\.html"):
        create_app(settings)
