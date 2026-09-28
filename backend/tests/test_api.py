import json
from pathlib import Path

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from open_ct600.config import Settings
from open_ct600.main import create_app

WEBHOOK = "https://webhook.site/00000000-0000-4000-8000-000000000000"

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

SIGNUP = {
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "company_name": "Acme Widgets Ltd",
    "accept_terms": True,
}


def client_for(handler=None, static_dir: Path | None = None) -> TestClient:
    settings = Settings(signup_webhook_url=WEBHOOK, static_dir=static_dir)
    transport = httpx.MockTransport(handler or (lambda _: httpx.Response(200)))
    return TestClient(create_app(settings, transport=transport))


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


def test_signup_is_delivered_to_the_webhook():
    delivered: list[httpx.Request] = []

    def webhook(request: httpx.Request) -> httpx.Response:
        delivered.append(request)
        return httpx.Response(200, text="ok")

    with client_for(webhook) as client:
        response = client.post("/api/signup", json=SIGNUP)

    assert response.status_code == 201
    reference = response.json()["reference"]
    assert reference.startswith("sgn_")
    [request] = delivered
    assert str(request.url) == WEBHOOK
    payload = json.loads(request.content)
    assert payload["event"] == "signup"
    assert payload["reference"] == reference
    assert payload["email"] == "ada@example.com"
    assert payload["company_name"] == "Acme Widgets Ltd"
    assert "accept_terms" not in payload


@pytest.mark.parametrize(
    ("field", "value"),
    [("email", "not-an-email"), ("accept_terms", False), ("full_name", "  ")],
)
def test_signup_rejects_invalid_details_without_calling_the_webhook(field, value):
    delivered: list[httpx.Request] = []

    def webhook(request: httpx.Request) -> httpx.Response:
        delivered.append(request)
        return httpx.Response(200)

    with client_for(webhook) as client:
        response = client.post("/api/signup", json={**SIGNUP, field: value})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]
    assert delivered == []


def test_signup_reports_a_webhook_error_without_logging_the_url(
    caplog: pytest.LogCaptureFixture,
):
    with client_for(lambda _: httpx.Response(500)) as client:
        response = client.post("/api/signup", json=SIGNUP)

    assert response.status_code == 502
    assert "could not create your account" in response.json()["detail"]
    assert "HTTP 500" in caplog.text
    assert WEBHOOK.rsplit("/", maxsplit=1)[-1] not in caplog.text


def test_signup_reports_an_unreachable_webhook():
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with client_for(unreachable) as client:
        response = client.post("/api/signup", json=SIGNUP)

    assert response.status_code == 502


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
    settings = Settings(signup_webhook_url=WEBHOOK, static_dir=tmp_path)

    with pytest.raises(RuntimeError, match=r"no index\.html"):
        create_app(settings)


def test_refuses_to_start_without_a_webhook(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.delenv("SIGNUP_WEBHOOK_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError, match="signup_webhook_url"):
        create_app()
