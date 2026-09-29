"""Relief sections of the iXBRL computation, validated by Arelle: group relief, s455, R&D."""

from decimal import Decimal

import pytest
from answers import PAYE_REFERENCE, RD_FORMS, boxes, make_return, period
from ixbrl_harness import Document, Rules, Validation, validate

from open_ct600.ct600 import compute_return
from open_ct600.ixbrl.computations import render_computations
from open_ct600.ixbrl.taxonomies import CT_COMP_2024

YEAR_TO_MARCH_2024 = period("2023-04-01", "2024-03-31", "2024-06-01")
LOSS_MAKING = {"profit_and_loss": {"turnover": 80_000, "other_expenses": 100_000}}


def research(scheme: str, expenditure: int, **answers) -> dict:
    return {**RD_FORMS, "scheme": scheme, "qualifying_expenditure": expenditure, **answers}


def paye(section: str) -> dict:
    names = {
        "SME": "PAYENICforWhichTheCompanyIsLiableInThisAccountingPeriod",
        "Step3": "PAYENICsForWhichTheCompanyIsLiableInThisAP",
    }
    return {section: {names[section]: "30000", "EmployerPAYEreference": PAYE_REFERENCE}}


LOANS_TO_TWO_PARTICIPATORS = {
    "BeforeEndPeriod": "no",
    "LoansInformation": {
        "Loan": [
            {"Name": "Ada Lovelace", "AmountOfLoan": "20000"},
            {"Name": "Charles Babbage", "AmountOfLoan": "8000"},
            {"Name": "Ada Lovelace", "AmountOfLoan": "5000"},
        ]
    },
    "ReliefEarlierThan": {
        "Loan": [{"Name": "Charles Babbage", "Date": "2025-06-30", "AmountRepaid": "8000"}]
    },
    "TotalLoansOutstanding": "25000",
}
GROUP_RELIEF_CLAIM = {
    "ClaimToGroupRelief": {
        "CompanyInformation": {
            "Company": [{"Name": "Sub Ltd", "TaxReference": "1234567891", "AmountClaimed": "30000"}]
        },
        "ClaimAuthorisation": {"CopyOfNoticesOfConsentAttached": "yes"},
    }
}

RETURNS = {
    "group-relief": make_return(supplementary_pages={"C": GROUP_RELIEF_CLAIM}),
    "loans-to-two-participators": make_return(
        supplementary_pages={"A": LOANS_TO_TWO_PARTICIPATORS}
    ),
    "sme-rd-before-april-2024": make_return(
        **YEAR_TO_MARCH_2024,
        **LOSS_MAKING,
        research_and_development=research("sme", 100_000, claim_payable_credit=True),
        supplementary_pages={"L": paye("SME")},
    ),
    "large-company-rdec-before-april-2024": make_return(
        **YEAR_TO_MARCH_2024,
        **LOSS_MAKING,
        research_and_development=research("rdec", 100_000, rd_workers_paye_and_nic=30_000),
        supplementary_pages={"L": {}},
    ),
    "merged-rdec-payable": make_return(
        **LOSS_MAKING,
        research_and_development=research("rdec", 200_000, company_is_sme=True),
        supplementary_pages={"L": paye("Step3")},
    ),
    "eris": make_return(
        **LOSS_MAKING,
        research_and_development=research(
            "eris", 50_000, intensity="35", claim_payable_credit=True
        ),
        supplementary_pages={"L": paye("SME")},
    ),
}
COMPUTATIONS = {name: compute_return(ct600) for name, ct600 in RETURNS.items()}
DOCUMENTS = {
    name: render_computations(ct600, COMPUTATIONS[name]) for name, ct600 in RETURNS.items()
}


@pytest.fixture(scope="module")
def validations() -> dict[str, Validation]:
    return validate(
        {
            name: Document(xhtml, CT_COMP_2024.package, Rules.COMPUTATIONS)
            for name, xhtml in DOCUMENTS.items()
        }
    )


def value(validation: Validation, name: str, context: str = "company") -> Decimal:
    return Decimal(validation.values(name)[context])


@pytest.mark.parametrize("name", RETURNS)
def test_relief_computations_pass_arelle_with_no_warnings(validations, name):
    assert validations[name].problems == ()


@pytest.mark.parametrize("name", RETURNS)
def test_tax_chargeable_and_payable_are_the_ct600_boxes(validations, name):
    result = boxes(COMPUTATIONS[name])

    assert value(validations[name], "ct-comp:TaxChargeable") == result["510"]
    assert value(validations[name], "ct-comp:TaxPayable") == result["528"]
    assert value(validations[name], "ct-comp:NetCorporationTaxPayable") == result["475"]


def test_group_relief_claimed(validations):
    result = boxes(COMPUTATIONS["group-relief"])

    assert result["310"] == 30_000
    assert value(validations["group-relief"], "ct-comp:GroupReliefClaimed") == 30_000


def test_loans_to_participators_are_tagged_per_participator(validations):
    document = validations["loans-to-two-participators"]
    result = boxes(COMPUTATIONS["loans-to-two-participators"])

    assert document.values("ct-comp:NameOfParticipator") == {
        "participator-1": "Ada Lovelace",
        "participator-2": "Charles Babbage",
    }
    assert document.values("ct-comp:LoanToParticipatorAmountTaxable") == {
        "participator-1": "25000",
        "participator-2": "8000",
    }
    assert document.values("ct-comp:LoanToParticipatorTaxRate") == {
        "participator-1": "0.3375",
        "participator-2": "0.3375",
    }
    assert document.values("ct-comp:LoanToParticipatorTaxPayable") == {
        "participator-1": "8437.50",
        "participator-2": "2700.00",
    }
    # 33,000 x 33.75% = 11,137.50 less 8,000 x 33.75% = 2,700.00 repaid within nine months
    assert result["480"] == Decimal("8437.50")
    assert value(document, "ct-comp:TaxPayableOnLoansToParticipators") == result["480"]
    assert result["510"] == result["475"] + result["480"]
    participator = next(fact for fact in document.facts if fact.context == "participator-2")
    assert participator.dimensions == {
        "ct-comp:BusinessTypeDimension": "ct-comp:Company",
        "ct-comp:ParticipatorDimension": "Charles Babbage",
    }


def test_sme_additional_deduction_surrendered_loss_and_payable_credit(validations):
    document = validations["sme-rd-before-april-2024"]
    computation = COMPUTATIONS["sme-rd-before-april-2024"]
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert relief.scheme == "sme"

    deduction = "ct-comp:AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME"
    assert value(document, deduction, "trade") == 86_000
    assert value(document, "ct-comp:LossTreatedAsSurrenderedForRDTaxCredit", "trade") == 106_000
    assert (
        value(document, "ct-comp:ResearchDevelopmentTaxCreditPayable") == boxes(computation)["875"]
    )
    assert document.values("ct-comp:AmountOfRDExpenditureCredit") == {}


def test_large_company_rdec_uses_the_payable_rdec_step_elements(validations):
    document = validations["large-company-rdec-before-april-2024"]
    result = boxes(COMPUTATIONS["large-company-rdec-before-april-2024"])
    relief = COMPUTATIONS["large-company-rdec-before-april-2024"].reliefs.research_and_development
    assert relief is not None
    assert relief.scheme == "large_company_rdec"

    assert value(document, "ct-comp:AmountOfRDExpenditureCredit", "trade") == relief.rdec
    payable = "ct-comp:PayableRDCreditCalculationAmountPayableToTheCompany"
    assert value(document, payable) == result["880"]


def test_merged_rdec_is_tagged_but_its_steps_are_not(validations):
    document = validations["merged-rdec-payable"]
    relief = COMPUTATIONS["merged-rdec-payable"].reliefs.research_and_development
    assert relief is not None
    assert relief.scheme == "merged_rdec"
    assert relief.payable_rdec

    assert value(document, "ct-comp:AmountOfRDExpenditureCredit", "trade") == relief.rdec
    assert not any(fact.name.startswith("ct-comp:PayableRDCredit") for fact in document.facts)
    assert f"{relief.payable_rdec:,.2f}" in DOCUMENTS["merged-rdec-payable"]
    assert "(box 880)" in DOCUMENTS["merged-rdec-payable"]


def test_eris_deduction_and_payable_credit(validations):
    document = validations["eris"]
    computation = COMPUTATIONS["eris"]
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert relief.scheme == "eris"

    deduction = "ct-comp:AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME"
    assert value(document, deduction, "trade") == relief.additional_deduction
    assert (
        value(document, "ct-comp:LossTreatedAsSurrenderedForRDTaxCredit", "trade")
        == relief.losses_surrendered
    )
    assert (
        value(document, "ct-comp:ResearchDevelopmentTaxCreditPayable") == boxes(computation)["875"]
    )
