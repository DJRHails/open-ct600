"""UK Corporation Tax computation for a single accounting period.

The rules implemented here follow CTA 2010 as amended by Finance Act 2021:

* Financial year N runs from 1 April N to 31 March N+1.
* Up to FY2022 every company paid a flat rate of 19%.
* From FY2023 the small profits rate (19%) applies where augmented profits do not
  exceed the lower limit, the main rate (25%) applies at or above the upper limit, and
  marginal relief tapers between the two.
* The lower and upper limits are divided by the number of associated companies plus one,
  and reduced proportionally for accounting periods shorter than twelve months.
* An accounting period that straddles 1 April is split by days, and each slice is taxed
  with the rates and limits of its own financial year.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

PENCE = Decimal("0.01")
DAYS_IN_YEAR = 365
LARGE_COMPANY_THRESHOLD = 1_500_000


@dataclass(frozen=True)
class FinancialYearRates:
    """Corporation Tax rates and limits for one financial year.

    Attributes:
        main_rate: Rate charged on profits at or above the upper limit.
        small_profits_rate: Rate charged at or below the lower limit, or ``None``
            when the year has a single flat rate.
        lower_limit: Annual lower limit for the small profits rate.
        upper_limit: Annual upper limit for marginal relief.
        marginal_relief_fraction: Standard fraction used in the marginal relief formula.
    """

    main_rate: Decimal
    small_profits_rate: Decimal | None = None
    lower_limit: int = 50_000
    upper_limit: int = 250_000
    marginal_relief_fraction: Fraction = Fraction(3, 200)


_FLAT_19 = FinancialYearRates(main_rate=Decimal("0.19"))
_TAPERED = FinancialYearRates(main_rate=Decimal("0.25"), small_profits_rate=Decimal("0.19"))

RATES: dict[int, FinancialYearRates] = {
    2017: _FLAT_19,
    2018: _FLAT_19,
    2019: _FLAT_19,
    2020: _FLAT_19,
    2021: _FLAT_19,
    2022: _FLAT_19,
    2023: _TAPERED,
    2024: _TAPERED,
    2025: _TAPERED,
    2026: _TAPERED,
}
FIRST_SUPPORTED_YEAR = min(RATES)
LAST_SUPPORTED_YEAR = max(RATES)


class PeriodError(ValueError):
    """Raised when an accounting period cannot be taxed by this engine."""


@dataclass(frozen=True)
class FinancialYearSlice:
    """The part of an accounting period that falls in one financial year.

    Attributes:
        financial_year: The financial year, named by the calendar year it starts in.
        start: First day of the slice.
        end: Last day of the slice.
        days: Number of days in the slice.
        profits: Taxable profits apportioned to the slice, in whole pounds.
        augmented_profits: Profits plus exempt distributions apportioned to the slice.
        lower_limit: Lower limit after apportionment and associated companies.
        upper_limit: Upper limit after apportionment and associated companies.
        band: Which rate applies: ``flat``, ``small``, ``marginal`` or ``main``.
        rate: The rate charged on ``profits`` before marginal relief.
        tax: ``profits`` multiplied by ``rate``, in pounds and pence.
        marginal_relief: Marginal relief deducted for this slice, in pounds and pence.
    """

    financial_year: int
    start: date
    end: date
    days: int
    profits: int
    augmented_profits: Decimal
    lower_limit: Decimal
    upper_limit: Decimal
    band: str
    rate: Decimal
    tax: Decimal
    marginal_relief: Decimal


@dataclass(frozen=True)
class TaxComputation:
    """Corporation Tax due for one accounting period.

    Attributes:
        period_start: First day of the accounting period.
        period_end: Last day of the accounting period.
        taxable_profits: Profits chargeable to Corporation Tax, in whole pounds.
        augmented_profits: Taxable profits plus exempt distributions.
        associated_companies: Associated companies, excluding this company.
        slices: One entry per financial year the period touches.
        tax_before_relief: Tax at the applicable rates before marginal relief.
        marginal_relief: Total marginal relief.
        tax_chargeable: Corporation Tax chargeable after marginal relief.
        effective_rate: ``tax_chargeable`` divided by ``taxable_profits``.
        payment_due: Normal due date for payment: 9 months after the day after the period
            ends, so a period ending 30 June is due on 1 April.
        filing_due: Deadline for filing the CT600 (12 months after the period).
        may_pay_by_instalments: Whether augmented profits exceed the large company threshold,
            in which case tax is usually paid in quarterly instalments instead of on
            ``payment_due``.
    """

    period_start: date
    period_end: date
    taxable_profits: int
    augmented_profits: int
    associated_companies: int
    slices: tuple[FinancialYearSlice, ...]
    tax_before_relief: Decimal
    marginal_relief: Decimal
    tax_chargeable: Decimal
    effective_rate: Decimal
    payment_due: date
    filing_due: date
    may_pay_by_instalments: bool


def financial_year_of(day: date) -> int:
    """Return the financial year containing ``day``."""
    return day.year if day >= date(day.year, 4, 1) else day.year - 1


def add_months(day: date, months: int) -> date:
    """Add calendar months to ``day``, clamping to the last day of a shorter month."""
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    next_month_start = date(year + month // 12, month % 12 + 1, 1)
    last_day = (next_month_start - timedelta(days=1)).day
    return date(year, month, min(day.day, last_day))


def twelve_month_period_end(start: date) -> date:
    """Return the last day of a twelve-month period beginning on ``start``.

    A period starting on 29 February ends on 28 February of the following year.
    """
    if start.month == 2 and start.day == 29:
        return date(start.year + 1, 2, 28)
    return add_months(start, 12) - timedelta(days=1)


def validate_period(start: date, end: date) -> None:
    """Check that an accounting period is one this engine can tax.

    Raises:
        PeriodError: If the period is reversed, longer than twelve months, or touches a
            financial year whose rates are not known.
    """
    if end < start:
        raise PeriodError("The end date must be the same as or after the start date")
    if end > twelve_month_period_end(start):
        raise PeriodError(
            "An accounting period for Corporation Tax cannot be longer than 12 months. "
            "Split a longer period of account into two returns."
        )
    first_year, last_year = financial_year_of(start), financial_year_of(end)
    if first_year < FIRST_SUPPORTED_YEAR:
        raise PeriodError(f"Periods before 1 April {FIRST_SUPPORTED_YEAR} are not supported")
    if last_year > LAST_SUPPORTED_YEAR:
        raise PeriodError(
            f"Rates for the financial year starting 1 April {last_year} have not been "
            f"set yet. The latest supported period ends 31 March {LAST_SUPPORTED_YEAR + 1}."
        )


def average_main_rate(start: date, end: date) -> Fraction:
    """The main rate over a period, weighted by the days in each financial year.

    Used where legislation charges "the main rate" for an accounting period that may straddle
    a change of rate (the RDEC notional tax before April 2024, the CFC charge).
    """
    validate_period(start, end)
    parts = _split_by_financial_year(start, end)
    weighted = sum(
        (Fraction(RATES[year].main_rate) * ((part_end - part_start).days + 1))
        for year, part_start, part_end in parts
    )
    return Fraction(weighted) / ((end - start).days + 1)


def _split_by_financial_year(start: date, end: date) -> list[tuple[int, date, date]]:
    parts = []
    cursor = start
    while cursor <= end:
        year = financial_year_of(cursor)
        slice_end = min(end, date(year + 1, 3, 31))
        parts.append((year, cursor, slice_end))
        cursor = slice_end + timedelta(days=1)
    return parts


def _pence(amount: Decimal | Fraction) -> Decimal:
    if isinstance(amount, Fraction):
        amount = Decimal(amount.numerator) / Decimal(amount.denominator)
    return amount.quantize(PENCE, rounding=ROUND_HALF_UP)


def _apportion_whole_pounds(total: int, weights: list[int]) -> list[int]:
    """Split ``total`` by ``weights``, rounding each share and giving the remainder to the last.

    Returns:
        Whole-pound shares that sum exactly to ``total``.
    """
    weight_sum = sum(weights)
    shares = [
        int((Decimal(total) * weight / weight_sum).quantize(Decimal(1), ROUND_HALF_UP))
        for weight in weights[:-1]
    ]
    return [*shares, total - sum(shares)]


def _tax_slice(
    part: tuple[int, date, date],
    profits: int,
    augmented: Fraction,
    limit_scale: Fraction,
) -> FinancialYearSlice:
    year, start, end = part
    rates = RATES[year]
    lower = rates.lower_limit * limit_scale
    upper = rates.upper_limit * limit_scale
    relief = Fraction(0)
    if rates.small_profits_rate is None:
        band, rate = "flat", rates.main_rate
    elif augmented <= lower:
        band, rate = "small", rates.small_profits_rate
    elif augmented >= upper:
        band, rate = "main", rates.main_rate
    else:
        band, rate = "marginal", rates.main_rate
        relief = rates.marginal_relief_fraction * (upper - augmented) * profits / augmented
    return FinancialYearSlice(
        financial_year=year,
        start=start,
        end=end,
        days=(end - start).days + 1,
        profits=profits,
        augmented_profits=_pence(augmented),
        lower_limit=_pence(lower),
        upper_limit=_pence(upper),
        band=band,
        rate=rate,
        tax=_pence(profits * rate),
        marginal_relief=_pence(relief),
    )


def compute_corporation_tax(
    period_start: date,
    period_end: date,
    taxable_profits: int,
    associated_companies: int = 0,
    exempt_distributions: int = 0,
) -> TaxComputation:
    """Compute Corporation Tax for one accounting period.

    Args:
        period_start: First day of the accounting period.
        period_end: Last day of the accounting period (at most twelve months later).
        taxable_profits: Profits chargeable to Corporation Tax, in whole pounds.
        associated_companies: Number of associated companies, excluding this one.
        exempt_distributions: Exempt distributions (dividends) received from
            non-group companies, which count towards augmented profits.

    Returns:
        The tax computation, with one slice per financial year the period touches.

    Raises:
        PeriodError: If the period is not one this engine can tax.
        ValueError: If any amount is negative.
    """
    validate_period(period_start, period_end)
    if min(taxable_profits, associated_companies, exempt_distributions) < 0:
        raise ValueError("Profits, associated companies and distributions cannot be negative")

    parts = _split_by_financial_year(period_start, period_end)
    total_days = (period_end - period_start).days + 1
    is_full_year = period_end == twelve_month_period_end(period_start)
    year_fraction = Fraction(1) if is_full_year else Fraction(total_days, DAYS_IN_YEAR)
    augmented_total = taxable_profits + exempt_distributions

    day_counts = [(end - start).days + 1 for _, start, end in parts]
    profit_shares = _apportion_whole_pounds(taxable_profits, day_counts)
    slices = tuple(
        _tax_slice(
            part,
            profits=profits,
            augmented=Fraction(augmented_total * days, total_days),
            limit_scale=year_fraction * Fraction(days, total_days) / (associated_companies + 1),
        )
        for part, days, profits in zip(parts, day_counts, profit_shares, strict=True)
    )

    tax_before_relief = sum((s.tax for s in slices), Decimal(0))
    marginal_relief = sum((s.marginal_relief for s in slices), Decimal(0))
    tax_chargeable = tax_before_relief - marginal_relief
    effective_rate = (
        (tax_chargeable / taxable_profits).quantize(Decimal("0.0001"), ROUND_HALF_UP)
        if taxable_profits
        else Decimal(0)
    )
    return TaxComputation(
        period_start=period_start,
        period_end=period_end,
        taxable_profits=taxable_profits,
        augmented_profits=augmented_total,
        associated_companies=associated_companies,
        slices=slices,
        tax_before_relief=tax_before_relief,
        marginal_relief=marginal_relief,
        tax_chargeable=tax_chargeable,
        effective_rate=effective_rate,
        payment_due=add_months(period_end + timedelta(days=1), 9),
        filing_due=add_months(period_end, 12),
        may_pay_by_instalments=(
            augmented_total > LARGE_COMPANY_THRESHOLD * year_fraction / (associated_companies + 1)
        ),
    )
