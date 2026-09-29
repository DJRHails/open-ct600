"""CT600M: Freeports and Investment Zones (information about enhanced allowances).

The page lists enhanced structures and buildings allowance (10% a year) claims per building
(M5) and enhanced capital allowance (100%) claims per site (M20). Its totals feed the main
return's capital allowance information: M10 is included in box 771 (qualifying expenditure on
structures and buildings), M15 in box 711 (allowances in the trading computation) and M25 in
box 760 (machinery and plant on which a first-year allowance is claimed) (rules 9655, 9658,
9667). The allowances themselves are part of the capital allowances deducted in the trading
computation, so they cannot be more than the capital allowances given for the main return.

Site codes (M5A, M20A) are HMRC's list in the CT600M guidance (1 to 19 as of April 2026); the
schema accepts 1 to 300 and the list grows, so it is not checked here.
"""

from dataclasses import dataclass

from open_ct600.pages.tree import PageTree


@dataclass(frozen=True)
class Freeports:
    """What CT600M gives the main return.

    Attributes:
        structures_expenditure: M10, qualifying expenditure on structures (box 771).
        structures_allowances: M15, enhanced structures and buildings allowances (box 711).
        plant_allowances: M25, enhanced capital allowances claimed (box 760).
    """

    structures_expenditure: int
    structures_allowances: int
    plant_allowances: int


def compute_freeports(page: PageTree, capital_allowances: int) -> Freeports:
    """Fill CT600M's totals and check them against the capital allowances claimed.

    Args:
        page: CT600M.
        capital_allowances: Capital allowances deducted in the trading computation.
    """
    buildings = page.rows("M5")
    plant = page.rows("M20")
    if not buildings and not plant:
        page.problem(
            "M5",
            "Enter at least one enhanced structures and buildings allowance or "
            "enhanced capital allowance claim",
        )
    for row in plant:
        if not (row.ticked("M20C") or row.has("M20D") or row.has("M20E")):
            row.problem(
                "M20D",
                "Enter the allowance claimed, the disposal value, or tick the "
                "Enterprise Zone claim",
            )
    if buildings:
        page.set("M10", page.total("M5E"))
        page.set("M15", page.total("M5F"))
    if page.answered_in_any_row("M20D"):
        page.set("M25", page.total("M20D"))
    if page.answered_in_any_row("M20E"):
        page.set("M30", page.total("M20E"))
    allowances = int(page.amount("M15") + page.amount("M25"))
    if allowances > capital_allowances:
        page.problem(
            "M15",
            f"The enhanced allowances on CT600M (£{allowances:,}) are part of the capital "
            f"allowances for the main return, so cannot be more than £{capital_allowances:,}",
        )
    return Freeports(
        structures_expenditure=int(page.amount("M10")),
        structures_allowances=int(page.amount("M15")),
        plant_allowances=int(page.amount("M25")),
    )
