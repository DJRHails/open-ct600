"""Read the facts of a filed Inline XBRL document: contexts, numbers and text, by local name.

Companies House filings use every FRC taxonomy year (2022 to 2026 namespaces) and a variety of
software, so concepts, dimensions and members are matched by local name and every number is
turned into a ``Decimal`` from its ix ``format``, ``scale`` and ``sign``.
"""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from lxml import etree

_IX_NAMESPACES = ("http://www.xbrl.org/2013/inlineXBRL", "http://www.xbrl.org/2008/inlineXBRL")
"""Inline XBRL 1.1 and 1.0: both are still filed."""
_FACT_TAGS = tuple(
    f"{{{namespace}}}{name}"
    for namespace in _IX_NAMESPACES
    for name in ("nonFraction", "nonNumeric")
)
_XBRLI = "{http://www.xbrl.org/2003/instance}"
_XBRLDI = "{http://xbrl.org/2006/xbrldi}"

_DOT_DECIMAL = frozenset(
    {"numdotdecimal", "num-dot-decimal", "numcommadot", "numspacedot", "numunitdecimal"}
)
"""Formats with a dot before the decimals, and commas or spaces between thousands."""
_COMMA_DECIMAL = frozenset({"numcommadecimal", "num-comma-decimal", "numdotcomma", "numspacecomma"})
"""Formats with a comma before the decimals, and dots or spaces between thousands."""
_ZERO = frozenset({"zerodash", "fixed-zero", "numdash", "nocontent", "fixed-empty"})
"""Formats that show nil as a dash or nothing at all."""
_TRUE = frozenset({"booleantrue", "fixed-true"})
_FALSE = frozenset({"booleanfalse", "fixed-false"})

_THOUSANDS_DOT = re.compile(
    r"""(?x)
    [,\s]      # thousands separators before a decimal dot: commas, spaces, no-break spaces
    """
)
_THOUSANDS_COMMA = re.compile(
    r"""(?x)
    [.\s]      # thousands separators before a decimal comma: dots, spaces
    """
)


class UnreadableFactError(ValueError):
    """A fact whose value cannot be read in the format it declares."""


@dataclass(frozen=True)
class Context:
    """An XBRL context: its period and its dimension members, by local name.

    Attributes:
        start: First day of a duration.
        end: Last day of a duration.
        instant: The date of an instant.
        members: ``(dimension, member)`` local-name pairs.
    """

    start: date | None
    end: date | None
    instant: date | None
    members: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class Fact:
    """One ``ix:nonFraction`` or ``ix:nonNumeric`` fact.

    Attributes:
        concept: The concept's local name, such as ``TurnoverRevenue``.
        context: Its context.
        numeric: Whether it is an ``ix:nonFraction``.
        text: Its displayed text, whitespace-trimmed.
        format: The local name of its ix format, if any.
        scale: Its power-of-ten scale.
        negative: Whether it has ``sign="-"``.
    """

    concept: str
    context: Context
    numeric: bool
    text: str
    format: str | None
    scale: int
    negative: bool

    def number(self) -> Decimal:
        """The fact's value.

        Raises:
            UnreadableFactError: If the text does not fit its format.
        """
        value = _parse_number(self.text, self.format, self.concept)
        value = value.scaleb(self.scale)
        return -value if self.negative else value

    def boolean(self) -> bool | None:
        """The fact's value as a boolean, or ``None`` if it is neither true nor false."""
        if self.format in _TRUE or self.text.lower() == "true":
            return True
        if self.format in _FALSE or self.text.lower() == "false":
            return False
        return None


def read_facts(root: etree._Element) -> list[Fact]:
    """Every fact in an Inline XBRL document, hidden ones included."""
    contexts = {
        element.get("id", ""): _context(element) for element in root.iter(f"{_XBRLI}context")
    }
    facts = []
    for element in root.iter(*_FACT_TAGS):
        context = contexts.get(element.get("contextRef", ""))
        if context is None:
            continue
        facts.append(
            Fact(
                concept=_local(element.get("name", "")),
                context=context,
                numeric=etree.QName(element).localname == "nonFraction",
                text=" ".join("".join(element.itertext()).split()),
                format=_local(element.get("format", "")) or None,
                scale=int(element.get("scale") or 0),
                negative=element.get("sign") == "-",
            )
        )
    return facts


def _context(element: etree._Element) -> Context:
    period = element.find(f"{_XBRLI}period")
    members = frozenset(
        (_local(member.get("dimension", "")), _local((member.text or "").strip()))
        for member in element.iter(f"{_XBRLDI}explicitMember")
    )
    return Context(
        start=_date(period, "startDate"),
        end=_date(period, "endDate"),
        instant=_date(period, "instant"),
        members=members,
    )


def _date(period: etree._Element | None, name: str) -> date | None:
    text = period.findtext(f"{_XBRLI}{name}") if period is not None else None
    return date.fromisoformat(text.strip()[:10]) if text else None


def _local(qname: str) -> str:
    return qname.rsplit(":", 1)[-1]


def _parse_number(text: str, format_name: str | None, concept: str) -> Decimal:
    if format_name in _ZERO or (format_name is None and text in {"", "-"}):
        return Decimal(0)
    if format_name is None or format_name in _DOT_DECIMAL:
        digits = _THOUSANDS_DOT.sub("", text)
    elif format_name in _COMMA_DECIMAL:
        digits = _THOUSANDS_COMMA.sub("", text).replace(",", ".")
    else:
        raise UnreadableFactError(f"{concept} uses the unsupported format {format_name!r}")
    if digits in {"", "-"}:
        return Decimal(0)
    try:
        return Decimal(digits)
    except InvalidOperation as error:
        raise UnreadableFactError(
            f"{concept} shows {text!r}, which is not a number in {format_name or 'plain'} format"
        ) from error
