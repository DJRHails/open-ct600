"""People's names as Companies House writes them, in the order people write them."""

import re

_SURNAME_FIRST = re.compile(
    r"""(?x)
    ^ \s* (?P<surname> [^,]+? ) \s* , \s* (?P<forenames> .+? ) \s* $   # "SURNAME, Forenames"
    """
)


def person_name(companies_house_name: str) -> str:
    """Turn ``"LOVELACE, Ada Augusta"`` into ``"Ada Augusta Lovelace"``.

    Companies House gives officers' names surname first, the surname in capitals
    (``"O'BRIEN"`` becomes ``"O'Brien"``). Only that form is reordered: names typed into
    filed accounts come in every order (``"Mr M Thompson"``, ``"Smith, Rev. John"``), so
    anything without a capitalised surname before a comma is returned as it is.
    """
    match = _SURNAME_FIRST.match(companies_house_name)
    if match is None or not match.group("surname").isupper():
        return " ".join(companies_house_name.split())
    surname = match.group("surname").title()
    return " ".join(f"{match.group('forenames')} {surname}".split())
