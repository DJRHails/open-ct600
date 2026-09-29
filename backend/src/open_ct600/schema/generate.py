"""Generate the CT600 schema spec from HMRC's XSD (v1.994) and box map (v1.995).

Run from ``backend/`` after changing either input::

    uv run python -m open_ct600.schema.generate

The output, ``ct600-v1.994.json``, is committed; a test fails while it is out of date. The walk
starts at ``IRenvelope`` and resolves named types, so every node has an absolute path. Box ids
come from the box map, which keys rows either by absolute path or by path within a named type
(``[CTA]/LoansInformation/Loan/Name``). Constructs the v1.994 schema does not use raise
``SchemaError`` rather than being skipped, so a new schema version cannot be half-understood.

Two deliberate omissions: the optional ``Currency`` attribute of monetary amounts (the service
files in sterling, HMRC's default), and the content of ``xsd:any`` wildcards (embedded iXBRL
documents), whose element gets kind ``any``.
"""

import csv
import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from lxml import etree

from open_ct600.schema.spec import PAGE_DEFINITIONS, RETURN_PATH, SPEC_PATH

REPO_ROOT = Path(__file__).resolve().parents[4]
XSD_PATH = REPO_ROOT / "specs/hmrc/ct600-v1.994/CT-2014-v1-994.xsd"
BOX_MAP_PATH = REPO_ROOT / "specs/hmrc/box-map-v1.995.tsv"
ROOT_ELEMENT = "IRenvelope"

_XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
_XS = f"{{{_XS_NAMESPACE}}}"
_XS_PREFIX = "xsd:"
_TARGET_PREFIX = "ct:"

_BOX_ID = re.compile(
    r"""(?x)
    ^
    (?P<page>[A-P])?     # supplementary page letter; absent for main return boxes
    [1-9][0-9]*          # box number, never zero-padded (internal ids like N095 are)
    (?:\.[0-9]+)?        # sub-box, like K15.1
    [A-Z]?               # column or part, like A10A
    [a-z0-9]?            # sub-part, like H5Ea or I145C1
    $
    """
)
_WORD = re.compile(
    r"""(?x)
    [A-Z]+(?=[A-Z][a-z])  # acronym followed by a capitalised word: CFC in CFCTax
    | [A-Z]?[a-z]+        # a word, capitalised or not
    | [A-Z]+              # a trailing acronym
    | [0-9]+              # digits
    """
)

_PAGE_ELEMENTS = {definition.element: definition.code for definition in PAGE_DEFINITIONS}
_POUNDS_TYPES = {
    "CT_IRnonNegativeWholeUnitsMonetaryType",
    "CT_IRnonNegativeNonZeroWholeUnitsMonetaryType",
}
_MONEY_TYPE_MARKERS = ("Monetary", "PoundPence")
_CURRENCY_TYPE = f"{_TARGET_PREFIX}CT_ISOcurrencyType"
_BUILTIN_KINDS = {
    "date": "date",
    "gYear": "year",
    "integer": "integer",
    "nonNegativeInteger": "integer",
    "string": "text",
    "anyURI": "text",
    "NCName": "text",
    "base64Binary": "binary",
}
_PATTERN_KINDS = {"text", "integer"}
"""Kinds whose XSD patterns constrain what users enter. For the others the patterns only fix
the XML lexical form (``1234.00``, ``2024-03-31``), which the XML writer produces."""
_DATE_KINDS = {"date", "year"}
_STEP = {"pounds": Decimal(1), "integer": Decimal(1)}
_PENNY = Decimal("0.01")
_PERCENT_MAX = Decimal(100)
_FACETS = {
    "enumeration",
    "pattern",
    "length",
    "minLength",
    "maxLength",
    "minInclusive",
    "maxInclusive",
    "minExclusive",
    "maxExclusive",
    "annotation",
    "simpleType",
}

Occurs = tuple[int, int | None]


class SchemaError(ValueError):
    """The XSD uses a construct the generator does not understand."""


@dataclass(frozen=True)
class _Bound:
    value: str
    exclusive: bool


@dataclass(frozen=True)
class _Simple:
    """A resolved simple type: its built-in base, derivation chain and merged facets."""

    builtin: str
    named: tuple[str, ...] = ()
    enum: tuple[tuple[str, str], ...] | None = None
    patterns: tuple[str, ...] = ()
    min_length: int | None = None
    max_length: int | None = None
    lower: _Bound | None = None
    upper: _Bound | None = None
    attributes: tuple[etree._Element, ...] = ()


@dataclass(frozen=True)
class _Context:
    """Where the walk is: the path, enclosing box map anchors, and supplementary page.

    An anchor ``(prefix, path)`` lets the box map name a descendant at ``path + rest`` as
    ``prefix + rest``: ``[CTA]/LoansInformation`` or ``/IRheader/Keys``.
    """

    path: str
    anchors: tuple[tuple[str, str], ...]
    page: str | None


@dataclass(frozen=True)
class _Node:
    """An element or attribute being built."""

    name: str
    parent: _Context
    context: _Context
    occurs: Occurs
    choice: str | None = None
    branch: str | None = None

    def anchored(self, prefix: str) -> "_Node":
        anchors = (*self.context.anchors, (prefix, self.context.path))
        return replace(self, context=replace(self.context, anchors=anchors))


def _attribute(element: etree._Element, name: str) -> str:
    value = element.get(name)
    if value is None:
        where = element.get("name") or etree.QName(element).localname
        raise SchemaError(f"xsd:{etree.QName(element).localname} {where} has no {name}")
    return value


def _local(qname: str, prefix: str) -> str:
    if not qname.startswith(prefix):
        raise SchemaError(f"Expected a {prefix} type, got {qname!r}")
    return qname.removeprefix(prefix)


def _children(element: etree._Element, *names: str) -> list[etree._Element]:
    wanted = {_XS + name for name in names}
    return [child for child in element if child.tag in wanted]


def _only(element: etree._Element, name: str) -> etree._Element:
    found = _children(element, name)
    if len(found) != 1:
        where = element.get("name") or etree.QName(element).localname
        raise SchemaError(f"Expected exactly one xsd:{name} in {where}, found {len(found)}")
    return found[0]


def _occurs(particle: etree._Element) -> Occurs:
    maximum = particle.get("maxOccurs", "1")
    return int(particle.get("minOccurs", "1")), None if maximum == "unbounded" else int(maximum)


def _documentation(element: etree._Element) -> str | None:
    texts = element.xpath(
        "xsd:annotation/xsd:documentation/text()", namespaces={"xsd": _XS_NAMESPACE}
    )
    words = " ".join(str(text) for text in texts).split()
    return " ".join(words) or None


def humanise(name: str) -> str:
    """Turn an element name into a sentence-case label: ``CFCTax`` → ``CFC tax``.

    Only elements the box map does not describe use this (mostly containers). HMRC also
    runs acronyms into lower-case words (``IRenvelope``), which cannot be told apart from
    camel case without a dictionary; those come out as ``I renvelope``.
    """
    words = _WORD.findall(name.removeprefix("@"))
    if not words:
        raise SchemaError(f"Cannot make a label from element name {name!r}")
    head, *rest = words
    tail = [word if word.isupper() else word.lower() for word in rest]
    return " ".join([head[0].upper() + head[1:], *tail])


def box_id(raw: str, page: str | None) -> str | None:
    """Return the box id from a box map cell if it names a form box on ``page``.

    The box map also carries internal ids (``[N095]``, ``[LOANSINFORMATION]``) for elements
    that are not boxes; these return ``None``. A box on a supplementary page starts with the
    page letter, and main return boxes have none.

    Args:
        raw: The cell, like ``[A10A]`` or ``[C105/C110]``.
        page: The page the element belongs to, or ``None`` for the main return.
    """
    identifier = raw.strip().removeprefix("[").removesuffix("]")
    matches = [_BOX_ID.match(part) for part in identifier.split("/")]
    if not identifier or any(match is None or match["page"] != page for match in matches):
        return None
    return identifier


@dataclass(frozen=True)
class BoxRow:
    """One row of the box map."""

    path: str
    box: str
    description: str


def load_box_map(path: Path) -> list[BoxRow]:
    """Read the box map's rows, in schema order."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        return [BoxRow(row["path"], row["box_id"], row["description"].strip()) for row in reader]


class BoxMap:
    """Box map rows indexed by path.

    Where a path appears twice (an element in two branches of a choice), the first row wins;
    both rows carry the same box id.
    """

    def __init__(self, rows: Iterable[BoxRow]) -> None:
        """Index ``rows``, which are in schema order."""
        self._rows: dict[str, BoxRow] = {}
        for row in rows:
            self._rows.setdefault(row.path, row)

    def match(self, keys: list[str]) -> BoxRow | None:
        """Return the row for an element known by ``keys``, most specific key first."""
        return next((self._rows[key] for key in keys if key in self._rows), None)


def _assign_boxes(root: dict[str, Any], rows: list[BoxRow]) -> None:
    """Fill in each node's box and label, consuming its private lookup keys."""
    box_map = BoxMap(rows)
    for node in iter_nodes(root):
        keys, page = node.pop("_keys"), node.pop("_page")
        row = box_map.match(keys)
        node["box"] = None if row is None else box_id(row.box, page)
        node["label"] = row.description if row is not None and row.description else None
        node["label"] = node["label"] or humanise(node["name"])


class _Generator:
    def __init__(self, schema: etree._ElementTree) -> None:
        root = schema.getroot()
        self._elements = {_attribute(el, "name"): el for el in _children(root, "element")}
        self._complex = {_attribute(el, "name"): el for el in _children(root, "complexType")}
        self._simple = {_attribute(el, "name"): el for el in _children(root, "simpleType")}
        self._stack: list[str] = []

    def generate(self) -> dict[str, Any]:
        top = self._elements[ROOT_ELEMENT]
        return self._element(top, _Context(path="", anchors=(), page=None))

    # Simple types ------------------------------------------------------------------------

    def _named_simple(self, qname: str) -> _Simple:
        if qname.startswith(_XS_PREFIX):
            return _Simple(builtin=_local(qname, _XS_PREFIX))
        name = _local(qname, _TARGET_PREFIX)
        if name in self._simple:
            resolved = self._restriction(_only(self._simple[name], "restriction"))
        elif name in self._complex:
            resolved = self._simple_content(_only(self._complex[name], "simpleContent"))
        else:
            raise SchemaError(f"Unknown type {qname!r}")
        return replace(resolved, named=(name, *resolved.named))

    def _inline_simple(self, simple_type: etree._Element) -> _Simple:
        return self._restriction(_only(simple_type, "restriction"))

    def _simple_content(self, content: etree._Element) -> _Simple:
        extensions = _children(content, "extension")
        if not extensions:
            return self._restriction(_only(content, "restriction"))
        (extension,) = extensions
        _reject_unknown(extension, "attribute")
        base = self._named_simple(_attribute(extension, "base"))
        return replace(base, attributes=(*base.attributes, *_children(extension, "attribute")))

    def _restriction(self, restriction: etree._Element) -> _Simple:
        base_name = restriction.get("base")
        if base_name is None:
            base = self._inline_simple(_only(restriction, "simpleType"))
        else:
            base = self._named_simple(base_name)
        return _apply_facets(base, restriction)

    # Elements ----------------------------------------------------------------------------

    def _element(
        self,
        declaration: etree._Element,
        parent: _Context,
        choice: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        occurs = _occurs(declaration)
        reference = declaration.get("ref")
        if reference is not None:
            declaration = self._elements[_local(reference, _TARGET_PREFIX)]
        name = _attribute(declaration, "name")
        path = f"{parent.path}/{name}"
        page = _PAGE_ELEMENTS.get(name) if parent.path == RETURN_PATH else parent.page
        context = _Context(path=path, anchors=parent.anchors, page=page)
        node = _Node(name, parent, context, occurs, choice, branch)
        if reference is not None:
            node = node.anchored(f"/{name}")
        type_name = declaration.get("type")
        if type_name is not None:
            return self._typed(node, type_name)
        return self._inline(node, declaration)

    def _typed(self, node: _Node, type_name: str) -> dict[str, Any]:
        if not type_name.startswith(_TARGET_PREFIX):
            return self._scalar(node, self._named_simple(type_name))
        local = _local(type_name, _TARGET_PREFIX)
        node = node.anchored(f"[{local}]")
        definition = self._complex.get(local)
        if definition is None or _children(definition, "simpleContent"):
            return self._scalar(node, self._named_simple(type_name))
        if local in self._stack:
            raise SchemaError(f"{node.context.path}: recursive type {local}")
        self._stack.append(local)
        try:
            return self._group(node, definition)
        finally:
            self._stack.pop()

    def _inline(self, node: _Node, declaration: etree._Element) -> dict[str, Any]:
        inline = _children(declaration, "complexType", "simpleType")
        if len(inline) != 1:
            raise SchemaError(f"{node.context.path}: expected a type attribute or one inline type")
        (definition,) = inline
        if definition.tag == _XS + "simpleType":
            return self._scalar(node, self._inline_simple(definition))
        content = _children(definition, "simpleContent")
        if content:
            return self._scalar(node, self._simple_content(content[0]))
        return self._group(node, definition)

    def _group(self, node: _Node, definition: etree._Element) -> dict[str, Any]:
        _reject_unknown(definition, "sequence", "choice", "attribute", "anyAttribute")
        children: list[dict[str, Any]] = []
        choices: list[dict[str, Any]] = []
        wildcard = False
        for particle in _children(definition, "sequence", "choice"):
            if particle.tag == _XS + "choice":
                nested, nested_choices = self._choice(particle, node.context)
            else:
                nested, nested_choices, sequence_wildcard = self._sequence(particle, node.context)
                wildcard = wildcard or sequence_wildcard
            children += nested
            choices += nested_choices
        children += self._attributes(_children(definition, "attribute"), node.context)
        kind = "any" if wildcard else "group"
        return self._build(node, kind, children, choices=choices)

    def _sequence(
        self, sequence: etree._Element, context: _Context
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
        if _occurs(sequence) != (1, 1):
            raise SchemaError(f"{context.path}: repeating or optional sequences are unsupported")
        children: list[dict[str, Any]] = []
        choices: list[dict[str, Any]] = []
        wildcard = False
        for item in sequence:
            if item.tag == _XS + "element":
                children.append(self._element(item, context))
            elif item.tag == _XS + "choice":
                nested, nested_choices = self._choice(item, context)
                children += nested
                choices += nested_choices
            elif item.tag == _XS + "any":
                wildcard = True
            else:
                raise SchemaError(f"{context.path}: unsupported sequence item {item.tag}")
        return children, choices, wildcard

    def _choice(
        self, choice: etree._Element, context: _Context
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        minimum, maximum = _occurs(choice)
        if maximum != 1:
            raise SchemaError(f"{context.path}: repeating choices are unsupported")
        branches = [_branch_elements(branch, context.path) for branch in choice]
        group_id = "|".join(_particle_name(branch[0]) for branch in branches)
        children = []
        for branch in branches:
            branch_name = _particle_name(branch[0])
            children += [self._element(el, context, group_id, branch_name) for el in branch]
        return children, [{"id": group_id, "min": minimum}]

    def _attributes(
        self, attributes: Iterable[etree._Element], context: _Context
    ) -> list[dict[str, Any]]:
        nodes = []
        for attribute in attributes:
            type_name = attribute.get("type")
            if type_name == _CURRENCY_TYPE:
                continue
            name = "@" + _attribute(attribute, "name")
            simple = (
                self._named_simple(type_name)
                if type_name is not None
                else self._inline_simple(_only(attribute, "simpleType"))
            )
            required = int(attribute.get("use", "optional") == "required")
            attribute_context = replace(context, path=f"{context.path}/{name}")
            nodes.append(
                self._scalar(_Node(name, context, attribute_context, (required, 1)), simple)
            )
        return nodes

    def _scalar(self, node: _Node, simple: _Simple) -> dict[str, Any]:
        kind = _kind(simple)
        children = self._attributes(simple.attributes, node.context)
        return self._build(node, kind, children, constraints=_constraints(simple, kind))

    def _build(
        self,
        node: _Node,
        kind: str,
        children: list[dict[str, Any]],
        *,
        choices: list[dict[str, Any]] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        found = constraints or {}
        minimum, maximum = node.occurs
        context = node.context
        # Box map keys: the absolute path, then paths within enclosing named types from the
        # outermost in, so ``[CTI]/…/Profits`` (a page box) beats the generic
        # ``[CT_ProfitsTaxStructure]/Profits``.
        keys = [context.path]
        keys += [prefix + context.path[len(start) :] for prefix, start in context.anchors]
        return {
            "name": node.name,
            "path": context.path,
            "box": None,
            "label": None,
            # A page root is a main return element; only its descendants are on the page.
            "_keys": keys,
            "_page": node.parent.page,
            "kind": kind,
            "min": minimum,
            "max": maximum,
            "choice": node.choice,
            "branch": node.branch,
            "enum": found.get("enum"),
            "patterns": found.get("patterns", []),
            "minLength": found.get("minLength"),
            "maxLength": found.get("maxLength"),
            "minValue": found.get("minValue"),
            "maxValue": found.get("maxValue"),
            "choices": choices or [],
            "children": children,
        }


def _branch_elements(branch: etree._Element, path: str) -> list[etree._Element]:
    if branch.tag == _XS + "element":
        return [branch]
    if branch.tag == _XS + "sequence" and all(item.tag == _XS + "element" for item in branch):
        return list(branch)
    raise SchemaError(f"{path}: choice branches must be elements or sequences of elements")


def _particle_name(element: etree._Element) -> str:
    name = element.get("name")
    return name if name is not None else _local(_attribute(element, "ref"), _TARGET_PREFIX)


def _reject_unknown(element: etree._Element, *allowed: str) -> None:
    known = {_XS + name for name in (*allowed, "annotation")}
    unknown = [child.tag for child in element if child.tag not in known]
    if unknown:
        raise SchemaError(f"Unsupported XSD constructs {unknown} in {element.get('name')}")


def _apply_facets(base: _Simple, restriction: etree._Element) -> _Simple:
    """Narrow ``base`` by a restriction's facets; a derived facet replaces the base's.

    Patterns are the exception: XSD requires a value to match a pattern from every derivation
    step, so each step's pattern is kept (alternatives within one step are joined).
    """
    values: dict[str, list[etree._Element]] = {}
    for child in restriction:
        local = etree.QName(child).localname
        if local not in _FACETS:
            raise SchemaError(f"Unsupported facet xsd:{local} (base {restriction.get('base')})")
        values.setdefault(local, []).append(child)
    values.pop("annotation", None)
    values.pop("simpleType", None)
    result = base
    if "enumeration" in values:
        options = [_attribute(el, "value") for el in values["enumeration"]]
        labels = [_documentation(el) for el in values["enumeration"]]
        enum = tuple((value, label or value) for value, label in zip(options, labels, strict=True))
        result = replace(result, enum=enum)
    if "pattern" in values:
        alternatives = [_attribute(el, "value") for el in values["pattern"]]
        step = "|".join(f"(?:{pattern})" for pattern in alternatives)
        own = step if len(alternatives) > 1 else alternatives[0]
        result = replace(result, patterns=(*result.patterns, own))
    first = {name: _attribute(els[0], "value") for name, els in values.items()}
    return _apply_bounds(result, first)


def _apply_bounds(simple: _Simple, first: dict[str, str]) -> _Simple:
    length = first.get("length")
    min_length = first.get("minLength", length)
    max_length = first.get("maxLength", length)
    lower = _bound(first.get("minInclusive"), first.get("minExclusive"))
    upper = _bound(first.get("maxInclusive"), first.get("maxExclusive"))
    return replace(
        simple,
        min_length=simple.min_length if min_length is None else int(min_length),
        max_length=simple.max_length if max_length is None else int(max_length),
        lower=lower or simple.lower,
        upper=upper or simple.upper,
    )


def _bound(inclusive: str | None, exclusive: str | None) -> _Bound | None:
    if inclusive is not None:
        return _Bound(inclusive, exclusive=False)
    if exclusive is not None:
        return _Bound(exclusive, exclusive=True)
    return None


def _kind(simple: _Simple) -> str:
    named = set(simple.named)
    if "CT_YesType" in named:
        return "yes"
    if "YesNoType" in named:
        return "yesno"
    if simple.enum is not None:
        return "enum"
    if simple.builtin == "decimal":
        return _decimal_kind(simple)
    if simple.builtin not in _BUILTIN_KINDS:
        raise SchemaError(f"Unsupported built-in type xsd:{simple.builtin} ({simple.named})")
    return _BUILTIN_KINDS[simple.builtin]


def _decimal_kind(simple: _Simple) -> str:
    """Whole pounds, pounds and pence, a percentage (at most 100) or another decimal."""
    if set(simple.named) & _POUNDS_TYPES:
        return "pounds"
    if any(marker in name for name in simple.named for marker in _MONEY_TYPE_MARKERS):
        return "money"
    at_most_100 = simple.upper is not None and Decimal(simple.upper.value) == _PERCENT_MAX
    return "percent" if at_most_100 else "decimal"


def _inclusive(bound: _Bound | None, kind: str, direction: int) -> int | Decimal | str | None:
    """Return a bound as an inclusive JSON value: a number, or an ISO date for dates.

    An exclusive numeric bound becomes the nearest inclusive one at the kind's precision
    (``> 0`` is ``>= 1`` for whole pounds and ``>= 0.01`` for money).
    """
    if bound is None:
        return None
    if kind in _DATE_KINDS:
        if bound.exclusive:
            raise SchemaError(f"Exclusive {kind} bounds are unsupported ({bound.value})")
        return bound.value
    value = Decimal(bound.value)
    if bound.exclusive:
        value += direction * _STEP.get(kind, _PENNY)
    return int(value) if value == value.to_integral_value() else value.normalize()


def _constraints(simple: _Simple, kind: str) -> dict[str, Any]:
    enum = None
    if kind == "enum" and simple.enum is not None:
        enum = [{"value": value, "label": label} for value, label in simple.enum]
    return {
        "enum": enum,
        "patterns": list(simple.patterns) if kind in _PATTERN_KINDS else [],
        "minLength": simple.min_length if kind == "text" else None,
        "maxLength": simple.max_length if kind == "text" else None,
        "minValue": _inclusive(simple.lower, kind, 1),
        "maxValue": _inclusive(simple.upper, kind, -1),
    }


def generate(xsd_path: Path = XSD_PATH, box_map_path: Path = BOX_MAP_PATH) -> dict[str, Any]:
    """Build the spec document from the XSD and box map.

    Args:
        xsd_path: HMRC's CT600 XSD.
        box_map_path: The box map TSV (box id, path, cardinality, description).

    Returns:
        The spec as JSON-ready data: ``{"schemaVersion", "boxMap", "root"}``.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    schema = etree.parse(str(xsd_path), parser)
    root = _Generator(schema).generate()
    _assign_boxes(root, load_box_map(box_map_path))
    return {"schemaVersion": "1.994", "boxMap": "1.995", "root": root}


def render(spec: dict[str, Any]) -> str:
    """Serialise the spec deterministically (schema order, one-space indent)."""
    return json.dumps(spec, indent=1, ensure_ascii=False, default=_encode_decimal) + "\n"


def _encode_decimal(value: object) -> float:
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot serialise {type(value).__name__} in the schema spec")


def iter_nodes(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield a JSON node and its descendants."""
    yield node
    for child in node["children"]:
        yield from iter_nodes(child)


def main() -> None:
    """Regenerate ``ct600-v1.994.json`` next to the spec loader."""
    spec = generate()
    SPEC_PATH.write_text(render(spec), encoding="utf-8")
    nodes = list(iter_nodes(spec["root"]))
    boxes = sum(1 for node in nodes if node["box"] is not None)
    print(f"Wrote {SPEC_PATH.name}: {len(nodes)} nodes, {boxes} with box ids")


if __name__ == "__main__":
    main()
