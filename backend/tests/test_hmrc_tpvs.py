"""Proof against HMRC's Third Party Validation Service. Opt in with ``pytest -m hmrc_tpvs``.

TPVS checks the body exactly as live does (schema, business rules, IRmark, iXBRL) and signs a
receipt. SYNTHETIC DATA ONLY: these tests send HMRC's own sample return and made-up companies
under HMRC's test UTR 8596148860.
"""

import asyncio
import re
from pathlib import Path

import httpx2
import pytest

from open_ct600.ct600 import CT600Return, Declaration, compute_return
from open_ct600.hmrc.client import BusinessErrors, IRmarkRejectedError, TransactionEngineClient
from open_ct600.hmrc.govtalk import Environment, Receipt, Vendor, build_submission
from open_ct600.hmrc.routes import render_ixbrl
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


SYNTHETIC_COMPANY = {
    "company": {
        "name": "Synthetic Widgets Ltd",
        "registration_number": "12345678",
        "utr": "8596148860",
        "principal_activity": "Manufacture of widgets",
    },
    "period": {"start": "2024-04-01", "end": "2025-03-31"},
    "profit_and_loss": {
        "turnover": 120_000,
        "interest_income": 500,
        "cost_of_sales": 20_000,
        "staff_costs": 30_000,
        "depreciation": 2_000,
        "other_expenses": 8_000,
    },
    "tax_adjustments": {
        "disallowable_expenses": 1_000,
        "capital_allowances": 5_000,
        "losses_brought_forward": 3_000,
        "qualifying_donations": 500,
        "associated_companies": 1,
    },
    "balance_sheet": {
        "fixed_assets": 10_000,
        "current_assets": 70_000,
        "creditors_within_one_year": 15_000,
        "called_up_share_capital": 100,
    },
    "accounts": {
        "standard": "micro",
        "approval_date": "2025-06-30",
        "directors": ["Jane Director"],
        "signing_director": "Jane Director",
        "average_employees": 2,
        "trading_status": "trading",
    },
}
COMPARATIVES = {
    "period": {"start": "2023-04-01", "end": "2024-03-31"},
    "profit_and_loss": {"turnover": 90_000, "staff_costs": 25_000, "other_expenses": 6_000},
    "balance_sheet": {
        "fixed_assets": 12_000,
        "current_assets": 30_000,
        "creditors_within_one_year": 9_000,
        "called_up_share_capital": 100,
    },
    "tax_on_profit": 11_210,
    "average_employees": 2,
}
END_TO_END = {
    "trading micro-entity (FRS 105)": {},
    "small company (FRS 102 section 1A)": {
        "accounts": {"standard": "small"},
        "profit_and_loss": {"turnover": 400_000},
    },
    "micro-entity with comparatives": {"accounts": {"comparatives": COMPARATIVES}},
    "small company limited by guarantee with comparatives": {
        "accounts": {
            "standard": "small",
            "legal_form": "private-company-limited-by-guarantee",
            "comparatives": COMPARATIVES,
        },
        "profit_and_loss": {"turnover": 400_000},
    },
    # Negative core:Equity and TotalAssetsLessCurrentLiabilities, which Arelle's HMRC.5.3
    # check flags; TPVS accepted them on 2026-09-29.
    "net liabilities": {
        "profit_and_loss": {"turnover": 10_000},
        "tax_adjustments": {"disallowable_expenses": 0},
        "balance_sheet": {
            "fixed_assets": 0,
            "current_assets": 5_000,
            "creditors_within_one_year": 30_000,
        },
    },
}


LOSS_MAKING = {
    "profit_and_loss": {"turnover": 10_000},
    "tax_adjustments": {"disallowable_expenses": 0, "losses_brought_forward": 0},
}
RD_FORMS = {"claimed_in_previous_three_years": True, "additional_information_submitted": True}
SME_PAYE = {
    "SME": {
        "PAYENICforWhichTheCompanyIsLiableInThisAccountingPeriod": "10000",
        "EmployerPAYEreference": [{"HMRCofficeNumber": "123", "EmployerPAYEreference": "AB12345"}],
    }
}
AUTHORISED = {
    "AuthorisationForSimplifiedArrangements": {
        "AuthorisationWhereSimplifiedArrangement": "yes",
        "CompanyName": "Synthetic Parent Ltd",
        "NameOfAuthorisedPerson": "Jane Director",
        "Status": "Director",
    }
}
RELIEFS = {
    "group relief claimant (CT600C)": (
        {
            "supplementary_pages": {
                "C": {
                    "ClaimToGroupRelief": {
                        "CompanyInformation": {
                            "Company": [
                                {
                                    "Name": "Synthetic Sub Ltd",
                                    "AccountingPeriod": {"From": "2024-07-01", "To": "2025-06-30"},
                                    "TaxReference": "1234567891",
                                    "AmountClaimed": "10000",
                                }
                            ]
                        },
                        "ClaimAuthorisation": AUTHORISED,
                    }
                }
            }
        },
        "//ct:ChargesAndReliefs/ct:GroupRelief",
        "10000.00",
    ),
    "close company s455 loans (CT600A)": (
        {
            "supplementary_pages": {
                "A": {
                    "BeforeEndPeriod": "no",
                    "LoansInformation": {"Loan": [{"Name": "J Smith", "AmountOfLoan": "40000"}]},
                    "ReliefEarlierThan": {
                        "Loan": [{"Name": "J Smith", "AmountRepaid": "15000", "Date": "2025-06-30"}]
                    },
                }
            }
        },
        "//ct:CalculationOfTaxOutstandingOrOverpaid/ct:LoansToParticipators",
        "8437.50",
    ),
    "SME R&D before April 2024 (CT600L)": (
        {
            "period": {"start": "2023-04-01", "end": "2024-03-31"},
            "accounts": {"approval_date": "2024-06-01"},
            **LOSS_MAKING,
            "research_and_development": {
                **RD_FORMS,
                "scheme": "sme",
                "qualifying_expenditure": 50_000,
                "intensity": "45",
                "claim_payable_credit": True,
            },
            "supplementary_pages": {"L": SME_PAYE},
        },
        "//ct:RepaymentsForThePeriodCoveredByThisReturn/ct:RandDTaxCredit",
        "13485.00",
    ),
    "merged RDEC from April 2024 (CT600L)": (
        {
            "research_and_development": {
                **RD_FORMS,
                "scheme": "rdec",
                "qualifying_expenditure": 50_000,
            },
            "supplementary_pages": {"L": {}},
        },
        "//ct:TaxReconciliation/ct:ResearchAndDevelopmentCredit",
        "10000.00",
    ),
    "ERIS payable credit, period ending March 2026 (CT600L)": (
        {
            "period": {"start": "2025-04-01", "end": "2026-03-31"},
            "accounts": {"approval_date": "2026-06-30"},
            **LOSS_MAKING,
            "research_and_development": {
                **RD_FORMS,
                "scheme": "eris",
                "qualifying_expenditure": 50_000,
                "intensity": "35",
                "claim_payable_credit": True,
            },
            "supplementary_pages": {"L": SME_PAYE},
        },
        "//ct:RepaymentsForThePeriodCoveredByThisReturn/ct:RandDTaxCredit",
        "13485.00",
    ),
    "tax avoidance scheme (CT600J)": (
        {
            "supplementary_pages": {
                "J": {
                    "AvoidanceSchemes": [
                        {"ReferenceNumber": "12345678", "AccountingPeriod": "2025-03-31"}
                    ]
                }
            }
        },
        "//ct:ReturnInfoSummary/ct:RegisteredAvoidanceScheme",
        "yes",
    ),
    "close investment-holding company at the main rate (box 4)": (
        {"company": {"company_type": 2}},
        "//ct:CorporationTaxChargeable/ct:FinancialYearOne/ct:Details/ct:TaxRate",
        "25.00",
    ),
    # 10,000 - 60,000 expenses + 2,000 depreciation - 5,000 capital allowances
    "trading loss in boxes 780/785": (
        LOSS_MAKING,
        "//ct:LossesDeficitsAndExcess/ct:AmountArising/ct:LossesOfTradesUK/ct:Arising",
        "53000.00",
    ),
    # Net trading profits 58,000 - 3,000 brought forward are ring fence profits
    "ring fence profits at 30% (CT600I)": (
        {
            "supplementary_pages": {
                "I": {
                    "CalculationOfSupplementaryCharge": {
                        "Trade": {"Amount": "55000", "Profits": "yes"}
                    }
                }
            }
        },
        "//ct:CompanyTaxCalculation/ct:RingFenceProfitsIncluded",
        "55000.00",
    ),
}


def synthetic(overrides):
    """The synthetic company with some sections changed or added."""
    answers = {
        section: {**values, **overrides.get(section, {})}
        for section, values in SYNTHETIC_COMPANY.items()
    }
    extra = {section: value for section, value in overrides.items() if section not in answers}
    return CT600Return.model_validate(answers | extra)


@pytest.mark.parametrize("overrides", END_TO_END.values(), ids=END_TO_END.keys())
def test_tpvs_accepts_a_generated_return_with_its_ixbrl(overrides):
    assert_tpvs_receipt(generated_envelope(synthetic(overrides)))


@pytest.mark.parametrize(("overrides", "box", "expected"), RELIEFS.values(), ids=RELIEFS.keys())
def test_tpvs_accepts_a_return_claiming_reliefs(overrides, box, expected):
    envelope = generated_envelope(synthetic(overrides))
    assert envelope.xpath(f"string({box})", namespaces={"ct": CT_NS}) == expected

    assert_tpvs_receipt(envelope)


def generated_envelope(ct600):
    """The return's IRenvelope with its rendered iXBRL, clean against HMRC's XSD and rules."""
    computation = compute_return(ct600)
    documents = render_ixbrl(ct600, computation)
    assert documents.missing == {}
    envelope = build_return_xml(
        ct600,
        computation,
        declaration=Declaration(name="Jane Director", capacity="director", confirmed=True),
        accounts_xhtml=documents.accounts,
        computations_xhtml=documents.computations,
    )
    assert validate_return(envelope) == []
    return envelope


def assert_tpvs_receipt(envelope):
    """Submit to TPVS and check the signed receipt carries our IRmark."""
    message, irmark = build_submission(
        envelope, environment=Environment.TPVS, vendor=VENDOR, credentials=None
    )

    outcome = submit_to_tpvs(message)

    assert isinstance(outcome, Receipt), outcome
    assert outcome.irmark == irmark.base64
    assert any(irmark.base32 in text for text in outcome.messages)
    assert b"dsig:SignatureValue" in outcome.response


def test_net_liabilities_case_really_tags_negative_equity():
    answers = {**SYNTHETIC_COMPANY, "balance_sheet": END_TO_END["net liabilities"]["balance_sheet"]}
    ct600 = CT600Return.model_validate(answers)
    accounts = render_ixbrl(ct600, compute_return(ct600)).accounts

    assert accounts is not None
    assert re.search(r'name="core:Equity"[^>]*sign="-"', accounts)
    assert re.search(r'name="core:TotalAssetsLessCurrentLiabilities"[^>]*sign="-"', accounts)
