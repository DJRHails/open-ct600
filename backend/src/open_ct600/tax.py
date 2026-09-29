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
* Some companies cannot have the small profits rate or marginal relief (``RateBasis``,
  from CT600 box 4): close investment-holding companies (CTA 2010 s18N), companies in the
  second or later year of liquidation, REIT residual companies and non-resident companies
  pay the main rate (HMRC rules 9143, 9203); authorised unit trusts and OEICs pay 20%
  (s618, rule 9202).
* Ring fence profits of an oil extraction trade (CT600I) are charged at the ring fence rates
  (s279A): 30% main, 19% small, marginal relief fraction 11/400, with the same limits and
  augmented profits as the rest of the company's profits. Supported from FY2023.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from fractions import Fraction

PENCE = Decimal("0.01")
DAYS_IN_YEAR = 365
LARGE_COMPANY_THRESHOLD = 1_500_000
FUND_RATE = Decimal("0.20")
"""The rate for authorised unit trusts and OEICs: the basic rate of income tax (s618)."""


class RateBasis(StrEnum):
    """Which rates a company pays, by its type (CT600 box 4).

    Attributes:
        STANDARD: The small profits rate and marginal relief where profits allow.
        MAIN_RATE: The main rate on all profits (no small profits rate or marginal relief).
        FUND: The authorised investment fund rate of 20%.
    """

    STANDARD = "standard"
    MAIN_RATE = "main_rate"
    FUND = "fund"


COMPANY_TYPE_RATES: dict[int, RateBasis] = {
    0: RateBasis.STANDARD,
    1: RateBasis.FUND,  # rule 9202, CTA 2010 s618: authorised investment funds at 20%
    2: RateBasis.MAIN_RATE,  # rules 9203, 9399, CTA 2010 s18N: close investment-holding
    3: RateBasis.MAIN_RATE,  # rules 9143, 9415: liquidation after the first year
    4: RateBasis.STANDARD,
    6: RateBasis.STANDARD,
    7: RateBasis.STANDARD,
    8: RateBasis.STANDARD,
    9: RateBasis.MAIN_RATE,  # rule 9143: REIT C residual company
    11: RateBasis.MAIN_RATE,  # rules 9143, 9874: non-resident company
}
"""The rates each supported company type (CT600 box 4) pays. Types 5 (insurance) and 10
(REIT C tax-exempt) need treatment this engine does not have, so are not supported."""


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
        ring_fence: The ring fence rates, or ``None`` where this engine does not support
            ring fence profits (before FY2023, when the ring fence limits were different).
    """

    main_rate: Decimal
    small_profits_rate: Decimal | None = None
    lower_limit: int = 50_000
    upper_limit: int = 250_000
    marginal_relief_fraction: Fraction = Fraction(3, 200)
    ring_fence: "RingFenceRates | None" = None


@dataclass(frozen=True)
class RingFenceRates:
    """Rates for ring fence profits (CTA 2010 s279A, s279B, s279C).

    Attributes:
        main_rate: The main ring fence profits rate.
        small_profits_rate: The small ring fence profits rate.
        marginal_relief_fraction: The ring fence marginal relief fraction.
    """

    main_rate: Decimal = Decimal("0.30")
    small_profits_rate: Decimal = Decimal("0.19")
    marginal_relief_fraction: Fraction = Fraction(11, 400)


_FLAT_19 = FinancialYearRates(main_rate=Decimal("0.19"))
_TAPERED = FinancialYearRates(
    main_rate=Decimal("0.25"), small_profits_rate=Decimal("0.19"), ring_fence=RingFenceRates()
)

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
class RingFenceSlice:
    """The ring fence profits of one financial year slice, taxed at the ring fence rates.

    Attributes:
        profits: Ring fence profits apportioned to the slice, in whole pounds.
        rate: The ring fence rate charged on them before marginal relief.
        tax: ``profits`` multiplied by ``rate``, in pounds and pence.
        marginal_relief: Ring fence marginal relief for the slice, in pounds and pence.
    """

    profits: int
    rate: Decimal
    tax: Decimal
    marginal_relief: Decimal


@dataclass(frozen=True)
class FinancialYearSlice:
    """The part of an accounting period that falls in one financial year.

    Attributes:
        financial_year: The financial year, named by the calendar year it starts in.
        start: First day of the slice.
        end: Last day of the slice.
        days: Number of days in the slice.
        profits: Taxable profits apportioned to the slice, in whole pounds, other than ring
            fence profits.
        augmented_profits: Profits plus exempt distributions apportioned to the slice.
        lower_limit: Lower limit after apportionment and associated companies.
        upper_limit: Upper limit after apportionment and associated companies.
        band: Which rate applies: ``flat``, ``small``, ``marginal``, ``main``, or ``fund``
            (the authorised investment fund rate).
        rate: The rate charged on ``profits`` before marginal relief.
        tax: ``profits`` multiplied by ``rate``, in pounds and pence.
        marginal_relief: Marginal relief deducted for this slice, in pounds and pence,
            including ring fence marginal relief.
        ring_fence: The slice's ring fence profits, if the company has any.
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
    ring_fence: RingFenceSlice | None = None

    @property
    def rows(self) -> tuple["RateRow", ...]:
        """The slice's lines of profit at a rate, as on the CT600 (boxes 335 to 375).

        The ordinary profits, then the ring fence profits at the ring fence rate; the ordinary
        line is left out when a ring fence company has no other profits.
        """
        rows = []
        if self.profits or self.ring_fence is None:
            rows.append(RateRow(self.profits, self.rate, self.tax))
        if self.ring_fence is not None:
            part = self.ring_fence
            rows.append(RateRow(part.profits, part.rate, part.tax))
        return tuple(rows)


@dataclass(frozen=True)
class RateRow:
    """Profits charged at one rate in one financial year.

    Attributes:
        profits: The profits, in whole pounds.
        rate: The rate.
        tax: The tax at that rate, in pounds and pence.
    """

    profits: int
    rate: Decimal
    tax: Decimal


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


def payment_due_date(period_end: date) -> date:
    """Return the normal date Corporation Tax is due: 9 months and 1 day after the period ends.

    That is 9 months after the day after the period, so a period ending 30 June is due on
    1 April (https://www.gov.uk/pay-corporation-tax). The frontend's ``filing/deadlines.ts``
    works this out the same way; both are tested against ``tests/fixtures/deadlines.json``.
    """
    return add_months(period_end + timedelta(days=1), 9)


def filing_due_date(period_end: date) -> date:
    """Return the deadline for filing the return: 12 months after the period ends.

    https://www.gov.uk/company-tax-returns. A period ending 29 February is due on 28 February.
    """
    return add_months(period_end, 12)


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
            "An accounting period for Corporation Tax cannot be longer than 12 months"
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


def _band(
    rates: FinancialYearRates, augmented: Fraction, limits: tuple[Fraction, Fraction], basis: str
) -> str:
    """Which rates apply: by the company's type, then by augmented profits and the limits."""
    lower, upper = limits
    if basis == RateBasis.FUND:
        return "fund"
    if rates.small_profits_rate is None:
        return "flat"
    if basis == RateBasis.MAIN_RATE or augmented >= upper:
        return "main"
    return "small" if augmented <= lower else "marginal"


def _ring_fence_part(
    rates: FinancialYearRates,
    band: str,
    profits: int,
    marginal: Fraction,
) -> RingFenceSlice:
    """Tax ring fence profits (s279A): 19% small, 30% main, fraction 11/400 in between.

    ``marginal`` is (upper limit - augmented profits) / augmented profits, 0 outside the
    marginal band; marginal relief is the fraction times it times the ring fence profits.
    """
    ring_fence = rates.ring_fence
    if ring_fence is None:
        raise PeriodError(
            "Ring fence profits (CT600I) are only supported for accounting periods from "
            "1 April 2023"
        )
    rate = ring_fence.small_profits_rate if band == "small" else ring_fence.main_rate
    relief = ring_fence.marginal_relief_fraction * marginal * profits
    return RingFenceSlice(
        profits=profits, rate=rate, tax=_pence(profits * rate), marginal_relief=_pence(relief)
    )


def _tax_slice(
    part: tuple[int, date, date],
    profits: tuple[int, int],
    augmented: Fraction,
    limit_scale: Fraction,
    basis: str,
) -> FinancialYearSlice:
    """Tax one financial year's slice.

    Args:
        part: The financial year and the slice's first and last days.
        profits: The slice's taxable profits, and the ring fence profits among them.
        augmented: The slice's augmented profits.
        limit_scale: What the annual limits are multiplied by for the slice.
        basis: The company's ``RateBasis``.
    """
    year, start, end = part
    total, ring_fence_profits = profits
    main_profits = total - ring_fence_profits
    rates = RATES[year]
    lower = rates.lower_limit * limit_scale
    upper = rates.upper_limit * limit_scale
    band = _band(rates, augmented, (lower, upper), basis)
    rate = {
        "fund": FUND_RATE,
        "small": rates.small_profits_rate or rates.main_rate,
    }.get(band, rates.main_rate)
    marginal = (upper - augmented) / augmented if band == "marginal" else Fraction(0)
    relief = rates.marginal_relief_fraction * marginal * main_profits
    ring_fence = None
    if ring_fence_profits:
        ring_fence = _ring_fence_part(rates, band, ring_fence_profits, marginal)
    return FinancialYearSlice(
        financial_year=year,
        start=start,
        end=end,
        days=(end - start).days + 1,
        profits=main_profits,
        augmented_profits=_pence(augmented),
        lower_limit=_pence(lower),
        upper_limit=_pence(upper),
        band=band,
        rate=rate,
        tax=_pence(main_profits * rate),
        marginal_relief=_pence(relief) + (ring_fence.marginal_relief if ring_fence else 0),
        ring_fence=ring_fence,
    )


def compute_corporation_tax(  # noqa: PLR0913 - the two options past five are keyword-only
    period_start: date,
    period_end: date,
    taxable_profits: int,
    associated_companies: int = 0,
    exempt_distributions: int = 0,
    *,
    basis: RateBasis = RateBasis.STANDARD,
    ring_fence_profits: int = 0,
) -> TaxComputation:
    """Compute Corporation Tax for one accounting period.

    Args:
        period_start: First day of the accounting period.
        period_end: Last day of the accounting period (at most twelve months later).
        taxable_profits: Profits chargeable to Corporation Tax, in whole pounds.
        associated_companies: Number of associated companies, excluding this one.
        exempt_distributions: Exempt distributions (dividends) received from
            non-group companies, which count towards augmented profits.
        basis: Which rates the company's type allows.
        ring_fence_profits: The part of ``taxable_profits`` that is ring fence profits
            (CT600 box 320), charged at the ring fence rates.

    Returns:
        The tax computation, with one slice per financial year the period touches.

    Raises:
        PeriodError: If the period is not one this engine can tax.
        ValueError: If any amount is negative, or ring fence profits exceed the profits.
    """
    validate_period(period_start, period_end)
    if min(taxable_profits, associated_companies, exempt_distributions, ring_fence_profits) < 0:
        raise ValueError("Profits, associated companies and distributions cannot be negative")
    if ring_fence_profits > taxable_profits:
        raise ValueError("Ring fence profits cannot be more than the taxable profits")

    parts = _split_by_financial_year(period_start, period_end)
    total_days = (period_end - period_start).days + 1
    is_full_year = period_end == twelve_month_period_end(period_start)
    year_fraction = Fraction(1) if is_full_year else Fraction(total_days, DAYS_IN_YEAR)
    augmented_total = taxable_profits + exempt_distributions

    day_counts = [(end - start).days + 1 for _, start, end in parts]
    profit_shares = _apportion_whole_pounds(taxable_profits, day_counts)
    ring_fence_shares = _apportion_whole_pounds(ring_fence_profits, day_counts)
    slices = tuple(
        _tax_slice(
            part,
            profits=(profits, ring_fence),
            augmented=Fraction(augmented_total * days, total_days),
            limit_scale=year_fraction * Fraction(days, total_days) / (associated_companies + 1),
            basis=basis,
        )
        for part, days, profits, ring_fence in zip(
            parts, day_counts, profit_shares, ring_fence_shares, strict=True
        )
    )

    tax_before_relief = sum(
        (s.tax + (s.ring_fence.tax if s.ring_fence else 0) for s in slices), Decimal(0)
    )
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
        payment_due=payment_due_date(period_end),
        filing_due=filing_due_date(period_end),
        may_pay_by_instalments=(
            augmented_total > LARGE_COMPANY_THRESHOLD * year_fraction / (associated_companies + 1)
        ),
    )
