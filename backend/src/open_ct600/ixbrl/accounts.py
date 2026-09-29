"""Statutory accounts as Inline XBRL on the FRC 2026 taxonomy.

Micro-entity accounts (FRS 105) use the Companies Act micro-entity profit and loss format;
small company accounts (FRS 102 section 1A) use format 1 (cost of sales, gross profit,
administrative expenses). Both use the micro-entity balance sheet the return collects.

A company whose profit and loss account is entirely nil is treated as dormant: its accounts
claim the section 480 audit exemption and omit the profit and loss account.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree

from open_ct600.ct600 import CT600Return, ReturnComputation
from open_ct600.ixbrl.layout import (
    SOFTWARE_NAME,
    SOFTWARE_VERSION,
    STYLESHEET,
    IxbrlRenderError,
    amount_row,
    period_ended,
    period_noun,
    table,
)
from open_ct600.ixbrl.taxonomies import FRC_2026
from open_ct600.ixbrl.xhtml import (
    Context,
    Duration,
    ExplicitMember,
    InlineDocument,
    Instant,
    Unit,
    html,
    long_date,
)

MAX_DIRECTORS = 40
"""The FRC taxonomy has members Director1 to Director40 for naming directors."""

_STANDARD_MEMBERS = {"micro": "bus:Micro-entities", "small": "bus:SmallEntities"}
_TRADING_STATUS_MEMBERS = {
    "never_traded": "bus:EntityHasNeverTraded",
    "no_longer_trading": "bus:EntityNoLongerTradingButTradedInPast",
}


@dataclass(frozen=True)
class _Contexts:
    duration: Context
    end: Context

    def during(self, id_: str, dimension: str, member: str) -> Context:
        return Context(id_, self.duration.period, (ExplicitMember(dimension, member),))

    def at_end(self, id_: str, dimension: str, member: str) -> Context:
        return Context(id_, self.end.period, (ExplicitMember(dimension, member),))

    def director(self, number: int) -> Context:
        return self.during(
            f"dur-director{number}", "bus:EntityOfficersDimension", f"bus:Director{number}"
        )


def is_dormant(ct600: CT600Return) -> bool:
    """Whether the profit and loss account is entirely nil."""
    return not any(ct600.profit_and_loss.model_dump().values())


def _whole_pounds(amount: Decimal) -> int:
    return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_accounts(ct600: CT600Return, computation: ReturnComputation) -> str:
    """Render the company's statutory accounts as an Inline XBRL (XHTML) document.

    Args:
        ct600: The return, including the accounts details.
        computation: The computed return; its accounts summary supplies the totals.

    Returns:
        The XHTML document.

    Raises:
        IxbrlRenderError: If the accounts name more directors than the taxonomy can tag.
    """
    details = ct600.accounts
    if len(details.directors) > MAX_DIRECTORS:
        raise IxbrlRenderError(
            f"iXBRL accounts can name at most {MAX_DIRECTORS} directors; "
            f"these accounts list {len(details.directors)}"
        )
    period = ct600.period
    contexts = _Contexts(
        duration=Context("dur", Duration(period.start, period.end)),
        end=Context("end", Instant(period.end)),
    )
    kind = "Micro-entity accounts" if details.standard == "micro" else "Financial statements"
    document = InlineDocument(
        taxonomy=FRC_2026,
        entity_identifier=ct600.company.registration_number,
        title=f"{ct600.company.name} - {kind} for the {period_ended(period.start, period.end)}",
        stylesheet=STYLESHEET,
    )
    _hide_report_facts(document, ct600, contexts)
    document.append(*_cover(document, ct600, contexts))
    document.append(*_directors_report(document, ct600, contexts))
    if not is_dormant(ct600):
        document.append(*_profit_and_loss(document, ct600, computation, contexts))
    document.append(*_balance_sheet(document, ct600, computation, contexts))
    document.append(*_notes(document, ct600, contexts))
    return document.serialise()


def _hide_report_facts(document: InlineDocument, ct600: CT600Return, contexts: _Contexts) -> None:
    details = ct600.accounts
    status_member = _TRADING_STATUS_MEMBERS.get(details.trading_status)
    trading_status = (
        contexts.duration
        if status_member is None
        else contexts.during(
            "dur-trading-status", "bus:EntityTradingStatusDimension", status_member
        )
    )
    signing_number = details.directors.index(details.signing_director) + 1
    document.hide(
        document.non_numeric(
            "bus:AccountingStandardsApplied",
            contexts.during(
                "dur-standard",
                "bus:AccountingStandardsDimension",
                _STANDARD_MEMBERS[details.standard],
            ),
        ),
        document.non_numeric(
            "bus:AccountsStatusAuditedOrUnaudited",
            contexts.during(
                "dur-status", "bus:AccountsStatusDimension", "bus:AuditExempt-NoAccountantsReport"
            ),
        ),
        document.non_numeric(
            "bus:AccountsType",
            contexts.during("dur-type", "bus:AccountsTypeDimension", "bus:FullAccounts"),
        ),
        document.non_numeric(
            "bus:LegalFormEntity",
            contexts.during(
                "dur-legal-form", "bus:LegalFormEntityDimension", "bus:PrivateLimitedCompanyLtd"
            ),
        ),
        document.non_numeric(
            "bus:ApplicableLegislation",
            contexts.during(
                "dur-legislation",
                "bus:ApplicableLegislationDimension",
                "bus:SmallCompaniesRegimeForAccounts",
            ),
        ),
        document.non_numeric("bus:EntityTradingStatus", trading_status),
        document.boolean("bus:EntityDormantTruefalse", contexts.duration, is_dormant(ct600)),
        document.non_numeric("bus:NameProductionSoftware", contexts.duration, SOFTWARE_NAME),
        document.non_numeric("bus:VersionProductionSoftware", contexts.duration, SOFTWARE_VERSION),
        document.non_numeric(
            "core:DirectorSigningFinancialStatements", contexts.director(signing_number)
        ),
    )


def _cover(
    document: InlineDocument, ct600: CT600Return, contexts: _Contexts
) -> list[etree._Element]:
    company, period = ct600.company, ct600.period
    audience = (
        "Unaudited micro-entity accounts"
        if ct600.accounts.standard == "micro"
        else "Unaudited financial statements prepared under FRS 102 Section 1A"
    )
    return [
        html.h1(
            document.non_numeric(
                "bus:EntityCurrentLegalOrRegisteredName", contexts.duration, company.name
            )
        ),
        html.p(
            "Company registration number ",
            document.non_numeric(
                "bus:UKCompaniesHouseRegisteredNumber",
                contexts.duration,
                company.registration_number,
            ),
        ),
        html.p(
            f"{audience} for the {period_noun(period.start, period.end)} from ",
            document.date_fact("bus:StartDateForPeriodCoveredByReport", contexts.end, period.start),
            " to ",
            document.date_fact("bus:EndDateForPeriodCoveredByReport", contexts.end, period.end),
        ),
    ]


def _directors_report(
    document: InlineDocument, ct600: CT600Return, contexts: _Contexts
) -> list[etree._Element]:
    details = ct600.accounts
    directors = [
        html.li(document.non_numeric("bus:NameEntityOfficer", contexts.director(number), name))
        for number, name in enumerate(details.directors, start=1)
    ]
    period = ct600.period
    return [
        html.h2("Directors' report"),
        html.p(
            "The principal activity of the company during the "
            f"{period_noun(period.start, period.end)} was: ",
            document.non_numeric(
                "bus:DescriptionPrincipalActivities",
                contexts.duration,
                ct600.company.principal_activity,
            ),
        ),
        html.p(
            f"The directors who served during the {period_noun(period.start, period.end)} were:"
        ),
        html.ul(*directors),
        html.p(
            document.non_numeric(
                "direp:StatementThatDirectorsReportHasBeenPreparedInAccordanceWithProvisionsSmallCompaniesRegime",
                contexts.duration,
                "This report has been prepared in accordance with the provisions applicable to "
                "companies entitled to the small companies exemption.",
            )
        ),
    ]


def _profit_and_loss(
    document: InlineDocument,
    ct600: CT600Return,
    computation: ReturnComputation,
    contexts: _Contexts,
) -> list[etree._Element]:
    period = ct600.period
    summary = computation.accounts
    tax = _whole_pounds(summary.corporation_tax)
    dur = contexts.duration
    rows = (
        _micro_operating_rows(document, ct600, dur)
        if ct600.accounts.standard == "micro"
        else _small_operating_rows(document, ct600, dur)
    )
    return [
        html.h2(f"Profit and loss account for the {period_ended(period.start, period.end)}"),
        table(
            *rows,
            amount_row(
                "Profit (loss) before tax",
                document.money(
                    "core:ProfitLossOnOrdinaryActivitiesBeforeTax", dur, summary.profit_before_tax
                ),
                total=True,
            ),
            amount_row(
                "Tax on profit",
                document.money("core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", dur, tax),
                deduction=True,
            ),
            amount_row(
                f"Profit (loss) for the financial {period_noun(period.start, period.end)}",
                document.money("core:ProfitLoss", dur, summary.profit_before_tax - tax),
                total=True,
            ),
        ),
    ]


def _micro_operating_rows(
    document: InlineDocument, ct600: CT600Return, dur: Context
) -> list[etree._Element]:
    pnl = ct600.profit_and_loss
    return [
        amount_row("Turnover", document.money("core:TurnoverRevenue", dur, pnl.turnover)),
        amount_row(
            "Other income",
            document.money("core:OtherOperatingIncomeFormat2", dur, pnl.interest_income),
        ),
        amount_row(
            "Cost of raw materials and consumables",
            document.money("core:RawMaterialsConsumablesUsed", dur, pnl.cost_of_sales),
            deduction=True,
        ),
        amount_row(
            "Staff costs",
            document.money("core:StaffCostsEmployeeBenefitsExpense", dur, pnl.staff_costs),
            deduction=True,
        ),
        amount_row(
            "Depreciation and other amounts written off assets",
            document.money("core:DepreciationAmortisationImpairmentExpense", dur, pnl.depreciation),
            deduction=True,
        ),
        amount_row(
            "Other charges",
            document.money("core:OtherOperatingExpensesFormat2", dur, pnl.other_expenses),
            deduction=True,
        ),
    ]


def _small_operating_rows(
    document: InlineDocument, ct600: CT600Return, dur: Context
) -> list[etree._Element]:
    pnl = ct600.profit_and_loss
    gross_profit = pnl.turnover - pnl.cost_of_sales
    administrative = pnl.staff_costs + pnl.depreciation + pnl.other_expenses
    return [
        amount_row("Turnover", document.money("core:TurnoverRevenue", dur, pnl.turnover)),
        amount_row(
            "Cost of sales",
            document.money("core:CostSales", dur, pnl.cost_of_sales),
            deduction=True,
        ),
        amount_row(
            "Gross profit (loss)",
            document.money("core:GrossProfitLoss", dur, gross_profit),
            total=True,
        ),
        amount_row(
            "Administrative expenses",
            document.money("core:AdministrativeExpenses", dur, administrative),
            deduction=True,
        ),
        amount_row(
            "Operating profit (loss)",
            document.money("core:OperatingProfitLoss", dur, gross_profit - administrative),
            total=True,
        ),
        amount_row(
            "Interest receivable and similar income",
            document.money(
                "core:OtherInterestReceivableSimilarIncomeFinanceIncome", dur, pnl.interest_income
            ),
        ),
    ]


def _balance_sheet(
    document: InlineDocument,
    ct600: CT600Return,
    computation: ReturnComputation,
    contexts: _Contexts,
) -> list[etree._Element]:
    summary, end = computation.accounts, contexts.end
    maturity = "core:MaturitiesOrExpirationPeriodsDimension"
    return [
        html.h2(
            "Balance sheet as at ",
            document.date_fact("bus:BalanceSheetDate", end, ct600.period.end),
        ),
        table(
            amount_row(
                "Called up share capital not paid",
                document.money(
                    "core:CalledUpShareCapitalNotPaidNotExpressedAsCurrentAsset",
                    end,
                    summary.called_up_share_capital_not_paid,
                ),
            ),
            amount_row(
                "Fixed assets", document.money("core:FixedAssets", end, summary.fixed_assets)
            ),
            amount_row(
                "Current assets",
                document.money("core:CurrentAssets", end, summary.current_assets),
            ),
            amount_row(
                "Prepayments and accrued income",
                document.money(
                    "core:PrepaymentsAccruedIncomeNotExpressedWithinCurrentAssetSubtotal",
                    end,
                    summary.prepayments_and_accrued_income,
                ),
            ),
            amount_row(
                "Creditors: amounts falling due within one year",
                document.money(
                    "core:Creditors",
                    contexts.at_end("end-within-one-year", maturity, "core:WithinOneYear"),
                    summary.creditors_within_one_year,
                ),
                deduction=True,
            ),
            amount_row(
                "Net current assets (liabilities)",
                document.money("core:NetCurrentAssetsLiabilities", end, summary.net_current_assets),
                total=True,
            ),
            amount_row(
                "Total assets less current liabilities",
                document.money(
                    "core:TotalAssetsLessCurrentLiabilities",
                    end,
                    summary.total_assets_less_current_liabilities,
                ),
                total=True,
            ),
            amount_row(
                "Creditors: amounts falling due after more than one year",
                document.money(
                    "core:Creditors",
                    contexts.at_end("end-after-one-year", maturity, "core:AfterOneYear"),
                    summary.creditors_after_one_year,
                ),
                deduction=True,
            ),
            amount_row(
                "Provisions for liabilities",
                document.money(
                    "core:ProvisionsForLiabilitiesBalanceSheetSubtotal", end, summary.provisions
                ),
                deduction=True,
            ),
            amount_row(
                "Accruals and deferred income",
                document.money(
                    "core:AccruedLiabilitiesNotExpressedWithinCreditorsSubtotal",
                    end,
                    summary.accruals_and_deferred_income,
                ),
                deduction=True,
            ),
            amount_row(
                "Net assets (liabilities)",
                document.money("core:NetAssetsLiabilities", end, summary.net_assets),
                total=True,
            ),
            *_capital_and_reserves(document, computation, contexts),
        ),
        *_statements(document, ct600, contexts),
    ]


def _capital_and_reserves(
    document: InlineDocument, computation: ReturnComputation, contexts: _Contexts
) -> list[etree._Element]:
    summary = computation.accounts
    equity = "core:EquityClassesDimension"
    return [
        html.tr(html.td(html.strong("Capital and reserves")), html.td()),
        amount_row(
            "Called up share capital",
            document.money(
                "core:Equity",
                contexts.at_end("end-share-capital", equity, "core:ShareCapital"),
                summary.called_up_share_capital,
            ),
        ),
        amount_row(
            "Profit and loss account",
            document.money(
                "core:Equity",
                contexts.at_end(
                    "end-retained-earnings", equity, "core:RetainedEarningsAccumulatedLosses"
                ),
                summary.profit_and_loss_reserve,
            ),
        ),
        amount_row(
            "Shareholders' funds",
            document.money("core:Equity", contexts.end, summary.net_assets),
            total=True,
        ),
    ]


def _statements(
    document: InlineDocument, ct600: CT600Return, contexts: _Contexts
) -> list[etree._Element]:
    period, details = ct600.period, ct600.accounts
    noun = period_noun(period.start, period.end)
    ending = long_date(period.end)
    exemption = (
        (
            "direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection480CompaniesAct2006RelatingToDormantCompanies",
            f"For the {noun} ending {ending} the company was entitled to exemption from audit "
            "under section 480 of the Companies Act 2006 relating to dormant companies.",
        )
        if is_dormant(ct600)
        else (
            "direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection477CompaniesAct2006RelatingToSmallCompanies",
            f"For the {noun} ending {ending} the company was entitled to exemption from audit "
            "under section 477 of the Companies Act 2006 relating to small companies.",
        )
    )
    regime = (
        "These accounts have been prepared in accordance with the provisions applicable to "
        "companies subject to the small companies regime and in accordance with the "
        "micro-entity provisions."
        if details.standard == "micro"
        else "These financial statements have been prepared in accordance with the provisions "
        "applicable to companies subject to the small companies regime and in accordance with "
        "FRS 102 Section 1A."
    )
    statements = [
        exemption,
        (
            "direp:StatementThatMembersHaveNotRequiredCompanyToObtainAnAudit",
            "The members have not required the company to obtain an audit in accordance with "
            "section 476 of the Companies Act 2006.",
        ),
        (
            "direp:StatementThatDirectorsAcknowledgeTheirResponsibilitiesUnderCompaniesAct",
            "The directors acknowledge their responsibilities for complying with the "
            "requirements of the Companies Act 2006 with respect to accounting records and the "
            "preparation of accounts.",
        ),
        (
            "direp:StatementThatAccountsHaveBeenPreparedInAccordanceWithProvisionsSmallCompaniesRegime",
            regime,
        ),
    ]
    signing_number = details.directors.index(details.signing_director) + 1
    return [
        *(
            html.p(document.non_numeric(concept, contexts.duration, text))
            for concept, text in statements
        ),
        html.p(
            "Approved by the board of directors on ",
            document.date_fact(
                "core:DateAuthorisationFinancialStatementsForIssue",
                contexts.end,
                details.approval_date,
            ),
            " and signed on its behalf by ",
            document.non_numeric(
                "bus:NameEntityOfficer",
                contexts.director(signing_number),
                details.signing_director,
            ),
            ", Director.",
        ),
    ]


def _notes(
    document: InlineDocument, ct600: CT600Return, contexts: _Contexts
) -> list[etree._Element]:
    period = ct600.period
    return [
        html.h2("Notes to the accounts"),
        html.h3("Employees"),
        html.p(
            "The average number of persons employed by the company (including directors) "
            f"during the {period_noun(period.start, period.end)} was ",
            document.non_fraction(
                "core:AverageNumberEmployeesDuringPeriod",
                contexts.duration,
                ct600.accounts.average_employees,
                unit=Unit.PURE,
            ),
            ".",
        ),
    ]
