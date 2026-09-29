"""Check a user's answers for one part of the CT600 against the schema spec.

Answers arrive as an *element tree*: JSON mirroring the XML, with element names as keys,
repeating elements as lists, attributes as ``"@Name"`` keys and every value as a string
(money ``"1234.56"``, whole pounds ``"1234"``, dates ``"2025-03-31"``, a tick ``"yes"``).
For example, a CT600A page::

    {"BeforeEndPeriod": "yes",
     "LoansInformation": {"Loan": [{"Name": "Ada Lovelace", "AmountOfLoan": "5000"}], ...}}

This validates user input only. The generated XML is checked separately against HMRC's XSD
and schematron, which also enforce cross-box rules this module does not attempt.
"""

import binascii
import re
from base64 import b64decode
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache

from open_ct600.schema.spec import ChoiceGroup, SpecNode

TreePath = tuple[str | int, ...]


@dataclass(frozen=True)
class TreeProblem:
    """Something wrong with an element tree.

    Attributes:
        path: Where in the tree, like ``("LoansInformation", "Loan", 0, "Name")``.
        box: The CT600 box id of the element, if it is a box.
        message: What to fix, in GOV.UK error message style.
    """

    path: TreePath
    box: str | None
    message: str


_POUNDS = re.compile(
    r"""(?x)
    ^[0-9]+$     # whole pounds: digits only
    """
)
_MONEY = re.compile(
    r"""(?x)
    ^-?                 # optional minus, where the element allows negatives
    [0-9]+              # pounds
    (?:\.[0-9]{1,2})?   # optional pence
    $
    """
)
_INTEGER = re.compile(
    r"""(?x)
    ^-?[0-9]+$   # optional minus and digits
    """
)
_DECIMAL = re.compile(
    r"""(?x)
    ^-?                 # optional minus
    [0-9]+              # whole part
    (?:\.[0-9]+)?       # optional fraction
    $
    """
)
_PERCENT = re.compile(
    r"""(?x)
    ^[0-9]+              # whole part
    (?:\.[0-9]{1,2})?    # up to two decimal places
    $
    """
)
_ISO_DATE = re.compile(
    r"""(?x)
    ^[0-9]{4}-[0-9]{2}-[0-9]{2}$   # YYYY-MM-DD
    """
)
_YEAR = re.compile(
    r"""(?x)
    ^[0-9]{4}$   # YYYY
    """
)
_CHARACTER_CLASS = re.compile(
    r"""(?x)
    ^\[ .* \] [*+]$   # a pattern that only restricts which characters may be used
    """
)


def validate_tree(
    node: SpecNode, tree: object, computed: frozenset[str] = frozenset()
) -> list[TreeProblem]:
    """Check an element tree for ``node`` (a group, such as a supplementary page root).

    Checks unknown keys, how many times each element occurs, that exactly one branch of each
    required choice is given (and never two), and every value against its kind, allowed
    values, pattern, length and bounds.

    Args:
        node: The spec node the tree is for.
        tree: The element tree (a dict of the node's children).
        computed: Schema paths of elements the service calculates. Answers must leave them
            out, and they are not required; see ``open_ct600.pages.definitions``.

    Returns:
        The problems found, in schema order; empty if the tree is valid.
    """
    return _group(node, tree, (), computed)


def _group(
    node: SpecNode, tree: object, path: TreePath, computed: frozenset[str]
) -> list[TreeProblem]:
    if not isinstance(tree, dict):
        return [TreeProblem(path, node.box, f"{_sentence(node.label)} must be a set of answers")]
    known = {child.name for child in node.children}
    problems = [
        TreeProblem((*path, key), None, f"Remove {key}: it is not part of {_phrase(node.label)}")
        for key in tree
        if key not in known
    ]
    chosen: set[str] = set()
    for group in node.choices:
        branches, problem = _choice(node, group, tree, path, computed)
        chosen |= branches
        problems += problem
    for child in node.children:
        child_path = (*path, child.name)
        if child.path in computed:
            if child.name in tree:
                problems.append(TreeProblem(child_path, child.box, _calculated(child)))
            continue
        if child.choice is not None and child.branch not in chosen:
            continue
        problems += _occurrences(child, tree.get(child.name), child_path, computed)
    return problems


def _calculated(node: SpecNode) -> str:
    box = f" (box {node.box})" if node.box else ""
    return f"Remove {_phrase(node.label)}{box}: it is calculated from your other answers"


def _choice(
    node: SpecNode, group: ChoiceGroup, tree: dict, path: TreePath, computed: frozenset[str]
) -> tuple[set[str], list[TreeProblem]]:
    members = [child for child in node.children if child.choice == group.id]
    if all(child.path in computed for child in members):
        return set(), []
    branches = {child.branch for child in members if child.name in tree and child.branch}
    heads = {child.branch: child for child in members if child.name == child.branch}
    options = " or ".join(_phrase(head.label) for head in heads.values())
    if len(branches) > 1:
        return branches, [TreeProblem(path, node.box, f"Answer only one of {options}")]
    if not branches and group.min > 0:
        return branches, [TreeProblem(path, node.box, f"Answer one of {options}")]
    return branches, []


def _occurrences(
    node: SpecNode, value: object, path: TreePath, computed: frozenset[str]
) -> list[TreeProblem]:
    if value is None:
        return [TreeProblem(path, node.box, _missing(node))] if node.min > 0 else []
    if not node.repeats:
        return _value(node, value, path, computed)
    if not isinstance(value, list):
        return [TreeProblem(path, node.box, f"{_sentence(node.label)} must be a list")]
    problems = []
    if len(value) < node.min:
        problems.append(TreeProblem(path, node.box, f"Add at least {node.min}: {node.label}"))
    if node.max is not None and len(value) > node.max:
        problems.append(TreeProblem(path, node.box, f"Add no more than {node.max}: {node.label}"))
    for index, item in enumerate(value):
        problems += _value(node, item, (*path, index), computed)
    return problems


def _value(
    node: SpecNode, value: object, path: TreePath, computed: frozenset[str]
) -> list[TreeProblem]:
    if node.kind == "group":
        return _group(node, value, path, computed)
    message = _scalar_problem(node, value)
    return [] if message is None else [TreeProblem(path, node.box, message)]


def _missing(node: SpecNode) -> str:
    if node.kind in {"yes", "yesno", "enum"}:
        return f"Select {_phrase(node.label)}"
    if node.kind == "group":
        return f"Complete {_phrase(node.label)}"
    return f"Enter {_phrase(node.label)}"


def _scalar_problem(node: SpecNode, value: object) -> str | None:
    if node.kind == "any":
        return f"{_sentence(node.label)} cannot be entered as an answer"
    if not isinstance(value, str):
        return f'{_sentence(node.label)} must be given as text, like "1234"'
    if not value.strip():
        return _missing(node)
    checks = {
        "pounds": _pounds_problem,
        "money": _money_problem,
        "integer": _integer_problem,
        "decimal": _decimal_problem,
        "percent": _percent_problem,
        "date": _date_problem,
        "year": _year_problem,
        "yes": _choice_problem,
        "yesno": _choice_problem,
        "enum": _choice_problem,
        "text": _text_problem,
        "binary": _binary_problem,
    }
    return checks[node.kind](node, value)


def _pounds_problem(node: SpecNode, value: str) -> str | None:
    if not _POUNDS.match(value):
        return f"{_sentence(node.label)} must be a whole number of pounds, like 1234"
    return _bounds_problem(node, Decimal(value), _format_pounds)


def _money_problem(node: SpecNode, value: str) -> str | None:
    if not _MONEY.match(value):
        return f"{_sentence(node.label)} must be an amount in pounds and pence, like 1234.56"
    return _bounds_problem(node, Decimal(value), _format_pounds)


def _integer_problem(node: SpecNode, value: str) -> str | None:
    if not _INTEGER.match(value):
        return f"{_sentence(node.label)} must be a whole number"
    return _pattern_problem(node, value) or _bounds_problem(node, Decimal(value), str)


def _decimal_problem(node: SpecNode, value: str) -> str | None:
    if not _DECIMAL.match(value):
        return f"{_sentence(node.label)} must be a number"
    return _bounds_problem(node, Decimal(value), str)


def _percent_problem(node: SpecNode, value: str) -> str | None:
    if not _PERCENT.match(value):
        return f"{_sentence(node.label)} must be a percentage, like 19 or 26.5"
    return _bounds_problem(node, Decimal(value), lambda bound: f"{bound}%")


def _date_problem(node: SpecNode, value: str) -> str | None:
    try:
        parsed = date.fromisoformat(value) if _ISO_DATE.match(value) else None
    except ValueError:
        parsed = None
    if parsed is None:
        return f"{_sentence(node.label)} must be a real date, like 2025-03-31"
    earliest, latest = node.min_value, node.max_value
    if isinstance(earliest, date) and parsed < earliest:
        return f"{_sentence(node.label)} must be on or after {_format_date(earliest)}"
    if isinstance(latest, date) and parsed > latest:
        return f"{_sentence(node.label)} must be on or before {_format_date(latest)}"
    return None


def _year_problem(node: SpecNode, value: str) -> str | None:
    if not _YEAR.match(value):
        return f"{_sentence(node.label)} must be a year, like 2025"
    return None


def _choice_problem(node: SpecNode, value: str) -> str | None:
    if node.kind == "yes":
        allowed = ("yes",)
    elif node.kind == "yesno":
        allowed = ("yes", "no")
    else:
        allowed = tuple(option.value for option in node.enum or ())
    if value in allowed:
        return None
    if node.kind == "yes":
        return f'{_sentence(node.label)} can only be "yes"; leave it out otherwise'
    if node.kind == "yesno":
        return f"Select yes or no for {_phrase(node.label)}"
    return f"Select {_phrase(node.label)} from the list"


def _text_problem(node: SpecNode, value: str) -> str | None:
    shortest, longest = node.min_length, node.max_length
    too_short = shortest is not None and len(value) < shortest
    too_long = longest is not None and len(value) > longest
    if too_short or too_long:
        if shortest is not None and longest is not None and shortest != longest:
            return f"Enter {_phrase(node.label)}, {shortest} to {longest} characters"
        if shortest is not None and shortest == longest:
            return f"Enter {_phrase(node.label)}, {shortest} characters"
        if longest is not None:
            return f"Enter {_phrase(node.label)} in {longest} characters or fewer"
        return f"Enter {_phrase(node.label)}, at least {shortest} characters"
    return _pattern_problem(node, value)


def _binary_problem(node: SpecNode, value: str) -> str | None:
    try:
        b64decode(value, validate=True)
    except binascii.Error:
        return f"{_sentence(node.label)} must be Base64 encoded"
    return None


def _pattern_problem(node: SpecNode, value: str) -> str | None:
    for pattern in node.patterns:
        if _compiled(pattern).fullmatch(value) is None:
            if _CHARACTER_CLASS.match(pattern):
                return f"{_sentence(node.label)} contains a character that is not allowed"
            return f"{_sentence(node.label)} is not in the right format"
    return None


def _bounds_problem(node: SpecNode, value: Decimal, show: Callable[[Decimal], str]) -> str | None:
    lowest, highest = node.min_value, node.max_value
    if isinstance(lowest, Decimal) and value < lowest:
        return f"{_sentence(node.label)} must be {show(lowest)} or more"
    if isinstance(highest, Decimal) and value > highest:
        return f"{_sentence(node.label)} must be {show(highest)} or less"
    return None


@cache
def _compiled(pattern: str) -> re.Pattern[str]:
    """Compile an XSD pattern; XSD patterns always match the whole value."""
    return re.compile(pattern, re.ASCII)


def _format_pounds(amount: Decimal) -> str:
    return f"£{amount:,}"


def _format_date(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


def _phrase(label: str) -> str:
    """Lower-case a label's first letter to use it mid-sentence, keeping acronyms."""
    if len(label) > 1 and label[1].isupper():
        return label
    return label[:1].lower() + label[1:]


def _sentence(label: str) -> str:
    return label[:1].upper() + label[1:]
