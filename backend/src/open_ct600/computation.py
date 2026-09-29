"""Compute a CT600: main-return boxes, supplementary pages' calculated boxes, and reliefs.

The main return follows the form and HMRC's schema rules where the HMRC guide differs (box 295
includes 285, box 315 deducts 312, box 470 is 445 + 450 + 465). The order of the computation
is the order the figures depend on each other:

1. Pages that stand alone (CT600A, B, E, F, H, I, M, N) and the claims on CT600C, L and P.
2. Profits, boxes 145 to 315: trading profits after R&D and creative additional deductions and
   with RDEC and AVEC/VGEC as taxable income; then 300 → 305 (donations) → 310 (group relief,
   C10) → 312 (group relief for carried-forward losses, C130) → 315.
3. Corporation Tax, boxes 326 to 475, including the tonnage tax training allowance (F45) in
   box 450.
4. The credit set-off steps: CT600L (from box 475) gives box 530, then CT600P (from 475 less
   530) gives 541, alongside the SME/ERIS and creative payable credits.
5. Other tax: 480 (A80), 490 (B30), 497 (N285), 500, 505 (I70), 510, 525, 527 (K35 on CT600K,
   which reads 525), 528, then the reconciliation 545, 570, 585, 590, 600 or 605, and the
   repayment boxes 875, 880, 885 and 886.

Every completed page is checked against the schema again, so a calculated value that HMRC's
schema would reject is reported rather than filed.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import JsonValue

from open_ct600.money import ZERO, whole_pounds_down
from open_ct600.pages.charity import compute_charity
from open_ct600.pages.controlled_foreign_companies import compute_controlled_foreign_companies
from open_ct600.pages.creative import CreativeClaims, creative_claims, redeem_creative
from open_ct600.pages.freeports import Freeports, compute_freeports
from open_ct600.pages.information import compute_royalties
from open_ct600.pages.residential_property import compute_residential_property_developer_tax
from open_ct600.pages.restitution import compute_restitution_tax
from open_ct600.pages.ring_fence import RingFence, compute_ring_fence
from open_ct600.pages.tonnage_tax import TonnageTax, compute_tonnage_tax
from open_ct600.pages.tree import PageTree
from open_ct600.problems import Problem
from open_ct600.reliefs.group_relief import (
    ClaimantPosition,
    CompanyFacts,
    GroupRelief,
    check_group_relief,
    fill_group_relief_totals,
)
from open_ct600.reliefs.loans_to_participators import (
    LoansToParticipators,
    compute_loans_to_participators,
)
from open_ct600.reliefs.research_and_development import (
    MERGED_SCHEME_START,
    Claim,
    PayableCredit,
    Redemption,
    StepInputs,
    TradingPosition,
    assess_claim,
    eris_needs_a_loss,
    notional_tax_rate,
    payable_credit,
    redeem,
)
from open_ct600.schema.spec import PageCode, load_spec
from open_ct600.schema.trees import validate_tree
from open_ct600.tax import TaxComputation, average_main_rate, compute_corporation_tax

if TYPE_CHECKING:
    from open_ct600.ct600 import CT600Return

BoxKind = Literal["pounds", "money", "count", "rate", "year", "flag"]

ASSOCIATED_COMPANIES_FROM = date(2023, 4, 1)
"""Box 326 is only given for periods ending on or after this date (rule 9389)."""


@dataclass(frozen=True)
class CT600Box:
    """One box on the CT600 form.

    Attributes:
        box: The box id: ``"145"`` on the main return, as in HMRC's CT600 schema.
        label: The box description.
        value: The box value; its meaning depends on ``kind``.
        kind: How to present ``value``: whole pounds, pounds and pence, a count, a
            rate, a financial year, or a tick box (1 ticked, 0 not).
    """

    box: str
    label: str
    value: Decimal
    kind: BoxKind


@dataclass(frozen=True)
class AccountsSummary:
    """Accounts derived from the answers, in whole pounds except tax.

    The balance sheet follows the micro-entity format: net current assets are current assets
    plus prepayments less creditors due within a year; total assets less current liabilities
    add fixed assets and share capital not paid; net assets then deduct creditors due after a
    year, provisions, and accruals and deferred income.
    """

    turnover: int
    interest_income: int
    total_expenses: int
    profit_before_tax: int
    corporation_tax: Decimal
    profit_after_tax: Decimal
    called_up_share_capital_not_paid: int
    fixed_assets: int
    current_assets: int
    prepayments_and_accrued_income: int
    creditors_within_one_year: int
    net_current_assets: int
    total_assets_less_current_liabilities: int
    creditors_after_one_year: int
    provisions: int
    accruals_and_deferred_income: int
    net_assets: int
    called_up_share_capital: int
    profit_and_loss_reserve: int


@dataclass(frozen=True)
class ResearchAndDevelopmentRelief:
    """The R&D claim's outcome.

    Attributes:
        scheme: ``sme``, ``large_company_rdec`` (before 1 April 2024), ``merged_rdec`` or
            ``eris``.
        qualifying_expenditure: Qualifying R&D expenditure claimed for.
        additional_deduction: SME scheme and ERIS: the additional deduction from trading
            profits.
        enhanced_expenditure: Box 660: qualifying expenditure plus the additional deduction.
        rdec: L15, RDEC arising (taxable trading income).
        notional_tax_rate: The step 2 rate applied to the RDEC, when step 2 is reached.
        set_off: Box 530 (L210), credits set against this return's liabilities.
        payable_rdec: Box 880 (L125), payable RDEC.
        payable_credit: Box 875 (L180), the SME or ERIS credit paid out.
        credit_claimed: L170, the SME or ERIS payable credit claimed.
        losses_surrendered: Trading losses surrendered for the payable credit.
        rdec_carried_forward: L150, RDEC carried forward to the next period.
    """

    scheme: str
    qualifying_expenditure: int
    additional_deduction: int
    enhanced_expenditure: int
    rdec: Decimal
    notional_tax_rate: Decimal | None
    set_off: Decimal
    payable_rdec: Decimal | None
    payable_credit: Decimal | None
    credit_claimed: Decimal | None
    losses_surrendered: int
    rdec_carried_forward: Decimal


@dataclass(frozen=True)
class CreativeIndustriesRelief:
    """CT600P's outcome.

    Attributes:
        expenditure_credit: P95, AVEC and VGEC for the period (taxable trading income).
        expenditure_credit_set_off: Box 541 (P245).
        expenditure_credit_payable: Box 886 (P190).
        expenditure_credit_carried_forward: P210.
        additional_deduction: Box 665 (P315).
        tax_credit: P320, predecessor and cultural payable credits.
        tax_credit_set_off: Box 540 (P325).
        tax_credit_payable: Box 885 (P330).
        losses_surrendered: Trading losses surrendered for the predecessor and cultural credits.
    """

    expenditure_credit: Decimal
    expenditure_credit_set_off: Decimal | None
    expenditure_credit_payable: Decimal | None
    expenditure_credit_carried_forward: Decimal
    additional_deduction: int
    tax_credit: Decimal
    tax_credit_set_off: Decimal | None
    tax_credit_payable: Decimal | None
    losses_surrendered: int


@dataclass(frozen=True)
class ReliefsSummary:
    """The reliefs and credits claimed through supplementary pages (``None`` when not claimed).

    Attributes:
        group_relief: CT600C.
        research_and_development: The R&D claim and CT600L.
        loans_to_participators: CT600A (s455 tax).
        creative_industries: CT600P.
    """

    group_relief: GroupRelief | None = None
    research_and_development: ResearchAndDevelopmentRelief | None = None
    loans_to_participators: LoansToParticipators | None = None
    creative_industries: CreativeIndustriesRelief | None = None


@dataclass(frozen=True)
class TradingAdjustments:
    """Adjustments to the trading result that come from reliefs, not from the answers.

    The trading result for tax (box 155 less the trading loss) is the profit per accounts,
    adjusted as the answers say (depreciation, disallowable expenses, capital allowances, bank
    interest), plus ``taxable_credits``, less both additional deductions, less
    ``exempt_charitable_result``.

    Attributes:
        research_and_development_deduction: The SME or ERIS additional deduction.
        creative_deduction: CT600P's predecessor and cultural additional deductions (P315).
        taxable_credits: RDEC (L15) and AVEC/VGEC (P95), taxable trading income, in whole
            pounds rounded down.
        exempt_charitable_result: A charity whose income is all exempt (E20): its trading
            result, which is left out of box 155.
        losses_surrendered: Trading losses surrendered for R&D and creative payable credits and
            as group relief (including carried-forward losses, C160); they do not carry
            forward.
    """

    research_and_development_deduction: int
    creative_deduction: int
    taxable_credits: int
    exempt_charitable_result: int
    losses_surrendered: int


@dataclass(frozen=True)
class ReturnComputation:
    """The computed CT600: boxes, tax computation, accounts, loss position and reliefs.

    Attributes:
        boxes: The main return's boxes, in box number order.
        tax: The Corporation Tax computation (boxes 326 to 440).
        accounts: The accounts derived from the answers.
        trading_loss_arising: This period's trading loss, after additional deductions.
        losses_carried_forward: Trading losses to carry forward: brought forward less used and
            surrendered as group relief, plus the loss arising less the losses surrendered for
            R&D and creative payable credits and as group relief.
        pages: The completed supplementary page trees by page code: the answers with every
            calculated box filled in (see ``open_ct600.pages.definitions``).
        reliefs: The reliefs claimed through supplementary pages.
        trading_adjustments: How reliefs change the trading result and the losses carried
            forward, for the tax computation document.
    """

    boxes: tuple[CT600Box, ...]
    tax: TaxComputation
    accounts: AccountsSummary
    trading_loss_arising: int
    losses_carried_forward: int
    pages: dict[str, dict[str, JsonValue]]
    reliefs: ReliefsSummary
    trading_adjustments: TradingAdjustments


BOX_LABELS: dict[int, str] = {
    65: "Notice of disclosable avoidance schemes",
    95: "Loans and arrangements to participators by close companies - form CT600A",
    96: "Creative industries - form CT600P",
    100: "Controlled foreign companies and foreign permanent establishment exemptions - "
    "form CT600B",
    105: "Group and consortium - form CT600C",
    110: "Insurance - form CT600D",
    115: "Charities and Community Amateur Sports Clubs (CASCs) - form CT600E",
    120: "Tonnage tax - form CT600F",
    130: "Cross-border royalties - form CT600H",
    135: "Supplementary charge in respect of ring fence trades - form CT600I",
    140: "Disclosure of Tax Avoidance Schemes - form CT600J",
    141: "Restitution tax - form CT600K",
    142: "Research and Development - form CT600L",
    143: "Freeports and Investment Zones - form CT600M",
    144: "Residential Property Developer Tax - form CT600N",
    145: "Total turnover from trade",
    155: "Trading profits",
    160: "Trading losses brought forward set against trading profits",
    165: "Net trading profits",
    170: "Bank, building society or other interest, and profits from non-trading loan "
    "relationships",
    200: "Tonnage tax profits",
    210: "Gross chargeable gains",
    220: "Net chargeable gains",
    235: "Profits before other deductions and reliefs",
    300: "Profits before qualifying donations and group relief",
    305: "Qualifying donations",
    310: "Group relief",
    312: "Group relief for carried forward losses",
    315: "Profits chargeable to Corporation Tax",
    326: "Number of associated companies in this period",
    329: "Small profits rate or marginal relief entitlement",
    330: "Financial year",
    335: "Amount of profit",
    340: "Rate of tax",
    345: "Tax",
    380: "Financial year",
    385: "Amount of profit",
    390: "Rate of tax",
    395: "Tax",
    430: "Corporation Tax",
    435: "Marginal relief",
    440: "Corporation Tax chargeable",
    450: "Double Taxation Relief",
    470: "Total reliefs and deductions in terms of tax",
    475: "Net Corporation Tax liability",
    480: "Tax payable on loans and arrangements to participators",
    485: "You completed box A70 in CT600A",
    490: "Controlled foreign companies (CFC) tax payable",
    497: "Residential Property Developer Tax payable",
    500: "CFC tax, bank levy, bank surcharge and RPDT payable",
    505: "Supplementary charge (ring fence trades) payable",
    510: "Tax chargeable",
    525: "Self-assessment of tax payable before restitution tax",
    527: "Restitution tax",
    528: "Self-assessment of tax payable",
    530: "Research and Development credit",
    540: "Creatives tax credit",
    541: "Audio-visual and video games expenditure credits",
    545: "Total of R&D credit, creatives tax credit and AVEC/VGEC",
    570: "Surplus R&D credits and creatives tax credit payable",
    585: "Ring fence Corporation Tax included",
    590: "Ring fence supplementary charge included",
    600: "Tax outstanding",
    605: "Tax overpaid including surplus or payable credits",
    645: "Has made cross-border royalty payments",
    650: "R&D claim made by an SME",
    653: "Claim made by an R&D intensive SME",
    655: "R&D claim made by a large company",
    656: "R&D claim notification form has been submitted",
    657: "R&D additional information form has been submitted",
    658: "Creatives additional information form has been submitted",
    659: "R&D expenditure qualifying for SME or R&D intensive SME relief",
    660: "R&D enhanced expenditure",
    663: "Creatives core expenditure",
    665: "Creatives additional deduction",
    670: "R&D enhanced expenditure and creatives additional deduction",
    711: "Structures and buildings allowances",
    760: "Machinery and plant on which first year allowance is claimed",
    771: "Structures and buildings qualifying expenditure",
    780: "Losses of trades carried on wholly or partly in the UK",
    785: "Losses of UK trades: maximum available for surrender as group relief",
    875: "Payable R&D tax credit",
    880: "Payable R&D expenditure credit",
    885: "Payable creatives tax credit",
    886: "Payable audio-visual and video games expenditure credits",
}
"""Labels of the main-return boxes the service fills, as printed on the CT600 (2026)."""

_PAGE_TICKS: dict[PageCode, int] = {
    "A": 95,
    "B": 100,
    "C": 105,
    "D": 110,
    "E": 115,
    "F": 120,
    "H": 130,
    "I": 135,
    "J": 140,
    "K": 141,
    "L": 142,
    "M": 143,
    "N": 144,
    "P": 96,
}
_TICKED_BY_PAGE: dict[PageCode, int] = {"H": 645, "J": 65}
"""Tick boxes that filing a page implies: royalty payments (rule 9130), schemes (9134)."""
_FINANCIAL_YEAR_BOXES = ((330, 335, 340, 345), (380, 385, 390, 395))


def main_return_boxes() -> frozenset[str]:
    """Box ids the main return can carry, for checking the labels (and tests)."""
    page_paths = {page.node.path for page in load_spec().pages()}
    found: set[str] = set()
    stack = [load_spec().root]
    while stack:
        node = stack.pop()
        if node.path in page_paths:
            continue
        if node.box is not None:
            found.add(node.box)
        found |= set(node.box_parts())
        stack.extend(node.children)
    return frozenset(found)


@dataclass
class _Profits:
    """Boxes 145 to 315 and the loss position (whole pounds)."""

    trading_result: int
    trading_profits: int
    losses_used: int
    loss_arising: int
    interest: int
    tonnage_tax: int
    gains: int
    before_deductions: int
    donations: int
    group_relief: int
    group_relief_carried_forward: int

    @property
    def ring_fenced(self) -> int:
        """Profits no donation or group relief can be set against: tonnage tax (box 200)."""
        return self.tonnage_tax

    @property
    def chargeable(self) -> int:
        """Box 315."""
        deductions = self.donations + self.group_relief + self.group_relief_carried_forward
        return max(self.before_deductions - deductions, 0)

    @property
    def available_for_group_relief(self) -> int:
        """Box 300 less box 305, ring-fenced profits, and the company's own trading loss.

        CTA 2010 s137(4)-(5) (CTM80145): the claimant's total profits available for group
        relief are reduced by its own current-period trading loss (s37(3)(a)) whether or not
        it claims that relief, so a loss is never relieved twice (review finding H2).
        """
        reduced = self.before_deductions - self.ring_fenced - self.donations - self.loss_arising
        return max(reduced, 0)


@dataclass
class _Evaluation:
    """Working state while a return is computed."""

    ct600: "CT600Return"
    pages: dict[PageCode, PageTree]
    problems: list[Problem] = field(default_factory=list)
    boxes: dict[int, CT600Box] = field(default_factory=dict)
    research_and_development: ResearchAndDevelopmentRelief | None = None
    creative_industries: CreativeIndustriesRelief | None = None

    @property
    def period(self) -> tuple[date, date]:
        """Boxes 30 and 35."""
        return self.ct600.period.start, self.ct600.period.end

    def box(self, number: int, value: int | Decimal, kind: BoxKind = "pounds") -> None:
        """Fill a main-return box."""
        self.boxes[number] = CT600Box(str(number), BOX_LABELS[number], Decimal(value), kind)

    def money(self, number: int, value: Decimal | None) -> None:
        """Fill a pounds-and-pence box, unless ``value`` is ``None``."""
        if value is not None:
            self.box(number, value, "money")

    def tick(self, number: int, ticked: bool = True) -> None:
        """Tick a box (ticks that are not given are left out)."""
        if ticked:
            self.box(number, 1, "flag")

    def value(self, number: int) -> Decimal:
        """A filled box's value, 0 when it is not filled."""
        filled = self.boxes.get(number)
        return ZERO if filled is None else filled.value


@dataclass(frozen=True)
class _StandalonePages:
    tonnage_tax: TonnageTax | None
    exempt_charity: bool
    freeports: Freeports | None
    cfc_tax: Decimal | None
    ring_fence: RingFence | None
    rpdt: Decimal | None
    creative: CreativeClaims | None


def _run_page[T](run: _Evaluation, code: PageCode, compute: Callable[[PageTree], T]) -> T | None:
    page = run.pages.get(code)
    return None if page is None else compute(page)


def _standalone_pages(run: _Evaluation) -> _StandalonePages:
    """Compute the pages that do not depend on the main return's figures."""
    start, end = run.period
    adjustments = run.ct600.tax_adjustments
    exempt = _run_page(run, "E", lambda page: compute_charity(page, end))
    _run_page(run, "H", lambda page: compute_royalties(page, start))
    return _StandalonePages(
        tonnage_tax=_run_page(run, "F", lambda page: compute_tonnage_tax(page, start)),
        exempt_charity=bool(exempt),
        freeports=_run_page(
            run, "M", lambda page: compute_freeports(page, adjustments.capital_allowances)
        ),
        cfc_tax=_run_page(
            run, "B", lambda page: compute_controlled_foreign_companies(page, start, end)
        ),
        ring_fence=_run_page(run, "I", compute_ring_fence),
        rpdt=_run_page(
            run, "N", lambda page: compute_residential_property_developer_tax(page, start, end)
        ),
        creative=_run_page(run, "P", lambda page: creative_claims(page, start)),
    )


def _trading_result(
    run: _Evaluation, claim: Claim | None, creative: CreativeClaims | None, rdec: bool
) -> int:
    """Trading profit (positive) or loss (negative) for tax, before losses brought forward.

    Args:
        run: The evaluation.
        claim: The R&D claim, for its additional deduction and RDEC.
        creative: CT600P's claims, for the additional deduction and AVEC/VGEC.
        rdec: Whether to include the RDEC (the merged scheme's step 2 rate looks at profits
            before it).
    """
    pnl, adjustments = run.ct600.profit_and_loss, run.ct600.tax_adjustments
    result = (
        pnl.turnover
        - pnl.total_expenses
        + pnl.depreciation
        + adjustments.disallowable_expenses
        - adjustments.capital_allowances
    )
    taxable_credits = ZERO
    if claim is not None:
        result -= claim.additional_deduction
        taxable_credits += claim.rdec if rdec else ZERO
    if creative is not None:
        result -= creative.additional_deduction
        taxable_credits += creative.expenditure_credit
    return result + whole_pounds_down(taxable_credits)


def _profits(run: _Evaluation, trading_result: int, standalone: _StandalonePages) -> _Profits:
    """Boxes 155 to 315, before the group relief claims are checked."""
    adjustments, pnl = run.ct600.tax_adjustments, run.ct600.profit_and_loss
    exempt = standalone.exempt_charity
    trading_profits = 0 if exempt else max(trading_result, 0)
    losses_used = min(adjustments.losses_brought_forward, trading_profits)
    interest = 0 if exempt else pnl.interest_income
    gains = 0 if exempt else adjustments.chargeable_gains
    tonnage = standalone.tonnage_tax.profits if standalone.tonnage_tax else 0
    before = trading_profits - losses_used + interest + gains + tonnage
    group_relief = run.pages.get("C")
    return _Profits(
        trading_result=trading_result,
        trading_profits=trading_profits,
        losses_used=losses_used,
        loss_arising=0 if exempt else max(-trading_result, 0),
        interest=interest,
        tonnage_tax=tonnage,
        gains=gains,
        before_deductions=before,
        donations=min(adjustments.qualifying_donations, max(before - tonnage, 0)),
        group_relief=int(group_relief.amount("C10")) if group_relief else 0,
        group_relief_carried_forward=int(group_relief.amount("C130")) if group_relief else 0,
    )


def _profit_boxes(run: _Evaluation, profits: _Profits) -> None:
    run.box(145, run.ct600.profit_and_loss.turnover)
    run.box(155, profits.trading_profits)
    run.box(160, profits.losses_used)
    run.box(165, profits.trading_profits - profits.losses_used)
    run.box(170, profits.interest)
    if profits.tonnage_tax or "F" in run.pages:
        run.box(200, profits.tonnage_tax)
    if profits.gains:
        run.box(210, profits.gains)
        run.box(220, profits.gains)
    run.box(235, profits.before_deductions)
    run.box(300, profits.before_deductions)
    run.box(305, profits.donations)
    if "C" in run.pages:
        run.box(310, profits.group_relief)
        run.box(312, profits.group_relief_carried_forward)
    run.box(315, profits.chargeable)


def _loss_boxes(run: _Evaluation, loss: int, surrendered: tuple[int, int, int]) -> None:
    """Boxes 780 and 785: the trading loss arising and the most available as group relief.

    CT600 guide boxes 780/785 (review M4): the loss of the period (CTA 2010 s99(1)(a),
    s100), less what was surrendered for R&D or creative payable credits, which cannot also be
    surrendered as group relief. Group relief actually surrendered (C45) stays in 785.
    """
    if loss <= 0:
        return
    research_and_development, creative, _ = surrendered
    run.box(780, loss)
    run.box(785, max(loss - research_and_development - creative, 0))


def _tax_boxes(run: _Evaluation, tax: TaxComputation) -> None:
    claims_relief = any(part.band in {"small", "marginal"} for part in tax.slices)
    if run.period[1] >= ASSOCIATED_COMPANIES_FROM:
        run.box(326, tax.associated_companies, "count")
    run.box(329, int(claims_relief), "flag")
    for (year_box, profit_box, rate_box, tax_box), part in zip(
        _FINANCIAL_YEAR_BOXES, tax.slices, strict=False
    ):
        run.box(year_box, part.financial_year, "year")
        run.box(profit_box, part.profits)
        run.box(rate_box, part.rate * 100, "rate")
        run.box(tax_box, part.tax, "money")
    run.box(430, tax.tax_before_relief, "money")
    run.box(435, tax.marginal_relief, "money")
    run.box(440, tax.tax_chargeable, "money")


def _loans(run: _Evaluation) -> LoansToParticipators | None:
    page = run.pages.get("A")
    if page is None:
        return None
    outcome, problems = compute_loans_to_participators(
        page, *run.period, run.ct600.participator_loan_dates
    )
    run.problems += problems
    return outcome


def _assess_research_and_development(run: _Evaluation) -> Claim | None:
    rd, page = run.ct600.research_and_development, run.pages.get("L")
    if rd is None:
        if page is not None and not (page.has("L5") or page.has("L20")):
            run.problems.append(
                Problem(
                    ("research_and_development",),
                    "Tell us about the R&D claim, or remove CT600L: without a claim it is only "
                    "for RDEC brought forward (L5) or treated as arising (L20)",
                )
            )
        return None
    claim, problems = assess_claim(rd, page, *run.period)
    run.problems += problems
    return claim


def _group_relief(run: _Evaluation, profits: _Profits) -> GroupRelief | None:
    page = run.pages.get("C")
    if page is None:
        if run.ct600.group_relief_surrenderers:
            run.problems.append(
                Problem(("group_relief_surrenderers",), "Add CT600C with the group relief claims")
            )
        return None
    adjustments = run.ct600.tax_adjustments
    losses_available = adjustments.losses_brought_forward - profits.losses_used
    # Older losses can only relieve the trade (s45), so box 160 is taken to use them first;
    # what is left of the April 2017 and later losses could relieve total profits (s45A).
    older = adjustments.losses_brought_forward_before_april_2017
    newer_used = max(profits.losses_used - older, 0)
    newer_unused = adjustments.losses_brought_forward - older - newer_used
    position = ClaimantPosition(
        available=profits.available_for_group_relief,
        trading_loss=profits.loss_arising,
        losses_available=losses_available,
        own_losses_against_total_profits=newer_unused,
    )
    outcome, problems = check_group_relief(
        page, _company_facts(run), position, run.ct600.group_relief_surrenderers
    )
    run.problems += problems
    return outcome


def _company_facts(run: _Evaluation) -> CompanyFacts:
    return CompanyFacts(run.ct600.company.name, run.ct600.company.utr, *run.period)


def _payable_credit(
    run: _Evaluation, claim: Claim | None, profits: _Profits, group: GroupRelief | None
) -> PayableCredit | None:
    if claim is None:
        return None
    before_deduction = profits.trading_result + claim.additional_deduction
    position = TradingPosition(
        loss_before_additional_deduction=max(-before_deduction, 0),
        loss=profits.loss_arising,
        other_profits=profits.interest + profits.gains,
        group_relief_surrendered=group.trading_losses_surrendered if group else 0,
    )
    refused = eris_needs_a_loss(claim, position)
    if refused is not None:
        run.problems.append(refused)
        return None
    page = run.pages.get("L")
    if page is None:
        return None
    credit, problems = payable_credit(claim, page, position, run.period)
    run.problems += problems
    return credit


def _check_losses_surrendered(
    run: _Evaluation,
    profits: _Profits,
    surrendered: tuple[int, int, int],
) -> None:
    """The loss surrendered for credits and as group relief cannot exceed the loss arising."""
    rd, creative, group = surrendered
    page = run.pages.get("P")
    if creative and page is not None and rd + creative + group > profits.loss_arising:
        most = max(profits.loss_arising - rd - group, 0)
        box = "P285D" if page.has("P285D") else "P305D"
        page.problem(
            box,
            f"Losses surrendered for creative tax credits must be £{most:,} or less: the "
            "trading loss of the period not already surrendered",
        )


def _reliefs_in_terms_of_tax(run: _Evaluation, tonnage: TonnageTax | None) -> None:
    """Boxes 450, 470 and 475: the tonnage tax training allowance is set against the tax."""
    chargeable = run.value(440)
    allowance = tonnage.training_allowance if tonnage else ZERO
    if allowance > chargeable:
        run.pages["F"].problem(
            "F45",
            f"The training allowance set against Corporation Tax must be £{chargeable:,} or "
            "less, the tax chargeable (box 440); carry the rest forward in F50",
        )
        allowance = chargeable
    if allowance > 0:
        run.money(450, allowance)
        run.money(470, allowance)
    run.money(475, chargeable - allowance)


def _main_rate_company(
    run: _Evaluation, claim: Claim, creative: CreativeClaims | None, standalone: _StandalonePages
) -> bool:
    """Whether profits before the RDEC are taxed at the main rate or with marginal relief."""
    profits = _profits(run, _trading_result(run, claim, creative, rdec=False), standalone)
    adjustments = run.ct600.tax_adjustments
    tax = compute_corporation_tax(
        *run.period,
        taxable_profits=profits.chargeable,
        associated_companies=adjustments.associated_companies,
        exempt_distributions=adjustments.exempt_distributions,
    )
    return any(part.band in {"main", "marginal"} for part in tax.slices)


def _scheme_name(claim: Claim) -> str:
    if claim.rd.scheme != "rdec":
        return claim.rd.scheme
    return "merged_rdec" if claim.merged else "large_company_rdec"


def _redeem_research_and_development(
    run: _Evaluation,
    claim: Claim | None,
    credit: PayableCredit | None,
    standalone: _StandalonePages,
) -> Redemption | None:
    page = run.pages.get("L")
    if page is None:
        return None
    rate = notional_tax_rate(
        run.period,
        claim is not None
        and claim.merged
        and _main_rate_company(run, claim, standalone.creative, standalone),
    )
    rd = claim.rd if claim else None
    inputs = StepInputs(
        rdec=claim.rdec if claim else ZERO,
        rdec_expenditure=claim.rdec_expenditure if claim else 0,
        corporation_tax=run.value(475),
        notional_rate=rate,
        merged=run.period[0] >= MERGED_SCHEME_START,
        old_cap=rd.rd_workers_paye_and_nic if rd else None,
        period=run.period,
    )
    redemption = redeem(page, inputs, credit)
    run.money(530, redemption.set_off)
    run.money(875, redemption.payable_credit)
    run.money(880, redemption.payable_rdec)
    if claim is not None:
        run.research_and_development = ResearchAndDevelopmentRelief(
            scheme=_scheme_name(claim),
            qualifying_expenditure=claim.rd.qualifying_expenditure,
            additional_deduction=claim.additional_deduction,
            enhanced_expenditure=claim.enhanced_expenditure,
            rdec=claim.rdec,
            notional_tax_rate=(
                Decimal(rate.numerator) / Decimal(rate.denominator) if page.has("L55") else None
            ),
            set_off=redemption.set_off,
            payable_rdec=redemption.payable_rdec,
            payable_credit=redemption.payable_credit,
            credit_claimed=credit.credit if credit else None,
            losses_surrendered=credit.loss_surrendered if credit else 0,
            rdec_carried_forward=redemption.carried_forward,
        )
    return redemption


def _claim_without_page(run: _Evaluation, claim: Claim | None) -> None:
    """An SME or ERIS claim without CT600L (additional deduction only) still has a summary."""
    if claim is None or "L" in run.pages:
        return
    run.research_and_development = ResearchAndDevelopmentRelief(
        scheme=_scheme_name(claim),
        qualifying_expenditure=claim.rd.qualifying_expenditure,
        additional_deduction=claim.additional_deduction,
        enhanced_expenditure=claim.enhanced_expenditure,
        rdec=claim.rdec,
        notional_tax_rate=None,
        set_off=ZERO,
        payable_rdec=None,
        payable_credit=None,
        credit_claimed=None,
        losses_surrendered=0,
        rdec_carried_forward=ZERO,
    )


def _redeem_creative(run: _Evaluation, claims: CreativeClaims | None) -> Decimal:
    """CT600P's steps and boxes 540, 541, 663, 665, 885, 886; return P170."""
    page = run.pages.get("P")
    if page is None or claims is None:
        return ZERO
    liability = max(run.value(475) - run.value(530), ZERO)
    redemption = redeem_creative(page, claims, liability, average_main_rate(*run.period))
    run.money(541, redemption.set_off)
    if redemption.payable:
        run.money(886, redemption.payable)
    relief_payable = None
    if claims.has_relief_section:
        run.money(540, page.amount("P325"))
        run.box(663, claims.core_expenditure)
        run.box(665, claims.additional_deduction)
        relief_payable = page.amount("P330")
        if relief_payable:
            run.money(885, relief_payable)
    run.creative_industries = CreativeIndustriesRelief(
        expenditure_credit=claims.expenditure_credit,
        expenditure_credit_set_off=redemption.set_off,
        expenditure_credit_payable=redemption.payable,
        expenditure_credit_carried_forward=redemption.carried_forward,
        additional_deduction=claims.additional_deduction,
        tax_credit=claims.tax_credit,
        tax_credit_set_off=page.amount("P325") if claims.has_relief_section else None,
        tax_credit_payable=relief_payable,
        losses_surrendered=claims.losses_surrendered,
    )
    return redemption.used_against_other_liabilities


def _other_tax(
    run: _Evaluation, standalone: _StandalonePages, loans: LoansToParticipators | None
) -> None:
    """Boxes 480 to 528."""
    if loans is not None:
        run.money(480, loans.tax_payable)
        run.tick(485, loans.relief_for_later_repayments)
    run.money(490, standalone.cfc_tax)
    run.money(497, standalone.rpdt)
    if standalone.cfc_tax is not None or standalone.rpdt is not None:
        run.money(500, run.value(490) + run.value(497))
    ring_fence = standalone.ring_fence
    if ring_fence is not None:
        run.money(505, ring_fence.supplementary_charge)
    chargeable = run.value(475) + run.value(480) + run.value(500) + run.value(505)
    run.money(510, chargeable)
    run.money(525, chargeable)
    restitution = run.pages.get("K")
    if restitution is not None:
        run.money(527, compute_restitution_tax(restitution, *run.period, chargeable))
    run.money(528, chargeable + run.value(527))
    if ring_fence is not None:
        _ring_fence_included(run, ring_fence)


def _ring_fence_included(run: _Evaluation, ring_fence: RingFence) -> None:
    """Boxes 585 and 590, the ring fence tax included in the totals."""
    page = run.pages["I"]
    included = ring_fence.corporation_tax_included
    if included is not None and included > run.value(525):
        page.problem(
            "I80", "Ring fence Corporation Tax must be no more than the tax payable (box 525)"
        )
    charge = ring_fence.supplementary_charge_included
    if charge is not None and charge > run.value(505):
        page.problem(
            "I85",
            "The supplementary charge included must be no more than the "
            "supplementary charge payable (I70)",
        )
    run.money(585, included)
    run.money(590, charge)


def _reconciliation(run: _Evaluation) -> None:
    """Boxes 545, 570 and 600 or 605."""
    credits = [run.boxes[number] for number in (530, 540, 541) if number in run.boxes]
    if not credits:
        return
    total = sum((credit.value for credit in credits), ZERO)
    payable = run.value(525)
    run.money(545, total)
    run.money(570, max(total - payable, ZERO))
    if payable >= total:
        run.money(600, payable - total)
    else:
        run.money(605, total - payable)


def _check_other_liabilities(run: _Evaluation, used: Decimal) -> None:
    """Credits used against liabilities on this return must not exceed boxes 480 to 505."""
    liabilities = run.value(480) + run.value(500) + run.value(505)
    if used <= liabilities:
        return
    for code, box in (("L", "L110"), ("L", "L175"), ("P", "P170")):
        page = run.pages.get(code)
        if page is not None and page.amount(box) > 0:
            page.problem(
                box,
                f"Credits used against other liabilities on this return must be £{liabilities:,} "
                "or less in total: the tax in boxes 480 to 505",
            )
            return


def _enhanced_expenditure(run: _Evaluation, claim: Claim | None) -> None:
    """Boxes 650 to 670: who claims R&D relief, and R&D and creatives expenditure."""
    rd = run.ct600.research_and_development
    if claim is not None and rd is not None:
        sme = rd.scheme != "rdec" or (rd.company_is_sme and claim.merged)
        run.tick(650, sme)
        run.tick(653, claim.intensive)
        run.tick(655, not sme)
        run.tick(656, rd.claim_notification_submitted)
        run.tick(657, rd.additional_information_submitted)
        if rd.scheme != "rdec":
            run.box(659, rd.qualifying_expenditure)
            run.box(660, claim.enhanced_expenditure)
    creatives = run.ct600.creative_industries
    if creatives is not None:
        run.tick(658, creatives.additional_information_submitted)
    if 660 in run.boxes or 665 in run.boxes:
        run.box(670, run.value(660) + run.value(665))


def _freeport_allowances(run: _Evaluation, freeports: Freeports | None) -> None:
    """Boxes 711, 760 and 771 include CT600M's totals."""
    if freeports is None:
        return
    for number, amount in (
        (711, freeports.structures_allowances),
        (760, freeports.plant_allowances),
        (771, freeports.structures_expenditure),
    ):
        if amount:
            run.box(number, amount)


def _ticks(run: _Evaluation) -> None:
    for code in run.pages:
        run.tick(_PAGE_TICKS[code])
        if code in _TICKED_BY_PAGE:
            run.tick(_TICKED_BY_PAGE[code])


def _check_creative_form(run: _Evaluation) -> None:
    if "P" not in run.pages:
        return
    creatives = run.ct600.creative_industries
    if creatives is None or not creatives.additional_information_submitted:
        run.problems.append(
            Problem(
                ("creative_industries", "additional_information_submitted"),
                "Submit the creatives additional information form before you file this "
                "return: HMRC rejects creative industries claims made without it",
            )
        )


def _check_completed_pages(run: _Evaluation) -> None:
    """Check each completed page against the schema, as HMRC will."""
    spec = load_spec()
    for code, page in run.pages.items():
        for problem in validate_tree(spec.page(code).node, page.tree):
            run.problems.append(
                Problem(("supplementary_pages", code, *problem.path), problem.message, problem.box)
            )


def _accounts(ct600: "CT600Return", corporation_tax: Decimal) -> AccountsSummary:
    pnl, sheet = ct600.profit_and_loss, ct600.balance_sheet
    profit_before_tax = pnl.turnover + pnl.interest_income - pnl.total_expenses
    net_current_assets = (
        sheet.current_assets
        + sheet.prepayments_and_accrued_income
        - sheet.creditors_within_one_year
    )
    total_less_current = (
        sheet.called_up_share_capital_not_paid + sheet.fixed_assets + net_current_assets
    )
    net_assets = (
        total_less_current
        - sheet.creditors_after_one_year
        - sheet.provisions
        - sheet.accruals_and_deferred_income
    )
    return AccountsSummary(
        turnover=pnl.turnover,
        interest_income=pnl.interest_income,
        total_expenses=pnl.total_expenses,
        profit_before_tax=profit_before_tax,
        corporation_tax=corporation_tax,
        profit_after_tax=profit_before_tax - corporation_tax,
        called_up_share_capital_not_paid=sheet.called_up_share_capital_not_paid,
        fixed_assets=sheet.fixed_assets,
        current_assets=sheet.current_assets,
        prepayments_and_accrued_income=sheet.prepayments_and_accrued_income,
        creditors_within_one_year=sheet.creditors_within_one_year,
        net_current_assets=net_current_assets,
        total_assets_less_current_liabilities=total_less_current,
        creditors_after_one_year=sheet.creditors_after_one_year,
        provisions=sheet.provisions,
        accruals_and_deferred_income=sheet.accruals_and_deferred_income,
        net_assets=net_assets,
        called_up_share_capital=sheet.called_up_share_capital,
        profit_and_loss_reserve=net_assets - sheet.called_up_share_capital,
    )


def _losses_carried_forward(
    run: _Evaluation, profits: _Profits, adjustments: TradingAdjustments
) -> int:
    brought_forward = run.ct600.tax_adjustments.losses_brought_forward
    remaining = brought_forward - profits.losses_used + profits.loss_arising
    return max(remaining - adjustments.losses_surrendered, 0)


def _trading_adjustments(
    stages: "_Stages", surrendered: tuple[int, int, int]
) -> TradingAdjustments:
    claim, creative = stages.claim, stages.standalone.creative
    credits = (claim.rdec if claim else ZERO) + (creative.expenditure_credit if creative else ZERO)
    group = stages.group
    carried_forward = group.carried_forward_trading_losses_surrendered if group else 0
    exempt = stages.standalone.exempt_charity
    return TradingAdjustments(
        research_and_development_deduction=claim.additional_deduction if claim else 0,
        creative_deduction=creative.additional_deduction if creative else 0,
        taxable_credits=whole_pounds_down(credits),
        exempt_charitable_result=stages.profits.trading_result if exempt else 0,
        losses_surrendered=sum(surrendered) + carried_forward,
    )


@dataclass(frozen=True)
class _Stages:
    """The results of the stages before the tax is known."""

    standalone: _StandalonePages
    loans: LoansToParticipators | None
    claim: Claim | None
    profits: _Profits
    group: GroupRelief | None
    credit: PayableCredit | None


def _before_tax(run: _Evaluation) -> _Stages:
    standalone = _standalone_pages(run)
    loans = _loans(run)
    if "C" in run.pages:
        fill_group_relief_totals(run.pages["C"], _company_facts(run))
    claim = _assess_research_and_development(run)
    trading_result = _trading_result(run, claim, standalone.creative, rdec=True)
    profits = _profits(run, trading_result, standalone)
    group = _group_relief(run, profits)
    credit = _payable_credit(run, claim, profits, group)
    return _Stages(standalone, loans, claim, profits, group, credit)


def evaluate(ct600: "CT600Return") -> tuple[ReturnComputation | None, list[Problem]]:
    """Compute a return, or find the problems that stop it being computed.

    Args:
        ct600: The return, with its supplementary pages already checked against the schema
            (calculated boxes left out).

    Returns:
        The computation and no problems, or ``None`` and the problems to fix.
    """
    run = _Evaluation(
        ct600, {code: PageTree(code, tree) for code, tree in ct600.supplementary_pages.items()}
    )
    stages = _before_tax(run)
    surrendered = (
        stages.credit.loss_surrendered if stages.credit else 0,
        stages.standalone.creative.losses_surrendered if stages.standalone.creative else 0,
        stages.group.trading_losses_surrendered if stages.group else 0,
    )
    _check_losses_surrendered(run, stages.profits, surrendered)
    _profit_boxes(run, stages.profits)
    _loss_boxes(run, stages.profits.loss_arising, surrendered)
    adjustments = ct600.tax_adjustments
    tax = compute_corporation_tax(
        *run.period,
        taxable_profits=stages.profits.chargeable,
        associated_companies=adjustments.associated_companies,
        exempt_distributions=adjustments.exempt_distributions,
    )
    _tax_boxes(run, tax)
    _reliefs_in_terms_of_tax(run, stages.standalone.tonnage_tax)
    redemption = _redeem_research_and_development(
        run, stages.claim, stages.credit, stages.standalone
    )
    _claim_without_page(run, stages.claim)
    creative_used = _redeem_creative(run, stages.standalone.creative)
    _other_tax(run, stages.standalone, stages.loans)
    _reconciliation(run)
    _enhanced_expenditure(run, stages.claim)
    _freeport_allowances(run, stages.standalone.freeports)
    _ticks(run)
    rd_used = redemption.used_against_other_liabilities if redemption else ZERO
    _check_other_liabilities(run, rd_used + creative_used)
    _check_creative_form(run)
    if ct600.accounts.dormant and run.value(510) > 0:
        run.problems.append(
            Problem(
                ("accounts", "dormant"),
                "A dormant company cannot have tax to pay: check "
                "the return's answers, or say the company was not dormant",
            )
        )
    problems = [*run.problems, *(p for page in run.pages.values() for p in page.problems)]
    if problems:
        return None, problems
    _check_completed_pages(run)
    if run.problems:
        return None, run.problems
    trading_adjustments = _trading_adjustments(stages, surrendered)
    computation = ReturnComputation(
        boxes=tuple(run.boxes[number] for number in sorted(run.boxes)),
        tax=tax,
        accounts=_accounts(ct600, tax.tax_chargeable),
        trading_loss_arising=stages.profits.loss_arising,
        losses_carried_forward=_losses_carried_forward(run, stages.profits, trading_adjustments),
        pages={str(code): page.tree for code, page in run.pages.items()},
        reliefs=ReliefsSummary(
            group_relief=stages.group,
            research_and_development=run.research_and_development,
            loans_to_participators=stages.loans,
            creative_industries=run.creative_industries,
        ),
        trading_adjustments=trading_adjustments,
    )
    return computation, []
