"""Previous-period comparatives and legal form in the accounts details."""

import pytest
from answers import make_return, problems

COMPARATIVES = {
    "period": {"start": "2023-04-01", "end": "2024-03-31"},
    "profit_and_loss": {"turnover": 90_000, "staff_costs": 20_000},
    "balance_sheet": {"current_assets": 15_000, "called_up_share_capital": 100},
    "tax_on_profit": 13_300,
    "average_employees": 4,
}


def with_comparatives(**changes) -> dict:
    return {"accounts": {"comparatives": {**COMPARATIVES, **changes}}}


def test_first_period_has_no_comparatives_and_is_a_private_limited_company():
    details = make_return().accounts

    assert details.comparatives is None
    assert details.legal_form == "private-limited-company"


def test_comparatives_are_read():
    comparatives = make_return(**with_comparatives()).accounts.comparatives

    assert comparatives is not None
    assert comparatives.profit_and_loss.turnover == 90_000
    assert comparatives.balance_sheet.current_assets == 15_000
    assert comparatives.tax_on_profit == 13_300
    assert comparatives.average_employees == 4


def test_previous_average_employees_may_be_unknown():
    comparatives = make_return(**with_comparatives(average_employees=None)).accounts.comparatives

    assert comparatives is not None
    assert comparatives.average_employees is None


def test_a_previous_period_of_up_to_18_months_is_allowed():
    ct600 = make_return(**with_comparatives(period={"start": "2022-10-01", "end": "2024-03-31"}))

    assert ct600.accounts.comparatives is not None


def test_a_previous_period_longer_than_18_months_is_refused():
    found = problems(**with_comparatives(period={"start": "2022-09-30", "end": "2024-03-31"}))

    assert found == {
        ("accounts", "comparatives", "period", "end"): (
            "A period of account cannot be longer than 18 months, so it must end by 29 March 2024"
        )
    }


def test_the_previous_period_must_end_the_day_before_this_one_starts():
    found = problems(**with_comparatives(period={"start": "2023-03-01", "end": "2024-02-29"}))

    assert found == {
        ("accounts", "comparatives", "period", "end"): (
            "The previous period of account must end on 31 March 2024, the day before this "
            "period starts"
        )
    }


def test_a_reversed_previous_period_is_refused():
    found = problems(**with_comparatives(period={"start": "2024-04-01", "end": "2024-03-31"}))

    assert list(found) == [("accounts", "comparatives", "period", "end")]


@pytest.mark.parametrize(
    "changes",
    [
        {"profit_and_loss": {"turnover": -1}},
        {"balance_sheet": {"current_assets": -1}},
        {"tax_on_profit": -1},
        {"average_employees": -1},
    ],
)
def test_previous_figures_cannot_be_negative(changes):
    found = problems(**with_comparatives(**changes))

    assert len(found) == 1
    (location,) = found
    assert location[:2] == ("accounts", "comparatives")


def test_legal_forms_are_the_supported_members():
    ct600 = make_return(accounts={"legal_form": "private-company-limited-by-guarantee"})

    assert ct600.accounts.legal_form == "private-company-limited-by-guarantee"
    assert ("accounts", "legal_form") in problems(accounts={"legal_form": "public-limited-company"})
