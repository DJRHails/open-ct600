"""The profit and loss account and balance sheet, with a column per period.

Each line is defined once and evaluated for this period and, when the company gives them, the
previous period's comparatives. Every amount in every column is tagged in that period's
context: the previous period's facts use a ``prev-`` duration and an instant at its end.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree

from open_ct600.computation import AccountsSummary
from open_ct600.ct600 import ProfitAndLoss
from open_ct600.ixbrl.layout import amount_cell
from open_ct600.ixbrl.xhtml import (
    Context,
    Duration,
    ExplicitMember,
    InlineDocument,
    Instant,
    html,
    long_date,
)

_MATURITY = "core:MaturitiesOrExpirationPeriodsDimension"
_EQUITY = "core:EquityClassesDimension"


def whole_pounds(amount: Decimal) -> int:
    """An amount rounded half up to whole pounds, as the accounts show it."""
    return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class PeriodColumn:
    """One period's column: its contexts and figures.

    Attributes:
        prefix: Prefix for the ids of the period's contexts: ``""`` now, ``"prev-"`` before.
        start: The first day of the period.
        end_date: The last day of the period.
        profit_and_loss: The period's profit and loss answers.
        summary: The period's accounts totals.
        tax: The tax charge in the profit and loss account, in whole pounds.
    """

    prefix: str
    start: date
    end_date: date
    profit_and_loss: ProfitAndLoss
    summary: AccountsSummary
    tax: int

    @property
    def duration(self) -> Context:
        """The period's duration context (``dur`` for this period)."""
        return Context(f"{self.prefix}dur", Duration(self.start, self.end_date))

    @property
    def end(self) -> Context:
        """The instant context at the period's end (``end`` for this period)."""
        return Context(f"{self.prefix}end", Instant(self.end_date))

    def context(self, suffix: str, dimension: str, member: str, *, instant: bool) -> Context:
        """A context of this period with one explicit dimension member."""
        base = self.end if instant else self.duration
        return Context(f"{self.prefix}{suffix}", base.period, (ExplicitMember(dimension, member),))


@dataclass(frozen=True)
class _Line:
    label: str
    concept: str
    amount: Callable[[PeriodColumn], int]
    member: tuple[str, str, str] | None = None
    """The context id suffix, dimension and member, for dimensional facts."""
    deduction: bool = False
    total: bool = False
    optional: bool = False
    """Shown only when some period has a non-nil amount."""
    section: str | None = None
    """A heading shown above the line, starting a section of the statement."""


def _rows(
    document: InlineDocument,
    line: _Line,
    columns: Sequence[PeriodColumn],
    *,
    instant: bool,
) -> list[etree._Element]:
    amounts = [line.amount(column) for column in columns]
    if line.optional and not any(amounts):
        return []
    heading = (
        [html.tr(html.td(html.strong(line.section)), *(html.td() for _ in columns))]
        if line.section
        else []
    )
    cells = []
    for column, amount in zip(columns, amounts, strict=True):
        if line.member is None:
            context = column.end if instant else column.duration
        else:
            suffix, dimension, member = line.member
            context = column.context(suffix, dimension, member, instant=instant)
        fact = document.money(line.concept, context, amount)
        cells.append(amount_cell(fact, deduction=line.deduction))
    row = html.tr(html.td(line.label), *cells)
    if line.total:
        row.set("class", "total")
    return [*heading, row]


def _table(
    document: InlineDocument,
    lines: Sequence[_Line],
    columns: Sequence[PeriodColumn],
    *,
    instant: bool,
) -> etree._Element:
    heading = html.tr(
        html.th(""),
        *(
            html.th(long_date(column.end_date), html.br(), "\N{POUND SIGN}", {"class": "n"})
            for column in columns
        ),
    )
    rows = [row for line in lines for row in _rows(document, line, columns, instant=instant)]
    return html.table(heading, *rows)


def _credits(column: PeriodColumn) -> int:
    return column.summary.other_income


def _micro_lines() -> list[_Line]:
    return [
        _Line("Turnover", "core:TurnoverRevenue", lambda c: c.profit_and_loss.turnover),
        _Line(
            "Other income",
            "core:OtherOperatingIncomeFormat2",
            lambda c: c.profit_and_loss.interest_income + _credits(c),
        ),
        _Line(
            "Cost of raw materials and consumables",
            "core:RawMaterialsConsumablesUsed",
            lambda c: c.profit_and_loss.cost_of_sales,
            deduction=True,
        ),
        _Line(
            "Staff costs",
            "core:StaffCostsEmployeeBenefitsExpense",
            lambda c: c.profit_and_loss.staff_costs,
            deduction=True,
        ),
        _Line(
            "Depreciation and other amounts written off assets",
            "core:DepreciationAmortisationImpairmentExpense",
            lambda c: c.profit_and_loss.depreciation,
            deduction=True,
        ),
        _Line(
            "Other charges",
            "core:OtherOperatingExpensesFormat2",
            lambda c: c.profit_and_loss.other_expenses,
            deduction=True,
        ),
    ]


def _gross_profit(column: PeriodColumn) -> int:
    return column.profit_and_loss.turnover - column.profit_and_loss.cost_of_sales


def _administrative(column: PeriodColumn) -> int:
    pnl = column.profit_and_loss
    return pnl.staff_costs + pnl.depreciation + pnl.other_expenses


def _small_lines() -> list[_Line]:
    """Format 1's lines; the RDEC and AVEC/VGEC are other operating income."""
    return [
        _Line("Turnover", "core:TurnoverRevenue", lambda c: c.profit_and_loss.turnover),
        _Line(
            "Cost of sales",
            "core:CostSales",
            lambda c: c.profit_and_loss.cost_of_sales,
            deduction=True,
        ),
        _Line("Gross profit (loss)", "core:GrossProfitLoss", _gross_profit, total=True),
        _Line(
            "Administrative expenses",
            "core:AdministrativeExpenses",
            _administrative,
            deduction=True,
        ),
        _Line(
            "Other operating income", "core:OtherOperatingIncomeFormat1", _credits, optional=True
        ),
        _Line(
            "Operating profit (loss)",
            "core:OperatingProfitLoss",
            lambda c: _gross_profit(c) - _administrative(c) + _credits(c),
            total=True,
        ),
        _Line(
            "Interest receivable and similar income",
            "core:OtherInterestReceivableSimilarIncomeFinanceIncome",
            lambda c: c.profit_and_loss.interest_income,
        ),
    ]


def profit_and_loss_table(
    document: InlineDocument,
    standard: str,
    columns: Sequence[PeriodColumn],
    profit_label: str,
) -> etree._Element:
    """The profit and loss account in the micro-entity format or format 1 (FRS 102 1A).

    Args:
        document: The accounts being built.
        standard: ``micro`` or ``small``.
        columns: This period, then the previous one if there are comparatives.
        profit_label: The label of the profit (loss) for the period.

    Returns:
        The table.
    """
    operating = _micro_lines() if standard == "micro" else _small_lines()
    return _table(
        document,
        [
            *operating,
            _Line(
                "Profit (loss) before tax",
                "core:ProfitLossOnOrdinaryActivitiesBeforeTax",
                lambda c: c.summary.profit_before_tax,
                total=True,
            ),
            _Line(
                "Tax on profit",
                "core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities",
                lambda c: c.tax,
                deduction=True,
            ),
            _Line(
                profit_label,
                "core:ProfitLoss",
                lambda c: c.summary.profit_before_tax - c.tax,
                total=True,
            ),
        ],
        columns,
        instant=False,
    )


def _balance_sheet_lines(funds_label: str) -> list[_Line]:
    return [
        _Line(
            "Called up share capital not paid",
            "core:CalledUpShareCapitalNotPaidNotExpressedAsCurrentAsset",
            lambda c: c.summary.called_up_share_capital_not_paid,
        ),
        _Line("Fixed assets", "core:FixedAssets", lambda c: c.summary.fixed_assets),
        _Line("Current assets", "core:CurrentAssets", lambda c: c.summary.current_assets),
        _Line(
            "Prepayments and accrued income",
            "core:PrepaymentsAccruedIncomeNotExpressedWithinCurrentAssetSubtotal",
            lambda c: c.summary.prepayments_and_accrued_income,
        ),
        _Line(
            "Creditors: amounts falling due within one year",
            "core:Creditors",
            lambda c: c.summary.creditors_within_one_year,
            member=("end-within-one-year", _MATURITY, "core:WithinOneYear"),
            deduction=True,
        ),
        _Line(
            "Net current assets (liabilities)",
            "core:NetCurrentAssetsLiabilities",
            lambda c: c.summary.net_current_assets,
            total=True,
        ),
        _Line(
            "Total assets less current liabilities",
            "core:TotalAssetsLessCurrentLiabilities",
            lambda c: c.summary.total_assets_less_current_liabilities,
            total=True,
        ),
        _Line(
            "Creditors: amounts falling due after more than one year",
            "core:Creditors",
            lambda c: c.summary.creditors_after_one_year,
            member=("end-after-one-year", _MATURITY, "core:AfterOneYear"),
            deduction=True,
        ),
        _Line(
            "Provisions for liabilities",
            "core:ProvisionsForLiabilitiesBalanceSheetSubtotal",
            lambda c: c.summary.provisions,
            deduction=True,
        ),
        _Line(
            "Accruals and deferred income",
            "core:AccruedLiabilitiesNotExpressedWithinCreditorsSubtotal",
            lambda c: c.summary.accruals_and_deferred_income,
            deduction=True,
        ),
        _Line(
            "Net assets (liabilities)",
            "core:NetAssetsLiabilities",
            lambda c: c.summary.net_assets,
            total=True,
        ),
        _Line(
            "Called up share capital",
            "core:Equity",
            lambda c: c.summary.called_up_share_capital,
            member=("end-share-capital", _EQUITY, "core:ShareCapital"),
            section="Capital and reserves",
        ),
        _Line(
            "Profit and loss account",
            "core:Equity",
            lambda c: c.summary.profit_and_loss_reserve,
            member=("end-retained-earnings", _EQUITY, "core:RetainedEarningsAccumulatedLosses"),
        ),
        _Line(funds_label, "core:Equity", lambda c: c.summary.net_assets, total=True),
    ]


def balance_sheet_table(
    document: InlineDocument, columns: Sequence[PeriodColumn], funds_label: str
) -> etree._Element:
    """The micro-entity format balance sheet at the end of each period.

    Args:
        document: The accounts being built.
        columns: This period, then the previous one if there are comparatives.
        funds_label: The label of total equity ("Shareholders' funds" or "Members' funds").

    Returns:
        The table.
    """
    return _table(document, _balance_sheet_lines(funds_label), columns, instant=True)
