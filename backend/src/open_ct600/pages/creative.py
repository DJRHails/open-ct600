"""CT600P: creative industries reliefs and credits.

Three kinds of claim, each entered per category (film, high-end TV, and so on):

* **AVEC and VGEC** (CTA 2009 Part 14A): the audio-visual and video games expenditure credits.
  The credit is taxable trading income (s1179CB), so it is added to box 155; it is then set
  against the company's Corporation Tax and paid out through the redemption steps (s1179CC),
  which mirror RDEC's: pre-step 1 (amounts brought forward, P50 to P70), step 1 (this period's
  CT, P75 to P115), step 2 (notional tax at the main rate, P120 to P140), steps 3 to 6 (other
  periods, group surrender, other liabilities, payment, P145 to P190). P245 is box 541 and P190
  box 886.
* **Predecessor reliefs** (film, TV, animation and video games tax relief) and **cultural
  reliefs** (theatre, orchestra, museums and galleries): an additional deduction (reducing
  trading profits) and a payable credit on the loss surrendered. P310 is box 663, P315 box 665,
  P325 (the credit set against liabilities on this return) box 540 and P330 box 885.

The credit amounts per production are worked out cumulatively over the production's life, so
the company enters them; the page checks the schema's limits (UK expenditure no more than
global, credits less than the expenditure or loss they come from).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction

from open_ct600.money import ZERO, pence
from open_ct600.pages.tree import PageTree

PREDECESSOR_RELIEFS_END = date(2027, 4, 1)
"""Periods starting on or after this date cannot claim the predecessor reliefs (rule 8061)."""

_AVEC_ROWS = ("P5", "P10", "P15", "P20", "P25")
_ZERO_CREDIT_ALLOWED = {"P5", "P10"}
_PREDECESSOR_ROWS = ("P260", "P265", "P270", "P275", "P280")
_CULTURAL_ROWS = ("P290", "P295", "P300")


@dataclass(frozen=True)
class CreativeClaims:
    """CT600P's claims, before the Corporation Tax they are set against is known.

    Attributes:
        expenditure_credit: P95, AVEC and VGEC for the period (taxable trading income).
        additional_deduction: P315, predecessor and cultural additional deductions (box 665).
        core_expenditure: P310, predecessor and cultural core expenditure (box 663).
        losses_surrendered: Trading losses surrendered for predecessor and cultural credits.
        tax_credit: P320, predecessor and cultural payable credits claimed.
        has_relief_section: Whether the predecessor and cultural totals (P310 to P330) apply.
    """

    expenditure_credit: Decimal
    additional_deduction: int
    core_expenditure: int
    losses_surrendered: int
    tax_credit: Decimal
    has_relief_section: bool


def _check_expenditure_row(page: PageTree, row: str) -> None:
    if page.amount(f"{row}B") > page.amount(f"{row}A"):
        page.problem(
            f"{row}B", "UK expenditure must be no more than the relevant global expenditure"
        )
    credit, qualifying = page.amount(f"{row}D"), page.amount(f"{row}C")
    zero_allowed = row in _ZERO_CREDIT_ALLOWED and credit == 0 and qualifying == 0
    if credit >= qualifying and not zero_allowed:
        page.problem(
            f"{row}D", "The expenditure credit must be less than the qualifying expenditure"
        )


def _check_relief_row(page: PageTree, row: str) -> None:
    if page.amount(f"{row}B") > page.amount(f"{row}A"):
        page.problem(f"{row}B", "UK core expenditure must be no more than total core expenditure")
    credit, losses = page.amount(f"{row}E"), page.amount(f"{row}D")
    if credit >= losses and not (credit == 0 and losses == 0):
        page.problem(f"{row}E", "The tax credit must be less than the losses surrendered for it")


def _column_totals(page: PageTree, rows: tuple[str, ...], total: str, columns: str) -> None:
    present = [row for row in rows if page.has(row)]
    for column in columns:
        answered = [row for row in present if page.has(f"{row}{column}")]
        value = sum((page.amount(f"{row}{column}") for row in answered), ZERO)
        optional = column == "E" and total == "P30"
        page.set(f"{total}{column}", None if optional and not answered else value)


def _expenditure_credits(page: PageTree) -> Decimal:
    """AVEC and VGEC rows and totals; return P95."""
    if page.section("AudioVisualExpenditureCredit") is not None:
        present = [row for row in _AVEC_ROWS if page.has(row)]
        if not present:
            page.problem("P30A", "Enter at least one audio-visual expenditure credit claim")
        for row in present:
            _check_expenditure_row(page, row)
        _column_totals(page, _AVEC_ROWS, "P30", "ABCDE")
    if page.has("P35"):
        _check_expenditure_row(page, "P35")
        _column_totals(page, ("P35",), "P45", "ABCD")
    return page.amount("P30D") + page.amount("P30E") + page.amount("P45D")


def creative_claims(page: PageTree, period_start: date) -> CreativeClaims:
    """Check CT600P's claims and fill their totals."""
    credit = _expenditure_credits(page)
    predecessor = page.section("FilmHighEndTVchildrensTVanimationAndVideoGamesTaxRelief")
    cultural = page.section("CulturalReliefs")
    if predecessor is not None and period_start >= PREDECESSOR_RELIEFS_END:
        page.problem(
            "P285A",
            "Film, TV, animation and video games tax relief ended for periods "
            "starting on or after 1 April 2027: claim the expenditure credits instead",
        )
    for rows, total, section in (
        (_PREDECESSOR_ROWS, "P285", predecessor),
        (_CULTURAL_ROWS, "P305", cultural),
    ):
        if section is None:
            continue
        for row in rows:
            if page.has(row):
                _check_relief_row(page, row)
        _column_totals(page, rows, total, "ABCDE")
    has_relief_section = predecessor is not None or cultural is not None
    if has_relief_section:
        page.set("P310", page.amount("P285A") + page.amount("P305A"))
        page.set("P315", page.amount("P285C") + page.amount("P305C"))
        tax_credit = page.amount("P285E") + page.amount("P305E")
        page.set("P320", tax_credit)
        set_off = page.amount("P325")
        if set_off > tax_credit:
            page.problem(
                "P325",
                f"The credit set off must be £{tax_credit:,} or less, the total tax credit claimed",
            )
        page.set("P325", min(set_off, tax_credit))
        page.set("P330", tax_credit - min(set_off, tax_credit))
    return CreativeClaims(
        expenditure_credit=credit,
        additional_deduction=int(page.amount("P315")),
        core_expenditure=int(page.amount("P310")),
        losses_surrendered=int(page.amount("P285D") + page.amount("P305D")),
        tax_credit=page.amount("P320"),
        has_relief_section=has_relief_section,
    )


@dataclass(frozen=True)
class CreativeRedemption:
    """What CT600P's redemption steps give the main return.

    Attributes:
        set_off: P245, AVEC and VGEC used against this return's liabilities (box 541), or
            ``None`` when there is nothing to redeem.
        payable: P190, payable AVEC and VGEC (box 886), or ``None`` when step 6 is not reached.
        carried_forward: P210, carried forward to the next period.
        used_against_other_liabilities: P170, used against boxes 480 to 505 of this return.
    """

    set_off: Decimal | None
    payable: Decimal | None
    carried_forward: Decimal
    used_against_other_liabilities: Decimal


def _entered(page: PageTree, box: str, most: Decimal, what: str) -> Decimal:
    value = page.amount(box)
    if value > most:
        page.problem(box, f"{what} must be £{max(most, ZERO):,} or less")
        return max(most, ZERO)
    return value


def _pre_step_1(page: PageTree, liability: Decimal) -> Decimal:
    if not page.has("P50"):
        return liability
    brought_forward = page.amount("P50")
    used = min(brought_forward, liability)
    page.set("P55", liability)
    page.set("P60", used)
    page.set("P65", brought_forward - used)
    page.set("P70", liability - used)
    return liability - used


def _step_1(page: PageTree, liability: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Fill step 1; return P95, P110 and P115."""
    copies = (("P75", "P30C"), ("P80", "P30D"), ("P81", "P30E"), ("P85", "P45C"), ("P90", "P45D"))
    for box, source in copies:
        page.set(box, page.amount(source) if page.has(source) else None)
    total = page.amount("P80") + page.amount("P81") + page.amount("P90")
    page.set("P95", total)
    page.set("P100", liability)
    if page.amount("P105") > 0:
        page.problem(
            "P105",
            "Leave box P105 blank: this service does not take income tax "
            "deducted from the company's income (box 515)",
        )
    page.set("P110", liability)
    used = min(total, liability)
    page.set("P115", used)
    return total, liability, used


def _step_2(page: PageTree, total: Decimal, available: Decimal, main_rate: Fraction) -> Decimal:
    """Fill step 2; return the restriction carried forward (P140)."""
    page.set("P120", total - min(total, available))
    charge = pence(main_rate * Fraction(total))
    page.set("P125", charge)
    page.set("P130", total - charge)
    beyond = max(total - available, ZERO)
    page.set("P135", beyond)
    restriction = max(beyond - (total - charge), ZERO)
    page.set("P140", restriction)
    return restriction


def _steps_3_to_6(page: PageTree, balance: Decimal) -> tuple[set[str], Decimal, Decimal | None]:
    """Fill steps 3 to 6; return the steps reached, P170 and P190."""
    reached = {"Step3"}
    page.set("P145", balance)
    balance -= _entered(page, "P150", balance, "The amount used for another period")
    used_on_return, payable = ZERO, None
    if balance > 0:
        reached.add("Step4")
        page.set("P155", balance)
        balance -= _entered(page, "P160", balance, "The credit surrendered")
    if balance > 0:
        reached.add("Step5")
        page.set("P165", balance)
        used_on_return = _entered(page, "P170", balance, "The amount used on this return")
        other = _entered(page, "P175", balance - used_on_return, "The amount used elsewhere")
        page.set("P180", used_on_return + other)
        balance -= used_on_return + other
    if balance > 0:
        reached.add("Step6")
        withheld = _entered(page, "P185", balance, "The amount not payable")
        payable = balance - withheld
        page.set("P190", payable)
    return reached, used_on_return, payable


def _carried_forward_and_surrendered(page: PageTree, pre_step: bool, step_2: bool) -> Decimal:
    carried = ZERO
    if pre_step or step_2:
        if pre_step:
            page.set("P195", page.amount("P65"))
        page.set("P200", page.amount("P140"))
        restricted = page.amount("P65") + page.amount("P140")
        surrendered = _entered(page, "P205", restricted, "The amount surrendered")
        carried = restricted - surrendered
        page.set("P210", carried)
    else:
        page.remove("AVECVGECcarriedForward")
    if page.amount("P160") > 0 or page.amount("P205") > 0:
        page.set("P215", page.amount("P205") if page.has("P205") else None)
        page.set("P220", page.amount("P160") if page.has("P160") else None)
        page.set("P225", page.amount("P205") + page.amount("P160"))
        if not page.rows("P250"):
            page.problem("P250", "Give the companies the credit was surrendered to")
    else:
        page.remove("AVECVGECsurrendered")
    if page.rows("P250"):
        page.set("P255", page.total("P250D"))
        if page.amount("P255") != page.amount("P225"):
            page.problem(
                "P250",
                "The amounts surrendered to each company must add up to the "
                "total surrendered (P225)",
            )
    return carried


def redeem_creative(
    page: PageTree, claims: CreativeClaims, liability: Decimal, main_rate: Fraction
) -> CreativeRedemption:
    """Run CT600P's AVEC and VGEC redemption steps.

    Args:
        page: CT600P.
        claims: The page's claims.
        liability: Box 475 less box 530, the Corporation Tax left for the credits.
        main_rate: The main rate of Corporation Tax for step 2.
    """
    pre_step = page.has("P50")
    remaining = _pre_step_1(page, liability)
    reached: set[str] = set()
    used_on_return, payable = ZERO, None
    if claims.expenditure_credit > 0 or pre_step:
        reached.add("Step1")
        total, available, used = _step_1(page, remaining)
        if total - used > 0:
            reached.add("Step2")
            balance = total - used - _step_2(page, total, available, main_rate)
            if balance > 0:
                later, used_on_return, payable = _steps_3_to_6(page, balance)
                reached |= later
    for step in ("Step1", "Step2", "Step3", "Step4", "Step5", "Step6"):
        if step not in reached:
            page.remove(step)
    carried = _carried_forward_and_surrendered(page, pre_step, "Step2" in reached)
    set_off = None
    if pre_step or "Step1" in reached:
        copies = (("P230", "P60"), ("P235", "P115"), ("P240", "P170"))
        for box, source in copies:
            page.set(box, page.amount(source) if page.has(source) else None)
        set_off = sum((page.amount(box) for box, _ in copies), ZERO)
        page.set("P245", set_off)
    return CreativeRedemption(
        set_off=set_off,
        payable=payable,
        carried_forward=carried,
        used_against_other_liabilities=used_on_return,
    )
