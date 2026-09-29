"""Tax on loans to participators by close companies, and its relief: CT600A.

A close company that lends to a participator (or confers a benefit under arrangements) pays tax
under CTA 2010 s455 on what is still outstanding at the end of the period, at the rate for the
date the loan was made. Repayment, release or write-off gives relief (s458) at that same rate:
within nine months of the period end in Part 2 (A25 to A45), later in Part 3 (A50 to A70).
A80, the tax still payable, is box 480 of the CT600.

**The 35.75% rate.** The rate is 35.75% for loans made on or after 6 April 2026 (Budget 2025),
33.75% from 6 April 2022, 32.5% from 6 April 2016 and 25% before. HMRC's online service, and
the live CT600 schema this service files against (v1.994), only take the new rate from
6 April 2027; until then HMRC tells companies to file at 33.75% and amend the return after
6 April 2027 (https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service).
So the page is filed at the rate HMRC accepts (``FILED_RATE_LIMIT``), and the result also gives
the tax at the statutory rates, so the company can see the amendment it will need to make.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import Field

from open_ct600.model import StrictModel
from open_ct600.money import ZERO, add_months_to_month_end, pence, rate_on
from open_ct600.pages.tree import PageTree, Row
from open_ct600.problems import Problem

S455_RATES: tuple[tuple[date, Decimal], ...] = (
    (date(1900, 1, 1), Decimal("0.25")),
    (date(2016, 4, 6), Decimal("0.325")),
    (date(2022, 4, 6), Decimal("0.3375")),
    (date(2026, 4, 6), Decimal("0.3575")),
)
"""The s455 rate by the date a loan is made (the dividend upper rate for that tax year)."""

FILED_RATE_LIMIT = Decimal("0.3375")
"""The highest s455 rate the CT600 v1.994 schema and HMRC's online service accept (until
6 April 2027)."""

Table = Literal["loans", "repaid_within_nine_months", "repaid_later"]
_TABLES: dict[Table, tuple[str, str]] = {
    "loans": ("A10B", "part 1"),
    "repaid_within_nine_months": ("A25", "part 2"),
    "repaid_later": ("A50", "part 3"),
}


class ParticipatorLoanDates(StrictModel):
    """When the loans on CT600A were made, one date per table row, in the same order.

    Only needed when the s455 rate changes during the accounting period (for example on
    6 April 2026), since the rate depends on the date each loan was made.

    Attributes:
        loans: For each loan in part 1 (A10), the date it was made.
        repaid_within_nine_months: For each row of part 2 (A25), the date the loan repaid,
            released or written off was made.
        repaid_later: For each row of part 3 (A50), the date that loan was made.
    """

    loans: list[date] = Field(default_factory=list)
    repaid_within_nine_months: list[date] = Field(default_factory=list)
    repaid_later: list[date] = Field(default_factory=list)


@dataclass(frozen=True)
class LoansToParticipators:
    """The outcome of CT600A.

    Attributes:
        tax_payable: A80, tax payable as filed (box 480).
        relief_for_later_repayments: Whether A70 is claimed (tick box 485).
        statutory_tax_payable: A80 at the statutory rates (35.75% for loans from 6 April 2026).
        amendment_due: How much more tax the company will need to pay by amending the return
            once HMRC accepts the 35.75% rate (6 April 2027).
    """

    tax_payable: Decimal
    relief_for_later_repayments: bool
    statutory_tax_payable: Decimal
    amendment_due: Decimal


def s455_rate(made_on: date) -> Decimal:
    """The statutory s455 rate for a loan made on ``made_on``."""
    return rate_on(made_on, S455_RATES)


def filed_s455_rate(made_on: date) -> Decimal:
    """The s455 rate the return is filed at for a loan made on ``made_on``."""
    return min(s455_rate(made_on), FILED_RATE_LIMIT)


def nine_months_after(period_end: date) -> date:
    """The last day for Part 2 relief: nine months after the period end (month ends kept)."""
    return add_months_to_month_end(period_end, 9)


def _table_rows(page: PageTree, table: Table) -> list[Row]:
    box = _TABLES[table][0]
    return page.rows(box)


def _loan_dates(
    page: PageTree,
    period: tuple[date, date],
    dates: ParticipatorLoanDates | None,
    problems: list[Problem],
) -> dict[Table, list[date]] | None:
    """Each row's loan date: given, or the period start when the rate cannot change."""
    start, end = period
    rate_changes = s455_rate(start) != s455_rate(end)
    found: dict[Table, list[date]] = {}
    for table, (_, part) in _TABLES.items():
        rows = _table_rows(page, table)
        given = getattr(dates, table) if dates is not None else []
        location = ("participator_loan_dates", table)
        if not given and not rate_changes:
            found[table] = [start] * len(rows)
        elif len(given) != len(rows):
            problems.append(
                Problem(
                    location,
                    f"Enter the date each loan in {part} of CT600A was made, one for each of "
                    f"its {len(rows)} rows: the rate of tax on loans to participators changed "
                    "during this accounting period",
                )
            )
        else:
            late = [index for index, made in enumerate(given) if not start <= made <= end]
            problems += [
                Problem(
                    (*location, index),
                    "The date the loan was made must be in this accounting period",
                )
                for index in late
            ]
            found[table] = given
    return found if len(found) == len(_TABLES) else None


def today() -> date:
    """The day the return is prepared, which the repayment dates are checked against."""
    return date.today()


def later_relief_due(period_end: date, repaid: date) -> date:
    """When relief for a repayment more than nine months after the period end falls due.

    CTA 2010 s458(5) (CTM61610): nine months and a day after the end of the accounting period
    in which the repayment, release or write-off happened. The company's later accounting
    periods are taken to run for 12 months each, as the return does not know them.
    """
    end = period_end
    while end < repaid:
        end = add_months_to_month_end(end, 12)
    return nine_months_after(end) + timedelta(days=1)


def _check_relief_rows(page: PageTree, period_end: date) -> None:
    limit = nine_months_after(period_end)
    filed = today()
    for row in page.rows("A25"):
        _check_amounts(row, "A25B", "A25C")
        made = row.day("A25D")
        if made is not None and not period_end < made <= limit:
            row.problem(
                "A25D",
                f"The date of repayment, release or write-off must be after {period_end:%-d %B %Y} "
                f"and no later than {limit:%-d %B %Y}; enter later ones in part 3",
            )
        elif made is not None and made > filed:
            row.problem("A25D", _FUTURE)
    for row in page.rows("A50"):
        _check_amounts(row, "A50B", "A50C")
        made = row.day("A50D")
        if made is not None and made <= limit:
            row.problem(
                "A50D",
                f"The date of repayment, release or write-off must be after "
                f"{limit:%-d %B %Y}; enter earlier ones in part 2",
            )
        elif made is not None and later_relief_due(period_end, made) > filed:
            # Review M5: part 3 is only for relief already due when the return is filed.
            due = later_relief_due(period_end, made)
            row.problem(
                "A50D",
                f"Relief for this repayment is not due until {due:%-d %B %Y} (nine months and "
                "a day after the end of the accounting period it was made in, CTA 2010 "
                "s458(5)): leave it out of this return and claim it once it is due",
            )


_FUTURE = "The date of repayment, release or write-off cannot be in the future"


def _check_amounts(row: Row, repaid: str, released: str) -> None:
    if row.amount(repaid) <= 0 and row.amount(released) <= 0:
        row.problem(repaid, "Enter the amount repaid, or the amount released or written off")


def _tax(rows: list[Row], amounts: tuple[str, ...], dates: list[date], statutory: bool) -> Decimal:
    rate = s455_rate if statutory else filed_s455_rate
    return pence(
        sum(
            (
                sum((row.amount(box) for box in amounts), ZERO) * rate(made)
                for row, made in zip(rows, dates, strict=True)
            ),
            ZERO,
        )
    )


@dataclass(frozen=True)
class _Part:
    table: Table
    columns: tuple[str, str]
    totals: tuple[str, str, str, str]
    """Boxes: total of column B, total of column C, both, relief due."""


_PARTS = (
    _Part("repaid_within_nine_months", ("A25B", "A25C"), ("A30", "A35", "A40", "A45")),
    _Part("repaid_later", ("A50B", "A50C"), ("A55", "A60", "A65", "A70")),
)


def _relief(page: PageTree, part: _Part, dates: list[date]) -> tuple[Decimal, Decimal]:
    """Fill a relief part's totals; return its relief as filed and at statutory rates."""
    rows = _table_rows(page, part.table)
    if not rows:
        return ZERO, ZERO
    repaid_box, released_box, total_box, relief_box = part.totals
    repaid = page.total(part.columns[0])
    released = page.total(part.columns[1])
    page.set(repaid_box, repaid if page.answered_in_any_row(part.columns[0]) else None)
    page.set(released_box, released if page.answered_in_any_row(part.columns[1]) else None)
    page.set(total_box, repaid + released)
    relief = _tax(rows, part.columns, dates, statutory=False)
    page.set(relief_box, relief)
    return relief, _tax(rows, part.columns, dates, statutory=True)


def compute_loans_to_participators(
    page: PageTree,
    period_start: date,
    period_end: date,
    dates: ParticipatorLoanDates | None,
) -> tuple[LoansToParticipators | None, list[Problem]]:
    """Fill CT600A's totals, tax and relief.

    Args:
        page: The CT600A answers; totals and tax boxes are filled in.
        period_start: Box 30.
        period_end: Box 35.
        dates: When each loan was made, needed if the s455 rate changes in the period.

    Returns:
        The page's outcome (``None`` when the loan dates are missing), and problems with the
        answers outside the page (the loan dates). Problems on the page go to ``page.problems``.
    """
    problems: list[Problem] = []
    loan_dates = _loan_dates(page, (period_start, period_end), dates, problems)
    _check_relief_rows(page, period_end)
    if loan_dates is None:
        return None, problems
    loans = _table_rows(page, "loans")
    charged = statutory_charged = ZERO
    if loans:
        page.set("A15", page.total("A10B"))
        charged = _tax(loans, ("A10B",), loan_dates["loans"], statutory=False)
        statutory_charged = _tax(loans, ("A10B",), loan_dates["loans"], statutory=True)
        page.set("A20", charged)
    elif _table_rows(page, "repaid_within_nine_months") or _table_rows(page, "repaid_later"):
        page.problem("A15", "Enter the loans in part 1 before claiming relief for repaying them")
    reliefs = [_relief(page, part, loan_dates[part.table]) for part in _PARTS]
    repaid = page.amount("A40") + page.amount("A65")
    if loans and repaid > page.amount("A15"):
        page.problem(
            "A40",
            "The amounts repaid, released or written off in parts 2 and 3 cannot be more than "
            "the loans in part 1",
        )
    tax_payable = max(ZERO, charged - sum(filed for filed, _ in reliefs))
    statutory = max(ZERO, statutory_charged - sum(full for _, full in reliefs))
    page.set("A80", tax_payable)
    outcome = LoansToParticipators(
        tax_payable=tax_payable,
        relief_for_later_repayments=page.amount("A70") > 0,
        statutory_tax_payable=statutory,
        amendment_due=statutory - tax_payable,
    )
    return outcome, problems
