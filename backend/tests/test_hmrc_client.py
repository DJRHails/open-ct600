"""The Transaction Engine client against a stub TE replaying HMRC's messages.

Replies come from real TPVS/ETS responses (``fixtures/hmrc``) and the samples in HMRC's
"Transaction Engine: Document Submission Protocol" v2.0.
"""

import asyncio
import logging
from pathlib import Path

import httpx2
import pytest
from pydantic import SecretStr

from open_ct600.hmrc.client import (
    AuthenticationFailedError,
    BusinessErrors,
    IRmarkRejectedError,
    MessageRejectedError,
    PollTimeoutError,
    ProcessingFailedError,
    SubmissionTooLargeError,
    TransactionEngineClient,
    TransactionEngineError,
    TransactionEngineUnavailableError,
    UnexpectedResponseError,
)
from open_ct600.hmrc.govtalk import (
    Environment,
    GatewayCredentials,
    Receipt,
    Vendor,
    build_submission,
)
from open_ct600.hmrc.xmldoc import CT_NS, GOVTALK_NS, parse_xml

FIXTURES = Path(__file__).parent / "fixtures/hmrc"
SAMPLE = Path(__file__).resolve().parents[2] / "specs/hmrc/samples/CT600-Sample-No-attachments.xml"
PASSWORD = "correct-horse-battery-staple"
CORRELATION_ID = "46DCD4CC7E194088B99857931C185829"
LIVE_TE = "https://transaction-engine.tax.service.gov.uk"


def te_reply(qualifier, function="submit", *, endpoint="", interval=10, errors="", body=""):
    """A Transaction Engine reply shaped like the samples in the TE protocol document."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<GovTalkMessage xmlns="http://www.govtalk.gov.uk/CM/envelope">
<EnvelopeVersion>2.0</EnvelopeVersion><Header><MessageDetails><Class>HMRC-CT-CT600</Class>
<Qualifier>{qualifier}</Qualifier><Function>{function}</Function><TransactionID/>
<CorrelationID>{CORRELATION_ID}</CorrelationID>
<ResponseEndPoint PollInterval="{interval}">{endpoint}</ResponseEndPoint>
<GatewayTimestamp>2017-02-13T09:28:14.772</GatewayTimestamp></MessageDetails><SenderDetails/>
</Header><GovTalkDetails><Keys/>{errors}</GovTalkDetails><Body>{body}</Body></GovTalkMessage>
""".encode()


def gateway_error(number, text="An error", error_type="fatal"):
    return te_reply(
        "error",
        errors=f"<GovTalkErrors><Error><RaisedBy>Gateway</RaisedBy><Number>{number}</Number>"
        f"<Type>{error_type}</Type><Text>{text}</Text><Location/></Error></GovTalkErrors>",
    )


def from_hmrc(fixture):
    """A real HMRC reply, given the CorrelationID the Transaction Engine would have assigned."""
    content = (FIXTURES / fixture).read_bytes()
    empty = b"<CorrelationID></CorrelationID>"
    assert empty in content
    return content.replace(empty, f"<CorrelationID>{CORRELATION_ID}</CorrelationID>".encode())


ACK = te_reply("acknowledgement", endpoint=f"{LIVE_TE}/poll", interval=5)
DELETED = te_reply("response", "delete")
SUCCESS = from_hmrc("tpvs-success-response.xml")


class StubTransactionEngine:
    """Serves queued replies and records what the client sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, request):
        root = parse_xml(request.content)
        details = f"{{{GOVTALK_NS}}}Header/{{{GOVTALK_NS}}}MessageDetails"
        self.requests.append(
            (
                str(request.url),
                root.findtext(f"{details}/{{{GOVTALK_NS}}}Qualifier"),
                root.findtext(f"{details}/{{{GOVTALK_NS}}}Function"),
                root.findtext(f"{details}/{{{GOVTALK_NS}}}CorrelationID"),
            )
        )
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, httpx2.Response):
            return reply
        return httpx2.Response(200, content=reply, headers={"content-type": "application/xml"})

    @property
    def verbs(self):
        return [(qualifier, function) for _, qualifier, function, _ in self.requests]


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def submission(environment=Environment.LIVE):
    envelope = parse_xml(SAMPLE.read_bytes()).find(f"{{{GOVTALK_NS}}}Body/{{{CT_NS}}}IRenvelope")
    assert envelope is not None
    credentials = (
        None
        if environment is Environment.TPVS
        else GatewayCredentials(user_id="123456789012", password=SecretStr(PASSWORD))
    )
    message, _ = build_submission(
        envelope,
        environment=environment,
        vendor=Vendor(vendor_id="0000", product="open-ct600", version="0.1.0"),
        credentials=credentials,
    )
    return message


def run(stub, environment=Environment.LIVE, clock=None, max_wait=600.0):
    clock = clock or FakeClock()

    async def go():
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(stub)) as http:
            client = TransactionEngineClient(
                environment, http=http, sleep=clock.sleep, clock=clock, max_wait=max_wait
            )
            return await client.submit(submission(environment))

    return asyncio.run(go())


def test_submit_poll_receipt_delete():
    stub = StubTransactionEngine(ACK, ACK, SUCCESS, DELETED)
    clock = FakeClock()

    outcome = run(stub, clock=clock)

    assert isinstance(outcome, Receipt)
    assert outcome.irmark == "YrgW02ybxWOff7gHrELynhp1gRw="
    assert outcome.correlation_id == CORRELATION_ID
    assert clock.sleeps == [5, 5]
    assert stub.verbs == [
        ("request", "submit"),
        ("poll", "submit"),
        ("poll", "submit"),
        ("request", "delete"),
    ]
    assert stub.requests[0][0] == f"{LIVE_TE}/submission"
    assert stub.requests[1][0] == f"{LIVE_TE}/poll"
    assert stub.requests[3][0] == f"{LIVE_TE}/submission"
    assert {request[3] for request in stub.requests[1:]} == {CORRELATION_ID}


def test_acknowledgement_without_endpoint_polls_the_service_poll_url():
    stub = StubTransactionEngine(te_reply("acknowledgement"), SUCCESS, DELETED)

    run(stub, environment=Environment.ETS)

    assert stub.requests[1][0] == "https://test-transaction-engine.tax.service.gov.uk/poll"


def test_business_errors_are_returned_and_deleted():
    stub = StubTransactionEngine(ACK, from_hmrc("tpvs-business-errors-response.xml"), DELETED)

    outcome = run(stub)

    assert isinstance(outcome, BusinessErrors)
    assert outcome.correlation_id == CORRELATION_ID
    assert [error.number for error in outcome.errors][:2] == [9200, 0]
    assert len(outcome.errors) == 7
    assert stub.verbs[-1] == ("request", "delete")


def test_authentication_failure_leaks_no_password(caplog):
    stub = StubTransactionEngine(
        (FIXTURES / "ets-authentication-failure-response.xml").read_bytes()
    )

    with caplog.at_level(logging.DEBUG), pytest.raises(AuthenticationFailedError) as raised:
        run(stub, environment=Environment.ETS)

    assert raised.value.errors[0].number == 1046
    assert raised.value.correlation_id == ""
    assert stub.verbs == [("request", "submit")]
    for text in (str(raised.value), repr(raised.value), repr(raised.value.args), caplog.text):
        assert PASSWORD not in text
    assert raised.value.__cause__ is None


def test_transport_failure_leaks_no_password(caplog):
    stub = StubTransactionEngine(httpx2.ConnectError("connection refused"))

    with caplog.at_level(logging.DEBUG), pytest.raises(TransactionEngineUnavailableError) as raised:
        run(stub)

    assert "may or may not have been sent" in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__
    for text in (str(raised.value), repr(raised.value.args), caplog.text):
        assert PASSWORD not in text


@pytest.mark.parametrize(
    ("reply", "error"),
    [
        (gateway_error(1002, "Authentication Failure"), AuthenticationFailedError),
        (
            gateway_error(1001, "Failed to validate against the GovTalk schema"),
            MessageRejectedError,
        ),
        (gateway_error(1020, "CorrelationID is reserved"), MessageRejectedError),
        (
            gateway_error(2001, "The document exceeds the maximum permitted size"),
            SubmissionTooLargeError,
        ),
        (gateway_error(1000, "System failure"), ProcessingFailedError),
    ],
)
def test_submission_errors(reply, error):
    stub = StubTransactionEngine(reply, DELETED)

    with pytest.raises(error) as raised:
        run(stub)

    assert raised.value.errors[0].text in str(raised.value)


def test_irmark_rejection():
    stub = StubTransactionEngine(ACK, from_hmrc("tpvs-irmark-incorrect-response.xml"), DELETED)

    with pytest.raises(IRmarkRejectedError, match="2021: The supplied IRmark is incorrect"):
        run(stub)

    assert stub.verbs[-1] == ("request", "delete")


def test_fatal_error_after_polling_is_deleted():
    fatal = te_reply(
        "error",
        errors="<GovTalkErrors><Error><RaisedBy>Department</RaisedBy><Number>3000</Number>"
        "<Type>fatal</Type><Text>The processing of your document failed</Text></Error>"
        "</GovTalkErrors>",
    )
    stub = StubTransactionEngine(ACK, fatal, DELETED)

    with pytest.raises(ProcessingFailedError) as raised:
        run(stub)

    assert raised.value.correlation_id == CORRELATION_ID
    assert stub.verbs[-1] == ("request", "delete")


def test_attachments_over_25_mb():
    too_large = te_reply(
        "error",
        errors="<GovTalkErrors><Error><RaisedBy>ChRIS</RaisedBy><Number>3001</Number>"
        "<Type>business</Type><Text>See below</Text></Error></GovTalkErrors>",
        body='<ErrorResponse xmlns="http://www.govtalk.gov.uk/CM/errorresponse" '
        'SchemaVersion="2.0"><Error><RaisedBy>ChRIS</RaisedBy><Number>1614</Number>'
        "<Type>business</Type><Text>Too large</Text></Error></ErrorResponse>",
    )
    stub = StubTransactionEngine(ACK, too_large, DELETED)

    with pytest.raises(SubmissionTooLargeError):
        run(stub)


def test_poll_timeout_names_the_correlation_id():
    stub = StubTransactionEngine(*[ACK] * 5)

    with pytest.raises(PollTimeoutError) as raised:
        run(stub, max_wait=12)

    assert raised.value.correlation_id == CORRELATION_ID
    assert CORRELATION_ID in str(raised.value)
    assert stub.verbs == [("request", "submit"), ("poll", "submit"), ("poll", "submit")]


def test_failed_delete_still_returns_the_receipt(caplog):
    stub = StubTransactionEngine(ACK, SUCCESS, gateway_error(1000, "System failure"))

    with caplog.at_level(logging.WARNING):
        outcome = run(stub)

    assert isinstance(outcome, Receipt)
    assert CORRELATION_ID in caplog.text


def test_delete_of_an_already_deleted_submission_is_quiet(caplog):
    stub = StubTransactionEngine(ACK, SUCCESS, gateway_error(2000, "Not found"))

    with caplog.at_level(logging.WARNING):
        run(stub)

    assert caplog.text == ""


def test_tpvs_is_synchronous():
    stub = StubTransactionEngine((FIXTURES / "tpvs-success-response.xml").read_bytes())

    outcome = run(stub, environment=Environment.TPVS)

    assert isinstance(outcome, Receipt)
    assert stub.verbs == [("request", "submit")]
    assert stub.requests[0][0] == "https://www.tpvs.hmrc.gov.uk/HMRC/CT600"


AKAMAI_403 = httpx2.Response(
    403,
    content=(FIXTURES / "tpvs-akamai-access-denied.html").read_bytes(),
    headers={"content-type": "text/html"},
)


def test_tpvs_retries_once_after_akamai_403():
    stub = StubTransactionEngine(AKAMAI_403, (FIXTURES / "tpvs-success-response.xml").read_bytes())

    assert isinstance(run(stub, environment=Environment.TPVS), Receipt)
    assert len(stub.requests) == 2


def test_repeated_403_is_reported():
    stub = StubTransactionEngine(AKAMAI_403, AKAMAI_403)

    with pytest.raises(UnexpectedResponseError, match="HTTP 403"):
        run(stub, environment=Environment.TPVS)


def test_non_govtalk_reply_is_reported():
    stub = StubTransactionEngine(b"<html><body>Service unavailable</body></html>")

    with pytest.raises(UnexpectedResponseError, match="not understood"):
        run(stub)


def test_all_errors_share_a_base_class():
    for error in (
        AuthenticationFailedError,
        MessageRejectedError,
        SubmissionTooLargeError,
        IRmarkRejectedError,
        ProcessingFailedError,
        PollTimeoutError,
        UnexpectedResponseError,
        TransactionEngineUnavailableError,
    ):
        assert issubclass(error, TransactionEngineError)
