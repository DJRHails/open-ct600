"""Rounding and time apportionment shared by the relief and page calculations.

Amounts are rounded half up, as HMRC's rules state ("round down for fractions less than half a
penny and round up for fractions of half a penny or greater"). Apportionment is by days, the
usual Corporation Tax basis; a full twelve-month period counts as one year even in a leap year.
"""

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from fractions import Fraction

from open_ct600.tax import DAYS_IN_YEAR, twelve_month_period_end

PENNY = Decimal("0.01")
ZERO = Decimal(0)


def _decimal(value: Decimal | Fraction | int) -> Decimal:
    if isinstance(value, Fraction):
        return Decimal(value.numerator) / Decimal(value.denominator)
    return Decimal(value)


def pence(value: Decimal | Fraction | int) -> Decimal:
    """Round to the nearest penny, half a penny up."""
    return _decimal(value).quantize(PENNY, rounding=ROUND_HALF_UP)


def pounds(value: Decimal | Fraction | int) -> int:
    """Round to the nearest pound, half a pound up."""
    return int(_decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def whole_pounds_down(value: Decimal | Fraction | int) -> int:
    """Round down to whole pounds, as for totals HMRC takes "in whole pounds"."""
    return int(_decimal(value).quantize(Decimal(1), rounding=ROUND_FLOOR))


def days_between(start: date, end: date) -> int:
    """Days from ``start`` to ``end``, counting both."""
    return (end - start).days + 1


def year_fraction(start: date, end: date) -> Fraction:
    """How much of a year the period is: 1 for twelve months, otherwise days over 365."""
    if end == twelve_month_period_end(start):
        return Fraction(1)
    return Fraction(days_between(start, end), DAYS_IN_YEAR)


def overlap(first: tuple[date, date], second: tuple[date, date]) -> tuple[date, date] | None:
    """The days two periods share, or ``None`` when they do not meet."""
    start, end = max(first[0], second[0]), min(first[1], second[1])
    return (start, end) if start <= end else None


def split_at(start: date, end: date, changes: Iterable[date]) -> list[tuple[date, date]]:
    """Split a period into parts at each change date that falls inside it.

    Args:
        start: First day of the period.
        end: Last day of the period.
        changes: Dates on which something (a rate) changes; each starts a new part.

    Returns:
        The parts, in order, covering the period exactly.
    """
    parts, cursor = [], start
    for change in sorted(changes):
        if cursor < change <= end:
            parts.append((cursor, change - timedelta(days=1)))
            cursor = change
    parts.append((cursor, end))
    return parts


def day_weighted_rate(start: date, end: date, rates: tuple[tuple[date, Decimal], ...]) -> Fraction:
    """The average of a rate that changes on given dates, weighted by days in the period.

    Args:
        start: First day of the period.
        end: Last day of the period.
        rates: ``(from, rate)`` pairs in date order; the first applies to all earlier dates.

    Returns:
        The exact day-weighted rate.
    """
    total = days_between(start, end)
    weighted = Fraction(0)
    for part_start, part_end in split_at(start, end, (change for change, _ in rates[1:])):
        weighted += Fraction(rate_on(part_start, rates)) * days_between(part_start, part_end)
    return weighted / total


def rate_on(day: date, rates: tuple[tuple[date, Decimal], ...]) -> Decimal:
    """The rate in force on ``day`` from ``(from, rate)`` pairs in date order."""
    applicable = rates[0][1]
    for change, rate in rates:
        if day >= change:
            applicable = rate
    return applicable


def add_months_to_month_end(day: date, months: int) -> date:
    """Add months; a month-end date stays at the month end (30 June + 9 months = 31 March)."""
    next_day = day + timedelta(days=1)
    target_month = day.month - 1 + months
    year, month = day.year + target_month // 12, target_month % 12 + 1
    if next_day.month != day.month:
        following = date(year + month // 12, month % 12 + 1, 1)
        return following - timedelta(days=1)
    last = (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)).day
    return date(year, month, min(day.day, last))
