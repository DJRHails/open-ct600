from decimal import Decimal

import pytest
from pydantic import ValidationError

from open_ct600.ct600 import CT600Return, compute_return


def make_return(**overrides) -> CT600Return:
    answers = {
        "company": {
            "name": "Acme Widgets Ltd",
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
            "creditors_within_one_year": 15_000,
            "creditors_after_one_year": 5_000,
            "called_up_share_capital": 100,
        },
        "accounts": {
            "standard": "micro",
            "approval_date": "2025-06-30",
            "directors": ["Ada Lovelace", "Charles Babbage"],
            "signing_director": "Ada Lovelace",
            "average_employees": 2,
            "trading_status": "trading",
        },
    }
    for section, values in overrides.items():
        current = answers.get(section)
        answers[section] = {**current, **values} if isinstance(current, dict) else values
    return CT600Return.model_validate(answers)


def boxes(ct600: CT600Return) -> dict[str, Decimal]:
    return {box.box: box.value for box in compute_return(ct600).boxes}


def error_locations(caught: pytest.ExceptionInfo[ValidationError]) -> list[tuple]:
    return [error["loc"] for error in caught.value.errors()]


def test_profit_boxes_follow_the_ct600_arithmetic():
    result = boxes(make_return())

    # 120,000 - 60,000 expenses + 2,000 depreciation + 1,000 disallowable - 5,000 allowances
    assert result["155"] == 58_000
    # The 3,000 of losses brought forward are from April 2017 or later: box 285 (s45A)
    assert result["160"] == 0
    assert result["165"] == 58_000
    assert result["170"] == 500
    assert result["235"] == 58_500
    assert (result["285"], result["295"], result["300"]) == (3_000, 3_000, 55_500)
    assert result["305"] == 500
    assert result["315"] == 55_000


def test_tax_boxes_show_marginal_relief():
    result = boxes(make_return())

    assert result["329"] == 1
    assert (result["330"], result["335"], result["340"]) == (2024, 55_000, 25)
    assert result["430"] == Decimal("13750.00")
    # 3/200 x (250,000 - 55,000)
    assert result["435"] == Decimal("2925.00")
    assert result["440"] == result["510"] == Decimal("10825.00")
    assert "380" not in result


def test_straddling_period_fills_both_financial_year_rows():
    result = boxes(
        make_return(
            period={"start": "2023-01-01", "end": "2023-12-31"},
            accounts={"approval_date": "2024-03-01"},
        )
    )

    assert (result["330"], result["380"]) == (2022, 2023)
    assert result["335"] + result["385"] == result["315"]


def test_accounts_are_derived_from_the_answers():
    accounts = compute_return(make_return()).accounts

    assert accounts.profit_before_tax == 60_500
    assert accounts.profit_after_tax == Decimal("49675.00")
    assert accounts.net_current_assets == 55_000
    assert accounts.net_assets == 60_000
    assert accounts.profit_and_loss_reserve == 59_900


def test_micro_entity_balance_sheet_includes_every_format_item():
    # The FRC 2026 micro-entity example: 50,000 + 1,000 - 15,000 = 36,000 net current assets;
    # + 8,000 fixed = 44,000; - 5,000 - 1,000 - 2,000 = 36,000 net assets.
    sheet = {
        "called_up_share_capital_not_paid": 0,
        "fixed_assets": 8_000,
        "current_assets": 50_000,
        "prepayments_and_accrued_income": 1_000,
        "creditors_within_one_year": 15_000,
        "creditors_after_one_year": 5_000,
        "provisions": 1_000,
        "accruals_and_deferred_income": 2_000,
        "called_up_share_capital": 100,
    }
    accounts = compute_return(make_return(balance_sheet=sheet)).accounts

    assert accounts.net_current_assets == 36_000
    assert accounts.total_assets_less_current_liabilities == 44_000
    assert accounts.net_assets == 36_000
    assert accounts.profit_and_loss_reserve == 35_900


def test_share_capital_not_paid_counts_towards_total_assets():
    accounts = compute_return(
        make_return(balance_sheet={"called_up_share_capital_not_paid": 100})
    ).accounts

    assert accounts.total_assets_less_current_liabilities == 65_100
    assert accounts.net_assets == 60_100


def test_trading_loss_is_carried_forward():
    computation = compute_return(
        make_return(
            profit_and_loss={"turnover": 50_000}, tax_adjustments={"qualifying_donations": 0}
        )
    )

    by_box = {box.box: box.value for box in computation.boxes}
    # 50,000 - 60,000 + 2,000 + 1,000 - 5,000
    assert computation.trading_loss_arising == 12_000
    assert by_box["155"] == by_box["160"] == 0
    # 500 of the 3,000 brought forward relieve the interest (box 285): 2,500 + 12,000 remain
    assert by_box["285"] == 500
    assert computation.losses_carried_forward == 14_500
    assert by_box["315"] == 0


def test_donations_cannot_exceed_profits():
    result = boxes(
        make_return(
            profit_and_loss={"turnover": 0, "interest_income": 100},
            tax_adjustments={"qualifying_donations": 5_000, "losses_brought_forward": 0},
        )
    )

    assert result["305"] == 100
    assert result["315"] == 0
    assert result["440"] == 0


def test_dormant_company_owes_nothing():
    empty = dict.fromkeys(
        [
            "turnover",
            "interest_income",
            "cost_of_sales",
            "staff_costs",
            "depreciation",
            "other_expenses",
        ],
        0,
    )
    no_adjustments = dict.fromkeys(
        [
            "disallowable_expenses",
            "capital_allowances",
            "losses_brought_forward",
            "qualifying_donations",
        ],
        0,
    )
    computation = compute_return(make_return(profit_and_loss=empty, tax_adjustments=no_adjustments))

    assert computation.tax.tax_chargeable == 0
    assert computation.losses_carried_forward == 0


def test_identifiers_are_normalised():
    ct600 = make_return(company={"registration_number": " sc 123456 ", "utr": "12345 67890"})

    assert ct600.company.registration_number == "SC123456"
    assert ct600.company.utr == "1234567890"


def test_company_type_defaults_to_a_uk_trading_company():
    assert make_return().company.company_type == 0
    assert make_return(company={"company_type": 8}).company.company_type == 8


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"company": {"registration_number": "1234"}}, "company registration number"),
        ({"company": {"utr": "12345"}}, "Unique Taxpayer Reference"),
        ({"company": {"company_type": 12}}, "less than or equal to 11"),
        ({"company": {"principal_activity": " "}}, "at least 1 character"),
        ({"period": {"start": "2024-04-01", "end": "2025-06-30"}}, "longer than 12 months"),
        ({"profit_and_loss": {"turnover": -1}}, "greater than or equal to 0"),
        ({"tax_adjustments": {"disallowable_expenses": 60_001}}, "Disallowable expenses"),
        ({"balance_sheet": {"goodwill": 1}}, "Extra inputs are not permitted"),
        ({"balance_sheet": {"provisions": -1}}, "greater than or equal to 0"),
        ({"accounts": {"standard": "large"}}, "'micro' or 'small'"),
        ({"accounts": {"directors": []}}, "at least 1 item"),
        ({"accounts": {"average_employees": -1}}, "greater than or equal to 0"),
        ({"accounts": {"trading_status": "dormant"}}, "'never_traded'"),
    ],
)
def test_invalid_answers_are_rejected(overrides, message):
    with pytest.raises(ValidationError, match=message):
        make_return(**overrides)


def test_accounts_details_are_required():
    answers = make_return().model_dump(mode="json", exclude={"accounts"})

    with pytest.raises(ValidationError) as caught:
        CT600Return.model_validate(answers)

    assert error_locations(caught) == [("accounts",)]


def test_disallowable_expenses_error_points_at_the_tax_adjustments_section():
    with pytest.raises(ValidationError) as caught:
        make_return(tax_adjustments={"disallowable_expenses": 60_001})

    assert error_locations(caught) == [("tax_adjustments",)]


def test_signing_director_must_be_one_of_the_directors():
    with pytest.raises(ValidationError) as caught:
        make_return(accounts={"signing_director": "Grace Hopper"})

    assert error_locations(caught) == [("accounts", "signing_director")]
    assert "director who signed" in caught.value.errors()[0]["msg"]


def test_each_director_is_listed_once():
    with pytest.raises(ValidationError) as caught:
        make_return(accounts={"directors": ["Ada Lovelace", "ada lovelace"]})

    assert error_locations(caught) == [("accounts", "directors", 1)]


@pytest.mark.parametrize("approved", ["2025-03-31", "2025-01-01"])
def test_accounts_are_approved_after_the_period_ends(approved):
    with pytest.raises(ValidationError) as caught:
        make_return(accounts={"approval_date": approved})

    assert error_locations(caught) == [("accounts", "approval_date")]
    assert "after the end of the accounting period" in caught.value.errors()[0]["msg"]


def loans_page(loan: dict[str, str]) -> dict:
    return {"BeforeEndPeriod": "no", "LoansInformation": {"Loan": [loan]}}


LOANS_PAGE = loans_page({"Name": "Ada Lovelace", "AmountOfLoan": "6000"})


def test_supplementary_pages_are_completed_with_their_calculated_boxes():
    ct600 = make_return(supplementary_pages={"A": LOANS_PAGE})

    # 6,000 x 33.75% (loans made 6 April 2022 to 5 April 2026) = 2,025.00
    assert compute_return(ct600).pages == {
        "A": {
            "BeforeEndPeriod": "no",
            "LoansInformation": {
                "Loan": [{"Name": "Ada Lovelace", "AmountOfLoan": "6000"}],
                "TotalLoans": "6000",
                "TaxChargeable": "2025.00",
            },
            "TaxPayable": "2025.00",
        }
    }
    assert ct600.supplementary_pages == {"A": LOANS_PAGE}
    assert compute_return(make_return()).pages == {}


def test_calculated_boxes_cannot_be_answered():
    page = {**LOANS_PAGE, "TaxPayable": "2025.00"}

    with pytest.raises(ValidationError) as caught:
        make_return(supplementary_pages={"A": page})

    (error,) = caught.value.errors()
    assert error["loc"] == ("supplementary_pages", "A", "TaxPayable")
    assert error["ctx"]["box"] == "A80"
    assert "calculated from your other answers" in error["msg"]


def test_page_problems_are_located_inside_the_page():
    loan = {"Name": "X", "AmountOfLoan": "0"}
    page = loans_page(loan)

    with pytest.raises(ValidationError) as caught:
        make_return(supplementary_pages={"A": page})

    errors = caught.value.errors()
    assert [error["loc"] for error in errors] == [
        ("supplementary_pages", "A", "LoansInformation", "Loan", 0, "Name"),
        ("supplementary_pages", "A", "LoansInformation", "Loan", 0, "AmountOfLoan"),
    ]
    assert errors[0]["msg"] == "Enter name of participator or associate, 2 to 56 characters"
    assert errors[0]["ctx"]["box"] == "A10A"
    assert errors[1]["input"] == "0"


def test_unknown_page_codes_are_rejected():
    with pytest.raises(ValidationError) as caught:
        make_return(supplementary_pages={"O": {}})

    assert error_locations(caught)[0][:2] == ("supplementary_pages", "O")


def test_the_dormant_northern_ireland_page_cannot_be_filed():
    with pytest.raises(ValidationError) as caught:
        make_return(supplementary_pages={"G": {}})

    assert error_locations(caught) == [("supplementary_pages", "G")]
    assert "Northern Ireland" in caught.value.errors()[0]["msg"]


def test_a_trading_loss_is_recorded_in_boxes_780_and_785():
    # Review M4. CT600 guide: losses of trades carried on in the UK go in box 780, and the
    # maximum available for surrender as group relief (CTA 2010 s99-s100) in box 785.
    computation = compute_return(
        make_return(profit_and_loss={"turnover": 20_000, "other_expenses": 60_000})
    )

    result = boxes_of(computation)
    # 20,000 - (20,000 + 30,000 + 2,000 + 60,000) + 2,000 depreciation + 1,000 disallowable
    # - 5,000 capital allowances = -94,000
    assert (result["155"], result["780"], result["785"]) == (0, 94_000, 94_000)


def test_boxes_780_and_785_are_not_given_without_a_loss():
    assert "780" not in boxes_of(compute_return(make_return()))


def boxes_of(computation) -> dict[str, Decimal]:
    return {box.box: box.value for box in computation.boxes}


def test_a_period_of_account_over_12_months_is_refused_without_suggesting_a_split():
    # Review L4: the service prepares the accounts for the return's own period, so splitting
    # a longer period of account into two returns would file two sets of accounts that do not
    # exist. Refuse it plainly instead.
    with pytest.raises(ValidationError) as caught:
        make_return(
            period={"start": "2024-01-01", "end": "2025-06-30"},
            accounts={"approval_date": "2025-09-01"},
        )

    (error,) = caught.value.errors()
    assert error["loc"] == ("period",)
    assert "Split" not in error["msg"]
    assert "period of account" in error["msg"]
    assert "cannot prepare" in error["msg"]
