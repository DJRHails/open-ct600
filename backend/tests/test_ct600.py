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
    }
    for section, values in overrides.items():
        answers[section] = {**answers[section], **values}
    return CT600Return.model_validate(answers)


def boxes(ct600: CT600Return) -> dict[int, Decimal]:
    return {box.number: box.value for box in compute_return(ct600).boxes}


def test_profit_boxes_follow_the_ct600_arithmetic():
    result = boxes(make_return())

    # 120,000 - 60,000 expenses + 2,000 depreciation + 1,000 disallowable - 5,000 allowances
    assert result[155] == 58_000
    assert result[160] == 3_000
    assert result[165] == 55_000
    assert result[170] == 500
    assert result[235] == 55_500
    assert result[305] == 500
    assert result[315] == 55_000


def test_tax_boxes_show_marginal_relief():
    result = boxes(make_return())

    assert result[329] == 1
    assert (result[330], result[335], result[340]) == (2024, 55_000, 25)
    assert result[430] == Decimal("13750.00")
    # 3/200 x (250,000 - 55,000)
    assert result[435] == Decimal("2925.00")
    assert result[440] == result[510] == Decimal("10825.00")
    assert 380 not in result


def test_straddling_period_fills_both_financial_year_rows():
    result = boxes(make_return(period={"start": "2023-01-01", "end": "2023-12-31"}))

    assert (result[330], result[380]) == (2022, 2023)
    assert result[335] + result[385] == result[315]


def test_accounts_are_derived_from_the_answers():
    accounts = compute_return(make_return()).accounts

    assert accounts.profit_before_tax == 60_500
    assert accounts.profit_after_tax == Decimal("49675.00")
    assert accounts.net_current_assets == 55_000
    assert accounts.net_assets == 60_000
    assert accounts.profit_and_loss_reserve == 59_900


def test_trading_loss_is_carried_forward():
    computation = compute_return(
        make_return(
            profit_and_loss={"turnover": 50_000}, tax_adjustments={"qualifying_donations": 0}
        )
    )

    by_number = {box.number: box.value for box in computation.boxes}
    # 50,000 - 60,000 + 2,000 + 1,000 - 5,000
    assert computation.trading_loss_arising == 12_000
    assert by_number[155] == by_number[160] == 0
    assert computation.losses_carried_forward == 15_000
    assert by_number[315] == 500


def test_donations_cannot_exceed_profits():
    result = boxes(
        make_return(
            profit_and_loss={"turnover": 0, "interest_income": 100},
            tax_adjustments={"qualifying_donations": 5_000},
        )
    )

    assert result[305] == 100
    assert result[315] == 0
    assert result[440] == 0


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


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"company": {"registration_number": "1234"}}, "company registration number"),
        ({"company": {"utr": "12345"}}, "Unique Taxpayer Reference"),
        ({"period": {"start": "2024-04-01", "end": "2025-06-30"}}, "longer than 12 months"),
        ({"profit_and_loss": {"turnover": -1}}, "greater than or equal to 0"),
        ({"tax_adjustments": {"disallowable_expenses": 60_001}}, "Disallowable expenses"),
        ({"balance_sheet": {"goodwill": 1}}, "Extra inputs are not permitted"),
    ],
)
def test_invalid_answers_are_rejected(overrides, message):
    with pytest.raises(ValidationError, match=message):
        make_return(**overrides)


def test_disallowable_expenses_error_points_at_the_tax_adjustments_section():
    with pytest.raises(ValidationError) as caught:
        make_return(tax_adjustments={"disallowable_expenses": 60_001})

    assert caught.value.errors()[0]["loc"] == ("tax_adjustments",)
