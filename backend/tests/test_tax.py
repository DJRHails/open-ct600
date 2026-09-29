import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from open_ct600.tax import (
    PeriodError,
    add_months,
    compute_corporation_tax,
    filing_due_date,
    financial_year_of,
    payment_due_date,
)

FY2024_START, FY2024_END = date(2024, 4, 1), date(2025, 3, 31)


@pytest.mark.parametrize(
    ("profits", "band", "before_relief", "relief", "chargeable"),
    [
        (0, "small", "0.00", "0.00", "0.00"),
        (50_000, "small", "9500.00", "0.00", "9500.00"),
        # 25% of 100,000 less 3/200 x (250,000 - 100,000)
        (100_000, "marginal", "25000.00", "2250.00", "22750.00"),
        (250_000, "main", "62500.00", "0.00", "62500.00"),
        (300_000, "main", "75000.00", "0.00", "75000.00"),
    ],
)
def test_full_financial_year_bands(profits, band, before_relief, relief, chargeable):
    result = compute_corporation_tax(FY2024_START, FY2024_END, profits)

    assert [s.band for s in result.slices] == [band]
    assert result.tax_before_relief == Decimal(before_relief)
    assert result.marginal_relief == Decimal(relief)
    assert result.tax_chargeable == Decimal(chargeable)


def test_associated_companies_divide_the_limits():
    # Limits become 25,000 and 125,000: relief is 3/200 x (125,000 - 100,000) = 375
    result = compute_corporation_tax(FY2024_START, FY2024_END, 100_000, associated_companies=1)

    assert result.slices[0].lower_limit == Decimal("25000.00")
    assert result.slices[0].upper_limit == Decimal("125000.00")
    assert result.tax_chargeable == Decimal("24625.00")


def test_exempt_distributions_count_towards_augmented_profits():
    # Augmented 60,000: relief is 3/200 x (250,000 - 60,000) x 40,000 / 60,000 = 1,900
    result = compute_corporation_tax(FY2024_START, FY2024_END, 40_000, exempt_distributions=20_000)

    assert result.slices[0].band == "marginal"
    assert result.marginal_relief == Decimal("1900.00")
    assert result.tax_chargeable == Decimal("8100.00")


def test_short_period_reduces_the_limits_proportionally():
    # 183 days: upper limit 250,000 x 183/365 = 125,342.47
    result = compute_corporation_tax(date(2024, 4, 1), date(2024, 9, 30), 40_000)

    part = result.slices[0]
    assert part.days == 183
    assert part.lower_limit == Decimal("25068.49")
    assert part.upper_limit == Decimal("125342.47")
    assert result.marginal_relief == Decimal("1280.14")
    assert result.tax_chargeable == Decimal("8719.86")


def test_period_straddling_1_april_2023_is_split_by_days():
    result = compute_corporation_tax(date(2023, 1, 1), date(2023, 12, 31), 100_000)

    flat, tapered = result.slices
    assert (flat.financial_year, flat.days, flat.profits) == (2022, 90, 24_658)
    assert (tapered.financial_year, tapered.days, tapered.profits) == (2023, 275, 75_342)
    assert flat.band == "flat"
    assert flat.tax == Decimal("4685.02")
    assert tapered.band == "marginal"
    assert tapered.tax == Decimal("18835.50")
    # 3/200 x (188,356.16 - 75,342.47) x 75,342 / 75,342.47
    assert tapered.marginal_relief == Decimal("1695.20")
    assert result.tax_chargeable == Decimal("21825.32")


def test_twelve_month_period_in_a_leap_year_keeps_the_full_limits():
    # 366 days is still a twelve-month period, so the upper limit stays 250,000
    result = compute_corporation_tax(date(2023, 4, 1), date(2024, 3, 31), 250_100)

    assert result.slices[0].upper_limit == Decimal("250000.00")
    assert result.slices[0].band == "main"
    assert result.marginal_relief == Decimal(0)


def test_flat_rate_years_ignore_the_limits():
    result = compute_corporation_tax(date(2021, 4, 1), date(2022, 3, 31), 100_000)

    assert result.slices[0].band == "flat"
    assert result.tax_chargeable == Decimal("19000.00")


def test_due_dates():
    result = compute_corporation_tax(FY2024_START, FY2024_END, 1_000)

    assert result.payment_due == date(2026, 1, 1)
    assert result.filing_due == date(2026, 3, 31)


def test_payment_is_due_nine_months_after_the_day_after_the_period():
    result = compute_corporation_tax(date(2024, 7, 1), date(2025, 6, 30), 1_000)

    assert result.payment_due == date(2026, 4, 1)
    assert result.filing_due == date(2026, 6, 30)


@pytest.mark.parametrize(
    ("profits", "associated", "expected"),
    [(1_500_000, 0, False), (1_500_001, 0, True), (800_000, 1, True)],
)
def test_large_companies_may_pay_by_instalments(profits, associated, expected):
    result = compute_corporation_tax(FY2024_START, FY2024_END, profits, associated)

    assert result.may_pay_by_instalments is expected


def test_effective_rate():
    assert compute_corporation_tax(FY2024_START, FY2024_END, 100_000).effective_rate == Decimal(
        "0.2275"
    )
    assert compute_corporation_tax(FY2024_START, FY2024_END, 0).effective_rate == Decimal(0)


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        (date(2024, 4, 1), date(2024, 3, 31), "same as or after the start date"),
        (date(2024, 4, 1), date(2025, 4, 1), "cannot be longer than 12 months"),
        (date(2017, 3, 1), date(2017, 12, 31), "before 1 April 2017"),
        (date(2027, 1, 1), date(2027, 12, 31), "financial year starting 1 April 2027"),
    ],
)
def test_rejects_periods_it_cannot_tax(start, end, message):
    with pytest.raises(PeriodError, match=message):
        compute_corporation_tax(start, end, 1_000)


def test_rejects_negative_amounts():
    with pytest.raises(ValueError, match="cannot be negative"):
        compute_corporation_tax(FY2024_START, FY2024_END, -1)


def test_period_starting_29_february_may_end_28_february():
    result = compute_corporation_tax(date(2024, 2, 29), date(2025, 2, 28), 10_000)

    assert result.tax_chargeable == Decimal("1900.00")


@pytest.mark.parametrize(
    ("day", "year"),
    [(date(2024, 3, 31), 2023), (date(2024, 4, 1), 2024), (date(2025, 1, 1), 2024)],
)
def test_financial_year_of(day, year):
    assert financial_year_of(day) == year


def test_add_months_clamps_to_month_end():
    assert add_months(date(2024, 5, 31), 9) == date(2025, 2, 28)
    assert add_months(date(2023, 12, 31), 2) == date(2024, 2, 29)


def _deadline_cases() -> list[dict[str, str]]:
    path = Path(__file__).parent / "fixtures" / "deadlines.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("case", _deadline_cases(), ids=lambda case: case["case"])
def test_deadlines_match_the_shared_cases(case):
    """The frontend's ``filing/deadlines.ts`` is tested against the same cases."""
    end = date.fromisoformat(case["period_end"])

    assert payment_due_date(end).isoformat() == case["payment_due"]
    assert filing_due_date(end).isoformat() == case["filing_due"]
