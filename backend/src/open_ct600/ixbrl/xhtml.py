"""A small, typed builder for Inline XBRL 1.1 documents in XHTML.

The builder owns everything that makes a document a valid iXBRL instance: namespaces, the
``ix:header`` (hidden facts, schema reference, contexts and units), and the tagging of each
fact with the HMRC-accepted 2011-07-31 transformation registry. Callers build the
human-readable page with :data:`html` and place the fact elements this module returns.

Output is XHTML serialised as ASCII, so any non-ASCII character is written as a numeric
character reference (``&#163;`` for a pound sign). HTML named entities never appear, and the
builder never emits script.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum

from lxml import etree
from lxml.builder import ElementMaker

XHTML = "http://www.w3.org/1999/xhtml"
IX = "http://www.xbrl.org/2013/inlineXBRL"
IXT = "http://www.xbrl.org/inlineXBRL/transformation/2011-07-31"
XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"
LINK = "http://www.xbrl.org/2003/linkbase"
XLINK = "http://www.w3.org/1999/xlink"
ISO4217 = "http://www.xbrl.org/2003/iso4217"

COMPANIES_HOUSE_SCHEME = "http://www.companieshouse.gov.uk/"

_BASE_NAMESPACES = {
    "ix": IX,
    "ixt": IXT,
    "xbrli": XBRLI,
    "xbrldi": XBRLDI,
    "link": LINK,
    "xlink": XLINK,
    "iso4217": ISO4217,
}

_QNAME = re.compile(
    r"""(?x)
    ^(?P<prefix>[A-Za-z_][\w.-]*)   # namespace prefix
    :                               # separator
    (?P<local>[A-Za-z_][\w.-]*)$    # local name
    """
)
_NCNAME = re.compile(
    r"""(?x)
    ^[A-Za-z_]     # starts with a letter or underscore
    [\w.-]*$       # then letters, digits, underscores, dots or hyphens
    """
)
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

html = ElementMaker(namespace=XHTML, nsmap={None: XHTML})
"""Element factory for the human-readable XHTML, e.g. ``html.p("text", {"class": "n"})``."""


class InlineXbrlError(ValueError):
    """Raised when a document would not be valid Inline XBRL."""


@dataclass(frozen=True)
class Taxonomy:
    """A published XBRL taxonomy that documents can be tagged against.

    Attributes:
        name: Human-readable name, e.g. ``"FRC 2026"``.
        schema_ref: The entry point referenced from ``ix:references``.
        namespaces: The prefixes the document may use for concepts and dimensions.
        package: The taxonomy package file name listed in ``specs/ixbrl/taxonomies.tsv``.
        accepted_period_start: HMRC accepts it for accounting periods starting on or after this.
        accepted_period_end: HMRC accepts it for periods ending on or before this; ``None``
            while HMRC has set no end date.
    """

    name: str
    schema_ref: str
    namespaces: Mapping[str, str]
    package: str
    accepted_period_start: date
    accepted_period_end: date | None

    def accepts(self, period_start: date, period_end: date) -> bool:
        """Whether HMRC accepts this taxonomy for an accounting period."""
        if period_start < self.accepted_period_start:
            return False
        return self.accepted_period_end is None or period_end <= self.accepted_period_end


@dataclass(frozen=True)
class Duration:
    """A period of time from ``start`` to ``end`` inclusive."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise InlineXbrlError(f"Duration ends ({self.end}) before it starts ({self.start})")


@dataclass(frozen=True)
class Instant:
    """A point in time, at the end of ``date``."""

    date: date


Period = Duration | Instant


@dataclass(frozen=True)
class ExplicitMember:
    """A domain member of an explicit dimension, e.g. ``bus:Director1``."""

    dimension: str
    member: str


@dataclass(frozen=True)
class TypedMember:
    """A typed dimension value, e.g. a trade's name in ``ct-comp:BusinessNameDimension``."""

    dimension: str
    domain: str
    value: str


Member = ExplicitMember | TypedMember


@dataclass(frozen=True)
class Context:
    """An XBRL context: a period and optional dimension members for the document's entity."""

    id: str
    period: Period
    members: tuple[Member, ...] = ()

    def __post_init__(self) -> None:
        if not _NCNAME.match(self.id):
            raise InlineXbrlError(f"Context id {self.id!r} is not a valid XML name")


class Unit(StrEnum):
    """Units of measure; the value is the unit id used in ``unitRef``."""

    GBP = "GBP"
    PURE = "pure"


_UNIT_MEASURES = {Unit.GBP: "iso4217:GBP", Unit.PURE: "xbrli:pure"}


@dataclass(frozen=True)
class _Measure:
    """How a number is tagged: its unit, accuracy, and the power of ten it is shown in."""

    unit: Unit
    decimals: int
    scale: int


@dataclass(frozen=True)
class _FactKey:
    concept: str
    context: str
    unit: Unit | None


@dataclass
class InlineDocument:
    """An Inline XBRL document under construction.

    Create facts with the ``non_fraction``, ``money``, ``percentage``, ``non_numeric``,
    ``date_fact`` and ``boolean`` methods; place them in the page (or pass them to ``hide``), add
    the page content with ``append``, then call ``serialise``. Contexts and units are declared
    automatically for the facts that use them.

    Attributes:
        taxonomy: The taxonomy the facts are tagged against.
        entity_identifier: The company registration number, used as every context's entity.
        title: The document title.
        stylesheet: CSS embedded in the document head.
    """

    taxonomy: Taxonomy
    entity_identifier: str
    title: str
    stylesheet: str = ""
    _contexts: dict[str, Context] = field(default_factory=dict, init=False)
    _units: set[Unit] = field(default_factory=set, init=False)
    _values: dict[_FactKey, Decimal | str] = field(default_factory=dict, init=False)
    _hidden: list[etree._Element] = field(default_factory=list, init=False)
    _body: list[etree._Element] = field(default_factory=list, init=False)

    def non_fraction(
        self,
        concept: str,
        context: Context,
        value: Decimal | int,
        *,
        unit: Unit,
        decimals: int = 0,
    ) -> etree._Element:
        """Tag a number, shown with thousands separators, or as a dash when zero.

        Negative values are shown without a minus sign and tagged ``sign="-"``; the caller
        decides how to present them (usually in brackets).

        Raises:
            InlineXbrlError: If ``value`` has more decimal places than ``decimals``.
        """
        return self._non_fraction(concept, context, Decimal(value), _Measure(unit, decimals, 0))

    def money(
        self, concept: str, context: Context, value: Decimal | int, *, decimals: int = 0
    ) -> etree._Element:
        """Tag an amount in pounds (``decimals=0``) or pounds and pence (``decimals=2``)."""
        return self.non_fraction(concept, context, value, unit=Unit.GBP, decimals=decimals)

    def percentage(self, concept: str, context: Context, fraction: Decimal) -> etree._Element:
        """Tag a rate given as a fraction (0.19), shown as a percentage (19) with scale -2."""
        shown = (fraction * 100).normalize()
        places = max(0, -int(shown.as_tuple().exponent))
        return self._non_fraction(concept, context, fraction, _Measure(Unit.PURE, places + 2, -2))

    def non_numeric(self, concept: str, context: Context, text: str = "") -> etree._Element:
        """Tag text; an empty ``text`` tags a fact whose meaning is carried by its context."""
        element = self._fact("nonNumeric", concept, context, None, text)
        element.text = text
        return element

    def date_fact(self, concept: str, context: Context, value: date) -> etree._Element:
        """Tag a date, shown as e.g. ``1 April 2025``."""
        shown = f"{value.day} {_MONTHS[value.month - 1]} {value.year}"
        element = self._fact("nonNumeric", concept, context, None, value.isoformat())
        element.set("format", "ixt:datedaymonthyearen")
        element.text = shown
        return element

    def boolean(
        self, concept: str, context: Context, value: bool, *, shown: str | None = None
    ) -> etree._Element:
        """Tag a true/false fact, shown as ``shown`` (default "Yes" or "No")."""
        element = self._fact("nonNumeric", concept, context, None, str(value).lower())
        element.set("format", "ixt:booleantrue" if value else "ixt:booleanfalse")
        element.text = shown if shown is not None else ("Yes" if value else "No")
        return element

    def hide(self, *facts: etree._Element) -> None:
        """Move facts that have no place on the page into ``ix:hidden``."""
        self._hidden.extend(facts)

    def append(self, *elements: etree._Element) -> None:
        """Add content to the end of the page body."""
        self._body.extend(elements)

    def serialise(self) -> str:
        """Render the complete XHTML document.

        Returns:
            The document, starting with an XML declaration, containing only ASCII.
        """
        root = etree.Element(f"{{{XHTML}}}html", nsmap=self._nsmap())
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
        root.append(self._head())
        body = etree.SubElement(root, f"{{{XHTML}}}body")
        body.append(html.div(self._header(), {"style": "display:none"}))
        body.extend(self._body)
        text = etree.tostring(root, encoding="us-ascii", pretty_print=True).decode("ascii")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + text

    def _non_fraction(
        self, concept: str, context: Context, value: Decimal, measure: _Measure
    ) -> etree._Element:
        unit, decimals, scale = measure.unit, measure.decimals, measure.scale
        if value != value.quantize(Decimal(1).scaleb(-decimals)):
            raise InlineXbrlError(
                f"{concept} value {value} has more decimal places than decimals={decimals}"
            )
        element = self._fact("nonFraction", concept, context, unit, value)
        element.set("unitRef", unit.value)
        element.set("decimals", str(decimals))
        if scale:
            element.set("scale", str(scale))
        if value == 0:
            element.set("format", "ixt:zerodash")
            element.text = "-"
            return element
        if value < 0:
            element.set("sign", "-")
        shown = abs(value).scaleb(-scale)
        element.set("format", "ixt:numdotdecimal")
        element.text = f"{shown:,.{max(decimals + scale, 0)}f}"
        return element

    def _fact(
        self, tag: str, concept: str, context: Context, unit: Unit | None, value: Decimal | str
    ) -> etree._Element:
        self._check_qname(concept)
        self._register_context(context)
        if unit is not None:
            self._units.add(unit)
        key = _FactKey(concept, context.id, unit)
        previous = self._values.setdefault(key, value)
        if previous != value:
            raise InlineXbrlError(
                f"{concept} in context {context.id} is tagged twice with different values "
                f"({previous} and {value}); HMRC rejects inconsistent duplicates (3314)"
            )
        element = etree.Element(f"{{{IX}}}{tag}")
        element.set("name", concept)
        element.set("contextRef", context.id)
        return element

    def _register_context(self, context: Context) -> None:
        for member in context.members:
            self._check_qname(member.dimension)
            self._check_qname(
                member.member if isinstance(member, ExplicitMember) else member.domain
            )
        existing = self._contexts.setdefault(context.id, context)
        if existing != context:
            raise InlineXbrlError(
                f"Context id {context.id!r} is used for two different contexts: "
                f"{existing} and {context}"
            )

    def _check_qname(self, qname: str) -> None:
        match = _QNAME.match(qname)
        if match is None:
            raise InlineXbrlError(f"{qname!r} is not a prefixed name like 'core:Equity'")
        if match["prefix"] not in self.taxonomy.namespaces:
            declared = ", ".join(sorted(self.taxonomy.namespaces))
            raise InlineXbrlError(
                f"{qname!r} uses prefix {match['prefix']!r}, which the {self.taxonomy.name} "
                f"taxonomy does not declare (declared: {declared})"
            )

    def _nsmap(self) -> dict[str | None, str]:
        clashes = set(self.taxonomy.namespaces) & set(_BASE_NAMESPACES)
        if clashes:
            raise InlineXbrlError(f"Taxonomy prefixes clash with iXBRL prefixes: {clashes}")
        return {None: XHTML, **_BASE_NAMESPACES, **self.taxonomy.namespaces}

    def _head(self) -> etree._Element:
        return html.head(
            html.meta({"http-equiv": "Content-Type", "content": "text/html; charset=UTF-8"}),
            html.title(self.title),
            html.style(self.stylesheet, {"type": "text/css"}),
        )

    def _header(self) -> etree._Element:
        header = etree.Element(f"{{{IX}}}header")
        if self._hidden:
            etree.SubElement(header, f"{{{IX}}}hidden").extend(self._hidden)
        references = etree.SubElement(header, f"{{{IX}}}references")
        schema_ref = etree.SubElement(references, f"{{{LINK}}}schemaRef")
        schema_ref.set(f"{{{XLINK}}}type", "simple")
        schema_ref.set(f"{{{XLINK}}}href", self.taxonomy.schema_ref)
        resources = etree.SubElement(header, f"{{{IX}}}resources")
        resources.extend(self._context_element(context) for context in self._contexts.values())
        resources.extend(_unit_element(unit) for unit in Unit if unit in self._units)
        return header

    def _context_element(self, context: Context) -> etree._Element:
        element = etree.Element(f"{{{XBRLI}}}context", id=context.id)
        entity = etree.SubElement(element, f"{{{XBRLI}}}entity")
        identifier = etree.SubElement(entity, f"{{{XBRLI}}}identifier")
        identifier.set("scheme", COMPANIES_HOUSE_SCHEME)
        identifier.text = self.entity_identifier
        if context.members:
            segment = etree.SubElement(entity, f"{{{XBRLI}}}segment")
            segment.extend(self._member_element(member) for member in context.members)
        element.append(_period_element(context.period))
        return element

    def _member_element(self, member: Member) -> etree._Element:
        if isinstance(member, ExplicitMember):
            element = etree.Element(f"{{{XBRLDI}}}explicitMember", dimension=member.dimension)
            element.text = member.member
            return element
        element = etree.Element(f"{{{XBRLDI}}}typedMember", dimension=member.dimension)
        prefix, local = member.domain.split(":")
        domain = etree.SubElement(element, f"{{{self.taxonomy.namespaces[prefix]}}}{local}")
        domain.text = member.value
        return element


def _period_element(period: Period) -> etree._Element:
    element = etree.Element(f"{{{XBRLI}}}period")
    if isinstance(period, Instant):
        etree.SubElement(element, f"{{{XBRLI}}}instant").text = period.date.isoformat()
        return element
    etree.SubElement(element, f"{{{XBRLI}}}startDate").text = period.start.isoformat()
    etree.SubElement(element, f"{{{XBRLI}}}endDate").text = period.end.isoformat()
    return element


def _unit_element(unit: Unit) -> etree._Element:
    element = etree.Element(f"{{{XBRLI}}}unit", id=unit.value)
    etree.SubElement(element, f"{{{XBRLI}}}measure").text = _UNIT_MEASURES[unit]
    return element
