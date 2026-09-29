"""CT600B: controlled foreign companies (CFCs), foreign PE exemption, hybrid mismatches.

For each CFC with a chargeable apportionment (columns D to J), the tax on chargeable profits
is the appropriate rate on the company's percentage of the CFC's chargeable profits (TIOPA 2010
s371BC): F = rate x D% x E. The charge due is J = F - (G + H + I), where G is the creditable
tax, H reliefs in terms of tax and I restricted ACT. The column totals go in B10 to B30, and
B30 is box 490 of the CT600 (rules 9455 to 9465).

The appropriate rate is taken to be the main rate, weighted by days where the accounting
period straddles a change: HMRC's manual (INTM194400) says so, while the statute's "rate
applicable" could be read as the small profits rate for smaller companies (unverified).
"""

from datetime import date
from decimal import Decimal
from fractions import Fraction

from open_ct600.money import ZERO, pence
from open_ct600.pages.tree import PageTree
from open_ct600.tax import average_main_rate

_COLUMN_TOTALS = (("B5F", "B10"), ("B5G", "B15"), ("B5H", "B20"), ("B5I", "B25"))


def compute_controlled_foreign_companies(
    page: PageTree, period_start: date, period_end: date
) -> Decimal | None:
    """Fill CT600B's tax, charge and totals.

    Returns:
        B30, the CFC tax payable (box 490), or ``None`` when no CFC has a charge.
    """
    rate = average_main_rate(period_start, period_end)
    charged = [row for row in page.rows("B5A") if row.has("B5D")]
    for row in charged:
        tax = pence(rate * Fraction(row.amount("B5D")) / 100 * Fraction(row.amount("B5E")))
        row.set("B5F", tax)
        deductions = row.amount("B5G") + row.amount("B5H") + row.amount("B5I")
        if deductions > tax:
            row.problem(
                "B5G",
                f"Creditable tax, reliefs and restricted ACT must add up to £{tax:,} or less, "
                "the tax on chargeable profits",
            )
        row.set("B5J", max(tax - deductions, ZERO))
    if not charged:
        return None
    for column, total in _COLUMN_TOTALS:
        amount = sum((row.amount(column) for row in charged), ZERO)
        page.set(total, amount if amount > 0 else None)
    charge = sum((row.amount("B5J") for row in charged), ZERO)
    page.set("B30", charge)
    return charge
