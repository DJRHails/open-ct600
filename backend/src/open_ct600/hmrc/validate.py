"""Offline validation of a CT600 return with HMRC's own artefacts: the v1.994 XSD and schematron.

HMRC checks a return against its schema first (errors 4000-4999) and then against the business
rules in its schematron (5004, 5005 and 9xxx). This module runs the same two stages with lxml, so
a user sees HMRC's error codes and messages before submitting.

The schematron's 3,537 diagnostics (codes and English/Welsh messages) make lxml's schematron
compiler take ~18 s, so they are stripped before compiling (0.2 s) and looked up here from the
assert that failed. Its ``exslt`` query binding runs on libxslt: every function it uses
(``date:seconds``, ``date:add``, ``date:difference``, ``date:year``, ``date:month-in-year``,
``date:day-in-month``, ``date:date``, ``math:abs``) is implemented by libexslt.
"""

import re
import threading
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from lxml import etree, isoschematron

from open_ct600.hmrc.xmldoc import CT_NS, GOVTALK_NS, parse_xml
from open_ct600.schema.spec import load_spec

ARTEFACTS = Path(__file__).parent / "artefacts"
_SCH_NS = "http://purl.oclc.org/dsdl/schematron"
_SVRL_NS = "http://purl.oclc.org/dsdl/svrl"
_XMLDSIG_SCHEMA_URL = "http://www.w3.org/TR/2001/PR-xmldsig-core-20010820/xmldsig-core-schema.xsd"

_POSITION = re.compile(
    r"""(?x)
    \[ [0-9]+ \]     # a positional predicate such as [2]
    """
)
_XSL = "{http://www.w3.org/1999/XSL/Transform}"
_PATTERN_MODE = re.compile(
    r"""(?x)
    M [0-9]+          # the XSLT mode the ISO skeleton gives each schematron pattern
    """
)
_ABSOLUTE_CHILD_PATH = re.compile(
    r"""(?x)
    (?: / [A-Za-z]+ : [A-Za-z0-9_]+ )+   # /prefix:Element steps from the root, child axis only
    (?: / @ [A-Za-z0-9_]+ )?             # optionally ending on an attribute
    """
)
_CLARK_NAMESPACE = re.compile(
    r"""(?x)
    \{ [^}]* \}      # the {namespace-uri} prefix of a Clark-notation name in lxml's messages
    """
)

_T = etree.ErrorTypes
_SCHEMA_ERROR_CODES: dict[int, int] = {
    _T.SCHEMAV_CVC_ATTRIBUTE_3: 4000,
    _T.SCHEMAV_CVC_ATTRIBUTE_4: 4000,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_3_1: 4000,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_3_2_1: 4000,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_3_2_2: 4000,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_4: 4001,
    _T.SCHEMAV_CVC_ELT_3_1: 4003,
    _T.SCHEMAV_CVC_DATATYPE_VALID_1_2_1: 4020,
    _T.SCHEMAV_CVC_DATATYPE_VALID_1_2_2: 4020,
    _T.SCHEMAV_CVC_DATATYPE_VALID_1_2_3: 4020,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_2_1: 4051,
    _T.SCHEMAV_CVC_ELT_3_2_1: 4051,
    _T.SCHEMAV_CVC_ELT_5_2_2_1: 4051,
    _T.SCHEMAV_CVC_TYPE_3_1_2: 4051,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_2_2: 4052,
    _T.SCHEMAV_CVC_COMPLEX_TYPE_2_3: 4053,
    _T.SCHEMAV_CVC_ELT_1: 4057,
    _T.SCHEMAV_CVC_ELT_5_2_2_2_1: 4058,
    _T.SCHEMAV_CVC_ELT_5_2_2_2_2: 4058,
    _T.SCHEMAV_ELEMENT_CONTENT: 4065,
    _T.SCHEMAV_CVC_TYPE_3_1_1: 4068,
    _T.SCHEMAV_CVC_ENUMERATION_VALID: 4080,
    _T.SCHEMAV_CVC_FRACTIONDIGITS_VALID: 4081,
    _T.SCHEMAV_CVC_LENGTH_VALID: 4082,
    _T.SCHEMAV_CVC_MINLENGTH_VALID: 4082,
    _T.SCHEMAV_CVC_MAXEXCLUSIVE_VALID: 4083,
    _T.SCHEMAV_CVC_MAXINCLUSIVE_VALID: 4083,
    _T.SCHEMAV_CVC_MAXLENGTH_VALID: 4083,
    _T.SCHEMAV_CVC_MINEXCLUSIVE_VALID: 4084,
    _T.SCHEMAV_CVC_MININCLUSIVE_VALID: 4084,
    _T.SCHEMAV_CVC_PATTERN_VALID: 4085,
    _T.SCHEMAV_CVC_TOTALDIGITS_VALID: 4086,
}
"""libxml2 schema-validity errors → HMRC's codes (``SchemaErrorMessages-v1-994``, by Xerces key)."""
_INCOMPLETE_CONTENT = 4066
_OTHER_SCHEMA_ERROR = 4999

# lxml's compiled XSLT and XMLSchema objects are not documented as safe to share between
# threads, and FastAPI runs sync endpoints on a thread pool.
_LOCK = threading.Lock()


@dataclass(frozen=True)
class Problem:
    """One reason HMRC would reject a return.

    Attributes:
        code: HMRC's error code: 4000-4999 for schema errors, 5004/5005/9xxx for business rules.
        message: HMRC's message for a business rule; libxml2's (naming the element and value)
            for a schema error.
        box: The CT600 box (``"475"``, ``"A80"``...) of the element at fault, when that
            element is a box in the schema spec (``open_ct600.schema``).
        path: The element at fault, such as
            ``/IRenvelope/CompanyTaxReturn/Declaration/Name``; ``[n]`` marks the n-th of
            repeated elements.
    """

    code: int
    message: str
    box: str | None
    path: str | None


def validate_return(document: etree._Element) -> list[Problem]:
    """Validate a CT600 return as HMRC does: schema first, then business rules.

    Business rules run only on a schema-valid return, because the schematron's arithmetic on
    malformed values produces misleading follow-on errors.

    Args:
        document: An ``IRenvelope``, or a whole GovTalk message holding one (whose envelope is
            then validated as well).

    Returns:
        Every problem found; empty when HMRC's schema and rules accept the return.

    Raises:
        ValueError: If ``document`` is neither an IRenvelope nor a GovTalk message holding one.
    """
    message = _as_message(document)
    ir_envelope = message.find(f"{{{GOVTALK_NS}}}Body/{{{CT_NS}}}IRenvelope")
    if ir_envelope is None:
        raise ValueError("The GovTalk message has no CT600 IRenvelope in its Body.")
    with _LOCK:
        problems = _schema_problems(_ct_schema(), etree.ElementTree(_detached(ir_envelope)))
        if message is document:
            problems += _schema_problems(_envelope_schema(), etree.ElementTree(message))
        if not problems:
            problems = _rule_problems(message)
    return problems


def _as_message(document: etree._Element) -> etree._Element:
    if document.tag == f"{{{GOVTALK_NS}}}GovTalkMessage":
        return document
    if document.tag != f"{{{CT_NS}}}IRenvelope":
        raise ValueError(f"Expected a CT600 IRenvelope or GovTalkMessage, got {document.tag!r}.")
    message = etree.Element(f"{{{GOVTALK_NS}}}GovTalkMessage", nsmap={None: GOVTALK_NS})
    details = etree.SubElement(message, f"{{{GOVTALK_NS}}}GovTalkDetails")
    keys = etree.SubElement(details, f"{{{GOVTALK_NS}}}Keys")
    for key in document.iterfind(f"{{{CT_NS}}}IRheader/{{{CT_NS}}}Keys/{{{CT_NS}}}Key"):
        etree.SubElement(keys, f"{{{GOVTALK_NS}}}Key", Type=key.get("Type", "")).text = key.text
    etree.SubElement(message, f"{{{GOVTALK_NS}}}Body").append(_detached(document))
    return message


def _detached(element: etree._Element) -> etree._Element:
    """Copy ``element`` into a document of its own, allowing iXBRL attachments over 10 MB."""
    return parse_xml(etree.tostring(element))


def _schema_problems(schema: etree.XMLSchema, tree: etree._ElementTree) -> list[Problem]:
    if schema.validate(tree):
        return []
    problems = []
    for error in schema.error_log:
        nodes = tree.xpath(error.path) if error.path else []
        element = nodes[0] if isinstance(nodes, list) and nodes else None
        path = _path(element) if isinstance(element, etree._Element) else None
        problems.append(
            Problem(
                code=_schema_error_code(error),
                message=_CLARK_NAMESPACE.sub("", error.message),
                box=_box(path),
                path=path,
            )
        )
    return problems


def _schema_error_code(error: etree._LogEntry) -> int:
    if error.type == _T.SCHEMAV_ELEMENT_CONTENT and "Missing child element" in error.message:
        return _INCOMPLETE_CONTENT
    return _SCHEMA_ERROR_CODES.get(error.type, _OTHER_SCHEMA_ERROR)


def _rule_problems(message: etree._Element) -> list[Problem]:
    rules = _rules()
    report = rules.stylesheet(etree.ElementTree(message))
    problems = []
    for failure in report.getroot().iter(f"{{{_SVRL_NS}}}failed-assert"):
        code, text = rules.diagnostics[failure.get("id", "")]
        nodes = message.getroottree().xpath(failure.get("location", ""))
        node = nodes[0] if isinstance(nodes, list) and nodes else None
        path = _node_path(node)
        problems.append(Problem(code=code, message=text, box=_box(path), path=path))
    return problems


def _node_path(node: object) -> str | None:
    if isinstance(node, etree._Element):
        return _path(node)
    if isinstance(node, etree._ElementUnicodeResult) and node.is_attribute:
        parent = node.getparent()
        return f"{_path(parent)}/@{node.attrname}" if parent is not None else None
    return None


def _path(element: etree._Element) -> str:
    """Return ``/IRenvelope/...`` (or ``/GovTalkMessage/...`` outside the return)."""
    steps = []
    current: etree._Element | None = element
    while current is not None:
        name = etree.QName(current)
        parent = current.getparent()
        siblings = parent.findall(name) if parent is not None else [current]
        position = f"[{siblings.index(current) + 1}]" if len(siblings) > 1 else ""
        steps.append(f"{name.localname}{position}")
        if name.text == f"{{{CT_NS}}}IRenvelope":
            break
        current = parent
    return "/" + "/".join(reversed(steps))


def _box(path: str | None) -> str | None:
    """Return the CT600 box of the element at ``path``, from the schema spec."""
    if path is None:
        return None
    try:
        return load_spec().node(_POSITION.sub("", path)).box
    except LookupError:
        # Outside the return (the GovTalk header), unknown to the schema (the element at fault
        # in a schema error), or in both branches of a choice (AttachedFiles): no single box.
        return None


class _LocalArtefacts(etree.Resolver):
    """Resolve the envelope XSD's xmldsig import to the local copy, never the network."""

    def resolve(self, system_url: str | None, public_id: str | None, context: object):
        """Map the W3C xmldsig schema URL to ``artefacts/xmldsig-core-schema.xsd``."""
        if system_url == _XMLDSIG_SCHEMA_URL:
            return self.resolve_filename(str(ARTEFACTS / "xmldsig-core-schema.xsd"), context)
        return None


def _artefact_parser() -> etree.XMLParser:
    parser = etree.XMLParser(no_network=True, resolve_entities=False, huge_tree=True)
    parser.resolvers.add(_LocalArtefacts())
    return parser


@cache
def _ct_schema() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(ARTEFACTS / "CT-2014-v1-994.xsd", _artefact_parser()))


@cache
def _envelope_schema() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(ARTEFACTS / "envelope-v2-0-HMRC.xsd", _artefact_parser()))


@dataclass(frozen=True)
class _Rules:
    stylesheet: etree.XSLT
    diagnostics: dict[str, tuple[int, str]]


@cache
def _rules() -> _Rules:
    """Compile HMRC's schematron without its diagnostics, keeping them in a lookup table."""
    schematron = etree.parse(ARTEFACTS / "CT-2014-v1-994.sch", _artefact_parser())
    root = schematron.getroot()
    texts = {
        element.get("id", ""): (element.text or "").strip()
        for element in root.iter(f"{{{_SCH_NS}}}diagnostic")
    }
    diagnostics = {}
    for check in root.iter(f"{{{_SCH_NS}}}assert"):
        assert_id = check.get("id", "")
        rule = assert_id.removeprefix("a_")
        if f"errorCode.{rule}" not in texts:
            raise RuntimeError(f"HMRC schematron assert {assert_id!r} has no error code.")
        message = texts.get(f"transactional.en.{rule}") or (check.text or "").strip()
        diagnostics[assert_id] = (int(texts[f"errorCode.{rule}"]), message)
        check.attrib.pop("diagnostics", None)
    for block in root.findall(f"{{{_SCH_NS}}}diagnostics"):
        root.remove(block)
    stylesheet = isoschematron.iso_svrl_for_xslt1(schematron)
    _visit_rule_contexts_only(stylesheet)
    return _Rules(stylesheet=etree.XSLT(stylesheet), diagnostics=diagnostics)


def _visit_rule_contexts_only(stylesheet: etree._ElementTree) -> None:
    """Make each pattern visit only its rule's context nodes, not the whole document.

    The ISO skeleton runs every pattern (620 here) as a walk over the whole document, twice
    (once more for an ``svrl:active-pattern`` report we do not read), so a return's cost grows
    with patterns x nodes: about 18 ms per extra CT600A loan. Every pattern in HMRC's
    schematron has one rule whose context is an absolute child path (no ``//``, no
    predicates, checked here), so selecting that path directly fires exactly the same rules:
    no descendant of a context node can match the same absolute path, which also makes the
    walk below a fired rule pointless.
    """
    templates = stylesheet.getroot().findall(f"{_XSL}template")
    rules = [template for template in templates if _is_rule(template)]
    contexts: dict[str, str] = {}
    for rule in rules:
        mode, match = rule.get("mode", ""), rule.get("match", "")
        if mode in contexts or not _ABSOLUTE_CHILD_PATH.fullmatch(match):
            raise RuntimeError(f"Unexpected schematron rule {match!r} in pattern {mode}.")
        contexts[mode] = match
        walk = rule[-1]
        if walk.tag != f"{_XSL}apply-templates":
            raise RuntimeError(f"Unexpected end {walk.tag} of schematron rule {match!r}.")
        rule.remove(walk)
    for template in templates:
        if template.get("match") == "@*|node()" and _PATTERN_MODE.fullmatch(
            template.get("mode", "")
        ):
            template[:] = []
        elif template.get("match") == "/" and template.get("mode") is None:
            _select_contexts(template, contexts)


def _is_rule(template: etree._Element) -> bool:
    mode, match = template.get("mode", ""), template.get("match", "")
    return bool(_PATTERN_MODE.fullmatch(mode)) and match not in {"text()", "@*|node()"}


def _select_contexts(root_template: etree._Element, contexts: dict[str, str]) -> None:
    for element in list(root_template.iter(f"{{{_SVRL_NS}}}active-pattern")):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)
    for apply in root_template.iter(f"{_XSL}apply-templates"):
        mode = apply.get("mode", "")
        if apply.get("select") == "/" and mode in contexts:
            apply.set("select", contexts[mode])
