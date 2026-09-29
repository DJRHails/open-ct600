"""Statutory accounts as Inline XBRL on the FRC 2026 taxonomy.

Micro-entity accounts (FRS 105) use the Companies Act micro-entity profit and loss format;
small company accounts (FRS 102 section 1A) use format 1 (cost of sales, gross profit,
administrative expenses). Both use the micro-entity balance sheet the return collects. After
the company's first period of account, the profit and loss account and balance sheet show the
previous period's figures beside this period's (``AccountsDetails.comparatives``).

A company that answers that it was dormant (``AccountsDetails.dormant``, which requires a nil
profit and loss account) has accounts that claim the section 480 audit exemption. They omit the
profit and loss account unless the previous period's has figures to compare.
"""

from dataclasses import dataclass
from decimal import Decimal

from lxml import etree

from open_ct600.computation import summarise_accounts
from open_ct600.ct600 import CT600Return, LegalForm, ReturnComputation
from open_ct600.ixbrl.layout import (
    SOFTWARE_NAME,
    SOFTWARE_VERSION,
    STYLESHEET,
    IxbrlRenderError,
    period_ended,
    period_noun,
)
from open_ct600.ixbrl.primary_statements import (
    PeriodColumn,
    balance_sheet_table,
    profit_and_loss_table,
    whole_pounds,
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
LEGAL_FORM_MEMBERS: dict[LegalForm, str] = {
    "private-limited-company": "bus:PrivateLimitedCompanyLtd",
    "private-company-limited-by-guarantee": "bus:CompanyLimitedByGuarantee",
    "private-unlimited-company": "bus:UnlimitedCompany",
    "community-interest-company": "bus:CommunityInterestCompanyCIC",
}
"""The ``bus:LegalFormEntityDimension`` member for each legal form."""


@dataclass(frozen=True)
class _Contexts:
    duration: Context
    end: Context

    def during(self, id_: str, dimension: str, member: str) -> Context:
        return Context(id_, self.duration.period, (ExplicitMember(dimension, member),))

    def director(self, number: int) -> Context:
        return self.during(
            f"dur-director{number}", "bus:EntityOfficersDimension", f"bus:Director{number}"
        )


def is_dormant(ct600: CT600Return) -> bool:
    """Whether the company says it was dormant throughout the period."""
    return ct600.accounts.dormant


def _columns(ct600: CT600Return, computation: ReturnComputation) -> list[PeriodColumn]:
    """This period's column, then the previous period's when there are comparatives."""
    current = PeriodColumn(
        prefix="",
        start=ct600.period.start,
        end_date=ct600.period.end,
        profit_and_loss=ct600.profit_and_loss,
        summary=computation.accounts,
        tax=whole_pounds(computation.accounts.corporation_tax),
    )
    comparatives = ct600.accounts.comparatives
    if comparatives is None:
        return [current]
    previous = PeriodColumn(
        prefix="prev-",
        start=comparatives.period.start,
        end_date=comparatives.period.end,
        profit_and_loss=comparatives.profit_and_loss,
        summary=summarise_accounts(
            comparatives.profit_and_loss,
            comparatives.balance_sheet,
            corporation_tax=Decimal(comparatives.tax_on_profit),
            other_income=0,
        ),
        tax=comparatives.tax_on_profit,
    )
    return [current, previous]


def _shows_profit_and_loss(ct600: CT600Return) -> bool:
    """Dormant accounts omit a nil profit and loss account with nothing to compare."""
    comparatives = ct600.accounts.comparatives
    has_previous_figures = comparatives is not None and (
        any(comparatives.profit_and_loss.model_dump().values()) or comparatives.tax_on_profit != 0
    )
    return not is_dormant(ct600) or has_previous_figures


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
    columns = _columns(ct600, computation)
    noun = period_noun(period.start, period.end)
    _hide_report_facts(document, ct600, contexts)
    document.append(*_cover(document, ct600, contexts))
    document.append(*_directors_report(document, ct600, contexts))
    if _shows_profit_and_loss(ct600):
        document.append(
            html.h2(f"Profit and loss account for the {period_ended(period.start, period.end)}"),
            profit_and_loss_table(
                document, details.standard, columns, f"Profit (loss) for the financial {noun}"
            ),
        )
    funds = (
        "Members' funds"
        if details.legal_form == "private-company-limited-by-guarantee"
        else "Shareholders' funds"
    )
    document.append(
        html.h2(
            "Balance sheet as at ",
            document.date_fact("bus:BalanceSheetDate", contexts.end, period.end),
        ),
        balance_sheet_table(document, columns, funds),
        *_statements(document, ct600, contexts),
    )
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
                "dur-legal-form",
                "bus:LegalFormEntityDimension",
                LEGAL_FORM_MEMBERS[details.legal_form],
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
    comparatives = ct600.accounts.comparatives
    previous: list[str | etree._Element] = []
    if comparatives is not None and comparatives.average_employees is not None:
        before = comparatives.period
        previous = [
            " (previous period: ",
            document.non_fraction(
                "core:AverageNumberEmployeesDuringPeriod",
                Context("prev-dur", Duration(before.start, before.end)),
                comparatives.average_employees,
                unit=Unit.PURE,
            ),
            ")",
        ]
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
            *previous,
            ".",
        ),
    ]
