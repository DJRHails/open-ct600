"""CT600F: tonnage tax.

Each qualifying ship's tonnage tax profit is a daily profit for its net tonnage, rounded down to
the nearest 100 tons, times the days it was operated in the period (FA 2000 Sch 22 para 4,
TTM01300): £0.60 per 100 tons up to 1,000 tons, £0.45 up to 10,000, £0.30 up to 25,000 and
£0.15 above. Ships only managed (code M, elections from 1 April 2024, FA 2024 Sch 8) earn a
fifth of those rates. F70, the total in whole pounds, is box 200 of the CT600; the offshore
training allowance F45 is included in box 450.

Tonnage tax profits are ring-fenced: no loss, deduction or group relief may be set against
them (TTM07200); the main return keeps box 200 out of the profits that donations and group
relief can use. The profit and loss entered for the main return should leave out the relevant
shipping profits the tonnage tax replaces.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from open_ct600.money import ZERO, pence, whole_pounds_down
from open_ct600.pages.tree import PageTree

FLAGGING_ABOLISHED = date(2022, 4, 1)
"""From this date the flagging conditions (F30, F35) no longer apply (FA 2022 s25)."""

OPERATED_BANDS = (
    (10, Decimal("0.60")),
    (90, Decimal("0.45")),
    (150, Decimal("0.30")),
    (None, Decimal("0.15")),
)
"""Daily profit per 100 net tons, band by band: (how many 100-ton units, rate)."""
MANAGED_FRACTION = Decimal("0.2")
MANAGED_ONLY = "M"


def daily_profit(net_tonnage: int, managed_only: bool = False) -> Decimal:
    """The daily tonnage tax profit of one ship.

    Args:
        net_tonnage: The ship's net tonnage.
        managed_only: Whether the company only manages the ship (interest code M).
    """
    units = net_tonnage // 100
    profit = ZERO
    for size, rate in OPERATED_BANDS:
        in_band = units if size is None else min(units, size)
        profit += in_band * rate
        units -= in_band
    return profit * MANAGED_FRACTION if managed_only else profit


@dataclass(frozen=True)
class TonnageTax:
    """What CT600F gives the main return.

    Attributes:
        profits: F70, tonnage tax profits (box 200).
        training_allowance: F45, set against Corporation Tax within box 450.
    """

    profits: int
    training_allowance: Decimal


def _check_information(page: PageTree, period_start: date) -> None:
    group_election = page.ticked("F5A/F5B")
    if group_election and not page.has("F10"):
        page.problem("F10", "Enter the name of the tonnage tax group")
    if not group_election and page.has("F10"):
        page.problem(
            "F10", "Only name a tonnage tax group if the company was party to a group election"
        )
    if group_election and page.text("F20A/F20B/F20C") != "na":
        page.problem("F20A/F20B/F20C", "Select not applicable: the group's limit is in F25")
    if group_election != page.has("F25A/F25B/F25C"):
        page.problem(
            "F25A/F25B/F25C", "Answer this only if the company was party to a group election"
        )
    if period_start >= FLAGGING_ABOLISHED and page.text("F30A/F30B/F30C") != "na":
        page.problem(
            "F30A/F30B/F30C",
            "Select not applicable: the flagging conditions do not "
            "apply to periods starting on or after 1 April 2022",
        )
    if (page.text("F30A/F30B/F30C") == "yes") != page.has("F35A/F35B"):
        page.problem(
            "F35A/F35B",
            "Answer this only if the company operated ships not "
            "registered in the UK for the first time",
        )
    offshore = page.ticked("F40A/F40B")
    if offshore != (page.section("TonnageTax", "OffshoreTrainingAllowance") is not None):
        page.problem(
            "F40A/F40B",
            "Give the offshore training allowance only if the company is "
            "subject to the special rules for offshore activities",
        )


def compute_tonnage_tax(page: PageTree, period_start: date) -> TonnageTax:
    """Fill each ship's tonnage tax profit and the total, and check the page's answers."""
    _check_information(page, period_start)
    ships = page.rows("F70A")
    if not ships and page.section("TonnageTax", "RelevantShippingProfits") is None:
        page.problem(
            "F70",
            "Give the company's qualifying ships (part 4) or its relevant "
            "shipping profits (part 3)",
        )
    for ship in ships:
        daily = daily_profit(
            int(ship.amount("F70E")), managed_only=ship.text("F70C") == MANAGED_ONLY
        )
        ship.set("F70G", pence(daily * ship.amount("F70F")))
    profits = whole_pounds_down(page.total("F70G")) if ships else 0
    if ships:
        page.set("F70", profits)
    return TonnageTax(profits=profits, training_allowance=page.amount("F45"))
