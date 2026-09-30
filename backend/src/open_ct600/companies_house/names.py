"""People's names as Companies House writes them, in the order people write them."""

import re

_SURNAME_FIRST = re.compile(
    r"""(?x)
    ^ \s* (?P<surname> [^,]+? ) \s*       # "SURNAME"
    , \s* (?P<forenames> [^,]+? ) \s*     # ", Forenames"
    (?: , (?P<title> .+? ) )? \s* $       # optionally ", Title" (and honours), as on the register
    """
)
_HONOURS = re.compile(
    r"""(?x)
    ^ (?! (?: MR | MRS | MS | MISS | MX | DR | SIR | DAME | LORD | LADY | REV | PROF ) $ )
                                          # (not a title typed in capitals)
      (?: [A-Z]{2,6}                      # post-nominal letters: OBE, KC, FRS, FRCP...
        | PhD | DPhil | FREng | FRSE      # and the usual mixed-case ones
      ) $
    """
)
_MC = re.compile(
    r"""(?x)
    \b Mc (?P<next> [a-z] )               # "Mcdonald" as str.title() writes "MCDONALD"
    """
)


def person_name(companies_house_name: str) -> str:
    """Turn ``"LOVELACE, Ada Augusta"`` into ``"Ada Augusta Lovelace"``.

    Companies House gives officers' names as ``SURNAME, Forenames``, the surname in capitals
    (``"O'BRIEN"`` becomes ``"O'Brien"``, ``"MCDONALD"`` ``"McDonald"``), with any title after
    a further comma: ``"DYSON, James, Sir"`` is ``"Sir James Dyson"``. In the title, honours
    (post-nominal letters, like ``OBE``) go after the surname: ``"HOPPER, Grace, Dr, OBE"`` is
    ``"Dr Grace Hopper OBE"``.

    Only that form is reordered: names typed into filed accounts come in every order
    (``"Mr M Thompson"``, ``"Smith, Rev. John"``), so anything without a capitalised surname
    before a comma is returned as it is.
    """
    match = _SURNAME_FIRST.match(companies_house_name)
    if match is None or not match.group("surname").isupper():
        return " ".join(companies_house_name.split())
    surname = _MC.sub(lambda mc: f"Mc{mc.group('next').upper()}", match.group("surname").title())
    words = (match.group("title") or "").replace(",", " ").split()
    titles = [word for word in words if not _HONOURS.match(word)]
    honours = [word for word in words if _HONOURS.match(word)]
    return " ".join([*titles, *match.group("forenames").split(), *surname.split(), *honours])
