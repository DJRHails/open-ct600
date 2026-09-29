"""CT600N: Residential Property Developer Tax (RPDT).

RPDT is 4% of a residential property developer's profits above its allowance (FA 2022 s33):
adjusted trading profit or loss (N230/N235) plus joint venture profits or losses (N240/N245),
floored at nil (N250); less loss relief and group relief (N255 to N265, N270); less the
allowance allocated for the period (N275, N280). N285 = 4% x N280 is box 497 of the CT600.

The allowance is £25 million a year, shared across a group by its allocation statement and
reduced pro rata (by days) for a short period (s43); the allowance entered in N275 cannot be
more than that. Loss relief (N255 and N265 together) is capped by s42: where profits exceed the
allowance, at half the excess less group relief (RPDT20440).
"""

from datetime import date
from decimal import Decimal
from fractions import Fraction

from open_ct600.money import ZERO, pence, whole_pounds_down, year_fraction
from open_ct600.pages.tree import PageTree

RPDT_RATE = Decimal("0.04")
ANNUAL_ALLOWANCE = 25_000_000
RPDT_START = date(2022, 4, 1)

_TOTALS = (
    ("N45D", "N50"),
    ("N80C", "N85"),
    ("N95D", "N100"),
    ("N120D", "N125"),
    ("N160D", "N165"),
    ("N190D", "N195"),
)


def _fill_totals(page: PageTree) -> None:
    for column, total in _TOTALS:
        if page.rows(column):
            page.set(total, page.total(column))
    if page.has("N100"):
        page.set("N260", page.amount("N100"))
    if page.has("N165"):
        page.set("N265", page.amount("N165"))


def _check_losses(page: PageTree, profits: Decimal, allowance: Decimal) -> None:
    losses = page.amount("N255") + page.amount("N265")
    if profits > allowance:
        cap = max((profits - allowance) / 2 - page.amount("N260"), ZERO)
        if losses > cap:
            page.problem(
                "N255",
                f"Loss relief (N255 and N265 together) must be £{whole_pounds_down(cap):,} or "
                "less: half the profits above the allowance, less group relief (N260)",
            )


def compute_residential_property_developer_tax(
    page: PageTree, period_start: date, period_end: date
) -> Decimal | None:
    """Fill CT600N's totals and RPDT.

    Returns:
        N285, RPDT payable (box 497), or ``None`` when the page has no calculation (section 4).
    """
    if period_start < RPDT_START:
        page.problem("N230", "CT600N is for accounting periods starting on or after 1 April 2022")
    _fill_totals(page)
    if page.section("Section4") is None:
        return None
    for profit, loss in (("N230", "N235"), ("N240", "N245")):
        if page.has(profit) and page.has(loss):
            page.problem(loss, "Enter a profit or a loss, not both")
    if not (page.has("N230") or page.has("N240")):
        page.problem(
            "N230",
            "Enter the adjusted trading profit or joint venture profit: "
            "the RPDT calculation is only for a period with RPD profits",
        )
    profits = max(
        page.amount("N230") + page.amount("N240") - page.amount("N235") - page.amount("N245"),
        ZERO,
    )
    page.set("N250", profits)
    maximum = whole_pounds_down(
        Fraction(ANNUAL_ALLOWANCE) * year_fraction(period_start, period_end)
    )
    allowance = page.amount("N275")
    if allowance > maximum:
        page.problem(
            "N275",
            f"The allowance must be £{maximum:,} or less: £25 million a year, "
            "reduced for a short period",
        )
    _check_losses(page, profits, allowance)
    relieved = page.amount("N255") + page.amount("N260") + page.amount("N265")
    rpd_profits = max(profits - relieved, ZERO)
    page.set("N270", rpd_profits)
    chargeable = max(rpd_profits - allowance, ZERO)
    page.set("N280", chargeable)
    tax = pence(chargeable * RPDT_RATE)
    page.set("N285", tax)
    return tax
