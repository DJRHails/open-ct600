"""A company's public record, shaped for prefilling a return.

The shapes are the contract in ``docs/design/companies-house-prefill.md``.
"""

import asyncio
import logging
import re
from collections.abc import Coroutine
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from open_ct600.companies_house.client import (
    CompaniesHouseClient,
    CompaniesHouseUnavailableError,
    CompanyNotFoundError,
)
from open_ct600.companies_house.filed_accounts import (
    AccountsNotReadableError,
    FiledAccounts,
    Period,
    read_filed_accounts,
)
from open_ct600.companies_house.names import person_name
from open_ct600.companies_house.periods import (
    AccountsFiling,
    SuggestedPeriod,
    accounts_filings,
    day_or_none,
    day_text,
    filing_before,
    last_period,
    suggested_period,
)
from open_ct600.companies_house.sic import sic_description
from open_ct600.ct600 import LegalForm

logger = logging.getLogger(__name__)

XHTML = "application/xhtml+xml"
MAX_SEARCH_RESULTS = 20

_CIC = "community-interest-company"
_LEGAL_FORMS: dict[str, LegalForm] = {
    "ltd": "private-limited-company",
    "private-limited-shares-section-30-exemption": "private-limited-company",
    "private-limited-guarant-nsc": "private-company-limited-by-guarantee",
    "private-limited-guarant-nsc-limited-exemption": "private-company-limited-by-guarantee",
    "private-unlimited": "private-unlimited-company",
    "private-unlimited-nsc": "private-unlimited-company",
    _CIC: _CIC,
}
"""Companies House company ``type`` → the model's ``LegalForm``. Other types (public limited
companies, LLPs, societies, overseas companies...) cannot prepare these accounts: ``None``."""

_DOCUMENT_ID = re.compile(
    r"""(?x)
    /document/ (?P<id> [A-Za-z0-9_-]{8,128} ) $   # the document id at the end of the link
    """
)

UNAVAILABLE_NO_ACCOUNTS = "Companies House has no accounts for this company yet."
UNAVAILABLE_NO_PERIOD = (
    "Companies House doesn't show a period of account that has ended, so there's no previous "
    "period to take figures from."
)
UNAVAILABLE_FIRST_PERIOD = (
    "This is the company's first period of account, so there are no previous figures."
)
UNAVAILABLE_PAPER = (
    "The previous period's accounts were filed on paper, so their figures can't be read."
)
UNAVAILABLE_PDF = (
    "The previous period's accounts were filed as a PDF, so their figures can't be read."
)
UNAVAILABLE_NOT_PUBLISHED = (
    "The previous period's accounts aren't available to download from Companies House yet."
)
UNAVAILABLE_FAILED = (
    "Companies House couldn't provide the previous period's accounts just now. Try again later."
)


class SearchResult(BaseModel):
    """One company found by a search."""

    number: str
    name: str
    status: str | None
    address: str | None
    incorporated_on: date | None


class SearchResults(BaseModel):
    """Companies matching a search, at most ``MAX_SEARCH_RESULTS``."""

    items: list[SearchResult]


class Address(BaseModel):
    """A postal address as lines and a postcode."""

    lines: list[str]
    postcode: str | None


class SicCode(BaseModel):
    """A nature-of-business code and Companies House's description of it."""

    code: str
    description: str | None


class Director(BaseModel):
    """A current director."""

    name: str
    appointed_on: date | None


class AccountsDates(BaseModel):
    """The company's accounting reference date and accounts periods.

    Attributes:
        reference_date: The accounting reference date as ``MM-DD``.
    """

    reference_date: str | None
    last_made_up_to: date | None
    next_period: Period | None


class PreviousAccounts(FiledAccounts):
    """The latest accounts filed at Companies House, and when they were filed."""

    filed_on: date


class CompanyRecord(BaseModel):
    """What Companies House says about a company, for prefilling its return."""

    number: str
    name: str
    status: str | None
    incorporated_on: date | None
    legal_form: LegalForm | None
    registered_office: Address | None
    sic_codes: list[SicCode]
    principal_activity: str | None
    directors: list[Director]
    accounts: AccountsDates
    suggested_period: SuggestedPeriod | None
    previous_accounts: PreviousAccounts | None
    previous_accounts_unavailable: str | None


async def search(client: CompaniesHouseClient, query: str) -> SearchResults:
    """Find companies by name or number; results without a company number are left out."""
    reply = await client.search(query, MAX_SEARCH_RESULTS)
    items = reply.get("items")
    return SearchResults(
        items=[
            SearchResult(
                number=item["company_number"],
                name=str(item.get("title") or ""),
                status=item.get("company_status"),
                address=item.get("address_snippet"),
                incorporated_on=day_or_none(item.get("date_of_creation")),
            )
            for item in (items if isinstance(items, list) else [])[:MAX_SEARCH_RESULTS]
            if isinstance(item, dict) and isinstance(item.get("company_number"), str)
        ]
    )


async def company_record(client: CompaniesHouseClient, number: str, today: date) -> CompanyRecord:
    """Assemble a company's record from its profile, officers and accounts filings.

    The suggested period is the return due on ``today`` and the previous accounts are the
    accounts for the period before it (see ``periods``). Only the profile is essential. If the
    officers can't be fetched (Companies House answers 404 for some companies without officer
    records), the record has no directors; if the accounts can't,
    ``previous_accounts_unavailable`` says why.

    Raises:
        CompanyNotFoundError: If Companies House has no such company.
        CompaniesHouseUnavailableError: If the profile cannot be fetched.
    """
    profile = await client.company(number)
    officers, history = await asyncio.gather(
        _safely(client.officers(number), "Company officers"),
        _safely(client.accounts_filings(number), "Previous accounts"),
    )
    profile_accounts = profile.get("accounts") or {}
    accounts = _accounts_dates(profile_accounts)
    incorporated_on = day_or_none(profile.get("date_of_creation"))
    filings = None if history is None else accounts_filings(history)
    last = last_period(profile_accounts.get("last_accounts") or {}, filings or [], incorporated_on)
    suggested = suggested_period(accounts.next_period, last, today)
    previous, unavailable = await _previous_accounts(client, filings, suggested, incorporated_on)
    sic_codes = [
        SicCode(code=code, description=sic_description(code))
        for code in profile.get("sic_codes", [])
    ]
    return CompanyRecord(
        number=str(profile.get("company_number") or number),
        name=profile.get("company_name", ""),
        status=profile.get("company_status"),
        incorporated_on=incorporated_on,
        legal_form=_legal_form(profile),
        registered_office=_address(profile.get("registered_office_address")),
        sic_codes=sic_codes,
        principal_activity=sic_codes[0].description if sic_codes else None,
        directors=_current_directors(officers or {}),
        accounts=accounts,
        suggested_period=suggested,
        previous_accounts=previous,
        previous_accounts_unavailable=unavailable,
    )


def _legal_form(profile: dict[str, Any]) -> LegalForm | None:
    """The model's legal form; a CIC (by type, subtype or flag) of a supported form is a CIC."""
    form = _LEGAL_FORMS.get(profile.get("type", ""))
    is_cic = profile.get("subtype") == _CIC or profile.get("is_community_interest_company")
    return "community-interest-company" if form is not None and is_cic else form


def _address(address: dict[str, str] | None) -> Address | None:
    if not address:
        return None
    first = " ".join(
        part for part in (address.get("premises"), address.get("address_line_1")) if part
    )
    candidates = [
        f"c/o {address['care_of']}" if address.get("care_of") else None,
        f"PO Box {address['po_box']}" if address.get("po_box") else None,
        first,
        address.get("address_line_2"),
        address.get("locality"),
        address.get("region"),
    ]
    return Address(
        lines=[line.strip() for line in candidates if line and line.strip()],
        postcode=address.get("postal_code"),
    )


def _current_directors(officers: dict[str, Any]) -> list[Director]:
    """Directors who have not resigned, in Companies House's order (corporate ones excluded)."""
    return [
        Director(name=person_name(officer["name"]), appointed_on=officer.get("appointed_on"))
        for officer in officers.get("items", [])
        if officer.get("officer_role") == "director" and not officer.get("resigned_on")
    ]


def _accounts_dates(accounts: dict[str, Any]) -> AccountsDates:
    """The profile's accounts dates; any that are missing or malformed are left out."""
    next_accounts = accounts.get("next_accounts") or {}
    start = day_or_none(next_accounts.get("period_start_on"))
    end = day_or_none(next_accounts.get("period_end_on"))
    return AccountsDates(
        reference_date=_reference_date(accounts.get("accounting_reference_date")),
        last_made_up_to=day_or_none((accounts.get("last_accounts") or {}).get("made_up_to")),
        next_period=Period(start=start, end=end) if start and end and start <= end else None,
    )


def _reference_date(reference: Any) -> str | None:
    """The accounting reference date as ``MM-DD``, if Companies House gives a real one."""
    if not isinstance(reference, dict):
        return None
    try:
        day = date(2000, int(reference["month"]), int(reference["day"]))  # a leap year
    except (KeyError, TypeError, ValueError):
        return None
    return f"{day:%m-%d}"


async def _previous_accounts(
    client: CompaniesHouseClient,
    filings: list[AccountsFiling] | None,
    period: SuggestedPeriod | None,
    incorporated_on: date | None,
) -> tuple[PreviousAccounts | None, str | None]:
    """The figures of the accounts for the period before ``period``, or why there are none.

    ``filings`` is ``None`` if the filing history couldn't be fetched.
    """
    if filings is None:
        return None, UNAVAILABLE_FAILED
    if period is None:
        return None, UNAVAILABLE_NO_PERIOD if filings else UNAVAILABLE_NO_ACCOUNTS
    filing = filing_before(filings, period.start)
    if filing is None:
        return None, _no_comparatives(filings, period.start, incorporated_on)
    if filing.item.get("paper_filed"):
        return None, UNAVAILABLE_PAPER
    document_id = _document_id(filing)
    if document_id is None:
        return None, UNAVAILABLE_NOT_PUBLISHED
    return await _read_document(client, document_id, filing)


def _no_comparatives(
    filings: list[AccountsFiling], period_start: date, incorporated_on: date | None
) -> str:
    """Why no accounts are made up to the day before the period starts."""
    if period_start == incorporated_on:
        return UNAVAILABLE_FIRST_PERIOD
    if not filings:
        return UNAVAILABLE_NO_ACCOUNTS
    day_before = day_text(period_start - timedelta(days=1))
    return (
        f"Companies House has no accounts made up to {day_before}, the day before this period "
        "starts."
    )


def _document_id(filing: AccountsFiling) -> str | None:
    """The Document API id from the filing's ``document_metadata`` link, if it has one."""
    links = filing.item.get("links")
    link = links.get("document_metadata") if isinstance(links, dict) else None
    match = _DOCUMENT_ID.search(link) if isinstance(link, str) else None
    return match.group("id") if match else None


async def _read_document(
    client: CompaniesHouseClient, document_id: str, filing: AccountsFiling
) -> tuple[PreviousAccounts | None, str | None]:
    metadata = await _safely(client.document_metadata(document_id), "Previous accounts")
    if metadata is None:
        return None, UNAVAILABLE_FAILED
    if XHTML not in (metadata.get("resources") or {}):
        return None, UNAVAILABLE_PDF
    content = await _safely(client.document_content(document_id, XHTML), "Previous accounts")
    if content is None:
        return None, UNAVAILABLE_FAILED
    try:
        filed = await run_in_threadpool(read_filed_accounts, content)
    except AccountsNotReadableError as error:
        logger.warning("Previous accounts %s unreadable: %s", document_id, error)
        return None, f"The previous period's accounts couldn't be read: {error}."
    if filed.period.end != filing.made_up_to:
        return None, (
            f"The previous period's accounts give their period as {day_text(filed.period.start)} "
            f"to {day_text(filed.period.end)}, but Companies House has them made up to "
            f"{day_text(filing.made_up_to)}, so their figures can't be used."
        )
    return PreviousAccounts(**filed.model_dump(), filed_on=filing.filed_on), None


async def _safely[T](request: Coroutine[Any, Any, T], part: str) -> T | None:
    """The request's result, or ``None`` if Companies House could not provide it.

    Everything but the profile is extra: a failure (even a 404) fetching ``part`` leaves the
    rest of the record usable, and is logged (the error names the path and status, never the
    key).
    """
    try:
        return await request
    except (CompaniesHouseUnavailableError, CompanyNotFoundError) as error:
        logger.warning("%s unavailable: %s", part, error)
        return None
