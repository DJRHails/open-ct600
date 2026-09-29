"""CT600 return: the answers a company gives, and computing the return from them.

The main return models a UK company preparing micro-entity or small company accounts, with
trading profits, bank interest, chargeable gains, trading losses brought forward and
qualifying charitable donations. Supplementary pages (CT600A to CT600P) are element trees
validated against HMRC's schema (see ``open_ct600.schema``), leaving out the boxes the service
calculates (``open_ct600.pages.definitions``). Reliefs claimed through the pages take a few
answers the pages have no box for: the R&D claim, figures from group relief surrendering
companies, the dates of loans to participators and the creatives additional information form.

A return is computed (``open_ct600.computation``) as part of validating it, so problems that
only the computation finds (a group relief claim larger than the profits, an R&D claim without
its additional information form) are reported like any other invalid answer.
"""

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    Field,
    JsonValue,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from open_ct600.computation import (
    AccountsSummary,
    CT600Box,
    ReliefsSummary,
    ReturnComputation,
    evaluate,
)
from open_ct600.model import MAX_POUNDS, Pounds, StrictModel
from open_ct600.pages.definitions import computed_paths
from open_ct600.problems import InvalidReturnError, Problem
from open_ct600.reliefs.group_relief import SurrenderingCompany
from open_ct600.reliefs.loans_to_participators import ParticipatorLoanDates
from open_ct600.reliefs.research_and_development import ResearchAndDevelopment
from open_ct600.schema.spec import PageCode, load_spec
from open_ct600.schema.trees import validate_tree
from open_ct600.tax import PeriodError, twelve_month_period_end, validate_period

__all__ = [
    "MAX_POUNDS",
    "AccountsDetails",
    "AccountsSummary",
    "BalanceSheet",
    "CT600Box",
    "CT600Return",
    "CompanyDetails",
    "CreativeIndustries",
    "Declaration",
    "Pounds",
    "ProfitAndLoss",
    "ReliefsSummary",
    "ReturnComputation",
    "ReturnPeriod",
    "SignatoryCapacity",
    "Submission",
    "TaxAdjustments",
    "compute_return",
]

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


class CompanyDetails(StrictModel):
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


class ReturnPeriod(StrictModel):
    """The accounting period the return covers, which is also the accounts' period of account.

    The service prepares the statutory accounts for this same period, so it cannot file for a
    period of account longer than 12 months: HMRC needs two returns for it, each with the
    accounts for the whole period of account (review finding L4).
    """

    start: date
    end: date

    @model_validator(mode="after")
    def _check_period(self) -> Self:
        if self.end > twelve_month_period_end(self.start):
            raise ValueError(
                "The period cannot be longer than 12 months. This service prepares the accounts "
                "for the same period as the return, so it cannot prepare a return for a period "
                "of account longer than 12 months: that needs two returns, each with the "
                "accounts for the whole period of account"
            )
        try:
            validate_period(self.start, self.end)
        except PeriodError as error:
            raise ValueError(str(error)) from error
        return self


class ProfitAndLoss(StrictModel):
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


class TaxAdjustments(StrictModel):
    """Adjustments that turn accounting profit into taxable profit.

    Attributes:
        losses_brought_forward_before_april_2017: The part of ``losses_brought_forward`` that
            arose before 1 April 2017. Those losses only relieve profits of the same trade
            (CTA 2010 s45); later ones can also relieve total profits (s45A), so they come
            before any group relief for carried-forward losses (CTM82010).
    """

    disallowable_expenses: Pounds = 0
    capital_allowances: Pounds = 0
    losses_brought_forward: Pounds = 0
    losses_brought_forward_before_april_2017: Pounds = 0
    chargeable_gains: Pounds = 0
    qualifying_donations: Pounds = 0
    exempt_distributions: Pounds = 0
    associated_companies: Annotated[int, Field(ge=0, le=999)] = 0

    @model_validator(mode="after")
    def _check_older_losses_are_part_of_the_total(self) -> Self:
        if self.losses_brought_forward_before_april_2017 > self.losses_brought_forward:
            raise _located_error(
                "Losses from before 1 April 2017 are part of the trading losses brought "
                "forward, so cannot be more than them",
                ("losses_brought_forward_before_april_2017",),
                self.losses_brought_forward_before_april_2017,
            )
        return self


class BalanceSheet(StrictModel):
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


class AccountsDetails(StrictModel):
    """Facts about the statutory accounts filed with the return.

    Attributes:
        standard: ``micro`` for FRS 105 micro-entity accounts, ``small`` for FRS 102
            section 1A small company accounts.
        approval_date: When the board approved the accounts; after the period ends.
        directors: Everyone who was a director during the period.
        signing_director: The director who signed the balance sheet; one of ``directors``.
        average_employees: Average number of employees (including directors) in the period.
        trading_status: Whether the company traded in the period, never has, or has stopped.
        dormant: Whether the company was dormant (had no significant accounting transactions)
            throughout the period, so files dormant accounts. A dormant company has no
            turnover, expenses, income or gains, does not trade, and has no tax to pay.
    """

    standard: Literal["micro", "small"]
    approval_date: date
    directors: Annotated[list[DirectorName], Field(min_length=1, max_length=50)]
    signing_director: DirectorName
    average_employees: Annotated[int, Field(ge=0, le=9_999_999)]
    trading_status: Literal["trading", "never_traded", "no_longer_trading"]
    dormant: bool = False

    @model_validator(mode="after")
    def _check_dormant_company_is_not_trading(self) -> Self:
        if self.dormant and self.trading_status == "trading":
            raise _located_error(
                "A dormant company cannot be trading: select whether it has never traded or "
                "has stopped trading, or say it was not dormant",
                ("trading_status",),
                self.trading_status,
            )
        return self

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


class CreativeIndustries(StrictModel):
    """Answers for creative industries claims (CT600P) that the page has no box for.

    Attributes:
        additional_information_submitted: Whether the creatives additional information form
            was submitted before the return (box 658); claims are invalid without it.
    """

    additional_information_submitted: bool


class CT600Return(StrictModel):
    """Everything needed to compute a company's CT600 return.

    Attributes:
        supplementary_pages: Supplementary pages by code (``"A"`` for CT600A), each an element
            tree for that page's root element (see ``open_ct600.schema.trees``), without the
            boxes the service calculates.
        research_and_development: The company's R&D claim (see CT600L), if any.
        group_relief_surrenderers: Figures from the returns of companies surrendering group
            relief to this one (CT600C), to limit each claim for non-coterminous periods and
            consortium shares; optional.
        participator_loan_dates: When the loans on CT600A were made, needed only when the s455
            rate changes during the period.
        creative_industries: Answers for CT600P claims.
    """

    company: CompanyDetails
    period: ReturnPeriod
    profit_and_loss: ProfitAndLoss
    tax_adjustments: TaxAdjustments
    balance_sheet: BalanceSheet
    accounts: AccountsDetails
    supplementary_pages: SupplementaryPages = Field(default_factory=dict)
    research_and_development: ResearchAndDevelopment | None = None
    group_relief_surrenderers: list[SurrenderingCompany] = Field(default_factory=list)
    participator_loan_dates: ParticipatorLoanDates | None = None
    creative_industries: CreativeIndustries | None = None

    @model_validator(mode="after")
    def _check_dormant_company_has_no_activity(self) -> Self:
        if not self.accounts.dormant:
            return self
        pnl, adjustments = self.profit_and_loss, self.tax_adjustments
        activity = {
            ("profit_and_loss", name): value for name, value in pnl.model_dump().items() if value
        }
        if adjustments.chargeable_gains:
            activity[("tax_adjustments", "chargeable_gains")] = adjustments.chargeable_gains
        details = [
            _answer_error(
                "A dormant company has no turnover, expenses, income or gains: enter 0, or say "
                "the company was not dormant",
                location,
                value,
            )
            for location, value in activity.items()
        ]
        if details:
            raise ValidationError.from_exception_data("CT600Return", details)
        return self

    @model_validator(mode="after")
    def _check_the_return_computes(self) -> Self:
        _, problems = evaluate(self)
        if problems:
            raise ValidationError.from_exception_data(
                "CT600Return", [self._problem_error(problem) for problem in problems]
            )
        return self

    def _problem_error(self, problem: Problem) -> InitErrorDetails:
        location = problem.location
        value: object = None
        if location[:1] == ("supplementary_pages",) and len(location) > 1:
            tree = self.supplementary_pages.get(str(location[1]))  # type: ignore[call-overload]
            value = _answer_at(tree, location[2:])
        return _answer_error(problem.message, location, value, problem.box)

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
                for problem in validate_tree(page.node, tree, computed_paths(code))
            ]
        if details:
            raise ValidationError.from_exception_data("SupplementaryPages", details)
        return pages


class SignatoryCapacity(StrEnum):
    """The capacity in which the person signs the declaration."""

    DIRECTOR = "director"
    COMPANY_SECRETARY = "company_secretary"
    AUTHORISED_AGENT = "authorised_agent"


class Declaration(StrictModel):
    """The statement the signatory makes when submitting the return."""

    name: Annotated[str, Field(min_length=1, max_length=120)]
    capacity: SignatoryCapacity
    confirmed: Literal[True]


class Submission(StrictModel):
    """A return and the declaration made when submitting it."""

    ct600: CT600Return
    declaration: Declaration


def compute_return(ct600: CT600Return) -> ReturnComputation:
    """Compute the CT600 boxes, supplementary pages, reliefs, tax and accounts for a return.

    Args:
        ct600: A validated return.

    Returns:
        The computed return.

    Raises:
        InvalidReturnError: If the return has problems; a validated return never does.
    """
    computation, problems = evaluate(ct600)
    if computation is None:
        raise InvalidReturnError(problems)
    return computation
