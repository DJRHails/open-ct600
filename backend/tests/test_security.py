"""Security properties of the API as a whole (review .data/review/security.md)."""

import json

import pytest
from fastapi.testclient import TestClient

from open_ct600.config import Settings
from open_ct600.main import create_app

PASSWORD = "correct-horse-battery-staple"
CT600 = {
    "company": {
        "name": "Acme Widgets Ltd",
        "registration_number": "01234567",
        "utr": "1234567890",
        "principal_activity": "Manufacture of widgets",
    },
    "period": {"start": "2024-04-01", "end": "2025-03-31"},
    "profit_and_loss": {"turnover": 100_000, "staff_costs": 40_000},
    "tax_adjustments": {},
    "balance_sheet": {"current_assets": 20_000},
    "accounts": {
        "standard": "micro",
        "approval_date": "2025-06-30",
        "directors": ["Ada Lovelace"],
        "signing_director": "Ada Lovelace",
        "average_employees": 1,
        "trading_status": "trading",
    },
}
SUBMIT = {
    "ct600": CT600,
    "declaration": {"name": "Ada Lovelace", "capacity": "director", "confirmed": True},
    "environment": "test-in-live",
    "gateway_user_id": "123456789012",
    "gateway_password": PASSWORD,
}
ENABLED = Settings(hmrc_submission_enabled=True, hmrc_vendor_id="0000")


def client_for(settings=ENABLED):
    return TestClient(create_app(settings))


@pytest.mark.parametrize(
    "request_body",
    [
        {key: value for key, value in SUBMIT.items() if key != "declaration"},
        {key: value for key, value in SUBMIT.items() if key != "environment"},
        {**SUBMIT, "gateway_password": 12345},
        {**SUBMIT, "declaration": {**SUBMIT["declaration"], "confirmed": False}},
    ],
    ids=["missing declaration", "missing environment", "password not a string", "unconfirmed"],
)
@pytest.mark.parametrize("settings", [ENABLED, Settings()], ids=["enabled", "disabled"])
def test_validation_errors_never_echo_the_request(request_body, settings):
    with client_for(settings) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=request_body)

    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert "12345" not in response.text
    for problem in response.json()["detail"]:
        assert set(problem) <= {"loc", "msg", "type", "ctx"}
        assert problem["loc"][0] == "body"


def test_validation_errors_keep_what_the_frontend_reads():
    ct600 = {**CT600, "company": {**CT600["company"], "utr": "123"}}

    with client_for() as client:
        response = client.post("/api/returns/compute", json=ct600)

    [problem] = response.json()["detail"]
    assert problem["loc"] == ["body", "company", "utr"]
    assert problem["msg"].startswith("Value error, Enter a Unique Taxpayer Reference")
    assert problem["type"] == "value_error"
    assert "ctx" not in problem


def test_validation_errors_keep_the_box_of_a_page_answer():
    ct600 = {**CT600, "supplementary_pages": {"A": {"BeforeEndPeriod": "maybe"}}}

    with client_for() as client:
        response = client.post("/api/returns/compute", json=ct600)

    problem = response.json()["detail"][0]
    assert problem["ctx"] == {"box": "A5"}
    assert "maybe" not in response.text


def test_oversized_request_body_is_refused_by_declared_length():
    body = b'{"padding": "' + b"x" * (2 * 1024 * 1024) + b'"}'

    with client_for() as client:
        response = client.post(
            "/api/returns/validate", content=body, headers={"content-type": "application/json"}
        )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_oversized_streamed_request_body_is_refused():
    def chunks():
        yield b'{"padding": "'
        for _ in range(3):
            yield b"x" * (1024 * 1024)
        yield b'"}'

    with client_for() as client:
        response = client.post(
            "/api/returns/validate", content=chunks(), headers={"content-type": "application/json"}
        )

    assert response.status_code == 413


def test_ordinary_request_body_is_accepted():
    with client_for() as client:
        response = client.post("/api/returns/compute", json=CT600)

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/health"), ("post", "/api/returns/compute"), ("get", "/api/missing")],
)
def test_every_response_carries_security_headers(method, path):
    with client_for() as client:
        response = client.request(method, path, json={})

    policy = response.headers["content-security-policy"]
    assert "default-src 'self'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    assert "base-uri 'self'" in policy
    assert "form-action 'self'" in policy
    assert "unsafe-inline" not in policy
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_static_pages_carry_security_headers(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Open CT600</title>")

    with client_for(Settings(static_dir=tmp_path)) as client:
        response = client.get("/file/company-details")

    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def with_answer(section, field, value):
    return {**CT600, section: {**CT600[section], field: value}}


@pytest.mark.parametrize(
    ("path", "body", "location"),
    [
        (
            "/api/returns/validate",
            {"ct600": with_answer("company", "name", "Acme\x01 Ltd")},
            ["body", "ct600", "company", "name"],
        ),
        (
            "/api/returns/ct600.xml",
            {"ct600": with_answer("accounts", "directors", ["Ada Lovelace", "Charles\x0bBabbage"])},
            ["body", "ct600", "accounts", "directors"],
        ),
        (
            "/api/returns/accounts.xhtml",
            {"ct600": with_answer("company", "principal_activity", "Widgets\x00")},
            ["body", "ct600", "company", "principal_activity"],
        ),
        (
            "/api/returns/validate",
            {
                "ct600": {
                    **CT600,
                    "supplementary_pages": {
                        "J": {
                            "AvoidanceSchemes": [
                                {
                                    "ReferenceNumber": "1234\x1f5678",
                                    "AccountingPeriod": "2025-03-31",
                                }
                            ]
                        }
                    },
                }
            },
            ["body", "ct600", "supplementary_pages"],
        ),
        (
            "/api/returns/submit-to-hmrc",
            {**SUBMIT, "gateway_user_id": "user\x07"},
            ["body", "gateway_user_id"],
        ),
        (
            "/api/returns/submit-to-hmrc",
            {**SUBMIT, "gateway_password": PASSWORD + "\x1b"},
            ["body", "gateway_password"],
        ),
        (
            "/api/returns/submit-to-hmrc",
            {**SUBMIT, "declaration": {**SUBMIT["declaration"], "name": "Ada\x02"}},
            ["body", "declaration", "name"],
        ),
    ],
)
def test_control_characters_are_a_validation_error_not_a_crash(path, body, location):
    with client_for() as client:
        response = client.post(path, json=body)

    assert response.status_code == 422
    assert location in [problem["loc"][: len(location)] for problem in response.json()["detail"]]
    assert PASSWORD not in response.text


def test_unpaired_surrogates_are_a_validation_error():
    body = '{"ct600": ' + json.dumps(CT600).replace("Acme Widgets", "Acme \\ud800") + "}"

    with client_for() as client:
        response = client.post(
            "/api/returns/validate", content=body, headers={"content-type": "application/json"}
        )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "ct600", "company", "name"]


def test_tabs_and_line_breaks_are_still_accepted():
    ct600 = with_answer("company", "principal_activity", "Widgets\tand\ngadgets")

    with client_for() as client:
        response = client.post("/api/returns/compute", json=ct600)

    assert response.status_code == 200
