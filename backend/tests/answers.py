"""Answers for tests of the reliefs and supplementary pages: a trading company's return."""

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from open_ct600.ct600 import CT600Return, ReturnComputation, compute_return

RD_FORMS = {"claimed_in_previous_three_years": True, "additional_information_submitted": True}
PAYE_REFERENCE = [{"HMRCofficeNumber": "123", "EmployerPAYEreference": "AB12345"}]
CREATIVES_FORM = {"creative_industries": {"additional_information_submitted": True}}
# The account HMRC pays money due back into (boxes 920 to 940): needed whenever a return shows a
# repayment or payable credit. Synthetic: sort code 00-00-00 is no real branch.
BANK_DETAILS = {
    "bank_name": "Synthetic Bank plc",
    "sort_code": "00-00-00",
    "account_number": "00000000",
    "account_name": "Acme Widgets Ltd",
}


def answers(**overrides) -> dict:
    """A company with £100,000 turnover and no expenses, for 1 April 2024 to 31 March 2025.

    Each keyword replaces (dicts: updates) one top-level section.
    """
    base: dict = {
        "company": {
            "name": "Acme Widgets Ltd",
            "registration_number": "01234567",
            "utr": "1234567890",
            "principal_activity": "Manufacture of widgets",
        },
        "period": {"start": "2024-04-01", "end": "2025-03-31"},
        "profit_and_loss": {"turnover": 100_000},
        "tax_adjustments": {},
        "balance_sheet": {"current_assets": 20_000},
        "accounts": {
            "standard": "micro",
            "approval_date": "2025-06-30",
            "directors": ["Ada Lovelace"],
            "signing_director": "Ada Lovelace",
            "average_employees": 1,
            "trading_status": "trading",
        },
    }
    for section, values in overrides.items():
        current = base.get(section)
        base[section] = {**current, **values} if isinstance(current, dict) else values
    return base


def make_return(**overrides) -> CT600Return:
    """A validated return (see ``answers``)."""
    return CT600Return.model_validate(answers(**overrides))


def compute(**overrides) -> ReturnComputation:
    """The computation of ``make_return(**overrides)``."""
    return compute_return(make_return(**overrides))


def boxes(computation: ReturnComputation) -> dict[str, Decimal]:
    """Main-return boxes by id."""
    return {box.box: box.value for box in computation.boxes}


def problems(**overrides) -> dict[tuple, str]:
    """The problems a return has, by location (without the pydantic prefix)."""
    with pytest.raises(ValidationError) as caught:
        make_return(**overrides)
    return {error["loc"]: error["msg"] for error in caught.value.errors()}


def period(start: str, end: str, approved: str) -> dict:
    """Overrides for a different accounting period."""
    return {"period": {"start": start, "end": end}, "accounts": {"approval_date": approved}}


def page_of(computation: ReturnComputation, code: str) -> Any:
    """A completed page tree, untyped for indexing in assertions."""
    return computation.pages[code]
