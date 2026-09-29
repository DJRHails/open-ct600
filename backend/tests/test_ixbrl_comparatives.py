"""Accounts with previous-period comparatives and each legal form, validated by Arelle."""

from typing import Any, get_args

import pytest
from answers import make_return
from ixbrl_harness import Document, Rules, Validation, validate

from open_ct600.ct600 import LegalForm, compute_return
from open_ct600.ixbrl.accounts import LEGAL_FORM_MEMBERS, render_accounts
from open_ct600.ixbrl.taxonomies import FRC_2026

PREVIOUS_PROFIT_AND_LOSS = {
    "turnover": 90_000,
    "interest_income": 150,
    "cost_of_sales": 10_000,
    "staff_costs": 20_000,
    "depreciation": 1_500,
    "other_expenses": 4_000,
}
PREVIOUS_BALANCE_SHEET = {
    "called_up_share_capital_not_paid": 50,
    "fixed_assets": 6_000,
    "current_assets": 40_000,
    "prepayments_and_accrued_income": 700,
    "creditors_within_one_year": 12_000,
    "creditors_after_one_year": 3_000,
    "provisions": 400,
    "accruals_and_deferred_income": 900,
    "called_up_share_capital": 100,
}
COMPARATIVES: dict[str, Any] = {
    "period": {"start": "2023-04-01", "end": "2024-03-31"},
    "profit_and_loss": PREVIOUS_PROFIT_AND_LOSS,
    "balance_sheet": PREVIOUS_BALANCE_SHEET,
    "tax_on_profit": 10_000,
    "average_employees": 3,
}
NIL_PROFIT_AND_LOSS = dict.fromkeys(PREVIOUS_PROFIT_AND_LOSS, 0)
DORMANT: dict[str, Any] = {
    "profit_and_loss": NIL_PROFIT_AND_LOSS,
    "balance_sheet": {"current_assets": 100, "called_up_share_capital": 100},
}
DORMANT_ACCOUNTS = {"dormant": True, "trading_status": "never_traded"}

RETURNS = {
    "micro-with-comparatives": make_return(accounts={"comparatives": COMPARATIVES}),
    "small-with-comparatives": make_return(
        accounts={"standard": "small", "comparatives": COMPARATIVES}
    ),
    "first-period": make_return(),
    "previous-tax-credit": make_return(
        accounts={"comparatives": {**COMPARATIVES, "tax_on_profit": -4_000}}
    ),
    "previous-tax-credit-and-no-tax-now": make_return(
        profit_and_loss={"turnover": 10_000, "other_expenses": 30_000},
        accounts={"comparatives": {**COMPARATIVES, "tax_on_profit": -4_000}},
    ),
    "dormant-with-nil-comparatives": make_return(
        **DORMANT,
        accounts={
            **DORMANT_ACCOUNTS,
            "comparatives": {
                "period": COMPARATIVES["period"],
                "profit_and_loss": NIL_PROFIT_AND_LOSS,
                "balance_sheet": {"current_assets": 100, "called_up_share_capital": 100},
            },
        },
    ),
    "dormant-after-trading": make_return(
        **DORMANT,
        accounts={
            **DORMANT_ACCOUNTS,
            "trading_status": "no_longer_trading",
            "comparatives": COMPARATIVES,
        },
    ),
    **{
        f"legal-form-{form}": make_return(
            accounts={"legal_form": form, "comparatives": COMPARATIVES}
        )
        for form in get_args(LegalForm)
    },
}
COMPUTATIONS = {name: compute_return(ct600) for name, ct600 in RETURNS.items()}
DOCUMENTS = {name: render_accounts(ct600, COMPUTATIONS[name]) for name, ct600 in RETURNS.items()}


@pytest.fixture(scope="module")
def validations() -> dict[str, Validation]:
    return validate(
        {
            name: Document(xhtml, FRC_2026.package, Rules.ACCOUNTS)
            for name, xhtml in DOCUMENTS.items()
        }
    )


def facts_in(validation: Validation, context: str) -> dict[str, str]:
    """Facts without dimensions in one context, by concept."""
    return {
        fact.name: fact.value
        for fact in validation.facts
        if fact.context == context and not fact.dimensions
    }


@pytest.mark.parametrize("name", RETURNS)
def test_accounts_pass_arelle_with_no_warnings(validations, name):
    assert validations[name].problems == ()


@pytest.mark.parametrize("name", ["micro-with-comparatives", "small-with-comparatives"])
def test_previous_period_facts_equal_the_comparatives(validations, name):
    previous = facts_in(validations[name], "prev-dur")
    at_previous_end = facts_in(validations[name], "prev-end")

    assert previous["core:TurnoverRevenue"] == "90000"
    # 90,150 - 35,500 = 54,650 before tax; 10,000 tax
    assert previous["core:ProfitLossOnOrdinaryActivitiesBeforeTax"] == "54650"
    assert previous["core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities"] == "10000"
    assert previous["core:ProfitLoss"] == "44650"
    assert at_previous_end["core:FixedAssets"] == "6000"
    assert at_previous_end["core:CurrentAssets"] == "40000"
    assert at_previous_end["core:CalledUpShareCapitalNotPaidNotExpressedAsCurrentAsset"] == "50"
    # 40,000 + 700 - 12,000 = 28,700; + 6,000 + 50 = 34,750; - 3,000 - 400 - 900 = 30,450
    assert at_previous_end["core:NetCurrentAssetsLiabilities"] == "28700"
    assert at_previous_end["core:TotalAssetsLessCurrentLiabilities"] == "34750"
    assert at_previous_end["core:NetAssetsLiabilities"] == "30450"
    assert at_previous_end["core:Equity"] == "30450"
    assert validations[name].values("core:Creditors") == {
        "end-within-one-year": "0",
        "end-after-one-year": "0",
        "prev-end-within-one-year": "12000",
        "prev-end-after-one-year": "3000",
    }
    assert validations[name].values("core:Equity")["prev-end-retained-earnings"] == "30350"


@pytest.mark.parametrize("name", ["micro-with-comparatives", "small-with-comparatives"])
def test_previous_average_employees_are_tagged(validations, name):
    assert validations[name].values("core:AverageNumberEmployeesDuringPeriod") == {
        "dur": "1",
        "prev-dur": "3",
    }
    assert "(previous period: " in DOCUMENTS[name]


def test_unknown_previous_average_employees_are_left_out(validations):
    document = validations["dormant-with-nil-comparatives"]

    assert document.values("core:AverageNumberEmployeesDuringPeriod") == {"dur": "1"}


def _tax_row(xhtml: str) -> str:
    start = xhtml.index("<td>Tax")
    return xhtml[start : xhtml.index("</tr>", start)]


def test_a_previous_tax_credit_is_tagged_negative_and_increases_profit(validations):
    previous = facts_in(validations["previous-tax-credit"], "prev-dur")
    this_period = facts_in(validations["previous-tax-credit"], "dur")

    # "Tax (tax credit) on profit or loss": a credit is entered as a negative value
    assert previous["core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities"] == "-4000"
    assert previous["core:ProfitLossOnOrdinaryActivitiesBeforeTax"] == "54650"
    assert previous["core:ProfitLoss"] == "58650"
    assert int(this_period["core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities"]) > 0


def test_the_tax_line_is_labelled_and_bracketed_by_whether_it_is_a_charge_or_credit():
    mixed = _tax_row(DOCUMENTS["previous-tax-credit"])
    credit_only = _tax_row(DOCUMENTS["previous-tax-credit-and-no-tax-now"])
    charge_only = _tax_row(DOCUMENTS["micro-with-comparatives"])

    assert mixed.startswith("<td>Tax (charge) or credit on profit</td>")
    assert credit_only.startswith("<td>Tax credit on profit</td>")
    assert charge_only.startswith("<td>Tax on profit</td>")
    # The charge is a deduction in brackets; the credit adds, so it has none
    assert mixed.count('<td class="n">(<ix:nonFraction') == 1
    assert 'sign="-" format="ixt:numdotdecimal">4,000</ix:nonFraction>\n        </td>' in mixed
    assert "(" not in credit_only.split("</td>", 1)[1]


def test_micro_previous_other_income_and_expenses(validations):
    previous = facts_in(validations["micro-with-comparatives"], "prev-dur")

    assert previous["core:OtherOperatingIncomeFormat2"] == "150"
    assert previous["core:RawMaterialsConsumablesUsed"] == "10000"
    assert previous["core:StaffCostsEmployeeBenefitsExpense"] == "20000"
    assert previous["core:DepreciationAmortisationImpairmentExpense"] == "1500"
    assert previous["core:OtherOperatingExpensesFormat2"] == "4000"


def test_small_previous_format_1_lines(validations):
    previous = facts_in(validations["small-with-comparatives"], "prev-dur")

    assert previous["core:CostSales"] == "10000"
    assert previous["core:GrossProfitLoss"] == "80000"
    assert previous["core:AdministrativeExpenses"] == "25500"
    assert previous["core:OperatingProfitLoss"] == "54500"
    assert previous["core:OtherInterestReceivableSimilarIncomeFinanceIncome"] == "150"


def test_first_period_has_only_this_periods_facts(validations):
    contexts = {fact.context for fact in validations["first-period"].facts}

    assert not any(context.startswith("prev-") for context in contexts)
    assert DOCUMENTS["first-period"].count("<th ") == 2
    assert DOCUMENTS["micro-with-comparatives"].count("<th ") == 4
    assert "31 March 2024<br/>" in DOCUMENTS["micro-with-comparatives"]


def test_dormant_accounts_omit_a_nil_profit_and_loss_account(validations):
    nil = validations["dormant-with-nil-comparatives"]
    after_trading = validations["dormant-after-trading"]

    assert nil.values("core:ProfitLoss") == {}
    assert facts_in(nil, "prev-end")["core:NetAssetsLiabilities"] == "100"
    assert after_trading.values("core:ProfitLoss") == {"dur": "0", "prev-dur": "44650"}
    for validation in (nil, after_trading):
        assert facts_in(validation, "dur")["bus:EntityDormantTruefalse"] == "true"


@pytest.mark.parametrize("form", get_args(LegalForm))
def test_legal_form_is_tagged_with_its_member(validations, form):
    fact = next(
        fact
        for fact in validations[f"legal-form-{form}"].facts
        if fact.name == "bus:LegalFormEntity"
    )

    assert fact.dimensions == {"bus:LegalFormEntityDimension": LEGAL_FORM_MEMBERS[form]}


def test_companies_limited_by_guarantee_have_members_funds():
    assert "Members' funds" in DOCUMENTS["legal-form-private-company-limited-by-guarantee"]
    assert "Shareholders' funds" in DOCUMENTS["legal-form-private-limited-company"]
