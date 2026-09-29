"""The relief and credit sections of the iXBRL tax computation.

ct-comp 2024 (published March 2024) predates the merged R&D scheme and enhanced R&D intensive
support (ERIS), which apply to periods starting on or after 1 April 2024:

- The SME and ERIS additional deductions are tagged
  ``AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME``. Losses surrendered for
  their payable credits are tagged ``LossTreatedAsSurrenderedForRDTaxCredit``, and the credits
  themselves (box 875) ``ResearchDevelopmentTaxCreditPayable``.
- RDEC arising under both the old large-company scheme and the merged scheme is tagged
  ``AmountOfRDExpenditureCredit``.
- The payable-RDEC step elements (``PayableRDCreditCalculation…``) describe the
  pre-April-2024 steps, with notional tax at the main rate. Only the old scheme's set-off
  (box 530) and payable RDEC (box 880) are tagged with them. The merged scheme's steps
  (notional tax at 19% or 25%) have no ct-comp element, so its set-off and payable RDEC are
  shown untagged, like marginal relief.
- Creative industries credits and other boxes without a ct-comp element are shown untagged.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from lxml import etree

from open_ct600.ct600 import CT600Return, ReturnComputation
from open_ct600.ixbrl.layout import amount_row, table, text_row, untagged_row
from open_ct600.ixbrl.xhtml import Context, ExplicitMember, InlineDocument, TypedMember, html
from open_ct600.money import pence
from open_ct600.pages.tree import PageTree
from open_ct600.reliefs.loans_to_participators import filed_s455_rate

_TAX_BOX_ELEMENTS = {
    "440": "ct-comp:CorporationTaxChargeable",
    "470": "ct-comp:TotalReliefsAndDeductionsInTermsOfTaxPayable",
    "475": "ct-comp:NetCorporationTaxPayable",
    "480": "ct-comp:TaxPayableOnLoansToParticipators",
    "510": "ct-comp:TaxChargeable",
    "528": "ct-comp:TaxPayable",
    "875": "ct-comp:ResearchDevelopmentTaxCreditPayable",
}
_LARGE_COMPANY_RDEC_ELEMENTS = {
    "530": "ct-comp:PayableRDCreditCalculationAmountToBeAppliedInDischargingAnyCTLiabilityOfAP",
    "880": "ct-comp:PayableRDCreditCalculationAmountPayableToTheCompany",
}
_TOTAL_BOXES = frozenset({"440", "510", "528", "600"})


def _shown_box(number: str) -> bool:
    """Tax and credit boxes the computation lists after the tax at each rate."""
    value = int(number) if number.isdigit() else 0
    return 440 <= value <= 600 or 875 <= value <= 886


def tax_and_credit_rows(
    document: InlineDocument, computation: ReturnComputation, company: Context
) -> list[etree._Element]:
    """Boxes 440 to 600 and the payable credits (875 to 886), tagged where ct-comp can.

    Args:
        document: The computation being built.
        computation: The computed return.
        company: The company-level duration context.

    Returns:
        One row per amount box the return has in those ranges, in box order.
    """
    elements = dict(_TAX_BOX_ELEMENTS)
    claim = computation.reliefs.research_and_development
    if claim is not None and claim.scheme == "large_company_rdec":
        elements |= _LARGE_COMPANY_RDEC_ELEMENTS
    rows = []
    for box in computation.boxes:
        if box.kind not in ("pounds", "money") or not _shown_box(box.box):
            continue
        label = f"{box.label} (box {box.box})"
        total = box.box in _TOTAL_BOXES
        concept = elements.get(box.box)
        decimals = 2 if box.kind == "money" else 0
        if concept is None:
            rows.append(untagged_row(label, box.value, decimals=decimals, total=total))
            continue
        fact = document.money(concept, company, box.value, decimals=decimals)
        rows.append(amount_row(label, fact, total=total))
    return rows


def taxable_credit_rows(
    document: InlineDocument, computation: ReturnComputation, trade: Context
) -> list[etree._Element]:
    """The RDEC and AVEC/VGEC added to trading profits, and their rounding to whole pounds."""
    claim = computation.reliefs.research_and_development
    creative = computation.reliefs.creative_industries
    rdec = claim.rdec if claim is not None else Decimal(0)
    expenditure_credit = creative.expenditure_credit if creative is not None else Decimal(0)
    rows = []
    if rdec:
        rows.append(
            amount_row(
                "Add: R&D expenditure credit (taxable)",
                document.money("ct-comp:AmountOfRDExpenditureCredit", trade, rdec, decimals=2),
            )
        )
    if expenditure_credit:
        rows.append(
            untagged_row(
                "Add: audio-visual and video games expenditure credits (taxable)",
                expenditure_credit,
            )
        )
    rounding = rdec + expenditure_credit - computation.trading_adjustments.taxable_credits
    if rounding:
        rows.append(
            untagged_row("Less: credits rounded down to whole pounds", rounding, deduction=True)
        )
    return rows


def losses_surrendered_rows(
    document: InlineDocument, computation: ReturnComputation, trade: Context
) -> list[etree._Element]:
    """Trading losses surrendered: for the R&D payable credit (tagged) and otherwise."""
    claim = computation.reliefs.research_and_development
    for_research = claim.losses_surrendered if claim is not None else 0
    others = computation.trading_adjustments.losses_surrendered - for_research
    rows = []
    if for_research:
        rows.append(
            amount_row(
                "Less: surrendered for the R&D payable credit",
                document.money(
                    "ct-comp:LossTreatedAsSurrenderedForRDTaxCredit", trade, for_research
                ),
                deduction=True,
            )
        )
    if others:
        rows.append(
            untagged_row(
                "Less: surrendered for creative tax credits or as group relief",
                others,
                deduction=True,
            )
        )
    return rows


@dataclass
class _Participator:
    name: str
    loans: list[tuple[Decimal, Decimal]] = field(default_factory=list)
    """Each loan's amount and the s455 rate it is filed at."""

    @property
    def amount(self) -> Decimal:
        return sum((amount for amount, _ in self.loans), Decimal(0))

    @property
    def tax(self) -> Decimal:
        return pence(sum((amount * rate for amount, rate in self.loans), Decimal(0)))

    @property
    def rate(self) -> Decimal | None:
        rates = {rate for _, rate in self.loans}
        return rates.pop() if len(rates) == 1 else None


def _participators(page: PageTree, dates: list[date]) -> list[_Participator]:
    """Part 1's loans grouped by participator, in the order they first appear."""
    participators: dict[str, _Participator] = {}
    for row, made in zip(page.rows("A10B"), dates, strict=True):
        name = row.text("A10A") or ""
        participator = participators.setdefault(name.casefold(), _Participator(name))
        participator.loans.append((row.amount("A10B"), filed_s455_rate(made)))
    return list(participators.values())


def _loan_dates(ct600: CT600Return, page: PageTree) -> list[date]:
    given = ct600.participator_loan_dates
    if given is not None and given.loans:
        return list(given.loans)
    return [ct600.period.start] * len(page.rows("A10B"))


def loans_to_participators(
    document: InlineDocument,
    ct600: CT600Return,
    computation: ReturnComputation,
    company: Context,
) -> list[etree._Element]:
    """The s455 section: each participator's loans and tax, then the tax payable (box 480).

    Each participator's facts carry the typed ``ct-comp:ParticipatorDimension``. The amount
    taxable is the loans made in the period and outstanding at its end (CT600A part 1). Relief
    for repayments is shown for the company as a whole, untagged, because CT600A records
    repayments by loan rather than by participator.

    Returns:
        The section, or nothing when the return has no CT600A.
    """
    if "A" not in computation.pages:
        return []
    page = PageTree("A", computation.pages["A"])
    rows = [
        row
        for number, participator in enumerate(
            _participators(page, _loan_dates(ct600, page)), start=1
        )
        for row in _participator_rows(document, company, number, participator)
    ]
    return [
        html.h2("Loans to participators (CTA 2010 s455)"),
        table(
            *rows,
            untagged_row("Tax on loans (CT600A box A20)", page.amount("A20"), total=True),
            untagged_row(
                "Less: relief for loans repaid within nine months (A45)",
                page.amount("A45"),
                deduction=True,
            ),
            untagged_row(
                "Less: relief for loans repaid later (A70)", page.amount("A70"), deduction=True
            ),
            amount_row(
                "Tax payable on loans to participators (A80, box 480)",
                document.money(
                    "ct-comp:TaxPayableOnLoansToParticipators",
                    company,
                    page.amount("A80"),
                    decimals=2,
                ),
                total=True,
            ),
        ),
    ]


def _participator_rows(
    document: InlineDocument, company: Context, number: int, participator: _Participator
) -> Iterator[etree._Element]:
    context = Context(
        f"participator-{number}",
        company.period,
        (
            ExplicitMember("ct-comp:BusinessTypeDimension", "ct-comp:Company"),
            TypedMember(
                "ct-comp:ParticipatorDimension", "ct-comp:ParticipatorDomain", participator.name
            ),
        ),
    )
    yield text_row(
        "Participator",
        document.non_numeric("ct-comp:NameOfParticipator", context, participator.name),
    )
    yield amount_row(
        "Loans made in the period and outstanding at its end",
        document.money("ct-comp:LoansMadeAndOutstanding", context, participator.amount),
    )
    yield amount_row(
        "Amount taxable",
        document.money("ct-comp:LoanToParticipatorAmountTaxable", context, participator.amount),
    )
    if participator.rate is not None:
        yield text_row(
            "Rate of tax",
            document.percentage("ct-comp:LoanToParticipatorTaxRate", context, participator.rate),
            "%",
        )
    yield amount_row(
        "Tax",
        document.money(
            "ct-comp:LoanToParticipatorTaxPayable", context, participator.tax, decimals=2
        ),
    )
