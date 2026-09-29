"""iXBRL accounts and computations rendered from representative returns, validated by Arelle."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import pytest
from ixbrl_harness import Document, Problem, Rules, Validation, validate

from open_ct600.ct600 import CT600Return, ReturnComputation, compute_return
from open_ct600.ixbrl.accounts import render_accounts
from open_ct600.ixbrl.computations import (
    UnsupportedComputationsPeriodError,
    render_computations,
)
from open_ct600.ixbrl.layout import IxbrlRenderError
from open_ct600.ixbrl.taxonomies import CT_COMP_2024, FRC_2026

NIL_PROFIT_AND_LOSS = {
    "turnover": 0,
    "interest_income": 0,
    "cost_of_sales": 0,
    "staff_costs": 0,
    "depreciation": 0,
    "other_expenses": 0,
}


def make_return(**overrides: dict[str, Any]) -> CT600Return:
    answers: dict[str, dict[str, Any]] = {
        "company": {
            "name": "Acme Widgets & Co Ltd",
            "registration_number": "01234567",
            "utr": "1234567890",
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
        },
        "balance_sheet": {
            "fixed_assets": 10_000,
            "current_assets": 70_000,
            "prepayments_and_accrued_income": 1_000,
            "creditors_within_one_year": 15_000,
            "creditors_after_one_year": 5_000,
            "provisions": 1_000,
            "accruals_and_deferred_income": 2_000,
            "called_up_share_capital": 100,
        },
        "accounts": {
            "standard": "micro",
            "approval_date": "2025-06-30",
            "directors": ["Ada Lovelace", "Charles Babbage"],
            "signing_director": "Charles Babbage",
            "average_employees": 2,
            "trading_status": "trading",
        },
    }
    for section, values in overrides.items():
        answers[section] = {**answers.get(section, {}), **values}
    return CT600Return.model_validate(answers)


RD_FORMS = {"claimed_in_previous_three_years": True, "additional_information_submitted": True}
GROUP_RELIEF_CLAIM = {
    "ClaimToGroupRelief": {
        "CompanyInformation": {
            "Company": [{"Name": "Sub Ltd", "TaxReference": "1234567891", "AmountClaimed": "10000"}]
        },
        "ClaimAuthorisation": {"CopyOfNoticesOfConsentAttached": "yes"},
    }
}
TONNAGE_TAX = {
    "TonnageTax": {
        "Information": {
            "TrainingCertificate": "yes",
            "CompanyMetCharteredInLimit": "yes",
            "NotRegistered": "na",
            "OffshoreActivities": "no",
        },
        "QualifyingShips": {
            "Ship": [
                {
                    "Name": "Northern Star",
                    "IMOnumber": "9123456",
                    "InterestInShip": "O",
                    "GrossTonnage": "45000",
                    "NetTonnage": "30099",
                    "NumberDays": "365",
                    "Flagged": "yes",
                    "FirstTime": "no",
                }
            ]
        },
    }
}
ALL_EXEMPT_CHARITY = {
    "ClaimExemption": {
        "Status": {"ClaimingExemptionAllOrPart": "yes", "AllCharitable": {"AllExempt": "yes"}}
    }
}
THEATRE = {
    "CulturalReliefs": {
        "Theatre": {
            "CoreExpenditure": "500000",
            "UKcoreExpenditure": "450000",
            "AdditionalDeduction": "400000",
            "LossesSurrenderedForTaxCredit": "300000",
            "TaxCreditClaimed": "120000.00",
        }
    }
}


RETURNS = {
    "trading-micro": make_return(),
    "small-frs102-1a-short-period": make_return(
        period={"start": "2024-07-01", "end": "2025-03-31"},
        profit_and_loss={"turnover": 400_000},
        accounts={"standard": "small"},
    ),
    "dormant": make_return(
        profit_and_loss=NIL_PROFIT_AND_LOSS,
        tax_adjustments={
            "disallowable_expenses": 0,
            "capital_allowances": 0,
            "losses_brought_forward": 0,
            "qualifying_donations": 0,
        },
        balance_sheet={
            "fixed_assets": 0,
            "current_assets": 100,
            "prepayments_and_accrued_income": 0,
            "creditors_within_one_year": 0,
            "creditors_after_one_year": 0,
            "provisions": 0,
            "accruals_and_deferred_income": 0,
        },
        accounts={"trading_status": "never_traded", "directors": ["Ada Lovelace"]}
        | {"signing_director": "Ada Lovelace", "average_employees": 0, "dormant": True},
    ),
    "loss-making-no-longer-trading": make_return(
        profit_and_loss={"turnover": 10_000},
        tax_adjustments={"disallowable_expenses": 0},
        accounts={"trading_status": "no_longer_trading"},
    ),
    "straddling-financial-years": make_return(
        period={"start": "2023-01-01", "end": "2023-12-31"},
        accounts={"approval_date": "2024-06-30"},
    ),
    "associated-companies": make_return(tax_adjustments={"associated_companies": 3}),
    "net-liabilities": make_return(
        profit_and_loss={"turnover": 10_000},
        tax_adjustments={"disallowable_expenses": 0},
        balance_sheet={
            "fixed_assets": 0,
            "current_assets": 5_000,
            "creditors_within_one_year": 30_000,
        },
    ),
    "eris-payable-credit": make_return(
        profit_and_loss={"turnover": 10_000},
        research_and_development={
            **RD_FORMS,
            "scheme": "eris",
            "qualifying_expenditure": 50_000,
            "intensity": "35",
            "claim_payable_credit": True,
        },
        supplementary_pages={"L": {}},
    ),
    "merged-rdec": make_return(
        research_and_development={**RD_FORMS, "scheme": "rdec", "qualifying_expenditure": 50_000},
        supplementary_pages={"L": {}},
    ),
    "group-relief-and-tonnage-tax": make_return(
        supplementary_pages={"C": GROUP_RELIEF_CLAIM, "F": TONNAGE_TAX},
    ),
    "charity-all-exempt": make_return(
        company={"company_type": 8},
        supplementary_pages={"E": ALL_EXEMPT_CHARITY},
    ),
    "theatre-tax-relief": make_return(
        creative_industries={"additional_information_submitted": True},
        supplementary_pages={"P": THEATRE},
    ),
}
COMPUTATIONS = {name: compute_return(ct600) for name, ct600 in RETURNS.items()}

AFTER_COMPUTATIONS_WINDOW = make_return(
    period={"start": "2025-05-01", "end": "2026-04-30"}, accounts={"approval_date": "2026-06-30"}
)

# Arelle's HMRC.5.3 check rejects any negative value for a concept whose label has no
# bracketed term. Equity (share capital, accumulated losses, total) and total assets less
# current liabilities genuinely go negative for a company with net liabilities; the FRC
# tagging guide (5.3.1 b) requires them to be entered as negative. These are the only
# problems a net-liabilities company may have.
GENUINE_NEGATIVES = {"core:Equity", "core:TotalAssetsLessCurrentLiabilities"}


def _is_genuine_negative(problem: Problem) -> bool:
    return problem.code == "HMRC.5.3" and problem.arguments.get("fact") in GENUINE_NEGATIVES


def _documents() -> dict[str, Document]:
    documents = {
        f"{name}-accounts": Document(
            render_accounts(ct600, COMPUTATIONS[name]), FRC_2026.package, Rules.ACCOUNTS
        )
        for name, ct600 in RETURNS.items()
    }
    documents |= {
        f"{name}-computations": Document(
            render_computations(ct600, COMPUTATIONS[name]),
            CT_COMP_2024.package,
            Rules.COMPUTATIONS,
        )
        for name, ct600 in RETURNS.items()
    }
    documents["after-computations-window-accounts"] = Document(
        render_accounts(AFTER_COMPUTATIONS_WINDOW, compute_return(AFTER_COMPUTATIONS_WINDOW)),
        FRC_2026.package,
        Rules.ACCOUNTS,
    )
    return documents


DOCUMENTS = _documents()


@pytest.fixture(scope="module")
def validations() -> dict[str, Validation]:
    return validate(DOCUMENTS)


def _only(validation: Validation, name: str, context: str | None = None) -> str:
    values = validation.values(name)
    if context is not None:
        return values[context]
    assert len(set(values.values())) == 1, f"{name} has several values: {values}"
    return next(iter(values.values()))


def _box(computation: ReturnComputation, box: str) -> Decimal:
    return next(item.value for item in computation.boxes if item.box == box)


@pytest.mark.parametrize("name", [n for n in DOCUMENTS if n != "net-liabilities-accounts"])
def test_documents_pass_arelle_with_no_warnings(validations, name):
    assert validations[name].problems == ()


def test_net_liabilities_accounts_only_report_genuine_negatives(validations):
    problems = validations["net-liabilities-accounts"].problems

    assert problems
    assert [problem for problem in problems if not _is_genuine_negative(problem)] == []


@pytest.mark.parametrize("name", RETURNS)
def test_accounts_carry_the_computed_figures(validations, name):
    accounts, summary = validations[f"{name}-accounts"], COMPUTATIONS[name].accounts

    assert _only(accounts, "core:Equity", "end") == str(summary.net_assets)
    assert _only(accounts, "core:NetAssetsLiabilities") == str(summary.net_assets)
    assert _only(accounts, "bus:UKCompaniesHouseRegisteredNumber") == "01234567"
    assert _only(accounts, "bus:EntityCurrentLegalOrRegisteredName") == "Acme Widgets & Co Ltd"
    assert _only(accounts, "bus:EndDateForPeriodCoveredByReport") == str(RETURNS[name].period.end)


@pytest.mark.parametrize("name", [n for n in RETURNS if n != "dormant"])
def test_profit_after_tax_uses_tax_rounded_to_pounds(validations, name):
    accounts, summary = validations[f"{name}-accounts"], COMPUTATIONS[name].accounts
    tax = summary.corporation_tax.quantize(Decimal(1), rounding=ROUND_HALF_UP)

    assert _only(accounts, "core:ProfitLoss") == str(summary.profit_before_tax - tax)


def test_trading_status_and_dormancy(validations):
    trading = validations["trading-micro-accounts"]
    dormant = validations["dormant-accounts"]
    stopped = validations["loss-making-no-longer-trading-accounts"]

    assert _only(trading, "bus:EntityDormantTruefalse") == "false"
    assert _only(dormant, "bus:EntityDormantTruefalse") == "true"
    assert dormant.values("core:ProfitLoss") == {}
    status = next(fact for fact in stopped.facts if fact.name == "bus:EntityTradingStatus")
    assert status.dimensions == {
        "bus:EntityTradingStatusDimension": "bus:EntityNoLongerTradingButTradedInPast"
    }


def test_dormant_accounts_claim_the_section_480_exemption(validations):
    section_480 = (
        "direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection480CompaniesAct2006"
        "RelatingToDormantCompanies"
    )
    section_477 = (
        "direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection477CompaniesAct2006"
        "RelatingToSmallCompanies"
    )

    assert validations["dormant-accounts"].values(section_480)
    assert validations["dormant-accounts"].values(section_477) == {}
    assert validations["trading-micro-accounts"].values(section_477)


def test_directors_are_named_and_the_signing_director_identified(validations):
    accounts = validations["trading-micro-accounts"]

    assert accounts.values("bus:NameEntityOfficer") == {
        "dur-director1": "Ada Lovelace",
        "dur-director2": "Charles Babbage",
    }
    assert set(accounts.values("core:DirectorSigningFinancialStatements")) == {"dur-director2"}


def test_accounting_standard_follows_the_answer(validations):
    def standard(document: str) -> str:
        fact = next(
            fact
            for fact in validations[document].facts
            if fact.name == "bus:AccountingStandardsApplied"
        )
        return fact.dimensions["bus:AccountingStandardsDimension"]

    assert standard("trading-micro-accounts") == "bus:Micro-entities"
    assert standard("small-frs102-1a-short-period-accounts") == "bus:SmallEntities"


@pytest.mark.parametrize("name", RETURNS)
def test_computations_carry_the_ct600_boxes(validations, name):
    computation, ct600 = COMPUTATIONS[name], RETURNS[name]
    document = validations[f"{name}-computations"]

    assert _only(document, "ct-comp:TaxReference") == ct600.company.utr
    assert _only(document, "ct-comp:EndOfPeriodCoveredByReturn") == str(ct600.period.end)
    assert _only(document, "ct-comp:CompanyIsAPartnerInAFirm") == "false"
    assert _only(document, "ct-comp:TotalProfitsChargeableToCorporationTax") == str(
        _box(computation, "315")
    )
    assert Decimal(_only(document, "ct-comp:CorporationTaxChargeable")) == _box(computation, "440")
    assert Decimal(_only(document, "ct-comp:TaxChargeable")) == _box(computation, "510")
    assert Decimal(_only(document, "ct-comp:TaxPayable")) == _box(computation, "528")


def test_straddling_period_has_a_row_per_financial_year(validations):
    document = validations["straddling-financial-years-computations"]
    computation = COMPUTATIONS["straddling-financial-years"]

    assert _only(document, "ct-comp:FinancialYear1CoveredByTheReturn") == "2022"
    assert _only(document, "ct-comp:FinancialYear2CoveredByTheReturn") == "2023"
    assert _only(document, "ct-comp:FY1FirstRateOfTax") == "0.19"
    assert Decimal(_only(document, "ct-comp:FY2AmountOfProfitChargeableAtFirstRate")) == _box(
        computation, "385"
    )


def test_associated_companies_are_tagged(validations):
    document = validations["associated-companies-computations"]

    assert _only(document, "ct-comp:NumberOfAssociatedCompaniesInThisPeriod") == "3"


def test_losses_are_carried_forward_per_trade(validations):
    document = validations["loss-making-no-longer-trading-computations"]
    computation = COMPUTATIONS["loss-making-no-longer-trading"]

    assert computation.losses_carried_forward > 0
    assert document.values("ct-comp:BalanceOfLossesBroughtForwardCarriedForward") == {
        "trade-start": "3000",
        "trade-end": str(computation.losses_carried_forward),
    }
    assert _only(document, "ct-comp:AdjustedLossOfPeriod") == str(computation.trading_loss_arising)
    assert int(_only(document, "ct-comp:ProfitLossPerAccounts")) < 0


def test_dormant_computation_has_no_trade(validations):
    document = validations["dormant-computations"]

    assert document.values("ct-comp:ProfitLossPerAccounts") == {}
    assert _only(document, "ct-comp:TotalProfitsChargeableToCorporationTax") == "0"


def test_marginal_relief_is_shown_but_not_tagged():
    ct600 = RETURNS["trading-micro"]
    computation = COMPUTATIONS["trading-micro"]
    assert computation.tax.marginal_relief > 0

    xhtml = render_computations(ct600, computation)

    assert "Less: marginal relief" in xhtml
    assert f"({computation.tax.marginal_relief:,.2f})" in xhtml
    assert "MarginalRelief" not in xhtml


def test_computations_are_refused_after_the_taxonomy_window():
    with pytest.raises(UnsupportedComputationsPeriodError, match="31 March 2026"):
        render_computations(AFTER_COMPUTATIONS_WINDOW, compute_return(AFTER_COMPUTATIONS_WINDOW))


def test_short_periods_are_described_as_periods():
    ct600 = RETURNS["small-frs102-1a-short-period"]

    xhtml = render_accounts(ct600, COMPUTATIONS["small-frs102-1a-short-period"])

    assert "for the period ended 31 March 2025" in xhtml
    assert "For the period ending 31 March 2025" in xhtml


def test_more_directors_than_the_taxonomy_can_name_are_refused():
    directors = [f"Director {number}" for number in range(41)]
    ct600 = make_return(accounts={"directors": directors, "signing_director": "Director 0"})

    with pytest.raises(IxbrlRenderError, match="at most 40 directors"):
        render_accounts(ct600, compute_return(ct600))
