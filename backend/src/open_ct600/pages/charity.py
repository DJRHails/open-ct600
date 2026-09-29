"""CT600E: charities and community amateur sports clubs (CASCs) claiming exemption.

The page is the claim. It records exempt income and expenditure; its totals are E90 (income,
E50 to E88), E125 (expenditure, E95 to E120) and E200 (legacies, copied to E88). A company
ticking E20 ("all income and gains are exempt") has no taxable profits: the main return's
profits are all exempt, so boxes 155 to 315 are nil and there is no tax (guidance E50). With
E25, the profits entered for the main return are taxed as usual: enter only the non-exempt
income and gains there.
"""

from datetime import date
from decimal import Decimal

from open_ct600.money import ZERO
from open_ct600.pages.tree import PageTree

_INCOME = ("E50", "E55", "E60", "E65", "E70", "E75", "E80", "E85", "E88")
_EXPENDITURE = ("E95", "E100", "E105", "E110", "E115", "E120")


def _check_rows(page: PageTree, period_end: date) -> None:
    for row in page.rows("E195"):
        if row.has("E195D") == row.ticked("E195E"):
            row.problem("E195D", "Enter the donor's postcode, or tick overseas, but not both")
        made = row.day("E195F")
        if made is not None and made > period_end:
            row.problem("E195F", f"The legacy date must be on or before {period_end:%-d %B %Y}")


def _check_costs(page: PageTree) -> None:
    if page.has("E95") and page.amount("E50") <= 0:
        page.problem("E95", "Only enter trading costs if there is exempt trading turnover (E50)")
    if page.has("E100") and page.amount("E60") <= 0:
        page.problem(
            "E100",
            "Only enter land and buildings costs if there is income from UK "
            "land and buildings (E60)",
        )
    if page.ticked("E180") and page.has("E185"):
        page.problem("E185", "Leave this blank if all investments and loans qualify (E180)")


def compute_charity(page: PageTree, period_end: date) -> bool:
    """Fill CT600E's totals and check its answers.

    Returns:
        Whether all the company's income and gains are exempt (E20).
    """
    _check_rows(page, period_end)
    _check_costs(page)
    if page.rows("E195"):
        legacies = page.total("E195G")
        page.set("E200", legacies)
        page.set("E88", legacies)
    if page.section("InformationRequired", "Income") is not None:
        page.set("E90", sum((page.amount(box) for box in _INCOME), ZERO))
    if page.section("InformationRequired", "Expenditure") is not None:
        page.set("E125", sum((page.amount(box) for box in _EXPENDITURE), Decimal(0)))
    return page.ticked("E20")
