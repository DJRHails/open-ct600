"""Which return to suggest from a company's record, and which filed accounts come before it.

A Company Tax Return is for a period that has ended, and the comparatives in its accounts are
the accounts for the period of account before it, which end the day before it starts.
Companies House's profile gives the accounts it has (``last_accounts``) and the period it
expects accounts for next (``next_accounts``), both already following any change of
accounting reference date. Its filing history gives each accounts filing's made-up date.

The cases, on ``today``:

- **Accounts due, not yet filed.** ``next_accounts`` has ended: the return is for that period.
  When accounts are overdue for several periods, ``next_accounts`` is the earliest of them,
  which is also the earliest return to catch up on. Comparatives are the accounts made up to
  the day before it starts, usually the latest filed.
- **Accounts filed, next period not yet ended.** This is the usual order, as the Companies
  House deadline (9 months) comes before HMRC's (12 months). The return is for the period the
  filed accounts cover, never the one still running, and the comparatives are the accounts
  filed before those.
- **First period, from incorporation.** It can run for up to 18 months. There are no earlier
  accounts, so no comparatives. While it is still running, there is nothing to suggest.
- **Change of accounting reference date.** A period can be shortened, or extended to up to 18
  months. A period over 12 months is cut at 12, since a return covers at most 12 months, and
  the note says the rest needs a second return. Comparatives are found by made-up date, so
  they follow the change too.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel

from open_ct600.companies_house.filed_accounts import Period
from open_ct600.tax import twelve_month_period_end

logger = logging.getLogger(__name__)


class SuggestedPeriod(BaseModel):
    """The return period to start from; ``note`` explains a shortened one."""

    start: date
    end: date
    note: str | None


@dataclass(frozen=True)
class AccountsFiling:
    """An accounts (``AA``) filing in the company's filing history.

    Attributes:
        made_up_to: The last day of the period the accounts are for.
        filed_on: When Companies House processed the filing.
        item: The filing history item.
    """

    made_up_to: date
    filed_on: date
    item: dict[str, Any]


def accounts_filings(filing_history: dict[str, Any]) -> list[AccountsFiling]:
    """The accounts filings, newest first; items without usable dates are skipped and logged."""
    filings = []
    for item in filing_history.get("items") or []:
        if not isinstance(item, dict) or item.get("type") != "AA":
            continue
        values = item.get("description_values")
        made_up_to = day_or_none(values.get("made_up_date") if isinstance(values, dict) else None)
        filed_on = day_or_none(item.get("date"))
        if made_up_to is None or filed_on is None:
            logger.warning(
                "Skipped accounts filing %r without a made-up or filing date",
                item.get("transaction_id"),
            )
            continue
        filings.append(AccountsFiling(made_up_to=made_up_to, filed_on=filed_on, item=item))
    return sorted(filings, key=lambda filing: filing.made_up_to, reverse=True)


def last_period(
    last_accounts: dict[str, Any], filings: list[AccountsFiling], incorporated_on: date | None
) -> Period | None:
    """The period of the latest accounts Companies House has.

    Companies House doesn't always give its start (older records have only ``made_up_to``).
    It then starts the day after the accounts before it were made up to or, with none, on
    incorporation.
    """
    end = day_or_none(last_accounts.get("period_end_on") or last_accounts.get("made_up_to"))
    if end is None:
        return None
    start = day_or_none(last_accounts.get("period_start_on"))
    if start is None:
        earlier = next((filing for filing in filings if filing.made_up_to < end), None)
        start = earlier.made_up_to + timedelta(days=1) if earlier else incorporated_on
    return Period(start=start, end=end) if start is not None and start <= end else None


def suggested_period(
    next_period: Period | None, last: Period | None, today: date
) -> SuggestedPeriod | None:
    """The period of account a return is due for, cut to 12 months; see the module docstring."""
    if next_period is not None and next_period.end < today:
        return _within_twelve_months(next_period)
    if last is not None and last.end < today:
        return _within_twelve_months(last)
    return None


def filing_before(filings: list[AccountsFiling], period_start: date) -> AccountsFiling | None:
    """The accounts made up to the day before ``period_start``: the period's comparatives."""
    day_before = period_start - timedelta(days=1)
    return next((filing for filing in filings if filing.made_up_to == day_before), None)


def _within_twelve_months(period: Period) -> SuggestedPeriod:
    """The period, cut to the 12 months a Corporation Tax period can cover."""
    twelve_months = twelve_month_period_end(period.start)
    if period.end <= twelve_months:
        return SuggestedPeriod(start=period.start, end=period.end, note=None)
    note = (
        f"The company's period of account runs from {day_text(period.start)} to "
        f"{day_text(period.end)}, which is longer than 12 months. A Company Tax Return covers "
        f"at most 12 months, so this one ends on {day_text(twelve_months)}; the rest of the "
        "period needs a second return."
    )
    return SuggestedPeriod(start=period.start, end=twelve_months, note=note)


def day_text(day: date) -> str:
    """A date as people write it, like "1 April 2025"."""
    return f"{day.day} {day:%B %Y}"


def day_or_none(value: Any) -> date | None:
    """An ISO date from Companies House, or ``None`` if it is missing or malformed."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
