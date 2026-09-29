"""Corporation Tax computations as Inline XBRL on HMRC's computational taxonomy.

The company has one UK trade, named by its principal activity. Trade-level facts carry
``ct-comp:BusinessTypeDimension=Trade``, ``TerritoryDimension=UK`` and the typed
``BusinessNameDimension``; company-level facts carry ``BusinessTypeDimension=Company``.

Marginal relief has no element in ct-comp 2024, so its row is shown untagged.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from lxml import etree

from open_ct600.ct600 import CT600Return, ReturnComputation
from open_ct600.ixbrl.layout import (
    SOFTWARE_NAME,
    SOFTWARE_VERSION,
    STYLESHEET,
    IxbrlRenderError,
    amount_row,
    period_ended,
    table,
    text_row,
)
from open_ct600.ixbrl.taxonomies import computations_taxonomy_for
from open_ct600.ixbrl.xhtml import (
    Context,
    Duration,
    ExplicitMember,
    InlineDocument,
    Instant,
    Member,
    TypedMember,
    Unit,
    html,
)
from open_ct600.tax import FinancialYearSlice


class UnsupportedComputationsPeriodError(IxbrlRenderError):
    """Raised when HMRC accepts no published computations taxonomy for the period."""


@dataclass(frozen=True)
class _Contexts:
    company_end: Context
    company: Context
    trade: Context
    trade_start: Context
    trade_end: Context


def _contexts(ct600: CT600Return) -> _Contexts:
    start, end = ct600.period.start, ct600.period.end
    company: tuple[Member, ...] = (
        ExplicitMember("ct-comp:BusinessTypeDimension", "ct-comp:Company"),
    )
    trade: tuple[Member, ...] = (
        ExplicitMember("ct-comp:BusinessTypeDimension", "ct-comp:Trade"),
        ExplicitMember("ct-comp:TerritoryDimension", "ct-comp:UK"),
        TypedMember(
            "ct-comp:BusinessNameDimension",
            "ct-comp:BusinessNameDomain",
            ct600.company.principal_activity,
        ),
    )
    duration = Duration(start, end)
    return _Contexts(
        company_end=Context("company-end", Instant(end), company),
        company=Context("company", duration, company),
        trade=Context("trade", duration, trade),
        trade_start=Context("trade-start", Instant(start - timedelta(days=1)), trade),
        trade_end=Context("trade-end", Instant(end), trade),
    )


def render_computations(ct600: CT600Return, computation: ReturnComputation) -> str:
    """Render the Corporation Tax computation as an Inline XBRL (XHTML) document.

    Args:
        ct600: The return.
        computation: The computed return; the tagged figures are its CT600 boxes.

    Returns:
        The XHTML document.

    Raises:
        UnsupportedComputationsPeriodError: If HMRC accepts no published computations
            taxonomy for the accounting period (periods ending after 31 March 2026 until
            HMRC publishes ct-comp 2025).
    """
    start, end = ct600.period.start, ct600.period.end
    taxonomy = computations_taxonomy_for(start, end)
    if taxonomy is None:
        raise UnsupportedComputationsPeriodError(
            f"HMRC has not published a computations taxonomy for accounting periods ending "
            f"after 31 March 2026, so iXBRL computations for the period ending {end} cannot "
            "be produced yet"
        )
    contexts = _contexts(ct600)
    document = InlineDocument(
        taxonomy=taxonomy,
        entity_identifier=ct600.company.registration_number,
        title=(
            f"{ct600.company.name} - Corporation Tax computation for the {period_ended(start, end)}"
        ),
        stylesheet=STYLESHEET,
    )
    document.hide(
        document.non_numeric(
            "ct-comp:NameOfProductionSoftware", contexts.company_end, SOFTWARE_NAME
        ),
        document.non_numeric(
            "ct-comp:VersionOfProductionSoftware", contexts.company_end, SOFTWARE_VERSION
        ),
    )
    boxes = {box.box: box.value for box in computation.boxes}
    document.append(*_company_information(document, ct600, contexts))
    if _has_trade(ct600):
        document.append(*_trade(document, ct600, computation, contexts))
    document.append(*_profits(document, boxes, contexts))
    document.append(*_tax(document, computation, contexts))
    return document.serialise()


def _has_trade(ct600: CT600Return) -> bool:
    adjustments = ct600.tax_adjustments
    trade_figures = (
        *ct600.profit_and_loss.model_dump().values(),
        adjustments.disallowable_expenses,
        adjustments.capital_allowances,
        adjustments.losses_brought_forward,
    )
    return ct600.accounts.trading_status != "never_traded" or any(trade_figures)


def _company_information(
    document: InlineDocument, ct600: CT600Return, contexts: _Contexts
) -> list[etree._Element]:
    start, end = ct600.period.start, ct600.period.end
    info = contexts.company_end
    return [
        html.h1(document.non_numeric("ct-comp:CompanyName", info, ct600.company.name)),
        html.p(f"Corporation Tax computation for the {period_ended(start, end)}"),
        html.table(
            text_row("Company registration number", ct600.company.registration_number),
            text_row(
                "Unique Taxpayer Reference",
                document.non_numeric("ct-comp:TaxReference", info, ct600.company.utr),
            ),
            text_row(
                "Period of account",
                document.date_fact("ct-comp:PeriodOfAccountStartDate", info, start),
                " to ",
                document.date_fact("ct-comp:PeriodOfAccountEndDate", info, end),
            ),
            text_row(
                "Period covered by the return",
                document.date_fact("ct-comp:StartOfPeriodCoveredByReturn", info, start),
                " to ",
                document.date_fact("ct-comp:EndOfPeriodCoveredByReturn", info, end),
            ),
            text_row(
                "Company is a partner in a firm",
                document.boolean("ct-comp:CompanyIsAPartnerInAFirm", contexts.company, False),
            ),
        ),
    ]


@dataclass(frozen=True)
class _TradeResult:
    profit_per_accounts: int
    depreciation: int
    disallowable: int
    non_trading_credits: int
    capital_allowances: int

    @property
    def adjusted(self) -> int:
        return (
            self.profit_per_accounts
            + self.depreciation
            + self.disallowable
            - self.non_trading_credits
            - self.capital_allowances
        )


def _trade_result(ct600: CT600Return, computation: ReturnComputation) -> _TradeResult:
    pnl, adjustments = ct600.profit_and_loss, ct600.tax_adjustments
    result = _TradeResult(
        profit_per_accounts=computation.accounts.profit_before_tax,
        depreciation=pnl.depreciation,
        disallowable=adjustments.disallowable_expenses,
        non_trading_credits=pnl.interest_income,
        capital_allowances=adjustments.capital_allowances,
    )
    boxes = {box.box: box.value for box in computation.boxes}
    if result.adjusted != boxes["155"] - computation.trading_loss_arising:
        raise RuntimeError(
            f"Adjusted trading result {result.adjusted} does not match box 155 "
            f"({boxes['155']}) less the trading loss ({computation.trading_loss_arising})"
        )
    return result


def _trade(
    document: InlineDocument,
    ct600: CT600Return,
    computation: ReturnComputation,
    contexts: _Contexts,
) -> list[etree._Element]:
    result = _trade_result(ct600, computation)
    trade = contexts.trade
    adjusted = (
        amount_row(
            "Adjusted trading profit",
            document.money("ct-comp:AdjustedProfitForThePeriod", trade, result.adjusted),
            total=True,
        )
        if result.adjusted >= 0
        else amount_row(
            "Adjusted trading loss",
            document.money("ct-comp:AdjustedLossOfPeriod", trade, -result.adjusted),
            deduction=True,
            total=True,
        )
    )
    return [
        html.h2(
            "Trading profits: ",
            document.non_numeric(
                "ct-comp:DescriptionOfTrade", trade, ct600.company.principal_activity
            ),
        ),
        table(
            amount_row(
                "Profit (loss) per accounts",
                document.money("ct-comp:ProfitLossPerAccounts", trade, result.profit_per_accounts),
            ),
            amount_row(
                "Add: depreciation",
                document.money("ct-comp:AdjustmentsDepreciation", trade, result.depreciation),
            ),
            amount_row(
                "Add: disallowable expenses",
                document.money("ct-comp:AdjustmentsOtherAdditions", trade, result.disallowable),
            ),
            amount_row(
                "Less: non-trading loan relationship credits (interest receivable)",
                document.money(
                    "ct-comp:AdjustmentsNon-tradingLoanRelationshipCreditsPerAccounts",
                    trade,
                    result.non_trading_credits,
                ),
                deduction=True,
            ),
            amount_row(
                "Less: capital allowances",
                document.money("ct-comp:TotalCapitalAllowances", trade, result.capital_allowances),
                deduction=True,
            ),
            adjusted,
        ),
        *_trade_losses(document, ct600, computation, contexts),
    ]


def _trade_losses(
    document: InlineDocument,
    ct600: CT600Return,
    computation: ReturnComputation,
    contexts: _Contexts,
) -> list[etree._Element]:
    boxes = {box.box: box.value for box in computation.boxes}
    return [
        html.h3("Trading losses"),
        table(
            amount_row(
                "Losses brought forward",
                document.money(
                    "ct-comp:BalanceOfLossesBroughtForwardCarriedForward",
                    contexts.trade_start,
                    ct600.tax_adjustments.losses_brought_forward,
                ),
            ),
            amount_row(
                "Less: used against trading profits of this period",
                document.money(
                    "ct-comp:LossesUsedAgainstTradingProfits", contexts.trade, boxes["160"]
                ),
                deduction=True,
            ),
            amount_row(
                "Add: trading loss of this period",
                document.money(
                    "ct-comp:AdjustedLossOfPeriod",
                    contexts.trade,
                    computation.trading_loss_arising,
                ),
            ),
            amount_row(
                "Losses carried forward",
                document.money(
                    "ct-comp:BalanceOfLossesBroughtForwardCarriedForward",
                    contexts.trade_end,
                    computation.losses_carried_forward,
                ),
                total=True,
            ),
        ),
    ]


def _profits(
    document: InlineDocument, boxes: dict[str, Decimal], contexts: _Contexts
) -> list[etree._Element]:
    company = contexts.company

    def row(label: str, concept: str, box: str, **style: bool) -> etree._Element:
        return amount_row(label, document.money(concept, company, boxes[box]), **style)

    return [
        html.h2("Profits chargeable to Corporation Tax"),
        table(
            row("Trading profits", "ct-comp:AdjustedTradingProfitOfThisPeriod", "155"),
            row(
                "Less: trading losses brought forward",
                "ct-comp:TradingLossesBroughtForwardSetAgainstTradingProfits",
                "160",
                deduction=True,
            ),
            row("Net trading profits", "ct-comp:NetTradingProfits", "165", total=True),
            row(
                "Profits from non-trading loan relationships",
                "ct-comp:ProfitsAndGainsFromNon-tradingLoanRelationships",
                "170",
            ),
            row("Chargeable gains", "ct-comp:NetChargeableGains", "210"),
            row(
                "Profits before other deductions and reliefs",
                "ct-comp:ProfitsBeforeOtherDeductionsAndReliefs",
                "235",
                total=True,
            ),
            row(
                "Profits before qualifying donations and group relief",
                "ct-comp:ProfitsBeforeChargesAndGroupRelief",
                "300",
                total=True,
            ),
            row("Less: qualifying donations", "ct-comp:QualifyingDonations", "305", deduction=True),
            row(
                "Total profits chargeable to Corporation Tax",
                "ct-comp:TotalProfitsChargeableToCorporationTax",
                "315",
                total=True,
            ),
        ),
    ]


def _tax(
    document: InlineDocument, computation: ReturnComputation, contexts: _Contexts
) -> list[etree._Element]:
    tax, company = computation.tax, contexts.company
    rows = [
        text_row(
            "Number of associated companies in this period",
            document.non_fraction(
                "ct-comp:NumberOfAssociatedCompaniesInThisPeriod",
                company,
                tax.associated_companies,
                unit=Unit.PURE,
            ),
        )
    ]
    for number, part in enumerate(tax.slices, start=1):
        rows += _financial_year_rows(document, number, part, company)
    if tax.marginal_relief:
        rows.append(
            html.tr(
                html.td("Less: marginal relief"),
                html.td(f"({tax.marginal_relief:,.2f})", {"class": "n"}),
            )
        )
    for label, concept in (
        ("Corporation Tax chargeable", "ct-comp:CorporationTaxChargeable"),
        ("Tax chargeable", "ct-comp:TaxChargeable"),
        ("Tax payable", "ct-comp:TaxPayable"),
    ):
        rows.append(
            amount_row(
                label, document.money(concept, company, tax.tax_chargeable, decimals=2), total=True
            )
        )
    return [html.h2("Corporation Tax"), table(*rows)]


def _financial_year_rows(
    document: InlineDocument, number: int, part: FinancialYearSlice, company: Context
) -> list[etree._Element]:
    prefix = f"ct-comp:FY{number}"
    return [
        text_row(
            "Financial year",
            document.non_numeric(
                f"ct-comp:FinancialYear{number}CoveredByTheReturn",
                company,
                str(part.financial_year),
            ),
            f" ({_describe_slice(part.start, part.end)})",
        ),
        amount_row(
            "Profits chargeable",
            document.money(f"{prefix}AmountOfProfitChargeableAtFirstRate", company, part.profits),
        ),
        text_row(
            "Rate of tax",
            document.percentage(f"{prefix}FirstRateOfTax", company, part.rate),
            "%",
        ),
        amount_row(
            "Tax at this rate",
            document.money(f"{prefix}TaxAtFirstRate", company, part.tax, decimals=2),
        ),
    ]


def _describe_slice(start: date, end: date) -> str:
    return f"{start:%d/%m/%Y} to {end:%d/%m/%Y}"
