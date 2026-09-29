"""R&D relief and CT600L.

Which scheme a claim uses depends on when the accounting period starts:

* **Before 1 April 2024**: the SME scheme (CTA 2009 Part 13) gives an additional deduction of
  130% of qualifying expenditure incurred before 1 April 2023 and 86% after, and an optional
  payable tax credit on the surrendered loss (14.5% before 1 April 2023; 10% after, or 14.5%
  for R&D-intensive SMEs whose R&D is at least 40% of their expenditure). Large companies claim
  RDEC (Part 3 Chapter 6A) at 11%, 12%, 13% or 20% depending on when the expenditure was
  incurred, with the step 2 notional tax at the main rate.
* **From 1 April 2024**: the merged RDEC scheme (Part 13 Chapter 1A) at 20%, with the step 2
  notional tax at 25% for companies whose profits (before the credit) are taxed at the main
  rate or with marginal relief, and 19% otherwise (s1042K, CIRD112100); or, for loss-making
  SMEs whose R&D is at least 30% of their expenditure, ERIS (Chapter 2): an 86% additional
  deduction and a 14.5% payable credit.

Payable credits (ERIS, the SME scheme from 1 April 2021, and merged RDEC at step 3) are capped
at £20,000 plus three times the company's (and connected companies') PAYE and NICs, the £20,000
reduced for a short period, unless the s1058D or s1112E exception applies. RDEC is taxable
trading income (box 155); additional deductions reduce trading profits (and increase losses);
losses surrendered for a payable credit no longer carry forward.

Decisions where HMRC's material is silent (documented in the CORE-2 lane report):

* An accounting period that straddles a change of rate (1 April 2023, or the old RDEC rate
  changes) is taken to incur its expenditure evenly, so rates are weighted by days.
* A merged-scheme RDEC claimant ticks box 650 when it is an SME and 655 otherwise.
* For an s1112E-exempt RDEC claim, L75 is set equal to L70, as HMRC's online service requires
  until April 2027.
* Claims under both merged RDEC and ERIS in the same period are not supported.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from typing import Annotated, Literal

from pydantic import Field

from open_ct600.model import Pounds, StrictModel
from open_ct600.money import ZERO, day_weighted_rate, pence, pounds, year_fraction
from open_ct600.pages.tree import PageTree
from open_ct600.problems import Problem
from open_ct600.tax import average_main_rate

MERGED_SCHEME_START = date(2024, 4, 1)
"""Accounting periods starting on or after this date use merged RDEC or ERIS."""
CLAIM_NOTIFICATION_START = date(2023, 4, 1)
"""Accounting periods starting on or after this date may need a claim notification."""
SME_PAYE_CAP_START = date(2021, 4, 1)
"""The SME payable credit is capped for accounting periods starting on or after this date."""
INTENSIVE_SME_START = date(2023, 4, 1)
"""The R&D-intensive SME credit applies to periods ending on or after this date (box 653)."""

_EARLIEST = date(1900, 1, 1)
OLD_RDEC_RATES = (
    (_EARLIEST, Decimal("0.11")),
    (date(2018, 1, 1), Decimal("0.12")),
    (date(2020, 4, 1), Decimal("0.13")),
    (date(2023, 4, 1), Decimal("0.20")),
)
MERGED_RDEC_RATE = Decimal("0.20")
SME_ADDITIONAL_DEDUCTION = ((_EARLIEST, Decimal("1.30")), (date(2023, 4, 1), Decimal("0.86")))
SME_CREDIT = ((_EARLIEST, Decimal("0.145")), (date(2023, 4, 1), Decimal("0.10")))
INTENSIVE_SME_CREDIT = ((_EARLIEST, Decimal("0.145")),)
ERIS_ADDITIONAL_DEDUCTION = Decimal("0.86")
ERIS_CREDIT = Decimal("0.145")
ERIS_INTENSITY = Decimal(30)
SME_INTENSITY = Decimal(40)
MERGED_STEP_2_MAIN_RATE = Decimal("0.25")
MERGED_STEP_2_SMALL_RATE = Decimal("0.19")
PAYE_CAP_ALLOWANCE = 20_000
PAYE_CAP_MULTIPLE = 3
CONNECTED_PERSONS_LIMIT = Decimal("0.15")

Scheme = Literal["sme", "rdec", "eris"]
Percentage = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
_WHERE = ("research_and_development",)


class ResearchAndDevelopment(StrictModel):
    """The company's R&D claim for the period.

    Attributes:
        scheme: ``sme`` (periods starting before 1 April 2024), ``rdec`` (the large-company
            scheme before 1 April 2024, the merged scheme after) or ``eris`` (from
            1 April 2024).
        company_is_sme: Whether the company is a small or medium-sized enterprise; decides
            box 650 or 655 for a merged-scheme RDEC claim.
        qualifying_expenditure: Qualifying R&D expenditure claimed for (box 659 for the SME
            scheme and ERIS, L10 for RDEC).
        rdec_expenditure: SME scheme only: expenditure on work subcontracted by a large company,
            or subsidised or capped, on which RDEC is claimed (L10); give the credit in L185 or
            L190 of CT600L.
        intensity: Relevant R&D expenditure as a percentage of total relevant expenditure;
            needed for ERIS (at least 30%) and for the R&D-intensive SME credit (40%).
        claim_payable_credit: SME scheme or ERIS: surrender the loss for a payable tax credit.
        rd_workers_paye_and_nic: RDEC for periods starting before 1 April 2024: the company's
            expenditure on R&D workers' PAYE and NICs, the step 3 cap (L75).
        claimed_in_previous_three_years: Whether the company has claimed R&D relief in the
            three years before the end of the claim notification period, so needs no claim
            notification.
        claim_notification_submitted: Whether a claim notification was sent (box 656).
        additional_information_submitted: Whether the additional information form was
            submitted, as every claim needs before the return (box 657).
    """

    scheme: Scheme
    company_is_sme: bool = False
    qualifying_expenditure: Pounds
    rdec_expenditure: Pounds = 0
    intensity: Percentage | None = None
    claim_payable_credit: bool = False
    rd_workers_paye_and_nic: Pounds | None = None
    claimed_in_previous_three_years: bool
    claim_notification_submitted: bool = False
    additional_information_submitted: bool


@dataclass(frozen=True)
class Claim:
    """An R&D claim's effect on trading profits, before losses and tax are known.

    Attributes:
        rd: The answers.
        merged: Whether the period starts on or after 1 April 2024.
        additional_deduction: SME scheme and ERIS: the extra deduction from trading profits.
        rdec: L15, the RDEC arising (taxable trading income).
        rdec_expenditure: L10, expenditure the RDEC is claimed on.
        credit_rates: SME scheme and ERIS: the payable credit rates, by date.
        intensive: Whether box 653 (R&D-intensive SME) is ticked.
    """

    rd: ResearchAndDevelopment
    merged: bool
    additional_deduction: int
    rdec: Decimal
    rdec_expenditure: int
    credit_rates: tuple[tuple[date, Decimal], ...]
    intensive: bool

    @property
    def enhanced_expenditure(self) -> int:
        """Box 660: qualifying expenditure plus the additional deduction (SME and ERIS)."""
        if self.rd.scheme == "rdec":
            return 0
        return self.rd.qualifying_expenditure + self.additional_deduction


def _check_answers(rd: ResearchAndDevelopment, period_start: date) -> list[Problem]:
    return [
        Problem((*_WHERE, field), message)
        for field, message in (
            *_scheme_problems(rd, period_start),
            *_filing_problems(rd, period_start),
        )
    ]


def _scheme_problems(rd: ResearchAndDevelopment, period_start: date) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []
    merged = period_start >= MERGED_SCHEME_START

    def problem(field: str, message: str) -> None:
        problems.append((field, message))

    if rd.scheme == "sme" and merged:
        problem(
            "scheme",
            "The SME scheme ended for periods starting on or after 1 April 2024: "
            "claim merged-scheme RDEC, or ERIS if the company is an R&D-intensive SME",
        )
    if rd.scheme == "eris" and not merged:
        problem(
            "scheme",
            "ERIS is for periods starting on or after 1 April 2024: claim under "
            "the SME scheme instead",
        )
    if rd.scheme == "eris" and (rd.intensity is None or rd.intensity < ERIS_INTENSITY):
        problem(
            "intensity",
            "ERIS needs R&D expenditure of at least 30% of the company's total "
            "relevant expenditure: enter the percentage, or claim merged-scheme RDEC",
        )
    if rd.rdec_expenditure and rd.scheme != "sme":
        problem("rdec_expenditure", "Only an SME scheme claim has separate RDEC expenditure")
    if rd.claim_payable_credit and rd.scheme == "rdec":
        problem(
            "claim_payable_credit",
            "RDEC is paid through CT600L's steps, not as a payable "
            "tax credit on a surrendered loss",
        )
    return problems


def _filing_problems(rd: ResearchAndDevelopment, period_start: date) -> list[tuple[str, str]]:
    """The additional information form (every claim) and claim notification (box 656)."""
    problems: list[tuple[str, str]] = []
    if not rd.additional_information_submitted:
        problems.append(
            (
                "additional_information_submitted",
                "Submit the R&D additional "
                "information form before you file this return: HMRC removes claims "
                "made without it",
            )
        )
    needs_notification = period_start >= CLAIM_NOTIFICATION_START
    if needs_notification and not (
        rd.claimed_in_previous_three_years or rd.claim_notification_submitted
    ):
        problems.append(
            (
                "claim_notification_submitted",
                "Submit a claim notification form "
                "before you claim: the company has not claimed R&D relief in the last "
                "3 years, so HMRC only accepts the claim if it was notified within 6 "
                "months of the period's end",
            )
        )
    return problems


def _rdec(
    rd: ResearchAndDevelopment, page: PageTree | None, period: tuple[date, date]
) -> tuple[Decimal, int, list[Problem]]:
    """L15 and L10: the RDEC arising and the expenditure it is claimed on."""
    start, end = period
    if rd.scheme == "rdec":
        rate = MERGED_RDEC_RATE if start >= MERGED_SCHEME_START else None
        weighted = Fraction(rate) if rate else day_weighted_rate(start, end, OLD_RDEC_RATES)
        return pence(weighted * rd.qualifying_expenditure), rd.qualifying_expenditure, []
    entered = ZERO if page is None else page.amount("L185") + page.amount("L190")
    if rd.rdec_expenditure and not entered:
        return (
            ZERO,
            0,
            [
                Problem(
                    (*_WHERE, "rdec_expenditure"),
                    "Enter the RDEC claimed on this expenditure in box L185 or L190 of CT600L",
                )
            ],
        )
    if entered and not rd.rdec_expenditure:
        return (
            ZERO,
            0,
            [
                Problem(
                    (*_WHERE, "rdec_expenditure"),
                    "Enter the expenditure the RDEC in boxes L185 and L190 is claimed on",
                )
            ],
        )
    if entered >= rd.rdec_expenditure > 0:
        return (
            ZERO,
            0,
            [
                Problem(
                    (*_WHERE, "rdec_expenditure"),
                    "The RDEC in boxes L185 and "
                    "L190 must be less than the expenditure it is claimed on",
                )
            ],
        )
    return entered, rd.rdec_expenditure, []


def assess_claim(
    rd: ResearchAndDevelopment, page: PageTree | None, period_start: date, period_end: date
) -> tuple[Claim | None, list[Problem]]:
    """Work out an R&D claim's additional deduction and RDEC.

    Args:
        rd: The claim.
        page: CT600L, if filed (for the SME scheme's RDEC in L185 and L190).
        period_start: Box 30.
        period_end: Box 35.

    Returns:
        The claim, or ``None`` with the problems that stop it being assessed.
    """
    problems = _check_answers(rd, period_start)
    rdec, rdec_expenditure, rdec_problems = _rdec(rd, page, (period_start, period_end))
    problems += rdec_problems
    needs_page = rd.scheme == "rdec" or rd.rdec_expenditure > 0 or rd.claim_payable_credit
    if needs_page and page is None:
        problems.append(
            Problem(
                (*_WHERE, "scheme"),
                "Add CT600L: it is needed for RDEC and for payable R&D tax credits",
            )
        )
    if problems:
        return None, problems
    merged = period_start >= MERGED_SCHEME_START
    intensive = rd.scheme == "eris" or (
        rd.scheme == "sme"
        and rd.intensity is not None
        and rd.intensity >= SME_INTENSITY
        and period_end >= INTENSIVE_SME_START
    )
    if rd.scheme == "eris":
        rate = Fraction(ERIS_ADDITIONAL_DEDUCTION)
        credit_rates: tuple[tuple[date, Decimal], ...] = ((_EARLIEST, ERIS_CREDIT),)
    elif rd.scheme == "sme":
        rate = day_weighted_rate(period_start, period_end, SME_ADDITIONAL_DEDUCTION)
        credit_rates = SME_CREDIT if not intensive else INTENSIVE_SME_CREDIT
    else:
        rate, credit_rates = Fraction(0), ()
    claim = Claim(
        rd=rd,
        merged=merged,
        additional_deduction=pounds(rate * rd.qualifying_expenditure),
        rdec=rdec,
        rdec_expenditure=rdec_expenditure,
        credit_rates=credit_rates,
        intensive=intensive,
    )
    return claim, []


@dataclass(frozen=True)
class TradingPosition:
    """The trading figures a payable credit is worked out from.

    Attributes:
        loss_before_additional_deduction: The trading loss before the R&D additional
            deduction (0 if the trade made a profit).
        loss: The trading loss of the period after the additional deduction.
        other_profits: Profits the loss could be set against in the same period (CTA 2010
            s37(3)(a)); that part of the loss is "relieved" whether or not the claim is made.
        group_relief_surrendered: Trading loss surrendered as group relief (C45).
    """

    loss_before_additional_deduction: int
    loss: int
    other_profits: int
    group_relief_surrendered: int


@dataclass(frozen=True)
class PayableCredit:
    """A payable tax credit on a surrendered loss (SME scheme or ERIS).

    Attributes:
        credit: L170, the credit claimed.
        loss_surrendered: The trading loss surrendered for it, which no longer carries forward.
        cap: The PAYE and NICs cap, or ``None`` when an exception applies.
    """

    credit: Decimal
    loss_surrendered: int
    cap: Decimal | None


def _paye_cap(
    page: PageTree, boxes: tuple[str, str, str, str], limit_base: int, period: tuple[date, date]
) -> Decimal | None:
    """The PAYE and NICs cap, or ``None`` when the exception box is ticked.

    Args:
        page: CT600L.
        boxes: The exception tick, connected-persons expenditure, the company's PAYE and NICs,
            and connected companies' PAYE and NICs (L167, L167A, L168, L169 or L71 to L73).
        limit_base: Expenditure the connected-persons amount may be at most 15% of.
        period: The accounting period.
    """
    exception, connected, own, others = boxes
    if page.ticked(exception):
        if not page.has(connected):
            page.problem(
                connected,
                "Enter the expenditure on externally provided workers and "
                "subcontracting from connected persons: the exception needs it",
            )
        elif page.amount(connected) > CONNECTED_PERSONS_LIMIT * limit_base:
            page.problem(
                connected,
                "For the exception to apply, expenditure on connected "
                f"persons must be no more than 15% of £{limit_base:,}",
            )
        if page.has(own):
            page.problem(own, "Leave out the company's PAYE and NICs when the exception applies")
        return None
    for box, reference in ((own, f"{own}A"), (others, f"{others}A")):
        if page.has(box) and not page.has(reference):
            page.problem(reference, "Enter the employer PAYE reference")
    allowance = Fraction(PAYE_CAP_ALLOWANCE) * year_fraction(*period)
    liabilities = Fraction(page.amount(own) + page.amount(others))
    return pence(allowance + PAYE_CAP_MULTIPLE * liabilities)


def payable_credit(
    claim: Claim, page: PageTree, position: TradingPosition, period: tuple[date, date]
) -> tuple[PayableCredit | None, list[Problem]]:
    """Work out the SME or ERIS payable credit and fill CT600L's SME section.

    Returns:
        The credit (``None`` if not claimed), and problems with the claim's answers.
    """
    rd = claim.rd
    if not rd.claim_payable_credit:
        return None, []
    if rd.scheme == "eris" and position.loss_before_additional_deduction <= 0:
        return None, [
            Problem(
                (*_WHERE, "scheme"),
                "ERIS is only for companies whose trade "
                "makes a loss before the additional deduction: claim "
                "merged-scheme RDEC instead",
            )
        ]
    unrelieved = max(position.loss - position.other_profits - position.group_relief_surrendered, 0)
    surrenderable = min(claim.enhanced_expenditure, unrelieved)
    if surrenderable <= 0:
        return None, [
            Problem(
                (*_WHERE, "claim_payable_credit"),
                "There is no loss to surrender "
                "for a payable credit: the trading loss is covered by the "
                "company's other profits this period",
            )
        ]
    rate = day_weighted_rate(*period, claim.credit_rates)
    capped = rd.scheme == "eris" or period[0] >= SME_PAYE_CAP_START
    limit_base = rd.qualifying_expenditure + (claim.rdec_expenditure if claim.merged else 0)
    cap = _paye_cap(page, ("L167", "L167A", "L168", "L169"), limit_base, period) if capped else None
    credit = pence(rate * surrenderable)
    loss_surrendered = surrenderable
    if cap is not None and credit > cap:
        credit = cap
        loss_surrendered = min(pounds(Fraction(cap) / rate), surrenderable)
    page.set("L166", rd.qualifying_expenditure)
    page.set("L170", credit)
    set_off = page.amount("L175")
    if set_off > credit:
        page.problem("L175", f"The credit set off must be £{credit:,} or less, the credit claimed")
    page.set("L180", credit - min(set_off, credit))
    return PayableCredit(credit=credit, loss_surrendered=loss_surrendered, cap=cap), []


def notional_tax_rate(period: tuple[date, date], main_rate_company: bool) -> Fraction:
    """The step 2 rate.

    Args:
        period: The accounting period.
        main_rate_company: Whether the company's profits before RDEC are taxed at the main
            rate or with marginal relief (only matters for the merged scheme).

    Returns:
        25% or 19% for the merged scheme; before it, the main rate weighted by days.
    """
    if period[0] >= MERGED_SCHEME_START:
        return Fraction(MERGED_STEP_2_MAIN_RATE if main_rate_company else MERGED_STEP_2_SMALL_RATE)
    return average_main_rate(*period)


@dataclass(frozen=True)
class Redemption:
    """What CT600L's steps give the main return.

    Attributes:
        set_off: L210, credits used against liabilities on this return (box 530).
        payable_rdec: L125, payable RDEC (box 880), or ``None`` when step 7 is not reached.
        payable_credit: L180, the SME or ERIS credit still payable (box 875), if claimed.
        carried_forward: L150, RDEC carried forward to the next period.
        used_against_other_liabilities: L110 plus L175, credits used against boxes 480 to 505.
    """

    set_off: Decimal
    payable_rdec: Decimal | None
    payable_credit: Decimal | None
    carried_forward: Decimal
    used_against_other_liabilities: Decimal


@dataclass(frozen=True)
class StepInputs:
    """What CT600L's steps read from the rest of the return.

    Attributes:
        rdec: L15, RDEC arising this period (0 without a claim).
        rdec_expenditure: L10.
        corporation_tax: Box 475.
        notional_rate: The step 2 rate.
        merged: Whether the period starts on or after 1 April 2024.
        old_cap: Periods before the merged scheme: the R&D workers' PAYE and NICs cap.
        period: The accounting period.
    """

    rdec: Decimal
    rdec_expenditure: int
    corporation_tax: Decimal
    notional_rate: Fraction
    merged: bool
    old_cap: int | None
    period: tuple[date, date]


_STEPS = ("Step1", "Step2", "Step3", "Step4", "Step5", "Step6", "Step7")


def _entered(page: PageTree, box: str, most: Decimal, what: str) -> Decimal:
    """An entered amount, checked against the most it can be."""
    value = page.amount(box)
    if value > most:
        page.problem(box, f"{what} must be £{max(most, ZERO):,} or less")
        return max(most, ZERO)
    return value


def _pre_step_1(page: PageTree, corporation_tax: Decimal) -> Decimal:
    """Fill the pre-step 1 restriction; return the CT liability left for step 1."""
    if not page.has("L5"):
        return corporation_tax
    brought_forward = page.amount("L5")
    used = min(brought_forward, corporation_tax)
    page.set("L6", corporation_tax)
    page.set("L7", used)
    page.set("L8", brought_forward - used)
    page.set("L9", corporation_tax - used)
    return corporation_tax - used


def _step_1(page: PageTree, inputs: StepInputs, liability: Decimal) -> tuple[Decimal, Decimal]:
    """Fill step 1; return the total RDEC and the CT it discharges (L25, L45)."""
    if inputs.rdec > 0:
        page.set("L10", inputs.rdec_expenditure)
        page.set("L15", inputs.rdec)
    total = inputs.rdec + page.amount("L20")
    page.set("L25", total)
    page.set("L30", liability)
    if page.amount("L35") > 0:
        page.problem(
            "L35",
            "Leave box L35 blank: this service does not take income tax "
            "deducted from the company's income (box 515)",
        )
    available = liability
    page.set("L40", available)
    used = min(total, available)
    page.set("L45", used)
    return total, used


def _step_2(page: PageTree, inputs: StepInputs, balance: Decimal, available: Decimal) -> Decimal:
    """Fill step 2; return the restriction carried forward (L65)."""
    page.set("L50", balance)
    net = ZERO
    if inputs.rdec > 0:
        charge = pence(inputs.notional_rate * Fraction(inputs.rdec))
        net = inputs.rdec - charge
        page.set("L55", charge)
        page.set("L60", net)
        page.set("L62", max(inputs.rdec - available, ZERO))
    restriction = max(page.amount("L62") - net, ZERO)
    page.set("L65", restriction)
    return restriction


def _step_3(page: PageTree, inputs: StepInputs, balance: Decimal) -> Decimal | None:
    """Fill step 3; return the restriction carried forward (L80), or ``None`` if uncapped."""
    page.set("L70", balance)
    if inputs.merged:
        cap = _paye_cap(page, ("L71", "L71A", "L72", "L73"), inputs.rdec_expenditure, inputs.period)
    else:
        if inputs.old_cap is None:
            page.problem(
                "L75",
                "Enter the company's expenditure on R&D workers' PAYE and NICs "
                "(rd_workers_paye_and_nic): step 3 caps the payable RDEC at it",
            )
            return None
        cap = Decimal(inputs.old_cap)
    page.set("L75", balance if cap is None else cap)
    restriction = ZERO if cap is None or page.ticked("L167") else max(balance - cap, ZERO)
    page.set("L80", restriction)
    return restriction


def _steps(
    page: PageTree, inputs: StepInputs, liability: Decimal
) -> tuple[set[str], Decimal, Decimal | None]:
    """Fill steps 1 to 7 as far as a balance remains.

    Returns:
        The steps reached, the credit used against other liabilities on this return (L110),
        and the payable RDEC (L125) when step 7 is reached.
    """
    if not (inputs.rdec > 0 or page.has("L20")):
        return set(), ZERO, None
    total, used = _step_1(page, inputs, liability)
    if total - used <= 0:
        return {"Step1"}, ZERO, None
    restriction = _step_2(page, inputs, total - used, page.amount("L40"))
    balance = total - used - restriction
    if balance <= 0:
        return {"Step1", "Step2"}, ZERO, None
    capped = _step_3(page, inputs, balance)
    if capped is None or balance - capped <= 0:
        return {"Step1", "Step2", "Step3"}, ZERO, None
    reached, used_on_return, payable = _steps_4_to_7(page, balance - capped)
    return {"Step1", "Step2", "Step3", *reached}, used_on_return, payable


def _steps_4_to_7(page: PageTree, balance: Decimal) -> tuple[set[str], Decimal, Decimal | None]:
    """Fill steps 4 to 7; return the steps reached, L110 and L125."""
    reached = {"Step4"}
    page.set("L85", balance)
    balance -= _entered(page, "L90", balance, "The amount used for another period")
    payable = None
    used_on_return = ZERO
    if balance > 0:
        reached.add("Step5")
        page.set("L95", balance)
        balance -= _entered(page, "L100", balance, "The credit surrendered")
    if balance > 0:
        reached.add("Step6")
        page.set("L105", balance)
        used_on_return = _entered(page, "L110", balance, "The amount used on this return")
        other = _entered(page, "L115", balance - used_on_return, "The amount used elsewhere")
        page.set("L120", used_on_return + other)
        balance -= used_on_return + other
    if balance > 0:
        reached.add("Step7")
        extinguished = _entered(page, "L123", balance, "The amount extinguished")
        payable = balance - extinguished
        page.set("L125", payable)
    return reached, used_on_return, payable


def _carried_forward(page: PageTree, pre_step: bool, step_2: bool) -> Decimal:
    if not (pre_step or step_2):
        page.remove("RDECcarriedForward")
        return ZERO
    restricted = page.amount("L8") + page.amount("L65")
    if pre_step:
        page.set("L129", page.amount("L8"))
    page.set("L130", page.amount("L65"))
    surrendered = _entered(page, "L135", restricted, "The amount surrendered")
    page.set("L140", restricted - surrendered)
    if page.has("L80"):
        page.set("L145", page.amount("L80"))
    total = restricted - surrendered + page.amount("L80")
    page.set("L150", total)
    return total


def _surrendered(page: PageTree) -> None:
    if page.section("Step5") is None and page.amount("L135") <= 0:
        page.remove("RDECsurrendered")
        return
    if page.has("L135"):
        page.set("L155", page.amount("L135"))
    if page.has("L100"):
        page.set("L160", page.amount("L100"))
    page.set("L165", page.amount("L135") + page.amount("L100"))


def _totals(page: PageTree) -> Decimal:
    copies = (("L194", "L7"), ("L195", "L45"), ("L200", "L110"), ("L205", "L175"))
    for total, source in copies:
        page.set(total, page.amount(source) if page.has(source) else None)
    set_off = sum((page.amount(total) for total, _ in copies), ZERO)
    page.set("L210", set_off)
    return set_off


def redeem(page: PageTree, inputs: StepInputs, credit: PayableCredit | None) -> Redemption:
    """Run CT600L's RDEC steps (and totals) once box 475 is known.

    Sections the figures do not reach are left out, as the form says ("only complete step 2
    if you have RDEC remaining after completing step 1"), with any answers in them.

    Args:
        page: CT600L.
        inputs: The RDEC and the return's figures the steps read.
        credit: The SME or ERIS payable credit, already in the SME section.

    Returns:
        What the steps give the main return.
    """
    liability = _pre_step_1(page, inputs.corporation_tax)
    reached, used_on_return, payable = _steps(page, inputs, liability)
    for step in _STEPS:
        if step not in reached:
            page.remove(step)
    if credit is None and not (page.has("L185") or page.has("L190")):
        page.remove("SME")
    carried = _carried_forward(page, page.has("L5"), "Step2" in reached)
    _surrendered(page)
    set_off = _totals(page)
    return Redemption(
        set_off=set_off,
        payable_rdec=payable,
        payable_credit=None if credit is None else page.amount("L180"),
        carried_forward=carried,
        used_against_other_liabilities=used_on_return + page.amount("L175"),
    )
