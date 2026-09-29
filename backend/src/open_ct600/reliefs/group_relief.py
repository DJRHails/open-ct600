"""Group and consortium relief: CT600C.

A company claims relief for losses surrendered by other members of its 75% group (or a
consortium) in Part 1 (current-period losses, CTA 2010 Part 5) and Part 3 (carried-forward
losses, Part 5A), and records what it surrenders to others in Parts 2 and 4. The claims are
deducted after qualifying donations: box 300 → 305 → 310 (C10) → 312 (C130) → 315.

Limits applied to each claim:

* In total, box 310 cannot be more than box 300 minus box 305, and box 312 cannot be more than
  that less box 310 (schema rules 9337 and 9374). Tonnage tax profits (box 200) are ring-fenced:
  no group relief or donation can be set against them (FA 2000 Sch 22 para 55).
* Where the surrendering company's accounting period is different (C5B), only the overlapping
  period counts (s138 to s142, CTM80255). The claim cannot be more than the claimant's available
  profits time-apportioned to the overlap, nor, when the surrendering company's figures are
  given (``SurrenderingCompany``), its surrenderable amount time-apportioned to the overlap less
  what it has already surrendered for that period.
* For a consortium claim, the surrenderable amount is limited to the member's ownership
  proportion (s143, s144): the lowest of its shares, profits, assets and votes.

Not modelled: "prior claims attributable to the overlap" between two of the company's own
claims with different overlapping periods (each claim is limited separately, and the total by
box 300 minus box 305), and the loss-restriction cap on carried-forward losses (s269ZD), which
only bites above the £5 million deductions allowance.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from typing import Annotated

from pydantic import Field

from open_ct600.model import Pounds, StrictModel
from open_ct600.money import days_between, overlap, whole_pounds_down
from open_ct600.pages.tree import PageTree, Row
from open_ct600.problems import Problem

Percentage = Annotated[Decimal, Field(gt=0, le=100, max_digits=5, decimal_places=2)]


class SurrenderingCompany(StrictModel):
    """Figures from a surrendering company's own return, to check a claim against.

    Attributes:
        tax_reference: The surrendering company's tax reference, as in C5C or C125C.
        surrenderable_amount: The amount it can surrender for its whole accounting period (the
            "maximum available for surrender" on its CT600, boxes 785 to 855).
        surrendered_to_others: What it has already surrendered to other companies for the
            period this company's accounting period overlaps.
        consortium_share: For a consortium claim, the lowest of this company's percentages of
            the surrendering company's shares, profits, assets and votes.
    """

    tax_reference: Annotated[str, Field(min_length=1, max_length=20)]
    surrenderable_amount: Pounds
    surrendered_to_others: Pounds = 0
    consortium_share: Percentage | None = None


@dataclass(frozen=True)
class GroupRelief:
    """The outcome of CT600C.

    Attributes:
        claimed: C10, group relief claimed (box 310).
        claimed_for_carried_forward_losses: C130, group relief for carried-forward losses
            (box 312).
        available: Profits it could be set against: box 300 less box 305 and tonnage tax.
        unused: ``available`` left after both claims.
        surrendered: C90, current-period amounts surrendered to other companies.
        trading_losses_surrendered: C45, the part of ``surrendered`` that is trading losses;
            it no longer carries forward.
        surrendered_carried_forward_losses: C195, carried-forward amounts surrendered.
        carried_forward_trading_losses_surrendered: C160, the trading-loss part of
            ``surrendered_carried_forward_losses``.
    """

    claimed: int
    claimed_for_carried_forward_losses: int
    available: int
    unused: int
    surrendered: int
    trading_losses_surrendered: int
    surrendered_carried_forward_losses: int
    carried_forward_trading_losses_surrendered: int


_PART_2_CATEGORIES = ("C45", "C50", "C55", "C60", "C65", "C70", "C75")
_PART_4_CATEGORIES = ("C160", "C165", "C170", "C175", "C180")


@dataclass(frozen=True)
class CompanyFacts:
    """This company's details that CT600C repeats (boxes 1, 3, 30 and 35)."""

    name: str
    utr: str
    period_start: date
    period_end: date


def fill_group_relief_totals(page: PageTree, company: CompanyFacts) -> None:
    """Fill CT600C's totals and the declarations' copies of the company's details."""
    if page.rows("C5D"):
        page.set("C10", page.total("C5D"))
    if page.rows("C125D"):
        page.set("C130", page.total("C125D"))
    if page.section("SurrenderedGroupRelief") is not None:
        page.set("C80", sum((page.amount(box) for box in _PART_2_CATEGORIES), Decimal(0)))
        page.set("C90", page.total("C85D"))
    if page.section("SurrenderedGroupReliefForCarriedForwardLosses") is not None:
        page.set("C185", sum((page.amount(box) for box in _PART_4_CATEGORIES), Decimal(0)))
        page.set("C195", page.total("C190D"))
    period = {"From": company.period_start.isoformat(), "To": company.period_end.isoformat()}
    declarations = (
        ("SurrenderedGroupRelief", ("C95", "C100", "C105/C110")),
        ("SurrenderedGroupReliefForCarriedForwardLosses", ("C200", "C205", "C210/C215")),
    )
    for part, (name, utr, dates) in declarations:
        if page.section(part, "ConsentToSurrender", "Declaration") is not None:
            page.set(name, company.name)
            page.set(utr, company.utr)
            page.set(dates, period)


def _claim_limit(
    row: Row,
    columns: tuple[str, str, str],
    company: CompanyFacts,
    available: int,
    surrenderers: dict[str, SurrenderingCompany],
) -> tuple[int, str] | None:
    """The most that one claim row can be, and why; ``None`` if the periods do not overlap."""
    period_box, reference_box, _ = columns
    own = (company.period_start, company.period_end)
    given = row.group(period_box)
    theirs = own
    if given is not None:
        theirs = (date.fromisoformat(str(given["From"])), date.fromisoformat(str(given["To"])))
    shared = overlap(own, theirs)
    if shared is None:
        return None
    shared_days = days_between(*shared)
    limit = whole_pounds_down(Fraction(available * shared_days, days_between(*own)))
    reason = (
        f"the company's profits available for the {shared_days} days its accounting period "
        "overlaps the surrendering company's"
    )
    facts = surrenderers.get((row.text(reference_box) or "").strip())
    if facts is not None:
        surrenderable = Fraction(facts.surrenderable_amount * shared_days, days_between(*theirs))
        surrenderable -= facts.surrendered_to_others
        if facts.consortium_share is not None:
            surrenderable *= Fraction(facts.consortium_share) / 100
        if whole_pounds_down(max(surrenderable, Fraction(0))) < limit:
            limit = whole_pounds_down(max(surrenderable, Fraction(0)))
            reason = "the amount the surrendering company can surrender for the overlapping period"
    return limit, reason


def _check_claims(
    page: PageTree,
    columns: tuple[str, str, str],
    company: CompanyFacts,
    available: int,
    surrenderers: dict[str, SurrenderingCompany],
) -> None:
    period_box, _, amount_box = columns
    for row in page.rows(amount_box):
        limit = _claim_limit(row, columns, company, available, surrenderers)
        if limit is None:
            row.problem(
                period_box,
                "The surrendering company's accounting period must overlap this return's "
                f"period, {company.period_start:%-d %B %Y} to {company.period_end:%-d %B %Y}",
            )
        elif row.amount(amount_box) > limit[0]:
            row.problem(
                amount_box,
                f"The amount claimed must be £{limit[0]:,} or less: that is {limit[1]}",
            )


def _check_surrenders(page: PageTree, trading_loss: int, losses_available: int) -> None:
    if page.section("SurrenderedGroupRelief") is not None:
        if page.amount("C45") > trading_loss:
            page.problem(
                "C45",
                f"Trading losses surrendered must be £{trading_loss:,} or less, the trading loss "
                "of this accounting period",
            )
        if page.amount("C90") != page.amount("C80"):
            page.problem("C90", "The amounts surrendered to each company must add up to box C80")
    if page.section("SurrenderedGroupReliefForCarriedForwardLosses") is not None:
        if page.amount("C160") > losses_available:
            page.problem(
                "C160",
                f"Carried-forward trading losses surrendered must be £{losses_available:,} or "
                "less, the losses brought forward that the company has not used",
            )
        if page.amount("C195") != page.amount("C185"):
            page.problem("C195", "The amounts surrendered to each company must add up to box C185")


def _check_surrenderers(
    page: PageTree, surrenderers: list[SurrenderingCompany], problems: list[Problem]
) -> None:
    references = {
        (row.text(box) or "").strip() for box in ("C5C", "C125C") for row in page.rows(box)
    }
    for index, facts in enumerate(surrenderers):
        if facts.tax_reference not in references:
            problems.append(
                Problem(
                    ("group_relief_surrenderers", index, "tax_reference"),
                    "Enter the tax reference of a surrendering company you claim from on CT600C",
                )
            )


@dataclass(frozen=True)
class ClaimantPosition:
    """The claimant's figures the claims are limited by.

    Attributes:
        available: Box 300 less box 305, less tonnage tax profits.
        trading_loss: This period's trading loss (the most that C45 can surrender).
        losses_available: Trading losses brought forward and not used (the most C160 can be).
    """

    available: int
    trading_loss: int
    losses_available: int


def check_group_relief(
    page: PageTree,
    company: CompanyFacts,
    position: ClaimantPosition,
    surrenderers: list[SurrenderingCompany],
) -> tuple[GroupRelief, list[Problem]]:
    """Check CT600C's claims and surrenders against the company's profits and losses.

    Args:
        page: CT600C, with totals filled in by ``fill_group_relief_totals``.
        company: The claimant's details.
        position: The profits the claims can use, and the losses the surrenders come from.
        surrenderers: Figures from surrendering companies' returns, if the company has them.

    Returns:
        The outcome, and problems with ``surrenderers``. Problems on the page are recorded on
        the page.
    """
    problems: list[Problem] = []
    _check_surrenderers(page, surrenderers, problems)
    by_reference = {facts.tax_reference: facts for facts in surrenderers}
    current = ("C5B", "C5C", "C5D")
    carried = ("C125B", "C125C", "C125D")
    available = position.available
    _check_claims(page, current, company, available, by_reference)
    claimed = int(page.amount("C10"))
    if claimed > available:
        page.problem(
            "C10",
            f"Group relief claimed must be £{available:,} or less in total: the profits left "
            "after qualifying donations (box 300 minus box 305), not counting tonnage tax profits",
        )
    remaining = max(available - claimed, 0)
    _check_claims(page, carried, company, remaining, by_reference)
    claimed_carried = int(page.amount("C130"))
    if claimed_carried > remaining:
        page.problem(
            "C130",
            f"Group relief for carried-forward losses must be £{remaining:,} or less: the "
            "profits left after qualifying donations and group relief (box 300 minus boxes 305 "
            "and 310)",
        )
    _check_surrenders(page, position.trading_loss, position.losses_available)
    outcome = GroupRelief(
        claimed=claimed,
        claimed_for_carried_forward_losses=claimed_carried,
        available=available,
        unused=max(remaining - claimed_carried, 0),
        surrendered=int(page.amount("C90")),
        trading_losses_surrendered=int(page.amount("C45")),
        surrendered_carried_forward_losses=int(page.amount("C195")),
        carried_forward_trading_losses_surrendered=int(page.amount("C160")),
    )
    return outcome, problems
