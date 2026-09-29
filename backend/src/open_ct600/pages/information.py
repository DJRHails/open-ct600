"""The information pages: CT600D, CT600H and CT600J.

CT600D is insurance, CT600H cross-border royalties, CT600J tax avoidance schemes. None of them
feeds a CT600 amount. CT600H's only calculation is the tax deducted from each royalty,
H5G = H5D x H5F / 100 to the nearest penny (rule 9750); filing it also ticks box 645
(cross-border royalty payments, rule 9130). Filing CT600J ticks box 65 (rule 9134). CT600D has
a single declaration, so an empty page is valid (the company files it without claiming the
overseas life assurance business basis).
"""

from datetime import date
from decimal import Decimal

from open_ct600.money import pence
from open_ct600.pages.tree import PageTree

IRD_ABOLISHED = date(2021, 6, 1)
"""The Interest and Royalties Directive route (H5Ea) ended for payments from this date (FA 2021
s34)."""


def compute_royalties(page: PageTree, period_start: date) -> None:
    """Fill the tax deducted from each royalty on CT600H."""
    for row in page.rows("H5A"):
        row.set("H5G", pence(row.amount("H5D") * row.amount("H5F") / Decimal(100)))
        if row.has("H5Ea") and period_start >= IRD_ABOLISHED:
            row.problem(
                "H5Ea",
                "The Interest and Royalties Directive does not apply to payments made on or "
                "after 1 June 2021: enter the double taxation agreement country instead",
            )
