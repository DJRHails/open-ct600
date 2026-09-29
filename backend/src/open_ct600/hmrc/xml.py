"""Build the CT600 ``IRenvelope`` (namespace CT/5, schema v1.994) for a computed return.

The return is assembled as an element tree (the JSON convention of ``open_ct600.schema.trees``:
element names as keys, lists for repeating elements, ``@Name`` attributes, string values) and
serialised generically in schema order from CORE's schema spec, which also decides how each
value is written: whole pounds as ``1234.00``, pounds and pence and rates to two places, a tick
as ``yes``. Main-return boxes are placed by their box id's path in the spec; supplementary pages
are the page trees as answered and computed.
"""

import base64
from decimal import Decimal
from functools import cache

from lxml import etree

from open_ct600.ct600 import (
    CT600Box,
    CT600Return,
    Declaration,
    ReturnComputation,
    SignatoryCapacity,
)
from open_ct600.hmrc.xmldoc import CT_NS
from open_ct600.schema.spec import PAGE_DEFINITIONS, RETURN_PATH, SpecNode, load_spec

SCHEMA_VERSION = "2025-v1.994"
ACCOUNTS_FILENAME = "accounts.xhtml"
COMPUTATIONS_FILENAME = "computations.xhtml"

_STATUS = {
    SignatoryCapacity.DIRECTOR: "Director",
    SignatoryCapacity.COMPANY_SECRETARY: "Company secretary",
    SignatoryCapacity.AUTHORISED_AGENT: "Authorised agent",
}
_PAGE_ELEMENT_BY_CODE: dict[str, str] = {
    definition.code: definition.element for definition in PAGE_DEFINITIONS
}
_TWO_PLACES = Decimal("0.01")
_WRITTEN_WHEN_NIL: dict[str, str | None] = {
    "326": "329",  # 9240: an associated companies section (329 ticked) must give box 326.
    "430": None,  # 9146: box 430 must be completed when box 345 or 395 is, even at 0.00.
    # Boxes a supplementary page's box is copied to must be given even at nil; CORE only
    # computes them when the page is filed.
    "200": None,  # 9127: CT600F (box 120) needs box 200.
    "310": None,  # 9506: C10 is copied to box 310.
    "312": None,  # 9550: C130 is copied to box 312.
    "480": None,  # 9428: A80 is copied to box 480.
    "490": None,  # 9465: B30 is copied to box 490.
    "497": None,  # 9865: N285 is copied to box 497.
    "500": None,  # 9434: box 500 totals 490 to 497.
    "527": None,  # 9239: K35 is copied to box 527.
    "528": None,  # 9367: box 527 needs box 528.
    "530": None,  # 9791: L210 is copied to box 530.
    "540": None,  # 9932: P325 is copied to box 540.
    "541": None,  # 9904: P245 is copied to box 541.
    "545": None,  # 9355, 9357: box 545 totals 530 to 541.
    "585": None,  # 9271: I80 is copied to box 585.
    "590": None,  # 9274: I85 is copied to box 590.
    "875": None,  # 9394: L180 is copied to box 875.
    "880": None,  # 9396: L125 is copied to box 880.
}
"""Optional boxes HMRC's rules need written at nil, and the box that must be given for that."""
_TICKED_BY_PAGE = {
    "H": "645",  # 9130: filing CT600H (box 130) means cross-border royalties were paid.
    "J": "65",  # 9134: filing CT600J (box 140) means a notifiable avoidance scheme.
}
"""Main-return tick boxes that filing a supplementary page implies."""

type Tree = dict[str, object]


class ReturnXMLError(ValueError):
    """A computed return that cannot be written as CT600 XML."""


def build_return_xml(
    ct600: CT600Return,
    computation: ReturnComputation,
    *,
    declaration: Declaration,
    accounts_xhtml: str | None,
    computations_xhtml: str | None,
) -> etree._Element:
    """Write a computed return as a CT600 ``IRenvelope``.

    Args:
        ct600: The return's answers.
        computation: Its computation (boxes and completed supplementary page trees).
        declaration: Who declares the return, and in what capacity (boxes 975 and 985).
        accounts_xhtml: The iXBRL accounts, attached base64-encoded when given.
        computations_xhtml: The iXBRL tax computations, attached base64-encoded when given.

    The return always declares accounts and computations for this period (boxes 80A and 80B),
    so HMRC accepts it only with both documents attached; without them the XML is a draft
    for checking and download.

    Returns:
        The ``IRenvelope``, with an empty ``IRmark`` for ``govtalk.build_submission`` to fill.

    Raises:
        ReturnXMLError: If a box or page value does not fit the schema.
    """
    envelope = etree.Element(f"{{{CT_NS}}}IRenvelope", nsmap={None: CT_NS})
    _header(envelope, ct600)
    tree = _return_tree(ct600, computation, declaration)
    node = load_spec().node(RETURN_PATH)
    element = _sub(envelope, "CompanyTaxReturn")
    _serialise(element, node, tree)
    _attach(element, accounts_xhtml=accounts_xhtml, computations_xhtml=computations_xhtml)
    return envelope


def _header(envelope: etree._Element, ct600: CT600Return) -> None:
    header = _sub(envelope, "IRheader")
    _sub(_sub(header, "Keys"), "Key", ct600.company.utr).set("Type", "UTR")
    _sub(header, "PeriodEnd", ct600.period.end.isoformat())
    _sub(header, "DefaultCurrency", "GBP")
    reference = _sub(_sub(_sub(header, "Manifest"), "Contains"), "Reference")
    _sub(reference, "Namespace", CT_NS)
    _sub(reference, "SchemaVersion", SCHEMA_VERSION)
    _sub(reference, "TopElementName", "CompanyTaxReturn")
    _sub(header, "IRmark").set("Type", "generic")
    _sub(header, "Sender", "Company")


def _return_tree(
    ct600: CT600Return, computation: ReturnComputation, declaration: Declaration
) -> Tree:
    company, period = ct600.company, ct600.period
    tree: Tree = {
        "@ReturnType": "new",
        "CompanyInformation": {
            "CompanyName": company.name,
            "RegistrationNumber": company.registration_number,
            "Reference": company.utr,
            "CompanyType": str(company.company_type),
            "PeriodCovered": {"From": period.start.isoformat(), "To": period.end.isoformat()},
        },
        "ReturnInfoSummary": _return_info(computation),
        "Declaration": {
            "AcceptDeclaration": "yes",
            "Name": declaration.name,
            "Status": _STATUS[declaration.capacity],
        },
    }
    given = {box.box for box in computation.boxes if box.value}
    for box in computation.boxes:
        _place_box(tree, box, given)
    for code, page in computation.pages.items():
        tree[_PAGE_ELEMENT_BY_CODE[code]] = page
        if code in _TICKED_BY_PAGE:
            _put(tree, _main_return_boxes()[_TICKED_BY_PAGE[code]], "yes")
    return tree


def _return_info(computation: ReturnComputation) -> Tree:
    """Boxes 80A and 80B (accounts and computations for this period) and the page flags."""
    summary: Tree = {
        "Accounts": {"ThisPeriodAccounts": "yes"},
        "Computations": {"ThisPeriodComputations": "yes"},
    }
    if computation.pages:
        summary["SupplementaryPages"] = {f"CT600{code}": "yes" for code in computation.pages}
    return summary


def _place_box(tree: Tree, box: CT600Box, given: set[str]) -> None:
    """Put a main-return box's value at its element's place in the tree.

    An optional box whose value is nil is left blank, as on the paper form: several such
    elements only accept amounts above zero (box 435, for one), and an unticked tick box has no
    XML form at all. HMRC's rules need a few nil boxes written (``_WRITTEN_WHEN_NIL``).
    """
    node = _main_return_boxes().get(box.box)
    if node is None:
        raise ReturnXMLError(f"Box {box.box} ({box.label}) is not a main-return box in v1.994.")
    if not box.value and node.min == 0:
        if box.box not in _WRITTEN_WHEN_NIL:
            return
        needed = _WRITTEN_WHEN_NIL[box.box]
        if needed is not None and needed not in given:
            return
    _put(tree, node, _box_value(node, box))


def _put(tree: Tree, node: SpecNode, value: str) -> None:
    """Set ``node``'s value in the tree, creating its groups (the first of repeating ones)."""
    steps = node.path.removeprefix(f"{RETURN_PATH}/").split("/")
    group: SpecNode | None = load_spec().node(RETURN_PATH)
    current = tree
    for step in steps[:-1]:
        group = group.child(step) if group is not None else None
        if group is None:
            raise ReturnXMLError(f"No group {step!r} on the way to {node.path}.")
        child = current.setdefault(step, [{}] if group.repeats else {})
        first = child[0] if isinstance(child, list) else child
        if not isinstance(first, dict):
            raise ReturnXMLError(f"{node.path}: {step} already holds a value, not a group.")
        current = first
    current[steps[-1]] = value


def _box_value(node: SpecNode, box: CT600Box) -> str:
    """Write a computed box in the element's form."""
    if node.kind == "yes":
        return "yes"
    if node.kind in {"integer", "year"}:
        return str(int(box.value))
    return _format(node, str(box.value))


def _format(node: SpecNode, value: str) -> str:
    """Write a tree value (``"1234"``, ``"19.5"``) in the element's XML form."""
    match node.kind:
        case "pounds":
            amount = Decimal(value)
            if amount != amount.to_integral_value():
                raise ReturnXMLError(f"Box {node.box} ({node.path}) is whole pounds, got {value}.")
            return f"{amount:.2f}"
        case "money" | "percent":
            return str(Decimal(value).quantize(_TWO_PLACES))
        case _:
            return value


@cache
def _main_return_boxes() -> dict[str, SpecNode]:
    """Main-return boxes by id (page boxes live in the page trees)."""
    boxes: dict[str, SpecNode] = {}
    for node in load_spec().node(RETURN_PATH).children:
        if node.name in _PAGE_ELEMENT_BY_CODE.values() or node.name == "AttachedFiles":
            continue
        for each in node.walk():
            if each.box is not None:
                boxes[each.box] = each
            boxes |= each.box_parts()
    return boxes


def _serialise(element: etree._Element, node: SpecNode, tree: Tree) -> None:
    """Append ``tree``'s children to ``element`` in the order ``node``'s schema gives.

    A required group with nothing in it is still written (``Income`` when every income box is
    nil), so the XML stays schema-valid.
    """
    known = {child.name for child in node.children}
    unknown = set(tree) - known
    if unknown:
        raise ReturnXMLError(f"{node.path} has no elements {sorted(unknown)} in v1.994.")
    for child in node.children:
        value = tree.get(child.name)
        if value is None and child.kind == "group" and child.min > 0 and child.choice is None:
            value = {}
        if value is None or child.name == "AttachedFiles":
            continue
        if child.name.startswith("@"):
            element.set(child.name[1:], _format(child, str(value)))
            continue
        for item in value if isinstance(value, list) else [value]:
            _serialise_one(element, child, item)


def _serialise_one(parent: etree._Element, node: SpecNode, value: object) -> None:
    element = _sub(parent, node.name)
    if isinstance(value, dict):
        _serialise(element, node, value)
    elif isinstance(value, str):
        element.text = _format(node, value)
    else:
        raise ReturnXMLError(f"{node.path} must be a string or group, got {value!r}.")


def _attach(
    return_element: etree._Element, *, accounts_xhtml: str | None, computations_xhtml: str | None
) -> None:
    """Add the iXBRL documents: computations before accounts, as the schema requires."""
    documents = [
        ("Computation", COMPUTATIONS_FILENAME, computations_xhtml),
        ("Accounts", ACCOUNTS_FILENAME, accounts_xhtml),
    ]
    present = [(name, filename, xhtml) for name, filename, xhtml in documents if xhtml]
    if not present:
        return
    submission = _sub(_sub(return_element, "AttachedFiles"), "XBRLsubmission")
    for name, filename, xhtml in present:
        instance = _sub(_sub(submission, name), "Instance")
        document = _sub(instance, "EncodedInlineXBRLDocument")
        document.set("Filename", filename)
        document.text = base64.b64encode(xhtml.encode("utf-8")).decode("ascii")


def _sub(parent: etree._Element, name: str, text: str | None = None) -> etree._Element:
    element = etree.SubElement(parent, f"{{{CT_NS}}}{name}")
    element.text = text
    return element
