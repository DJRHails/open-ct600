"""CT600I: supplementary charge on ring fence trades.

The supplementary charge is 10% (for periods beginning on or after 1 January 2016, FA 2016 s58)
of adjusted ring fence profits: the ring fence profit or loss (I5) with financing costs added
back (I30), adjusted for decommissioning (I40), less losses (I50), the decommissioning
reduction (I55) and allowances (I60) (CTA 2010 s330, rules 9802 to 9818). I70 is box 505 of the
CT600; the ring fence Corporation Tax and supplementary charge net of deductions in terms of tax
(I80, I85) are entered by the company and carried to boxes 585 and 590.

Not modelled: ring fence Corporation Tax itself (30%, with 19% and 11/400 marginal relief for
small ring fence profits). The main return taxes all profits at the ordinary rates, so a
company with ring fence profits must check boxes 330 to 440 against its own computation.

The transferred tax history tables (I135 to I160) are tracked per asset: carried forward is
brought forward less transferred and used (I135D, I140D), tracked profits add this period's
profit or loss and adjustments (I145D, I150D), and activated amounts add up (I155C, I160C).
"""

from dataclasses import dataclass
from decimal import Decimal

from open_ct600.money import ZERO, pence
from open_ct600.pages.tree import PageTree, Row

SUPPLEMENTARY_CHARGE_RATE = Decimal("0.10")


@dataclass(frozen=True)
class RingFence:
    """What CT600I gives the main return.

    Attributes:
        supplementary_charge: I70 (box 505), or ``None`` when there are no net profits.
        corporation_tax_included: I80 (box 585), if entered.
        supplementary_charge_included: I85 (box 590), if entered.
    """

    supplementary_charge: Decimal | None
    corporation_tax_included: Decimal | None
    supplementary_charge_included: Decimal | None


def _adjusted_profits(page: PageTree) -> Decimal:
    """I30, I35 and I45: ring fence profits with financing costs added back."""
    financing = page.amount("I20") + page.amount("I25")
    if page.has("I20") or page.has("I25"):
        page.set("I30", financing)
    result = page.amount("I5")
    adjusted = max(financing - result, ZERO) if page.ticked("I15") else result + financing
    page.set("I35", adjusted)
    if page.ticked("I15") and result - page.amount("I20") > 0 and not page.has("I75"):
        page.problem(
            "I75",
            "Enter the ring fence trade losses arising in the period, worked "
            "out without financing costs",
        )
    revised = adjusted + page.amount("I40")
    page.set("I45", revised)
    return revised


def _net_profits(page: PageTree, revised: Decimal) -> Decimal:
    """I65: revised profits less losses, the decommissioning reduction and allowances."""
    adjusted = page.amount("I35")
    losses = page.amount("I50")
    if losses > adjusted:
        page.problem(
            "I50", f"Losses must be £{adjusted:,} or less, the adjusted ring fence profits (I35)"
        )
    if page.amount("I60") > adjusted - losses:
        page.problem(
            "I60",
            "Allowances must be no more than the adjusted ring fence profits "
            "less losses (I35 minus I50)",
        )
    net = max(revised - losses - page.amount("I55") - page.amount("I60"), ZERO)
    page.set("I65", net)
    return net


def _pair(row: Row, box: str) -> tuple[Decimal, Decimal]:
    group = row.group(box) or {}
    return Decimal(str(group.get("Profits", "0"))), Decimal(str(group.get("Tax", "0")))


def _set_pair(row: Row, box: str, profits: Decimal, tax: Decimal) -> None:
    row.set(box, {"Profits": str(int(profits)), "Tax": f"{pence(tax):f}"})


def _signed(row: Row, box: str) -> Decimal:
    group = row.group(box) or {}
    if "Losses" in group:
        return -Decimal(str(group["Losses"]))
    return Decimal(str(group.get("Profits", "0")))


def _tracking(row: Row) -> None:
    """Fill one asset's transferred tax history balances."""
    for table in ("I135", "I140"):
        if row.has(table):
            brought, transferred, used = (_pair(row, f"{table}{c}") for c in "ABC")
            _set_pair(
                row,
                f"{table}D",
                brought[0] - transferred[0] - used[0],
                brought[1] - transferred[1] - used[1],
            )
    tracked = _signed(row, "I145A") + _signed(row, "I145B")
    tracked += row.amount("I145C1") - row.amount("I145C2")
    carried = {"Losses": str(int(-tracked))} if tracked < 0 else {"Profits": str(int(tracked))}
    row.set("I145D", dict(carried))
    if row.has("I150"):
        spent = row.amount("I150A") + row.amount("I150B")
        row.set("I150D", spent + row.amount("I150C1") - row.amount("I150C2"))
    for table in ("I155", "I160"):
        if row.has(table):
            previously, now = _pair(row, f"{table}A"), _pair(row, f"{table}B")
            _set_pair(row, f"{table}C", previously[0] + now[0], previously[1] + now[1])


def compute_ring_fence(page: PageTree) -> RingFence:
    """Fill CT600I's supplementary charge and transferred tax history balances."""
    revised = _adjusted_profits(page)
    net = _net_profits(page, revised)
    charge = pence(net * SUPPLEMENTARY_CHARGE_RATE) if net > 0 else None
    page.set("I70", charge)
    for asset in page.rows("I110"):
        _tracking(asset)
    return RingFence(
        supplementary_charge=charge,
        corporation_tax_included=page.amount("I80") if page.has("I80") else None,
        supplementary_charge_included=page.amount("I85") if page.has("I85") else None,
    )
