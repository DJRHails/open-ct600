"""CT600K: restitution tax.

Restitution interest (compound interest HMRC pays on a restitution claim, CTA 2010 Part 8C) is
taxed at 45% (s357YK), outside the company's other profits: no relief or set-off reduces it
(s357YL), and it must not be included in box 170. Where the accounting period straddles
1 April the interest is split between the two financial years by days (the form and HMRC do
not prescribe the basis; the rate is the same, so only pence change), the first year's share
rounded to the nearest pound (rules 9220 to 9235). K35, the tax still payable after tax HMRC
withheld (K25), is box 527 of the CT600; K5 copies box 525 and K30 adds the two.
"""

from datetime import date
from decimal import Decimal
from fractions import Fraction

from open_ct600.money import days_between, pence, pounds
from open_ct600.pages.tree import PageTree
from open_ct600.tax import financial_year_of

RESTITUTION_RATE = Decimal("0.45")


def compute_restitution_tax(
    page: PageTree, period_start: date, period_end: date, tax_payable: Decimal
) -> Decimal:
    """Fill CT600K from the restitution interest and box 525.

    Args:
        page: CT600K.
        period_start: Box 30.
        period_end: Box 35.
        tax_payable: Box 525, self-assessment of tax payable before restitution tax.

    Returns:
        K35, restitution tax now payable (box 527).
    """
    interest = int(page.amount("K10"))
    first_year = financial_year_of(period_start)
    straddles = financial_year_of(period_end) != first_year
    first_share = interest
    if straddles:
        first_end = date(first_year + 1, 3, 31)
        first_share = pounds(
            Fraction(interest * days_between(period_start, first_end))
            / days_between(period_start, period_end)
        )
    rows = [("K15.1", first_year, first_share)]
    if straddles:
        rows.append(("K15.2", first_year + 1, interest - first_share))
    total = Decimal(0)
    for row, year, amount in rows:
        tax = pence(amount * RESTITUTION_RATE)
        page.set(f"{row}A", year)
        page.set(f"{row}B", amount)
        page.set(f"{row}C", RESTITUTION_RATE * 100)
        page.set(f"{row}D", tax)
        total += tax
    withheld = page.amount("K25")
    if withheld > total:
        page.problem(
            "K25", f"Tax already withheld must be £{total:,} or less, the total restitution tax"
        )
    payable = max(total - withheld, Decimal(0))
    page.set("K5", tax_payable)
    page.set("K20", total)
    page.set("K30", tax_payable + total - withheld)
    page.set("K35", payable)
    return payable
