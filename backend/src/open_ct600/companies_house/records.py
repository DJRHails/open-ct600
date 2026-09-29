"""A company's public record, shaped for prefilling a return.

The shapes are the contract in ``docs/design/companies-house-prefill.md``.
"""

import asyncio
import logging
import re
from collections.abc import Coroutine
from datetime import date
from typing import Any, Literal

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
from open_ct600.companies_house.sic import sic_description
from open_ct600.tax import twelve_month_period_end

logger = logging.getLogger(__name__)

XHTML = "application/xhtml+xml"
MAX_SEARCH_RESULTS = 20

LegalForm = Literal[
    "private-limited-company",
    "private-company-limited-by-guarantee",
    "private-unlimited-company",
    "community-interest-company",
    "public-limited-company",
    "limited-liability-partnership",
]
_LEGAL_FORMS: dict[str, LegalForm] = {
    "ltd": "private-limited-company",
    "private-limited-shares-section-30-exemption": "private-limited-company",
    "private-limited-guarant-nsc": "private-company-limited-by-guarantee",
    "private-limited-guarant-nsc-limited-exemption": "private-company-limited-by-guarantee",
    "private-unlimited": "private-unlimited-company",
    "private-unlimited-nsc": "private-unlimited-company",
    "plc": "public-limited-company",
    "llp": "limited-liability-partnership",
}
"""Companies House company ``type`` → legal form; other types (societies, overseas
companies, charitable incorporated organisations...) have none we support."""

_DOCUMENT_ID = re.compile(
    r"""(?x)
    /document/ (?P<id> [A-Za-z0-9_-]{8,128} ) $   # the document id at the end of the link
    """
)

UNAVAILABLE_NO_ACCOUNTS = "Companies House has no accounts for this company yet."
UNAVAILABLE_PAPER = "The latest accounts were filed on paper, so their figures can't be read."
UNAVAILABLE_PDF = "The latest accounts were filed as a PDF, so their figures can't be read."
UNAVAILABLE_NOT_PUBLISHED = (
    "The latest accounts aren't available to download from Companies House yet."
)
UNAVAILABLE_FAILED = (
    "Companies House couldn't provide the latest accounts just now. Try again later."
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


class SuggestedPeriod(BaseModel):
    """The return period to start from; ``note`` explains a shortened one."""

    start: date
    end: date
    note: str | None


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
    """Find companies by name or number."""
    reply = await client.search(query, MAX_SEARCH_RESULTS)
    return SearchResults(
        items=[
            SearchResult(
                number=item["company_number"],
                name=item.get("title", ""),
                status=item.get("company_status"),
                address=item.get("address_snippet"),
                incorporated_on=item.get("date_of_creation"),
            )
            for item in reply.get("items", [])[:MAX_SEARCH_RESULTS]
        ]
    )


async def company_record(client: CompaniesHouseClient, number: str) -> CompanyRecord:
    """Assemble a company's record from its profile, officers and latest accounts.

    Raises:
        CompanyNotFoundError: If Companies House has no such company.
        CompaniesHouseUnavailableError: If the profile or officers cannot be fetched.
    """
    profile = await client.company(number)
    officers, (previous, unavailable) = await asyncio.gather(
        client.officers(number), _previous_accounts(client, number)
    )
    sic_codes = [
        SicCode(code=code, description=sic_description(code))
        for code in profile.get("sic_codes", [])
    ]
    accounts = _accounts_dates(profile.get("accounts") or {})
    return CompanyRecord(
        number=profile["company_number"],
        name=profile.get("company_name", ""),
        status=profile.get("company_status"),
        incorporated_on=profile.get("date_of_creation"),
        legal_form=_legal_form(profile),
        registered_office=_address(profile.get("registered_office_address")),
        sic_codes=sic_codes,
        principal_activity=sic_codes[0].description if sic_codes else None,
        directors=_current_directors(officers),
        accounts=accounts,
        suggested_period=_suggested_period(accounts.next_period),
        previous_accounts=previous,
        previous_accounts_unavailable=unavailable,
    )


def _legal_form(profile: dict[str, Any]) -> LegalForm | None:
    form = _LEGAL_FORMS.get(profile.get("type", ""))
    is_cic = profile.get("subtype") == "community-interest-company" or profile.get(
        "is_community_interest_company"
    )
    return "community-interest-company" if form == "private-limited-company" and is_cic else form


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
    reference = accounts.get("accounting_reference_date") or {}
    reference_date = (
        f"{int(reference['month']):02d}-{int(reference['day']):02d}"
        if reference.get("day") and reference.get("month")
        else None
    )
    next_accounts = accounts.get("next_accounts") or {}
    start, end = next_accounts.get("period_start_on"), next_accounts.get("period_end_on")
    return AccountsDates(
        reference_date=reference_date,
        last_made_up_to=(accounts.get("last_accounts") or {}).get("made_up_to"),
        next_period=Period(start=start, end=end) if start and end else None,
    )


def _suggested_period(next_period: Period | None) -> SuggestedPeriod | None:
    """The next period of account, cut to the 12 months a Corporation Tax period can cover."""
    if next_period is None:
        return None
    twelve_months = twelve_month_period_end(next_period.start)
    if next_period.end <= twelve_months:
        return SuggestedPeriod(start=next_period.start, end=next_period.end, note=None)
    note = (
        f"The company's period of account runs from {_day(next_period.start)} to "
        f"{_day(next_period.end)}, which is longer than 12 months. A Company Tax Return covers "
        f"at most 12 months, so this one ends on {_day(twelve_months)}; the rest of the period "
        "needs a second return."
    )
    return SuggestedPeriod(start=next_period.start, end=twelve_months, note=note)


def _day(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


async def _previous_accounts(
    client: CompaniesHouseClient, number: str
) -> tuple[PreviousAccounts | None, str | None]:
    """The latest filed accounts' figures, or why there are none."""
    filings = await _safely(client.accounts_filings(number))
    if filings is None:
        return None, UNAVAILABLE_FAILED
    latest = next((item for item in filings.get("items", []) if item.get("type") == "AA"), None)
    if latest is None:
        return None, UNAVAILABLE_NO_ACCOUNTS
    if latest.get("paper_filed"):
        return None, UNAVAILABLE_PAPER
    match = _DOCUMENT_ID.search((latest.get("links") or {}).get("document_metadata", ""))
    if match is None:
        return None, UNAVAILABLE_NOT_PUBLISHED
    return await _read_document(client, match.group("id"), filed_on=latest["date"])


async def _read_document(
    client: CompaniesHouseClient, document_id: str, *, filed_on: str
) -> tuple[PreviousAccounts | None, str | None]:
    metadata = await _safely(client.document_metadata(document_id))
    if metadata is None:
        return None, UNAVAILABLE_FAILED
    if XHTML not in (metadata.get("resources") or {}):
        return None, UNAVAILABLE_PDF
    content = await _safely(client.document_content(document_id, XHTML))
    if content is None:
        return None, UNAVAILABLE_FAILED
    try:
        filed = await run_in_threadpool(read_filed_accounts, content)
    except AccountsNotReadableError as error:
        return None, f"The latest accounts couldn't be read: {error}."
    return PreviousAccounts(**filed.model_dump(), filed_on=date.fromisoformat(filed_on)), None


async def _safely[T](request: Coroutine[Any, Any, T]) -> T | None:
    """The request's result, or ``None`` if Companies House could not provide it.

    Previous accounts are extra: a failure there leaves the rest of the record usable, is
    logged, and is reported as ``previous_accounts_unavailable``.
    """
    try:
        return await request
    except (CompaniesHouseUnavailableError, CompanyNotFoundError) as error:
        logger.warning("Previous accounts unavailable: %s", error)
        return None
