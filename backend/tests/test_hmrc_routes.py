import base64
import threading
from pathlib import Path

import httpx2
import pytest
from fastapi.testclient import TestClient
from lxml import etree

from open_ct600.config import Settings
from open_ct600.hmrc.irmark import compute_irmark
from open_ct600.hmrc.routes import http_client, ixbrl_renderer, render_ixbrl
from open_ct600.hmrc.xmldoc import CT_NS, parse_xml
from open_ct600.main import create_app

FIXTURES = Path(__file__).parent / "fixtures/hmrc"
PASSWORD = "correct-horse-battery-staple"
CORRELATION_ID = "46DCD4CC7E194088B99857931C185829"

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
AFTER_MARCH_2026 = {
    **CT600,
    "period": {"start": "2025-05-01", "end": "2026-04-30"},
    "accounts": {**CT600["accounts"], "approval_date": "2026-06-30"},
}
DECLARATION = {"name": "Ada Lovelace", "capacity": "director", "confirmed": True}
SUBMIT = {
    "ct600": CT600,
    "declaration": DECLARATION,
    "environment": "test-in-live",
    "gateway_user_id": "123456789012",
    "gateway_password": PASSWORD,
}
UNAUTHORISED_CLAIM_PAGE = {
    "ClaimToGroupRelief": {
        "CompanyInformation": {
            "Company": [
                {"Name": "Parent Ltd", "TaxReference": "1234567891", "AmountClaimed": "1000"}
            ]
        }
    }
}
"""A group relief claim without its claim authorisation, which HMRC's rules require (9518)."""
ENABLED = Settings(hmrc_submission_enabled=True, hmrc_vendor_id="0000")


def te_reply(qualifier, function="submit", body="", errors=""):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<GovTalkMessage xmlns="http://www.govtalk.gov.uk/CM/envelope"><EnvelopeVersion>2.0</EnvelopeVersion>
<Header><MessageDetails><Class>HMRC-CT-CT600-TIL</Class><Qualifier>{qualifier}</Qualifier>
<Function>{function}</Function><CorrelationID>{CORRELATION_ID}</CorrelationID>
<ResponseEndPoint PollInterval="0"></ResponseEndPoint></MessageDetails><SenderDetails/></Header>
<GovTalkDetails><Keys/>{errors}</GovTalkDetails><Body>{body}</Body></GovTalkMessage>""".encode()


def from_hmrc(fixture):
    content = (FIXTURES / fixture).read_bytes()
    return content.replace(
        b"<CorrelationID></CorrelationID>",
        f"<CorrelationID>{CORRELATION_ID}</CorrelationID>".encode(),
    )


class StubTransactionEngine:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.messages = []

    def __call__(self, request):
        self.messages.append(request.content)
        return httpx2.Response(200, content=self.replies.pop(0))


def client_for(settings=ENABLED, *, engine=None):
    app = create_app(settings)
    if engine is not None:

        async def stub_client():
            async with httpx2.AsyncClient(transport=httpx2.MockTransport(engine)) as client:
                yield client

        app.dependency_overrides[http_client] = stub_client
    return TestClient(app)


def test_validate_accepts_a_complete_return():
    with client_for() as client:
        response = client.post("/api/returns/validate", json={"ct600": CT600})

    assert response.status_code == 200
    assert response.json() == {"valid": True, "documents_attached": True, "problems": []}


def test_validate_explains_computations_missing_after_march_2026():
    with client_for() as client:
        report = client.post("/api/returns/validate", json={"ct600": AFTER_MARCH_2026}).json()

    assert report["valid"] is False
    assert report["documents_attached"] is False
    assert sorted(problem["code"] for problem in report["problems"]) == [9316, 9965]
    for problem in report["problems"]:
        assert "computations taxonomy" in problem["message"]
        assert "2026-04-30" in problem["message"]


def test_validate_locates_problems_on_supplementary_pages():
    ct600 = {**CT600, "supplementary_pages": {"C": UNAUTHORISED_CLAIM_PAGE}}

    with client_for() as client:
        report = client.post("/api/returns/validate", json={"ct600": ct600}).json()

    problem = next(p for p in report["problems"] if p["code"] == 9518)
    assert problem["page"] == "C"
    assert problem["path"] == "/IRenvelope/CompanyTaxReturn/GroupAndConsortium/ClaimToGroupRelief"
    assert "Claim authorisation section must be completed" in problem["message"]
    main_return = next(p for p in report["problems"] if p["code"] == 9955)
    assert (main_return["page"], main_return["box"]) == (None, "310")


def test_validate_explains_accounts_that_cannot_be_tagged():
    directors = [f"Director {chr(65 + n // 26)}{chr(65 + n % 26)}" for n in range(41)]
    accounts = {**CT600["accounts"], "directors": directors, "signing_director": directors[0]}

    with client_for() as client:
        report = client.post(
            "/api/returns/validate", json={"ct600": {**CT600, "accounts": accounts}}
        ).json()

    assert sorted(problem["code"] for problem in report["problems"]) == [9113, 9315]
    for problem in report["problems"]:
        assert "at most 40 directors" in problem["message"]


def test_validate_rejects_malformed_answers():
    with client_for() as client:
        response = client.post("/api/returns/validate", json={"ct600": {**CT600, "period": {}}})

    assert response.status_code == 422


def test_download_ct600_xml():
    with client_for() as client:
        response = client.post(
            "/api/returns/ct600.xml", json={"ct600": CT600, "declaration": DECLARATION}
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="ct600-1234567890-2025-03-31.xml"'
    )
    envelope = parse_xml(response.content)
    assert envelope.tag == f"{{{CT_NS}}}IRenvelope"
    assert envelope.findtext(f".//{{{CT_NS}}}Declaration/{{{CT_NS}}}Name") == "Ada Lovelace"
    assert attachments(envelope) == {
        "Computation": ("computations.xhtml", b"ct-comp"),
        "Accounts": ("accounts.xhtml", b"frc"),
    }
    assert "x-ct600-missing-attachments" not in response.headers


def test_download_after_march_2026_leaves_out_computations_and_says_why():
    with client_for() as client:
        response = client.post("/api/returns/ct600.xml", json={"ct600": AFTER_MARCH_2026})

    assert response.status_code == 200
    assert list(attachments(parse_xml(response.content))) == ["Accounts"]
    assert response.headers["x-ct600-missing-attachments"] == "computations"
    assert "computations taxonomy" in response.headers["x-ct600-missing-reason"]


def attachments(envelope):
    """Attached iXBRL documents by kind: filename and a taxonomy marker from the document."""
    found = {}
    for document in envelope.iterfind(f".//{{{CT_NS}}}EncodedInlineXBRLDocument"):
        kind = etree.QName(document.getparent().getparent()).localname
        xhtml = base64.b64decode(document.text or "")
        marker = next(m for m in (b"ct-comp", b"frc") if m in xhtml)
        found[kind] = (document.get("Filename"), marker)
    return found


@pytest.mark.parametrize(
    "settings",
    [Settings(), Settings(hmrc_submission_enabled=True), Settings(hmrc_vendor_id="0000")],
)
def test_submission_is_off_unless_enabled_with_a_vendor_id(settings):
    engine = StubTransactionEngine()

    with client_for(settings, engine=engine) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "submission_disabled"
    assert engine.messages == []


def test_submission_after_march_2026_is_refused_before_anything_is_sent():
    engine = StubTransactionEngine()

    with client_for(engine=engine) as client:
        response = client.post(
            "/api/returns/submit-to-hmrc", json={**SUBMIT, "ct600": AFTER_MARCH_2026}
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["error"] == "ixbrl_unavailable"
    assert "computations taxonomy" in detail["message"]
    assert engine.messages == []


def test_invalid_return_is_not_sent():
    engine = StubTransactionEngine()
    claim = {"C": UNAUTHORISED_CLAIM_PAGE}
    submission = {**SUBMIT, "ct600": {**CT600, "supplementary_pages": claim}}

    with client_for(engine=engine) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=submission)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_return"
    assert [error["code"] for error in detail["errors"]] == [9955, 9518]
    assert engine.messages == []


def test_accepted_submission_returns_hmrc_receipt():
    engine = StubTransactionEngine(
        te_reply("acknowledgement"),
        from_hmrc("tpvs-success-response.xml"),
        te_reply("response", "delete"),
    )

    with client_for(engine=engine) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 200
    receipt = response.json()
    assert receipt["status"] == "accepted"
    assert receipt["environment"] == "test-in-live"
    assert receipt["correlation_id"] == CORRELATION_ID
    assert receipt["irmark_base32"] == compute_irmark(engine.messages[0]).base32
    assert receipt["receipt_xml"].startswith("<?xml")
    sent = parse_xml(engine.messages[0])
    assert sent.findtext(".//{http://www.govtalk.gov.uk/CM/envelope}Class") == "HMRC-CT-CT600-TIL"
    assert sent.findtext(".//{http://www.govtalk.gov.uk/CM/envelope}URI") == "0000"
    assert len(engine.messages) == 3


def test_rejected_submission_lists_hmrc_errors_on_the_form():
    engine = StubTransactionEngine(
        te_reply("acknowledgement"),
        from_hmrc("tpvs-business-errors-response.xml"),
        te_reply("response", "delete"),
    )

    with client_for(engine=engine) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 200
    rejection = response.json()
    assert rejection["status"] == "rejected"
    rate = rejection["errors"][0]
    assert rate["number"] == 9200
    assert rate["box"] == "340"
    assert rate["page"] is None
    assert rejection["errors"][1]["type"] == "xbrl.ixbrl.HeaderAbsent"
    assert rejection["errors"][1]["box"] is None


def test_authentication_failure_does_not_echo_the_password():
    engine = StubTransactionEngine(
        (FIXTURES / "ets-authentication-failure-response.xml").read_bytes()
    )

    with client_for(engine=engine) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "authentication_failed"
    assert response.json()["detail"]["errors"][0]["number"] == 1046
    assert PASSWORD not in response.text


def test_hmrc_unreachable_is_a_bad_gateway():
    def unreachable(request):
        raise httpx2.ConnectError("connection refused")

    with client_for(engine=unreachable) as client:
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "hmrc_error"
    assert PASSWORD not in response.text


def test_only_test_in_live_and_live_are_offered():
    with client_for(engine=StubTransactionEngine()) as client:
        response = client.post(
            "/api/returns/submit-to-hmrc", json={**SUBMIT, "environment": "tpvs"}
        )

    assert response.status_code == 422
    assert PASSWORD not in response.text


@pytest.mark.parametrize(
    ("settings", "enabled"),
    [
        (ENABLED, True),
        (Settings(), False),
        (Settings(hmrc_submission_enabled=True), False),
        (Settings(hmrc_vendor_id="0000"), False),
    ],
)
def test_submission_status_says_whether_to_ask_for_credentials(settings, enabled):
    with client_for(settings) as client:
        response = client.get("/api/submission")

    assert response.status_code == 200
    assert response.json() == {"enabled": enabled, "environments": ["test-in-live", "live"]}


def test_overlong_password_is_a_validation_error_not_a_crash():
    engine = StubTransactionEngine()
    long_password = "p" * 257

    with client_for(engine=engine) as client:
        response = client.post(
            "/api/returns/submit-to-hmrc", json={**SUBMIT, "gateway_password": long_password}
        )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "gateway_password"]
    assert long_password not in response.text
    assert engine.messages == []


def test_submission_work_runs_off_the_event_loop():
    threads = {}

    def render(ct600, computation):
        threads["render"] = threading.get_ident()
        return render_ixbrl(ct600, computation)

    class RecordingEngine(StubTransactionEngine):
        def __call__(self, request):
            threads.setdefault("event loop", threading.get_ident())
            return super().__call__(request)

    engine = RecordingEngine(
        te_reply("acknowledgement"),
        from_hmrc("tpvs-success-response.xml"),
        te_reply("response", "delete"),
    )
    with client_for(engine=engine) as client:
        client.app.dependency_overrides[ixbrl_renderer] = lambda: render
        response = client.post("/api/returns/submit-to-hmrc", json=SUBMIT)

    assert response.status_code == 200
    assert threads["render"] != threads["event loop"]
