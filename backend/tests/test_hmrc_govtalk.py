from datetime import datetime
from pathlib import Path

import pytest
from pydantic import SecretStr

from open_ct600.hmrc.govtalk import (
    Acknowledgement,
    DeleteConfirmation,
    Environment,
    ErrorReport,
    GatewayCredentials,
    MessageBuildError,
    Receipt,
    UnexpectedReplyError,
    Vendor,
    build_delete,
    build_poll,
    build_submission,
    parse_reply,
)
from open_ct600.hmrc.irmark import compute_irmark
from open_ct600.hmrc.xmldoc import CT_NS, GOVTALK_NS, MalformedXMLError, parse_xml

FIXTURES = Path(__file__).parent / "fixtures/hmrc"
SAMPLE = Path(__file__).resolve().parents[2] / "specs/hmrc/samples/CT600-Sample-No-attachments.xml"
VENDOR = Vendor(vendor_id="0000", product="open-ct600", version="0.1.0")
CREDENTIALS = GatewayCredentials(user_id="123456789012", password=SecretStr("s3cret-pa55"))
GT = {"gt": GOVTALK_NS, "ct": CT_NS}


def sample_envelope():
    return parse_xml(SAMPLE.read_bytes()).find(f"{{{GOVTALK_NS}}}Body/{{{CT_NS}}}IRenvelope")


def text(root, path):
    return root.xpath(f"string({path})", namespaces=GT)


@pytest.mark.parametrize(
    ("environment", "message_class", "gateway_test"),
    [
        (Environment.LIVE, "HMRC-CT-CT600", "0"),
        (Environment.TEST_IN_LIVE, "HMRC-CT-CT600-TIL", "0"),
        (Environment.ETS, "HMRC-CT-CT600", "1"),
    ],
)
def test_submission_header(environment, message_class, gateway_test):
    message, _ = build_submission(
        sample_envelope(), environment=environment, vendor=VENDOR, credentials=CREDENTIALS
    )
    root = parse_xml(message)

    details = "/gt:GovTalkMessage/gt:Header/gt:MessageDetails"
    assert text(root, f"{details}/gt:Class") == message_class
    assert text(root, f"{details}/gt:Qualifier") == "request"
    assert text(root, f"{details}/gt:Function") == "submit"
    assert root.xpath(f"{details}/gt:CorrelationID", namespaces=GT)[0].text is None
    assert text(root, f"{details}/gt:GatewayTest") == gateway_test
    auth = "/gt:GovTalkMessage/gt:Header/gt:SenderDetails/gt:IDAuthentication"
    assert text(root, f"{auth}/gt:SenderID") == "123456789012"
    assert text(root, f"{auth}/gt:Authentication/gt:Method") == "clear"
    assert text(root, f"{auth}/gt:Authentication/gt:Role") == "principal"
    assert text(root, f"{auth}/gt:Authentication/gt:Value") == "s3cret-pa55"
    govtalk = "/gt:GovTalkMessage/gt:GovTalkDetails"
    assert text(root, f"{govtalk}/gt:Keys/gt:Key[@Type='UTR']") == "8596148860"
    assert text(root, f"{govtalk}/gt:TargetDetails/gt:Organisation") == "HMRC"
    assert text(root, f"{govtalk}/gt:ChannelRouting/gt:Channel/gt:URI") == "0000"
    assert text(root, f"{govtalk}/gt:ChannelRouting/gt:Channel/gt:Product") == "open-ct600"


def test_submission_carries_its_irmark_without_comments():
    message, irmark = build_submission(
        sample_envelope(), environment=Environment.TPVS, vendor=VENDOR, credentials=None
    )
    root = parse_xml(message)

    assert b"<!--" not in message
    assert text(root, "//ct:IRheader/ct:IRmark") == irmark.base64
    assert compute_irmark(message) == irmark
    assert not root.xpath("//gt:SenderDetails", namespaces=GT)


def test_submission_does_not_modify_the_envelope():
    envelope = sample_envelope()
    comments = len(envelope.xpath(".//comment()"))
    assert comments > 0

    build_submission(envelope, environment=Environment.TPVS, vendor=VENDOR, credentials=None)

    assert len(envelope.xpath(".//comment()")) == comments


def test_live_needs_credentials():
    with pytest.raises(MessageBuildError, match="need Government Gateway credentials"):
        build_submission(
            sample_envelope(), environment=Environment.LIVE, vendor=VENDOR, credentials=None
        )


def test_tpvs_refuses_credentials():
    with pytest.raises(MessageBuildError, match="takes no credentials"):
        build_submission(
            sample_envelope(), environment=Environment.TPVS, vendor=VENDOR, credentials=CREDENTIALS
        )


def test_submission_needs_a_utr_key():
    envelope = sample_envelope()
    key = envelope.find(f"{{{CT_NS}}}IRheader/{{{CT_NS}}}Keys/{{{CT_NS}}}Key")
    key.getparent().remove(key)

    with pytest.raises(MessageBuildError, match="no UTR key"):
        build_submission(envelope, environment=Environment.TPVS, vendor=VENDOR, credentials=None)


def test_vendor_id_is_four_digits():
    with pytest.raises(ValueError, match="4 digits"):
        Vendor(vendor_id="Enter your 4 digit vendor ID", product="p", version="1")


def test_credentials_repr_hides_the_password():
    assert "s3cret-pa55" not in repr(CREDENTIALS)
    assert "s3cret-pa55" not in str(CREDENTIALS)


def test_poll_message():
    root = parse_xml(build_poll("46DCD4CC7E194088B99857931C185829", Environment.ETS))

    details = "/gt:GovTalkMessage/gt:Header/gt:MessageDetails"
    assert text(root, f"{details}/gt:Class") == "HMRC-CT-CT600"
    assert text(root, f"{details}/gt:Qualifier") == "poll"
    assert text(root, f"{details}/gt:Function") == "submit"
    assert text(root, f"{details}/gt:CorrelationID") == "46DCD4CC7E194088B99857931C185829"
    assert text(root, f"{details}/gt:GatewayTest") == "1"
    assert not root.xpath("//gt:SenderDetails | //gt:Body", namespaces=GT)


def test_delete_message():
    root = parse_xml(build_delete("46DCD4CC7E194088B99857931C185829", Environment.TEST_IN_LIVE))

    details = "/gt:GovTalkMessage/gt:Header/gt:MessageDetails"
    assert text(root, f"{details}/gt:Class") == "HMRC-CT-CT600-TIL"
    assert text(root, f"{details}/gt:Qualifier") == "request"
    assert text(root, f"{details}/gt:Function") == "delete"


@pytest.mark.parametrize("correlation_id", ["", "abc", "0" * 33, "46DCD4CC</CorrelationID>"])
def test_follow_ups_reject_bad_correlation_ids(correlation_id):
    with pytest.raises(MessageBuildError, match="CorrelationID"):
        build_poll(correlation_id, Environment.ETS)


def test_parses_tpvs_receipt():
    reply = parse_reply((FIXTURES / "tpvs-success-response.xml").read_bytes())

    assert isinstance(reply, Receipt)
    assert reply.irmark == "YrgW02ybxWOff7gHrELynhp1gRw="
    assert reply.accepted_time is not None
    assert reply.accepted_time.year == 2026
    assert any("IRmark was" in message for message in reply.messages)
    assert reply.response.startswith(b"<?xml")


def test_parses_hmrc_worked_example_receipt():
    content = (
        Path(__file__).resolve().parents[2] / "specs/hmrc/irmark/irmarkexample-response.xml"
    ).read_bytes()

    reply = parse_reply(content)

    assert isinstance(reply, Receipt)
    assert reply.correlation_id == "21F036214BD4A8679D14CDF57EB55D23"
    assert reply.irmark == "RPfWtxHeCZRcwfitnIJmK9xc4OQ="
    assert reply.accepted_time == datetime(2006, 7, 13, 14, 11, 25, 781000)
    assert "IT35NNYR3YEZIXGB7CWZZATGFPOFZYHE" in reply.messages[0]


def test_parses_business_errors():
    reply = parse_reply((FIXTURES / "tpvs-business-errors-response.xml").read_bytes())

    assert isinstance(reply, ErrorReport)
    assert [error.number for error in reply.errors] == [3001]
    assert reply.details[0].number == 9200
    assert reply.details[0].location.endswith("ct:TaxRate[1]")
    assert reply.details[1].number == 0
    assert reply.details[1].error_type == "xbrl.ixbrl.HeaderAbsent"
    assert len(reply.details) == 7


def test_parses_authentication_failure():
    reply = parse_reply((FIXTURES / "ets-authentication-failure-response.xml").read_bytes())

    assert isinstance(reply, ErrorReport)
    assert reply.errors[0].number == 1046
    assert reply.errors[0].raised_by == "Gateway"
    assert reply.details == ()


ACKNOWLEDGEMENT = b"""<?xml version="1.0"?>
<GovTalkMessage xmlns="http://www.govtalk.gov.uk/CM/envelope">
<EnvelopeVersion>2.0</EnvelopeVersion>
<Header><MessageDetails><Class>HMRC-CT-CT600</Class><Qualifier>acknowledgement</Qualifier>
<Function>submit</Function><TransactionID></TransactionID>
<CorrelationID>46DCD4CC7E194088B99857931C185829</CorrelationID>
<ResponseEndPoint PollInterval="10">%s</ResponseEndPoint>
<GatewayTimestamp>2017-02-13T09:28:14.772</GatewayTimestamp></MessageDetails><SenderDetails/>
</Header><GovTalkDetails><Keys/></GovTalkDetails><Body/></GovTalkMessage>"""


def test_parses_acknowledgement():
    content = ACKNOWLEDGEMENT % b"https://test-transaction-engine.tax.service.gov.uk/poll"

    assert parse_reply(content) == Acknowledgement(
        correlation_id="46DCD4CC7E194088B99857931C185829",
        endpoint="https://test-transaction-engine.tax.service.gov.uk/poll",
        poll_interval=10,
    )


def test_acknowledgement_without_endpoint_url():
    reply = parse_reply(ACKNOWLEDGEMENT % b"")

    assert isinstance(reply, Acknowledgement)
    assert reply.endpoint is None


def test_parses_delete_response():
    content = (
        ACKNOWLEDGEMENT.replace(b"acknowledgement", b"response")
        .replace(b"<Function>submit", b"<Function>delete")
        .replace(b"%s", b"")
    )

    assert parse_reply(content) == DeleteConfirmation("46DCD4CC7E194088B99857931C185829")


def test_rejects_html():
    with pytest.raises(MalformedXMLError):
        parse_reply((FIXTURES / "tpvs-akamai-access-denied.html").read_bytes())


def test_rejects_foreign_xml():
    with pytest.raises(UnexpectedReplyError, match="GovTalkMessage"):
        parse_reply(b"<html/>")


def test_rejects_unknown_qualifier():
    with pytest.raises(UnexpectedReplyError, match="Qualifier='poll'"):
        parse_reply(ACKNOWLEDGEMENT.replace(b"acknowledgement", b"poll") % b"")
