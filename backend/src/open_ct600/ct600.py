"""CT600 return: the answers a company gives, and the boxes and accounts derived from them.

The main return models a UK company preparing micro-entity or small company accounts, with
trading profits, bank interest, chargeable gains, trading losses brought forward and
qualifying charitable donations. Supplementary pages (CT600A to CT600P) are element trees
validated against HMRC's schema (see ``open_ct600.schema``).
"""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from open_ct600.schema.spec import PageCode, load_spec
from open_ct600.schema.trees import validate_tree
from open_ct600.tax import PeriodError, TaxComputation, compute_corporation_tax, validate_period

MAX_POUNDS = 99_999_999_999
Pounds = Annotated[int, Field(ge=0, le=MAX_POUNDS)]

_COMPANY_NUMBER = re.compile(
    r"""(?x)          # verbose
    ^(?:
      \d{8}           # England and Wales: eight digits
    | [A-Z]{2}\d{6}   # two-letter prefix (SC, NI, OC, ...) and six digits
    )$
    """
)
_UTR = re.compile(
    r"""(?x)  # verbose
    ^\d{10}$  # Unique Taxpayer Reference: ten digits
    """
)
_WHITESPACE = re.compile(
    r"""(?x)  # verbose
    \s+       # any run of whitespace
    """
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _answer_error(
    message: str, location: tuple[str | int, ...], value: object, box: str | None = None
) -> InitErrorDetails:
    """One answer's validation error, located below the field being validated.

    The message goes in the error's context (``{message}``) because pydantic only takes
    literal message templates; ``box`` is the CT600 box id, when there is one.
    """
    context = {"message": message, "box": box}
    error = PydanticCustomError("invalid_answer", "{message}", context)
    return InitErrorDetails(type=error, loc=location, input=value)


def _located_error(message: str, location: tuple[str | int, ...], value: object) -> ValueError:
    """A validation error pointing below the field being validated (pydantic prefixes it)."""
    details = [_answer_error(message, location, value)]
    return ValidationError.from_exception_data("CT600Return", details)


class CompanyDetails(_Strict):
    """Who the return is for.

    Attributes:
        company_type: CT600 box 4, the type of company. ``0`` is a UK trading company (or any
            company not listed); ``1`` a unit trust or open-ended investment company; ``2`` a
            community interest company; ``3`` a company in liquidation, for its second or later
            accounting period; ``4`` a qualifying asset holding company; ``5`` an insurance
            company whose policyholders' share of profits is charged at the basic rate; ``6`` a
            members' club or voluntary association; ``7`` a property management company; ``8``
            a charity or company owned by a charity; ``9`` a REIT group company's residual
            business; ``10`` a REIT's tax-exempt business; ``11`` a non-resident company.
        principal_activity: What the company does, as stated in its accounts.
    """

    name: Annotated[str, Field(min_length=1, max_length=160)]
    registration_number: str
    utr: str
    company_type: Annotated[int, Field(ge=0, le=11)] = 0
    principal_activity: Annotated[str, Field(min_length=1, max_length=200)]

    @field_validator("registration_number")
    @classmethod
    def _check_registration_number(cls, value: str) -> str:
        normalised = _WHITESPACE.sub("", value).upper()
        if not _COMPANY_NUMBER.match(normalised):
            raise ValueError(
                "Enter a company registration number in the correct format, "
                "like 01234567 or SC123456"
            )
        return normalised

    @field_validator("utr")
    @classmethod
    def _check_utr(cls, value: str) -> str:
        normalised = _WHITESPACE.sub("", value)
        if not _UTR.match(normalised):
            raise ValueError(
                "Enter a Unique Taxpayer Reference in the correct format, like 1234567890"
            )
        return normalised


class ReturnPeriod(_Strict):
    """The accounting period the return covers."""

    start: date
    end: date

    @model_validator(mode="after")
    def _check_period(self) -> Self:
        try:
            validate_period(self.start, self.end)
        except PeriodError as error:
            raise ValueError(str(error)) from error
        return self


class ProfitAndLoss(_Strict):
    """Figures from the company's profit and loss account, in whole pounds."""

    turnover: Pounds
    interest_income: Pounds = 0
    cost_of_sales: Pounds = 0
    staff_costs: Pounds = 0
    depreciation: Pounds = 0
    other_expenses: Pounds = 0

    @property
    def total_expenses(self) -> int:
        """All expenses charged in the accounts, including depreciation."""
        return self.cost_of_sales + self.staff_costs + self.depreciation + self.other_expenses


class TaxAdjustments(_Strict):
    """Adjustments that turn accounting profit into taxable profit."""

    disallowable_expenses: Pounds = 0
    capital_allowances: Pounds = 0
    losses_brought_forward: Pounds = 0
    chargeable_gains: Pounds = 0
    qualifying_donations: Pounds = 0
    exempt_distributions: Pounds = 0
    associated_companies: Annotated[int, Field(ge=0, le=999)] = 0


class BalanceSheet(_Strict):
    """Balance sheet at the end of the period in the micro-entity format, in whole pounds.

    The items are those of the Companies Act micro-entity balance sheet (FRS 105): called up
    share capital not paid (A), fixed assets (B), current assets (C), prepayments and accrued
    income (D), creditors within one year (E), creditors after more than one year (H),
    provisions for liabilities (I), accruals and deferred income (J) and called up share
    capital (part of K). Totals are derived in ``AccountsSummary``.
    """

    called_up_share_capital_not_paid: Pounds = 0
    fixed_assets: Pounds = 0
    current_assets: Pounds = 0
    prepayments_and_accrued_income: Pounds = 0
    creditors_within_one_year: Pounds = 0
    creditors_after_one_year: Pounds = 0
    provisions: Pounds = 0
    accruals_and_deferred_income: Pounds = 0
    called_up_share_capital: Pounds = 0


DirectorName = Annotated[str, Field(min_length=1, max_length=120)]


class AccountsDetails(_Strict):
    """Facts about the statutory accounts filed with the return.

    Attributes:
        standard: ``micro`` for FRS 105 micro-entity accounts, ``small`` for FRS 102
            section 1A small company accounts.
        approval_date: When the board approved the accounts; after the period ends.
        directors: Everyone who was a director during the period.
        signing_director: The director who signed the balance sheet; one of ``directors``.
        average_employees: Average number of employees (including directors) in the period.
        trading_status: Whether the company traded in the period, never has, or has stopped.
    """

    standard: Literal["micro", "small"]
    approval_date: date
    directors: Annotated[list[DirectorName], Field(min_length=1, max_length=50)]
    signing_director: DirectorName
    average_employees: Annotated[int, Field(ge=0, le=9_999_999)]
    trading_status: Literal["trading", "never_traded", "no_longer_trading"]

    @field_validator("directors")
    @classmethod
    def _check_directors_are_distinct(cls, directors: list[str]) -> list[str]:
        seen: set[str] = set()
        for index, director in enumerate(directors):
            if director.casefold() in seen:
                raise _located_error(
                    f"{director} is already listed; enter each director once", (index,), director
                )
            seen.add(director.casefold())
        return directors

    @model_validator(mode="after")
    def _check_signing_director(self) -> Self:
        if self.signing_director not in self.directors:
            raise _located_error(
                "Select the director who signed the accounts from the list of directors",
                ("signing_director",),
                self.signing_director,
            )
        return self


SupplementaryPages = dict[PageCode, dict[str, JsonValue]]


def _answer_at(tree: JsonValue, path: tuple[str | int, ...]) -> JsonValue:
    """The answer at ``path`` in an element tree, or ``None`` where it is missing."""
    answer = tree
    for step in path:
        if isinstance(step, int) and isinstance(answer, list) and step < len(answer):
            answer = answer[step]
        elif isinstance(step, str) and isinstance(answer, dict):
            answer = answer.get(step)
        else:
            return None
    return answer


class CT600Return(_Strict):
    """Everything needed to compute a company's CT600 return.

    Attributes:
        supplementary_pages: Supplementary pages by code (``"A"`` for CT600A), each an element
            tree for that page's root element (see ``open_ct600.schema.trees``).
    """

    company: CompanyDetails
    period: ReturnPeriod
    profit_and_loss: ProfitAndLoss
    tax_adjustments: TaxAdjustments
    balance_sheet: BalanceSheet
    accounts: AccountsDetails
    supplementary_pages: SupplementaryPages = Field(default_factory=dict)

    @field_validator("tax_adjustments")
    @classmethod
    def _check_disallowable_within_expenses(
        cls, adjustments: TaxAdjustments, info: ValidationInfo
    ) -> TaxAdjustments:
        profit_and_loss = info.data.get("profit_and_loss")
        if profit_and_loss is None:
            return adjustments
        if adjustments.disallowable_expenses > profit_and_loss.total_expenses:
            raise ValueError(
                "Disallowable expenses cannot be more than the total expenses in your "
                "profit and loss account"
            )
        return adjustments

    @field_validator("accounts")
    @classmethod
    def _check_accounts_approved_after_period(
        cls, accounts: AccountsDetails, info: ValidationInfo
    ) -> AccountsDetails:
        period = info.data.get("period")
        if period is not None and accounts.approval_date <= period.end:
            raise _located_error(
                "The date the accounts were approved must be after the end of the accounting "
                "period",
                ("approval_date",),
                accounts.approval_date.isoformat(),
            )
        return accounts

    @field_validator("supplementary_pages")
    @classmethod
    def _check_supplementary_pages(cls, pages: SupplementaryPages) -> SupplementaryPages:
        spec = load_spec()
        details: list[InitErrorDetails] = []
        for code, tree in pages.items():
            page = spec.page(code)
            if page.dormant:
                message = (
                    f"Remove CT600{code} ({page.title}): the page is not in use because no "
                    f"{page.title} rate of Corporation Tax is in force"
                )
                details.append(_answer_error(message, (code,), tree))
                continue
            details += [
                _answer_error(
                    problem.message,
                    (code, *problem.path),
                    _answer_at(tree, problem.path),
                    problem.box,
                )
                for problem in validate_tree(page.node, tree)
            ]
        if details:
            raise ValidationError.from_exception_data("SupplementaryPages", details)
        return pages


class SignatoryCapacity(StrEnum):
    """The capacity in which the person signs the declaration."""

    DIRECTOR = "director"
    COMPANY_SECRETARY = "company_secretary"
    AUTHORISED_AGENT = "authorised_agent"


class Declaration(_Strict):
    """The statement the signatory makes when submitting the return."""

    name: Annotated[str, Field(min_length=1, max_length=120)]
    capacity: SignatoryCapacity
    confirmed: Literal[True]


class Submission(_Strict):
    """A return and the declaration made when submitting it."""

    ct600: CT600Return
    declaration: Declaration


BoxKind = Literal["pounds", "money", "count", "rate", "year", "flag"]


@dataclass(frozen=True)
class CT600Box:
    """One box on the CT600 form.

    Attributes:
        box: The box id: ``"145"`` on the main return, ``"A80"`` or ``"L210"`` on a
            supplementary page, as in HMRC's CT600 schema.
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
class ReturnComputation:
    """The computed CT600: boxes, tax computation, accounts and loss position.

    Attributes:
        pages: The completed supplementary page trees, by page code. For now these are the
            validated answers as given; computed page boxes are not yet filled in.
    """

    boxes: tuple[CT600Box, ...]
    tax: TaxComputation
    accounts: AccountsSummary
    trading_loss_arising: int
    losses_carried_forward: int
    pages: dict[str, dict[str, JsonValue]]


def _box(number: int, label: str, value: int | Decimal, kind: BoxKind = "pounds") -> CT600Box:
    """A main return box; their ids are plain numbers."""
    return CT600Box(box=str(number), label=label, value=Decimal(value), kind=kind)


@dataclass(frozen=True)
class _ProfitPosition:
    boxes: list[CT600Box]
    chargeable: int
    losses_used: int
    trading_loss_arising: int


def _profit_boxes(ct600: CT600Return) -> _ProfitPosition:
    """Compute boxes 145 to 315 and the trading loss position."""
    pnl, adjustments = ct600.profit_and_loss, ct600.tax_adjustments
    trading_result = (
        pnl.turnover
        - pnl.total_expenses
        + pnl.depreciation
        + adjustments.disallowable_expenses
        - adjustments.capital_allowances
    )
    trading_profits = max(trading_result, 0)
    losses_used = min(adjustments.losses_brought_forward, trading_profits)
    net_trading_profits = trading_profits - losses_used
    before_deductions = net_trading_profits + pnl.interest_income + adjustments.chargeable_gains
    donations = min(adjustments.qualifying_donations, before_deductions)
    chargeable = before_deductions - donations
    boxes = [
        _box(145, "Total turnover from trade", pnl.turnover),
        _box(155, "Trading profits", trading_profits),
        _box(160, "Trading losses brought forward set against trading profits", losses_used),
        _box(165, "Net trading profits", net_trading_profits),
        _box(
            170,
            "Bank, building society or other interest, and profits from non-trading "
            "loan relationships",
            pnl.interest_income,
        ),
        _box(210, "Chargeable gains", adjustments.chargeable_gains),
        _box(235, "Profits before other deductions and reliefs", before_deductions),
        _box(300, "Profits before qualifying donations and group relief", before_deductions),
        _box(305, "Qualifying donations", donations),
        _box(315, "Profits chargeable to Corporation Tax", chargeable),
    ]
    return _ProfitPosition(
        boxes=boxes,
        chargeable=chargeable,
        losses_used=losses_used,
        trading_loss_arising=max(-trading_result, 0),
    )


_FINANCIAL_YEAR_BOXES = ((330, 335, 340, 345), (380, 385, 390, 395))


def _tax_boxes(tax: TaxComputation) -> list[CT600Box]:
    """Compute boxes 326 to 525 from the tax computation."""
    claims_relief = any(s.band in {"small", "marginal"} for s in tax.slices)
    boxes = [
        _box(
            326, "Number of associated companies in this period", tax.associated_companies, "count"
        ),
        _box(329, "Small profits rate or marginal relief entitlement", int(claims_relief), "flag"),
    ]
    for (year_box, profit_box, rate_box, tax_box), part in zip(
        _FINANCIAL_YEAR_BOXES, tax.slices, strict=False
    ):
        boxes += [
            _box(year_box, "Financial year", part.financial_year, "year"),
            _box(profit_box, "Amount of profit", part.profits),
            _box(rate_box, "Rate of tax", part.rate * 100, "rate"),
            _box(tax_box, "Tax", part.tax, "money"),
        ]
    boxes += [
        _box(430, "Corporation Tax", tax.tax_before_relief, "money"),
        _box(435, "Marginal relief", tax.marginal_relief, "money"),
        _box(440, "Corporation Tax chargeable", tax.tax_chargeable, "money"),
        _box(475, "Net Corporation Tax liability", tax.tax_chargeable, "money"),
        _box(510, "Tax payable", tax.tax_chargeable, "money"),
        _box(525, "Self-assessment of tax payable", tax.tax_chargeable, "money"),
    ]
    return boxes


def _accounts(ct600: CT600Return, corporation_tax: Decimal) -> AccountsSummary:
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


def compute_return(ct600: CT600Return) -> ReturnComputation:
    """Compute the CT600 boxes, Corporation Tax and accounts for a return.

    Args:
        ct600: A validated return.

    Returns:
        The computed return.
    """
    position = _profit_boxes(ct600)
    adjustments = ct600.tax_adjustments
    tax = compute_corporation_tax(
        ct600.period.start,
        ct600.period.end,
        taxable_profits=position.chargeable,
        associated_companies=adjustments.associated_companies,
        exempt_distributions=adjustments.exempt_distributions,
    )
    return ReturnComputation(
        boxes=(*position.boxes, *_tax_boxes(tax)),
        tax=tax,
        accounts=_accounts(ct600, tax.tax_chargeable),
        trading_loss_arising=position.trading_loss_arising,
        losses_carried_forward=(
            adjustments.losses_brought_forward
            - position.losses_used
            + position.trading_loss_arising
        ),
        pages={str(code): tree for code, tree in ct600.supplementary_pages.items()},
    )
