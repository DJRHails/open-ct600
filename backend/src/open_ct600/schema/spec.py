"""Load the generated CT600 schema spec (``ct600-v1.994.json``) as typed, immutable nodes.

The spec is one tree mirroring HMRC's CT600 XSD: a node per element and attribute, each carrying
its box id (when the element is a box on the form), a label, a value kind, cardinality, choice
membership and the XSD's value constraints. ``python -m open_ct600.schema.generate`` writes it.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any, Literal, cast, get_args

SPEC_PATH = Path(__file__).with_name("ct600-v1.994.json")
RETURN_PATH = "/IRenvelope/CompanyTaxReturn"

Kind = Literal[
    "group",
    "any",
    "pounds",
    "money",
    "integer",
    "decimal",
    "percent",
    "date",
    "year",
    "yes",
    "yesno",
    "text",
    "enum",
    "binary",
]
"""How a node's value is entered.

``group`` has child elements; ``any`` holds a document from another namespace (attachments);
``pounds`` is whole pounds, ``money`` pounds and pence, ``yes`` a tick box (only ``"yes"``),
``yesno`` ``"yes"`` or ``"no"``, ``enum`` one of the node's ``enum`` values, ``binary`` Base64.
"""

PageCode = Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P"]
PAGE_CODES: tuple[PageCode, ...] = get_args(PageCode)


@dataclass(frozen=True)
class EnumOption:
    """One allowed value of an ``enum`` node, with HMRC's description of it."""

    value: str
    label: str


@dataclass(frozen=True)
class ChoiceGroup:
    """An ``xsd:choice`` among a group's children.

    Attributes:
        id: The branch names joined by ``|``, e.g. ``"Profits|Losses"``; children in the choice
            carry it as their ``choice``.
        min: 1 if one branch must be given, 0 if the whole choice is optional.
    """

    id: str
    min: int


@dataclass(frozen=True)
class SpecNode:
    """One element (or ``@attribute``) of the CT600 schema.

    Attributes:
        name: Element name, or ``@Name`` for an attribute.
        path: Absolute path from ``/IRenvelope``.
        box: The CT600 box id (``"145"``, ``"A10A"``, ``"C105/C110"``), if the element is a box.
        label: The box description, or the element name in words.
        kind: How the value is entered; see ``Kind``.
        min: Minimum occurrences.
        max: Maximum occurrences; ``None`` means unbounded.
        choice: Id of the parent's ``ChoiceGroup`` this node belongs to, if any.
        branch: Within that choice, the name of the first element of this node's branch. Nodes
            sharing a branch are given together.
        enum: Allowed values of an ``enum`` node.
        patterns: XSD regular expressions the whole value must match (all of them).
        min_length: Minimum length of a text value.
        max_length: Maximum length of a text value.
        min_value: Inclusive lower bound of a numeric value (a ``date`` for dates).
        max_value: Inclusive upper bound of a numeric value (a ``date`` for dates).
        choices: Choice groups among this node's children.
        children: Child elements and attributes, in schema order.
    """

    name: str
    path: str
    box: str | None
    label: str
    kind: Kind
    min: int
    max: int | None
    choice: str | None
    branch: str | None
    enum: tuple[EnumOption, ...] | None
    patterns: tuple[str, ...]
    min_length: int | None
    max_length: int | None
    min_value: Decimal | date | None
    max_value: Decimal | date | None
    choices: tuple[ChoiceGroup, ...]
    children: tuple["SpecNode", ...]

    @property
    def repeats(self) -> bool:
        """Whether the element may occur more than once (a list in element trees)."""
        return self.max is None or self.max > 1

    def child(self, name: str) -> "SpecNode | None":
        """Return the first child called ``name`` (``@Name`` for attributes), if any."""
        return next((child for child in self.children if child.name == name), None)

    def box_parts(self) -> dict[str, "SpecNode"]:
        """The boxes inside a paired box such as ``780/785``, by their own ids.

        The pair is an amount arising and the most available for surrender. HMRC's box map
        gives the pair to the group and nothing to its two elements. Empty for other nodes.
        """
        names = [child.name for child in self.children]
        if self.box is None or "/" not in self.box or names != ["Arising", "SurrenderMaximum"]:
            return {}
        arising, maximum = self.box.split("/")
        return {arising: self.children[0], maximum: self.children[1]}

    def walk(self) -> Iterator["SpecNode"]:
        """Yield this node and all its descendants, depth first in schema order."""
        yield self
        for child in self.children:
            yield from child.walk()

    def to_json(self) -> dict[str, Any]:
        """Return the node in the spec file's JSON form."""
        return {
            "name": self.name,
            "path": self.path,
            "box": self.box,
            "label": self.label,
            "kind": self.kind,
            "min": self.min,
            "max": self.max,
            "choice": self.choice,
            "branch": self.branch,
            "enum": (
                None
                if self.enum is None
                else [{"value": o.value, "label": o.label} for o in self.enum]
            ),
            "patterns": list(self.patterns),
            "minLength": self.min_length,
            "maxLength": self.max_length,
            "minValue": _json_bound(self.min_value),
            "maxValue": _json_bound(self.max_value),
            "choices": [{"id": group.id, "min": group.min} for group in self.choices],
            "children": [child.to_json() for child in self.children],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "SpecNode":
        """Build a node (and its subtree) from the spec file's JSON form."""
        enum = data["enum"]
        return cls(
            name=data["name"],
            path=data["path"],
            box=data["box"],
            label=data["label"],
            kind=data["kind"],
            min=data["min"],
            max=data["max"],
            choice=data["choice"],
            branch=data["branch"],
            enum=None if enum is None else tuple(EnumOption(**option) for option in enum),
            patterns=tuple(data["patterns"]),
            min_length=data["minLength"],
            max_length=data["maxLength"],
            min_value=_bound(data["minValue"]),
            max_value=_bound(data["maxValue"]),
            choices=tuple(ChoiceGroup(**group) for group in data["choices"]),
            children=tuple(cls.from_json(child) for child in data["children"]),
        )


def _json_bound(value: Decimal | date | None) -> int | float | str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return int(value) if value == value.to_integral_value() else float(value)


def _bound(value: int | float | str | None) -> Decimal | date | None:
    """Read a bound: JSON numbers are exact decimals, strings are ISO dates."""
    if value is None:
        return None
    if isinstance(value, str):
        return date.fromisoformat(value)
    return Decimal(str(value))


@dataclass(frozen=True)
class PageDefinition:
    """A supplementary page: its code, root element and title."""

    code: PageCode
    element: str
    title: str
    dormant: bool = False


PAGE_DEFINITIONS: tuple[PageDefinition, ...] = (
    PageDefinition("A", "LoansByCloseCompanies", "Loans to participators by close companies"),
    PageDefinition(
        "B",
        "ControlledForeignCompanies",
        "Controlled foreign companies, foreign permanent establishment exemptions, "
        "hybrid and other mismatches",
    ),
    PageDefinition("C", "GroupAndConsortium", "Group and consortium"),
    PageDefinition("D", "Insurance", "Insurance"),
    PageDefinition("E", "Charity", "Charities and Community Amateur Sports Clubs (CASCs)"),
    PageDefinition("F", "TonnageTax", "Tonnage tax"),
    PageDefinition("G", "NorthernIreland", "Northern Ireland", dormant=True),
    PageDefinition("H", "CrossBorderRoyalties", "Cross-border royalties"),
    PageDefinition("I", "RingFenceTrade", "Supplementary charge in respect of ring fence trades"),
    PageDefinition("J", "TaxAvoidanceSchemes", "Disclosure of tax avoidance schemes"),
    PageDefinition("K", "RestitutionTax", "Restitution tax"),
    PageDefinition("L", "ResearchAndDevelopment", "Research and development"),
    PageDefinition("M", "Freeports", "Freeports and Investment Zones"),
    PageDefinition("N", "ResidentialPropertyDeveloperTax", "Residential Property Developer Tax"),
    PageDefinition("P", "CreativeIndustries", "Creative industries"),
)
"""The 15 supplementary pages, in form order.

CT600G (Northern Ireland) is dormant: no form is published and no Northern Ireland rate is in
force, so HMRC accepts its boxes only for periods ending on or after 1 April 2050.
"""


@dataclass(frozen=True)
class Page:
    """A supplementary page and its subtree of the spec.

    Attributes:
        code: Page letter, ``"A"`` for CT600A.
        element: Root element name under ``CompanyTaxReturn``.
        title: The page's title on the form.
        dormant: Whether the page cannot currently be filed (CT600G).
        node: The page's root node.
    """

    code: PageCode
    element: str
    title: str
    dormant: bool
    node: SpecNode


class Spec:
    """The CT600 schema spec, indexed by path."""

    def __init__(self, root: SpecNode) -> None:
        """Index ``root`` and its descendants by path."""
        self.root = root
        index: dict[str, list[SpecNode]] = {}
        for node in root.walk():
            index.setdefault(node.path, []).append(node)
        self._index = index

    def node(self, path: str) -> SpecNode:
        """Return the node at an absolute path like ``/IRenvelope/CompanyTaxReturn/Turnover``.

        Raises:
            KeyError: No element has that path.
            LookupError: The path names elements in two branches of a choice (only
                ``AttachedFiles`` does); walk the parent's children instead.
        """
        nodes = self._index.get(path)
        if nodes is None:
            raise KeyError(f"No CT600 schema element at {path!r}")
        if len(nodes) > 1:
            raise LookupError(
                f"{path!r} names {len(nodes)} elements in different branches of a choice; "
                "use the parent's children"
            )
        return nodes[0]

    def pages(self) -> tuple[Page, ...]:
        """Return the 15 supplementary pages A to P (including dormant G), in form order."""
        return tuple(
            Page(
                code=definition.code,
                element=definition.element,
                title=definition.title,
                dormant=definition.dormant,
                node=self.node(f"{RETURN_PATH}/{definition.element}"),
            )
            for definition in PAGE_DEFINITIONS
        )

    def page(self, code: PageCode) -> Page:
        """Return one supplementary page by its code."""
        return next(page for page in self.pages() if page.code == code)


@cache
def load_spec() -> Spec:
    """Load the committed spec (once per process)."""
    data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    return Spec(SpecNode.from_json(cast(dict[str, Any], data["root"])))
