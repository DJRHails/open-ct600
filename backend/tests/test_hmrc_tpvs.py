"""Proof against HMRC's Third Party Validation Service. Opt in with ``pytest -m hmrc_tpvs``.

TPVS checks the body exactly as live does (schema, business rules, IRmark, iXBRL) and signs a
receipt. SYNTHETIC DATA ONLY: these tests send HMRC's own sample return (test UTR 8596148860).
"""

import asyncio
from pathlib import Path

import httpx2
import pytest

from open_ct600.ct600 import CT600Return, Declaration, compute_return
from open_ct600.hmrc.client import BusinessErrors, IRmarkRejectedError, TransactionEngineClient
from open_ct600.hmrc.govtalk import Environment, Receipt, Vendor, build_submission
from open_ct600.hmrc.validate import validate_return
from open_ct600.hmrc.xml import build_return_xml
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


def test_tpvs_accepts_our_ct600_apart_from_placeholder_ixbrl():
    """Until the iXBRL renderers land, TPVS may only object to the placeholder documents."""
    ct600 = CT600Return.model_validate(
        {
            "company": {
                "name": "Synthetic Widgets Ltd",
                "registration_number": "12345678",
                "utr": "8596148860",
                "principal_activity": "Manufacture of widgets",
            },
            "period": {"start": "2024-04-01", "end": "2025-03-31"},
            "profit_and_loss": {"turnover": 120_000, "staff_costs": 40_000},
            "tax_adjustments": {"associated_companies": 1},
            "balance_sheet": {"current_assets": 20_000},
            "accounts": {
                "standard": "micro",
                "approval_date": "2025-06-30",
                "directors": ["Jane Director"],
                "signing_director": "Jane Director",
                "average_employees": 1,
                "trading_status": "trading",
            },
        }
    )
    placeholder = '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>x</p></body></html>'
    envelope = build_return_xml(
        ct600,
        compute_return(ct600),
        declaration=Declaration(name="Jane Director", capacity="director", confirmed=True),
        accounts_xhtml=placeholder,
        computations_xhtml=placeholder,
    )
    assert validate_return(envelope) == []
    message, _ = build_submission(
        envelope, environment=Environment.TPVS, vendor=VENDOR, credentials=None
    )

    outcome = submit_to_tpvs(message)

    assert isinstance(outcome, BusinessErrors), outcome
    assert {error.location for error in outcome.errors} <= {"Accounts", "Computations"}
    assert all(error.error_type.startswith("xbrl.") for error in outcome.errors)
