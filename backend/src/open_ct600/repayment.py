"""The account HMRC pays money due back into: CT600 boxes 920 to 940.

HMRC pays repayments and payable credits (boxes 865 to 895) by direct credit into the account
on the return. The Company Tax Return guide says payable R&D and creative credits need these
details ("you need to enter account details if you are claiming payable research and
development [or] creative industries credit"), and that a repayment of £100 or less is held
against later periods without them; HMRC's schema and business rules never require them. So
the computation asks for them whenever the return shows money due back
(``computation._repayment_claim``).

The lengths and characters allowed come from the schema spec (``BankAccountDetails`` in
CT-2014-v1-994.xsd), so a value accepted here is one HMRC's schema accepts. The messages follow
the GOV.UK bank details pattern.
"""

import re
from functools import cache

from pydantic import field_validator

from open_ct600.model import StrictModel
from open_ct600.schema.spec import RETURN_PATH, SpecNode, load_spec

BANK_ACCOUNT_DETAILS = f"{RETURN_PATH}/OverpaymentsAndRepayments/BankAccountDetails"

_ALLOWED_CHARACTERS = (
    "letters a to z, numbers, spaces and these characters: "
    ", . ( ) / & ' - \" ! % * _ + : @ < > ? = ;"
)
"""What the schema's ``CT_CTstringType`` lets text contain, as a user would read it."""

_SEPARATORS = re.compile(
    r"""(?x)   # verbose
    [\s\-\u2013]  # spaces, hyphens and en dashes people write sort codes and account numbers with
    """
)
_DIGITS = re.compile(
    r"""(?x)   # verbose
    [0-9]+     # digits only
    """
)


@cache
def _node(name: str) -> SpecNode:
    return load_spec().node(f"{BANK_ACCOUNT_DETAILS}/{name}")


def _text_problem(value: str, element: str, label: str) -> str | None:
    """Why ``value`` does not fit the schema's text element ``element``, if it does not."""
    node = _node(element)
    if node.min_length is not None and len(value) < node.min_length:
        return f"{label} must be {node.min_length} characters or more"
    if node.max_length is not None and len(value) > node.max_length:
        return f"{label} must be {node.max_length} characters or fewer"
    if any(re.fullmatch(pattern, value, re.ASCII) is None for pattern in node.patterns):
        return f"{label} must only include {_ALLOWED_CHARACTERS}"
    return None


def _check_text(value: str, element: str, label: str, missing: str) -> str:
    if not value:
        raise ValueError(missing)
    problem = _text_problem(value, element, label)
    if problem:
        raise ValueError(problem)
    return value


def _check_digits(value: str, element: str, messages: tuple[str, str, str]) -> str:
    """A sort code or account number, without the spaces and hyphens people write it with."""
    missing, invalid, wrong_length = messages
    digits = _SEPARATORS.sub("", value)
    if not digits:
        raise ValueError(missing)
    if not _DIGITS.fullmatch(digits):
        raise ValueError(invalid)
    node = _node(element)
    if len(digits) != node.min_length or _text_problem(digits, element, element):
        raise ValueError(wrong_length)
    return digits


class BankDetails(StrictModel):
    """The account a repayment or payable credit is paid into.

    Attributes:
        bank_name: Box 920, the name of the bank or building society.
        sort_code: Box 925, 6 digits (``"12-34-56"`` is read as ``"123456"``).
        account_number: Box 930, 8 digits.
        account_name: Box 935, the name on the account.
        building_society_reference: Box 940, a building society roll number, if the account
            has one.
    """

    bank_name: str
    sort_code: str
    account_number: str
    account_name: str
    building_society_reference: str | None = None

    @field_validator("bank_name")
    @classmethod
    def _check_bank_name(cls, value: str) -> str:
        return _check_text(
            value,
            "BankName",
            "Name of the bank or building society",
            "Enter the name of the bank or building society",
        )

    @field_validator("sort_code")
    @classmethod
    def _check_sort_code(cls, value: str) -> str:
        return _check_digits(
            value,
            "SortCode",
            (
                "Enter a sort code",
                "Enter a valid sort code like 309430",
                "Sort code must be 6 digits long",
            ),
        )

    @field_validator("account_number")
    @classmethod
    def _check_account_number(cls, value: str) -> str:
        return _check_digits(
            value,
            "AccountNumber",
            (
                "Enter an account number",
                "Enter a valid account number like 00733445",
                "Account number must be 8 digits long. If yours is 6 or 7 digits, add zeros to "
                "the start",
            ),
        )

    @field_validator("account_name")
    @classmethod
    def _check_account_name(cls, value: str) -> str:
        return _check_text(
            value, "AccountName", "Name on the account", "Enter the name on the account"
        )

    @field_validator("building_society_reference")
    @classmethod
    def _check_building_society_reference(cls, value: str | None) -> str | None:
        if not value:
            return None
        problem = _text_problem(value, "BuildingSocReference", "Building society roll number")
        if problem:
            raise ValueError(problem)
        return value
