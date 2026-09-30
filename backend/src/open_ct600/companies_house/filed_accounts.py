"""Last year's figures from the accounts a company filed at Companies House (Inline XBRL).

The figures are mapped onto ``ProfitAndLoss`` and ``BalanceSheet`` field names so they can be
used as comparatives. Only the filing's own period is read, not its comparatives: the period is
the most-used duration ending on the latest date, and balance sheet figures are the instants
on its last day.

**Profit and loss.** Micro-entity (FRS 105) and small (FRS 102 section 1A, format 1) accounts
lay the same result out differently, so the figures are mapped by what they are and the rest is
a balancing figure:

- ``turnover``: ``TurnoverRevenue``; else gross profit plus cost of sales; else (shown but not
  tagged) profit before tax plus the tagged expenses less other income.
- ``interest_income``: other income: the micro format's ``OtherOperatingIncomeFormat2``, and
  format 1's ``OtherOperatingIncomeFormat1`` plus interest receivable. Our micro accounts show
  this field as "Other income".
- ``cost_of_sales``: ``CostSales`` (format 1), else the micro format's
  ``RawMaterialsConsumablesUsed``.
- ``staff_costs`` and ``depreciation``: when tagged, on the face or in the notes (in format 1
  they are part of administrative expenses).
- ``other_expenses``: whatever else lies between turnover plus other income and the filed
  profit before tax (administrative, distribution and other operating expenses, interest
  payable, and in format 1 the rest of administrative expenses). So the comparatives always
  reproduce the filed profit before tax. If the tagged staff costs and depreciation exceed
  that (they were also counted in cost of sales), they are folded back into
  ``other_expenses``; if cost of sales alone exceeds it, the excess counts as other income.
- ``tax`` and ``profit_after_tax``: as filed (a tax credit is negative).

Filleted accounts, which leave the profit and loss account out, give no profit and loss: a
profit figure alone (as in a tax note) is not enough, one of its face lines must be tagged.

**Balance sheet.** Lines a filer showed but did not tag are worked out from the subtotals:
fixed assets from total assets less current liabilities and net current assets, current assets
or creditors due within a year from each other and net current assets (or current assets from
their parts), and anything between total assets less current liabilities and net assets not
tagged as creditors after one year or accruals counts as provisions (the line filers most often
leave untagged). Net liabilities tagged without ``sign="-"`` are corrected when the lines add up
to the negative.

Assets and liabilities are read as positive amounts whatever sign the filer used; creditors
come from ``Creditors`` by ``MaturitiesOrExpirationPeriodsDimension`` (within one year, after
one year), also accepting ``FinancialInstrumentCurrentNon-currentDimension``; share capital is
``Equity`` for the ``ShareCapital`` member of ``EquityClassesDimension``; net assets keep their
sign.
"""

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from lxml import etree
from pydantic import BaseModel

from open_ct600.companies_house.ixbrl_facts import Fact, UnreadableFactError, read_facts
from open_ct600.companies_house.names import person_name

_DIRECTOR_MEMBER = re.compile(
    r"""(?x)
    Director (?P<number> [0-9]+ )   # EntityOfficersDimension members Director1, Director2, ...
    """
)
type Members = frozenset[tuple[str, str]]
NO_MEMBERS: Members = frozenset()
_MATURITY = "MaturitiesOrExpirationPeriodsDimension"
_INSTRUMENT = "FinancialInstrumentCurrentNon-currentDimension"
_WITHIN_ONE_YEAR: tuple[Members, ...] = (
    frozenset({(_MATURITY, "WithinOneYear")}),
    frozenset({(_MATURITY, "WithinOneYear"), (_INSTRUMENT, "CurrentFinancialInstruments")}),
    frozenset({(_INSTRUMENT, "CurrentFinancialInstruments")}),
)
"""Creditors due within a year: filers tag them by maturity, as current instruments, or both."""
_AFTER_ONE_YEAR: tuple[Members, ...] = (
    frozenset({(_MATURITY, "AfterOneYear")}),
    frozenset({(_MATURITY, "AfterOneYear"), (_INSTRUMENT, "Non-currentFinancialInstruments")}),
    frozenset({(_INSTRUMENT, "Non-currentFinancialInstruments")}),
)
_SHARE_CAPITAL: tuple[Members, ...] = (frozenset({("EquityClassesDimension", "ShareCapital")}),)
_STANDARD = "AccountingStandardsDimension"
_LEGISLATION = "ApplicableLegislationDimension"


class AccountsNotReadableError(ValueError):
    """A filing whose figures cannot be read."""


class Period(BaseModel):
    """A period of account."""

    start: date
    end: date


class FiledProfitAndLoss(BaseModel):
    """A filed profit and loss account, in ``ProfitAndLoss`` terms (whole pounds)."""

    turnover: int
    interest_income: int
    cost_of_sales: int
    staff_costs: int
    depreciation: int
    other_expenses: int
    tax: int
    profit_after_tax: int


class FiledBalanceSheet(BaseModel):
    """A filed balance sheet, in ``BalanceSheet`` terms (whole pounds)."""

    fixed_assets: int
    current_assets: int
    called_up_share_capital_not_paid: int
    prepayments_and_accrued_income: int
    creditors_within_one_year: int
    creditors_after_one_year: int
    provisions: int
    accruals_and_deferred_income: int
    called_up_share_capital: int
    net_assets: int


class FiledAccounts(BaseModel):
    """What the latest filed accounts say, for prefilling comparatives and details.

    Attributes:
        profit_and_loss: ``None`` when the accounts were filed without one (filleted).
    """

    period: Period
    standard: Literal["micro", "small"] | None
    dormant: bool | None
    profit_and_loss: FiledProfitAndLoss | None
    balance_sheet: FiledBalanceSheet
    average_employees: int | None
    directors: list[str]
    principal_activity: str | None


def read_filed_accounts(xhtml: bytes) -> FiledAccounts:
    """Read a filed Inline XBRL accounts document.

    Raises:
        AccountsNotReadableError: If the document is not Inline XBRL we can read, including
            any malformed date, scale or figure in it.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    try:
        root = etree.fromstring(xhtml, parser)
    except etree.XMLSyntaxError as error:
        raise AccountsNotReadableError(f"the document is not valid XHTML ({error})") from error
    try:
        return _read(root)
    except AccountsNotReadableError:
        raise
    except UnreadableFactError as error:
        raise AccountsNotReadableError(str(error)) from error
    except (ValueError, ArithmeticError) as error:
        raise AccountsNotReadableError(
            f"a date, scale or figure in it is malformed ({type(error).__name__})"
        ) from error


def _read(root: etree._Element) -> FiledAccounts:
    facts = read_facts(root)
    if not facts:
        raise AccountsNotReadableError("the document has no Inline XBRL facts")
    return _Filing(facts).read()


@dataclass
class _Filing:
    facts: list[Fact]

    def __post_init__(self) -> None:
        self.period = _own_period(self.facts)

    def read(self) -> FiledAccounts:
        return FiledAccounts(
            period=self.period,
            standard=self._standard(),
            dormant=self._dormant(),
            profit_and_loss=_profit_and_loss(self),
            balance_sheet=_balance_sheet(self),
            average_employees=_whole(self.number("AverageNumberEmployeesDuringPeriod")),
            directors=self._directors(),
            principal_activity=self.text("DescriptionPrincipalActivities"),
        )

    def _matching(self, concept: str, members: Members) -> list[Fact]:
        return [
            fact
            for fact in self.facts
            if fact.concept == concept and fact.context.members == members and self._own(fact)
        ]

    def _own(self, fact: Fact) -> bool:
        context = self.period
        if fact.context.instant is not None:
            return fact.context.instant == context.end
        return fact.context.start == context.start and fact.context.end == context.end

    def number(
        self, *concepts: str, members: tuple[Members, ...] = (NO_MEMBERS,)
    ) -> Decimal | None:
        """The first of ``concepts`` tagged for this period with exactly one of ``members``."""
        for concept in concepts:
            for exact in members:
                found = [fact for fact in self._matching(concept, exact) if fact.numeric]
                if found:
                    return found[0].number()
        return None

    def text(self, concept: str) -> str | None:
        found = self._matching(concept, frozenset())
        return found[0].text or None if found else None

    def _standard(self) -> Literal["micro", "small"] | None:
        """Micro-entity (FRS 105) or small accounts; ``None`` for anything else.

        Small means FRS 102 section 1A, or FRS 102 under the small companies regime.
        """
        members = {member for fact in self.facts for member in fact.context.members}
        standards = {member for dimension, member in members if dimension == _STANDARD}
        if "Micro-entities" in standards:
            return "micro"
        small_regime = (_LEGISLATION, "SmallCompaniesRegimeForAccounts") in members
        if "SmallEntities" in standards or ("FRS102" in standards and small_regime):
            return "small"
        return None

    def _dormant(self) -> bool | None:
        found = [fact for fact in self.facts if fact.concept == "EntityDormantTruefalse"]
        return found[0].boolean() if found else None

    def _directors(self) -> list[str]:
        numbered: dict[int, str] = {}
        for fact in self.facts:
            if fact.concept != "NameEntityOfficer" or not fact.text:
                continue
            for dimension, member in fact.context.members:
                match = _DIRECTOR_MEMBER.fullmatch(member)
                if dimension == "EntityOfficersDimension" and match:
                    numbered.setdefault(int(match.group("number")), person_name(fact.text))
        return list(dict.fromkeys(numbered[number] for number in sorted(numbered)))


def _own_period(facts: list[Fact]) -> Period:
    """The filing's own period: the most-used duration among those ending last."""
    durations = Counter(
        (fact.context.start, fact.context.end)
        for fact in facts
        if fact.context.start is not None and fact.context.end is not None
    )
    if not durations:
        raise AccountsNotReadableError("the document has no period of account")
    latest = max(end for _, end in durations)
    (start, end), _ = max(
        ((span, count) for span, count in durations.items() if span[1] == latest),
        key=lambda item: item[1],
    )
    if start is None or end is None:
        raise AccountsNotReadableError("the document has no period of account")
    return Period(start=start, end=end)


_FACE_LINES = (
    "TurnoverRevenue",
    "GrossProfitLoss",
    "CostSales",
    "RawMaterialsConsumablesUsed",
    "AdministrativeExpenses",
    "OperatingProfitLoss",
    "OtherOperatingIncomeFormat1",
    "OtherOperatingIncomeFormat2",
)
"""Lines only the profit and loss account itself shows (staff costs, depreciation and tax
also appear in notes to filleted accounts)."""
_OTHER_INCOME = (
    "OtherOperatingIncomeFormat2",
    "OtherOperatingIncomeFormat1",
    "OtherInterestReceivableSimilarIncomeFinanceIncome",
)
_OTHER_CHARGES = (
    "AdministrativeExpenses",
    "DistributionCosts",
    "OtherOperatingExpensesFormat1",
    "OtherOperatingExpensesFormat2",
    "InterestPayableSimilarChargesFinanceCosts",
)
"""Expenses outside our named lines, used only when turnover itself was not tagged."""


def _profit_and_loss(filing: _Filing) -> FiledProfitAndLoss | None:
    tax = filing.number("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities") or Decimal(0)
    after_tax = filing.number("ProfitLoss")
    before_tax = filing.number("ProfitLossOnOrdinaryActivitiesBeforeTax", "ProfitLossBeforeTax")
    if before_tax is None and after_tax is not None:
        before_tax = after_tax + tax
    if before_tax is None or all(filing.number(line) is None for line in _FACE_LINES):
        return None
    cost_of_sales = _amount(filing, "CostSales", "RawMaterialsConsumablesUsed")
    turnover = filing.number("TurnoverRevenue")
    gross = filing.number("GrossProfitLoss")
    if turnover is None and gross is not None:
        turnover = gross + cost_of_sales
    lines = _Lines(
        turnover=abs(turnover) if turnover is not None else Decimal(0),
        income=sum((_amount(filing, concept) for concept in _OTHER_INCOME), Decimal(0)),
        cost_of_sales=cost_of_sales,
        staff=_amount(filing, "StaffCostsEmployeeBenefitsExpense"),
        depreciation=_amount(
            filing,
            "DepreciationAmortisationImpairmentExpense",
            "DepreciationExpensePropertyPlantEquipment",
        ),
    )
    if turnover is None:
        lines = lines.without_turnover(filing, before_tax)
    lines = lines.balanced(before_tax)
    return FiledProfitAndLoss(
        turnover=_pounds(lines.turnover),
        interest_income=_pounds(lines.income),
        cost_of_sales=_pounds(lines.cost_of_sales),
        staff_costs=_pounds(lines.staff),
        depreciation=_pounds(lines.depreciation),
        other_expenses=_pounds(lines.other),
        tax=_pounds(tax),
        profit_after_tax=_pounds(after_tax if after_tax is not None else before_tax - tax),
    )


def _amount(filing: _Filing, *concepts: str) -> Decimal:
    """A profit and loss line as a positive amount, nil when not tagged."""
    value = filing.number(*concepts)
    return Decimal(0) if value is None else abs(value)


@dataclass(frozen=True)
class _Lines:
    turnover: Decimal
    income: Decimal
    cost_of_sales: Decimal
    staff: Decimal
    depreciation: Decimal
    other: Decimal = Decimal(0)

    def without_turnover(self, filing: _Filing, before_tax: Decimal) -> "_Lines":
        """Work out turnover a filer showed but did not tag, from the tagged expenses.

        Administrative expenses include staff costs and depreciation in format 1, so those
        are not counted again when administrative expenses are tagged.
        """
        charges = sum((_amount(filing, concept) for concept in _OTHER_CHARGES), Decimal(0))
        named = self.staff + self.depreciation
        if filing.number("AdministrativeExpenses") is not None:
            named = Decimal(0)
        turnover = before_tax + self.cost_of_sales + named + charges - self.income
        return _Lines(**{**self.__dict__, "turnover": max(turnover, Decimal(0))})

    def balanced(self, before_tax: Decimal) -> "_Lines":
        """Set ``other`` so the lines give ``before_tax`` (see the module docstring)."""
        explained = self.cost_of_sales + self.staff + self.depreciation
        other = self.turnover + self.income - explained - before_tax
        if other >= 0:
            return _Lines(**{**self.__dict__, "other": other})
        other += self.staff + self.depreciation
        folded = {"staff": Decimal(0), "depreciation": Decimal(0)}
        if other >= 0:
            return _Lines(**{**self.__dict__, **folded, "other": other})
        return _Lines(**{**self.__dict__, **folded, "income": self.income - other})


_FIXED_ASSET_PARTS = (
    "IntangibleAssets",
    "PropertyPlantEquipment",
    "InvestmentProperty",
    "InvestmentsFixedAssets",
)
_CURRENT_ASSET_PARTS = ("TotalInventories", "Debtors", "CurrentAssetInvestments", "CashBankOnHand")


@dataclass(frozen=True)
class _Totals:
    """The balance sheet's subtotals, signed, where the filer tagged them."""

    net_current: int | None
    less_current: int | None
    net_assets: int | None


def _balance_sheet(filing: _Filing) -> FiledBalanceSheet:
    """Read the balance sheet's lines, then fill in lines shown but not tagged.

    The subtotals (net current assets, total assets less current liabilities, net assets)
    say what the untagged lines must be; see the module docstring.
    """
    totals = _Totals(
        net_current=_signed(filing.number("NetCurrentAssetsLiabilities")),
        less_current=_signed(filing.number("TotalAssetsLessCurrentLiabilities")),
        net_assets=_signed(filing.number("NetAssetsLiabilities", "Equity")),
    )
    # Only the balance sheet line; CalledUpShareCapitalNotPaid is a note figure, which
    # filers also use for their issued share capital.
    not_paid = _positive(filing, "CalledUpShareCapitalNotPaidNotExpressedAsCurrentAsset")
    prepayments = _positive(
        filing, "PrepaymentsAccruedIncomeNotExpressedWithinCurrentAssetSubtotal"
    )
    current_assets, creditors_within = _current_items(filing, totals, prepayments)
    after = _positive(filing, "Creditors", members=_AFTER_ONE_YEAR)
    accruals = _positive(
        filing,
        "AccruedLiabilitiesNotExpressedWithinCreditorsSubtotal",
        "AccruedLiabilitiesDeferredIncome",
    )
    provisions = _positive(
        filing,
        "ProvisionsForLiabilitiesBalanceSheetSubtotal",
        "TaxationIncludingDeferredTaxationBalanceSheetSubtotal",
    )
    if totals.less_current is not None and totals.net_assets is not None:
        untagged = totals.less_current - totals.net_assets - after - accruals - provisions
        provisions += max(untagged, 0)
    sheet = FiledBalanceSheet(
        fixed_assets=_fixed_assets(filing, totals, not_paid),
        current_assets=current_assets,
        called_up_share_capital_not_paid=not_paid,
        prepayments_and_accrued_income=prepayments,
        creditors_within_one_year=creditors_within,
        creditors_after_one_year=after,
        provisions=provisions,
        accruals_and_deferred_income=accruals,
        called_up_share_capital=_positive(filing, "Equity", members=_SHARE_CAPITAL),
        net_assets=totals.net_assets or 0,
    )
    if sheet.net_assets and sheet.net_assets == -net_assets_from_lines(sheet):
        # Net liabilities tagged without sign="-": the lines say which way round it is.
        return sheet.model_copy(update={"net_assets": -sheet.net_assets})
    return sheet


def net_assets_from_lines(sheet: FiledBalanceSheet) -> int:
    """Net assets as the balance sheet's lines add up (micro-entity format)."""
    return (
        sheet.fixed_assets
        + sheet.current_assets
        + sheet.called_up_share_capital_not_paid
        + sheet.prepayments_and_accrued_income
        - sheet.creditors_within_one_year
        - sheet.creditors_after_one_year
        - sheet.provisions
        - sheet.accruals_and_deferred_income
    )


def _current_items(filing: _Filing, totals: _Totals, prepayments: int) -> tuple[int, int]:
    """Current assets and creditors due within a year.

    Either one, if untagged, follows from the other and net current assets; current assets
    without net current assets are the sum of their parts. Creditors tagged without saying
    when they fall due count as due within a year only when nothing else says.
    """
    current = _optional_positive(filing, "CurrentAssets")
    within = _optional_positive(filing, "Creditors", members=_WITHIN_ONE_YEAR)
    if within is None and current is not None and totals.net_current is not None:
        within = max(current + prepayments - totals.net_current, 0)
    if within is None:
        within = _optional_positive(filing, "Creditors")
    if current is None and totals.net_current is not None:
        current = max(totals.net_current + (within or 0) - prepayments, 0)
    if current is None:
        current = sum(
            _positive(filing, part, members=(NO_MEMBERS, *_WITHIN_ONE_YEAR))
            for part in _CURRENT_ASSET_PARTS
        )
    return current, within or 0


def _fixed_assets(filing: _Filing, totals: _Totals, not_paid: int) -> int:
    """``FixedAssets``, or what the subtotals or its parts say it is.

    Untagged, it is total assets less current liabilities less net current assets and
    unpaid share capital; without those subtotals, the sum of its parts.
    """
    total = _optional_positive(filing, "FixedAssets")
    if total is not None:
        return total
    if totals.less_current is not None and totals.net_current is not None:
        return max(totals.less_current - totals.net_current - not_paid, 0)
    return sum(_positive(filing, part) for part in _FIXED_ASSET_PARTS)


def _optional_positive(
    filing: _Filing, *concepts: str, members: tuple[Members, ...] = (NO_MEMBERS,)
) -> int | None:
    value = filing.number(*concepts, members=members)
    return None if value is None else _pounds(abs(value))


def _positive(filing: _Filing, *concepts: str, members: tuple[Members, ...] = (NO_MEMBERS,)) -> int:
    return _optional_positive(filing, *concepts, members=members) or 0


def _signed(value: Decimal | None) -> int | None:
    return None if value is None else _pounds(value)


def _pounds(value: Decimal | int) -> int:
    return int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _whole(value: Decimal | None) -> int | None:
    return None if value is None else _pounds(value)
