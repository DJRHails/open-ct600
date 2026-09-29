"""CT600 box 4, type of company: the rates each type pays (review finding H1)."""

from datetime import date
from decimal import Decimal

import pytest
from answers import boxes, compute, problems
from test_hmrc_xml import build, make_return

from open_ct600.hmrc.validate import validate_return
from open_ct600.tax import RateBasis, compute_corporation_tax

SMALL_PROFITS = {"turnover": 30_000}


@pytest.mark.parametrize(
    ("company_type", "rate", "tax"),
    [
        (0, 19, "5700.00"),  # small profits rate
        (1, 20, "6000.00"),  # authorised unit trust or OEIC: 20% (rule 9202, CTA 2010 s618)
        (2, 25, "7500.00"),  # close investment-holding company: main rate (9203, s18N)
        (3, 25, "7500.00"),  # liquidation, second or later year: main rate (9143)
        (9, 25, "7500.00"),  # REIT group residual company: main rate (9143)
        (11, 25, "7500.00"),  # non-resident company: main rate (9143)
    ],
)
def test_each_supported_company_type_pays_its_rate(company_type, rate, tax):
    computation = compute(company={"company_type": company_type}, profit_and_loss=SMALL_PROFITS)

    result = boxes(computation)
    assert (result["340"], result["440"]) == (rate, Decimal(tax))
    # Box 329 (small profits rate or marginal relief) only for companies that can have it
    # (rules 9398, 9399, 9415, 9874).
    assert ("329" in result and result["329"] == 1) is (company_type == 0)


@pytest.mark.parametrize("company_type", [1, 2, 3, 9, 11])
def test_returns_for_each_company_type_are_accepted_by_hmrc(company_type):
    ct600 = make_return(company={"company_type": company_type}, profit_and_loss=SMALL_PROFITS)

    assert validate_return(build(ct600)) == []


@pytest.mark.parametrize(("company_type", "text"), [(5, "Insurance"), (10, "tax-exempt")])
def test_company_types_the_service_does_not_model_are_refused(company_type, text):
    found = problems(company={"company_type": company_type})

    assert text in found[("company", "company_type")]


def test_main_rate_basis_has_no_marginal_relief():
    tax = compute_corporation_tax(
        date(2024, 4, 1), date(2025, 3, 31), 100_000, basis=RateBasis.MAIN_RATE
    )

    assert (tax.tax_chargeable, tax.marginal_relief) == (Decimal("25000.00"), 0)
    assert tax.slices[0].band == "main"


def test_main_rate_basis_before_april_2023_is_the_single_rate():
    tax = compute_corporation_tax(
        date(2022, 4, 1), date(2023, 3, 31), 100_000, basis=RateBasis.MAIN_RATE
    )

    assert tax.tax_chargeable == Decimal("19000.00")


def test_fund_basis_is_20_percent_in_every_year():
    tax = compute_corporation_tax(
        date(2022, 10, 1), date(2023, 9, 30), 100_000, basis=RateBasis.FUND
    )

    assert [part.rate for part in tax.slices] == [Decimal("0.20"), Decimal("0.20")]
    assert tax.tax_chargeable == Decimal("20000.00")
