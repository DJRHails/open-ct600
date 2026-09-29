"""Proof against HMRC's Third Party Validation Service. Opt in with ``pytest -m hmrc_tpvs``.

TPVS checks the body exactly as live does (schema, business rules, IRmark, iXBRL) and signs a
receipt. SYNTHETIC DATA ONLY: these tests send HMRC's own sample return (test UTR 8596148860).
"""

import asyncio
from pathlib import Path

import httpx2
import pytest

from open_ct600.hmrc.client import BusinessErrors, IRmarkRejectedError, TransactionEngineClient
from open_ct600.hmrc.govtalk import Environment, Receipt, Vendor, build_submission
from open_ct600.hmrc.xmldoc import CT_NS, GOVTALK_NS, parse_xml

pytestmark = pytest.mark.hmrc_tpvs

SAMPLE = Path(__file__).resolve().parents[2] / "specs/hmrc/samples/CT600-Sample-No-attachments.xml"
VENDOR = Vendor(vendor_id="0000", product="open-ct600", version="0.1.0")


def hmrc_sample(edits=()):
    content = SAMPLE.read_bytes()
    for old, new in edits:
        assert old in content
        content = content.replace(old, new)
    envelope = parse_xml(content).find(f"{{{GOVTALK_NS}}}Body/{{{CT_NS}}}IRenvelope")
    assert envelope is not None
    return build_submission(envelope, environment=Environment.TPVS, vendor=VENDOR, credentials=None)


def submit_to_tpvs(message):
    async def go():
        async with httpx2.AsyncClient(timeout=120) as http:
            return await TransactionEngineClient(Environment.TPVS, http=http).submit(message)

    return asyncio.run(go())


def test_tpvs_accepts_hmrc_sample_with_our_irmark():
    message, irmark = hmrc_sample()

    outcome = submit_to_tpvs(message)

    assert isinstance(outcome, Receipt), outcome
    assert outcome.irmark == irmark.base64
    assert any(irmark.base32 in text for text in outcome.messages)
    assert outcome.accepted_time is not None


def test_tpvs_rejects_a_wrong_irmark():
    message, irmark = hmrc_sample()
    tampered = message.replace(irmark.base64.encode(), b"AAAAAAAAAAAAAAAAAAAAAAAAAAA=")

    with pytest.raises(IRmarkRejectedError, match="2021"):
        submit_to_tpvs(tampered)


def test_tpvs_reports_business_errors_as_our_validator_does():
    message, _ = hmrc_sample(
        edits=[
            (b"<CompanyType>6</CompanyType>", b"<CompanyType>0</CompanyType>"),
            (b"<TaxRate>19.00</TaxRate>", b"<TaxRate>18.00</TaxRate>"),
        ]
    )

    outcome = submit_to_tpvs(message)

    assert isinstance(outcome, BusinessErrors), outcome
    assert 9200 in {error.number for error in outcome.errors}
